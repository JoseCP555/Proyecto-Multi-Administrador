"""Servicio central de notificaciones reales.

Una notificación es una fila persistente por usuario. Nace de dos fuentes:

1. **Hechos del sistema** (`notificar()`): se llama desde los routers cuando
   alguien crea un evento, registra un pago, sube un documento, reporta un
   mantenimiento, etc. Llega a todos los usuarios que pueden ver ese módulo
   en ese conjunto.
2. **Recordatorios calculados** (`sincronizar_recordatorios()`): moras,
   vencimientos próximos, eventos de los próximos 7 días y mantenimientos
   críticos sin resolver. Se generan de forma perezosa al consultar la
   campana, con `referencia` estable para no duplicarlos.

Cada aviso se entrega (si el usuario lo permite) por **correo** y por
**Web Push**, y se puede marcar como leído o descartar desde la interfaz.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.conjunto_ctx import conjuntos_del_usuario, ve_todos_los_conjuntos
from app.correo_notificaciones import canal_habilitado, enviar_correo_notificacion
from app.deps import usuario_tiene_permiso
from app.email_config import mail_configurado
from app.push import configurado as push_configurado
from app.push import enviar_push

logger = logging.getLogger(__name__)

# Permiso necesario para ver cada tipo. `None` = visible para todos.
PERMISO_POR_TIPO: dict[str, str | None] = {
    "mora": "finanzas.ver",
    "proximo": "finanzas.ver",
    "pago": "finanzas.ver",
    "evento": "eventos.ver",
    "mantenimiento": "mantenimiento.ver",
    "documento": "documentos.ver",
    "residente": "residentes.ver",
    "propiedad": "propiedades.ver",
    "usuario": None,
    "conjunto": "conjuntos.ver",
    "sistema": None,
    "prueba": None,
}

URL_POR_TIPO: dict[str, str] = {
    "mora": "/dashboard/finanzas",
    "proximo": "/dashboard/finanzas",
    "pago": "/dashboard/finanzas",
    "evento": "/dashboard/eventos",
    "mantenimiento": "/dashboard/mantenimiento",
    "documento": "/dashboard/documentos",
    "residente": "/dashboard/residentes",
    "propiedad": "/dashboard/propiedades",
    "usuario": "/dashboard/usuarios",
    "conjunto": "/dashboard",
    "sistema": "/dashboard/inicio",
    "prueba": "/dashboard/inicio",
}

# Hechos discretos que merecen correo (los recordatorios diarios no, para
# no inundar la bandeja de entrada; los de severidad alta sí lo envían).
TIPOS_CON_CORREO = {
    "evento", "documento", "mantenimiento", "pago",
    "usuario", "sistema", "prueba",
}

# Throttle perezoso del generador de recordatorios (por proceso).
_ultima_sinc: dict[int, datetime] = {}
VENTANA_SINC = timedelta(seconds=30)


def permiso_para(tipo: str) -> str | None:
    return PERMISO_POR_TIPO.get(tipo)


def url_para(tipo: str, url: str | None = None) -> str:
    return url or URL_POR_TIPO.get(tipo, "/dashboard/inicio")


def _money(v) -> str:
    return f"${float(v or 0):,.0f}".replace(",", ".")


# ---------------------------------------------------------------------------
# Destinatarios
# ---------------------------------------------------------------------------
def destinatarios(
    db: Session,
    id_conjunto: int | None,
    tipo: str,
    excluir_usuario_id: int | None = None,
) -> list[models.Usuario]:
    """Usuarios activos que pueden ver este tipo de aviso en ese conjunto."""
    permiso = permiso_para(tipo)
    usuarios = db.query(models.Usuario).filter(models.Usuario.activo.is_(True)).all()

    asignados: set[int] = set()
    if id_conjunto is not None:
        asignados = {
            fila[0]
            for fila in db.query(models.UsuarioConjunto.usuario_id)
            .filter(models.UsuarioConjunto.conjunto_id == id_conjunto)
            .all()
        }

    resultado = []
    for u in usuarios:
        if excluir_usuario_id is not None and u.id == excluir_usuario_id:
            continue
        if permiso and not usuario_tiene_permiso(db, u, permiso):
            continue
        if id_conjunto is not None and not ve_todos_los_conjuntos(db, u):
            propio = getattr(u, "id_conjunto", None) or getattr(u, "id_copropiedad", None)
            if u.id not in asignados and propio != id_conjunto:
                continue
        resultado.append(u)
    return resultado


def _insertar(
    db: Session,
    usuario: models.Usuario,
    *,
    tipo: str,
    titulo: str,
    mensaje: str,
    referencia: str,
    severidad: str = "media",
    url: str | None = None,
    id_conjunto: int | None = None,
    fecha: date | None = None,
) -> models.Notificacion | None:
    """Inserta un aviso sin duplicados. Devuelve None si ya existía."""
    existe = (
        db.query(models.Notificacion.id)
        .filter(
            models.Notificacion.usuario_id == usuario.id,
            models.Notificacion.referencia == referencia,
        )
        .first()
    )
    if existe:
        return None

    aviso = models.Notificacion(
        usuario_id=usuario.id,
        id_conjunto=id_conjunto,
        tipo=tipo,
        severidad=severidad,
        titulo=titulo[:200],
        mensaje=mensaje,
        url=url_para(tipo, url),
        fecha=fecha,
        referencia=referencia[:160],
        leida=False,
        descartada=False,
        enviada_correo=False,
        enviada_push=False,
        fecha_creacion=datetime.utcnow(),
    )
    try:
        # Savepoint: si otro request insertó la misma referencia, solo se
        # descarta este INSERT y no el resto de la transacción.
        with db.begin_nested():
            db.add(aviso)
            db.flush()
    except IntegrityError:
        return None
    return aviso


def _entregar(
    db: Session,
    usuario: models.Usuario,
    aviso: models.Notificacion,
    *,
    correo: bool,
    push: bool,
) -> None:
    """Envía por los canales permitidos y marca lo que ya se entregó."""
    if correo and not aviso.enviada_correo and getattr(usuario, "notificaciones_correo", True):
        try:
            r = enviar_correo_notificacion(
                usuario.correo, usuario.nombre, aviso.titulo, aviso.mensaje or "", aviso.url
            )
            if r.get("enviado"):
                aviso.enviada_correo = True
        except Exception:  # noqa: BLE001
            logger.exception("[notif] falló el correo de la notificación %s", aviso.id)

    if push and not aviso.enviada_push and getattr(usuario, "notificaciones_push", True):
        if push_configurado():
            try:
                enviados = enviar_push(
                    db, usuario.id, aviso.titulo, aviso.mensaje or "", aviso.url, aviso.id
                )
                if enviados:
                    aviso.enviada_push = True
            except Exception:  # noqa: BLE001
                logger.exception("[notif] falló el push de la notificación %s", aviso.id)


def _entregar_en_hilo(entregas: list[tuple[int, bool, bool]]) -> None:
    """Entrega avisos ya persistidos usando una sesión propia.

    Se ejecuta en un hilo aparte con `SessionLocal()`: la sesión del request
    ya se cerró (o está a punto de cerrarse) y SQLAlchemy no es thread-safe.
    """
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        for notificacion_id, correo, push in entregas:
            aviso = db.query(models.Notificacion).get(notificacion_id)
            if not aviso or aviso.descartada:
                continue
            usuario = db.query(models.Usuario).get(aviso.usuario_id)
            if not usuario:
                continue
            _entregar(db, usuario, aviso, correo=correo, push=push)
        db.commit()
    except Exception:  # noqa: BLE001
        logger.exception("[notif] error en la entrega en segundo plano")
        db.rollback()
    finally:
        db.close()


def _programar_entrega(entregas: list[tuple[int, bool, bool]]) -> None:
    if not entregas:
        return
    import threading

    threading.Thread(
        target=_entregar_en_hilo,
        args=(list(entregas),),
        daemon=True,
        name="notificaciones-entrega",
    ).start()


# ---------------------------------------------------------------------------
# API pública del servicio
# ---------------------------------------------------------------------------
def notificar(
    db: Session,
    *,
    id_conjunto: int | None,
    tipo: str,
    titulo: str,
    mensaje: str,
    clave: str,
    severidad: str = "media",
    url: str | None = None,
    fecha: date | None = None,
    autor_id: int | None = None,
    correo: bool | None = None,
    push: bool = True,
    solo_usuario_id: int | None = None,
) -> list[models.Notificacion]:
    """Crea (una vez) el aviso para cada destinatario y lo entrega.

    Debe llamarse DESPUÉS de que el router haya hecho `commit()` de su propio
    cambio: esta función confirma sus filas y hace la entrega por separado
    para que un error de SMTP/push nunca revierta el dato guardado.
    """
    if correo is None:
        correo = severidad == "alta" or tipo in TIPOS_CON_CORREO

    referencia = f"{tipo}:{id_conjunto or 0}:{clave}"
    if solo_usuario_id is not None:
        u = db.query(models.Usuario).get(solo_usuario_id)
        usuarios = [u] if u else []
    else:
        usuarios = destinatarios(db, id_conjunto, tipo, excluir_usuario_id=autor_id)
    creadas: list[tuple[models.Usuario, models.Notificacion]] = []
    try:
        for usuario in usuarios:
            aviso = _insertar(
                db, usuario,
                tipo=tipo, titulo=titulo, mensaje=mensaje, referencia=referencia,
                severidad=severidad, url=url, id_conjunto=id_conjunto, fecha=fecha,
            )
            if aviso:
                creadas.append((usuario, aviso))
        if not creadas:
            return []
        # Los ids ya están asignados por el flush de _insertar.
        entregas = [(aviso.id, correo, push) for _, aviso in creadas]
        db.commit()
    except Exception:  # noqa: BLE001
        logger.exception("[notif] no se pudieron guardar los avisos (%s)", referencia)
        db.rollback()
        return []

    # La entrega (SMTP / Web Push) se hace en segundo plano: un correo lento
    # nunca debe retrasar la respuesta del endpoint que originó el aviso.
    _programar_entrega(entregas)
    return [aviso for _, aviso in creadas]


def notificar_seguro(**kwargs) -> None:
    """`notificar()` para usar desde los routers: un fallo nunca rompe la API."""
    try:
        notificar(**kwargs)
    except Exception:  # noqa: BLE001
        logger.exception("[notif] error al crear aviso desde un router")


def sincronizar_recordatorios(db: Session, usuario: models.Usuario, forzar: bool = False) -> None:
    """Genera (sin duplicar) los recordatorios derivados de los datos reales.

    Se ejecuta como mucho una vez cada 30 s por usuario. La primera vez no
    dispara push: así una base con datos de demo no manda decenas de avisos
    de golpe al abrir la campana por primera vez.
    """
    ahora = datetime.utcnow()
    if not forzar and usuario.id in _ultima_sinc and ahora - _ultima_sinc[usuario.id] < VENTANA_SINC:
        return
    _ultima_sinc[usuario.id] = ahora

    primera_vez = (
        db.query(models.Notificacion.id)
        .filter(models.Notificacion.usuario_id == usuario.id)
        .first()
        is None
    )
    entregar_push = not primera_vez

    try:
        hoy = date.today()
        ve = lambda modulo: usuario_tiene_permiso(db, usuario, f"{modulo}.ver")  # noqa: E731
        conjuntos = conjuntos_del_usuario(db, usuario)
        creadas: list[tuple[models.Usuario, models.Notificacion, bool]] = []

        def add(tipo, titulo, mensaje, clave, severidad, cid, fecha=None):
            aviso = _insertar(
                db, usuario, tipo=tipo, titulo=titulo, mensaje=mensaje,
                referencia=f"{tipo}:{cid}:{clave}", severidad=severidad, fecha=fecha,
                id_conjunto=cid,
            )
            if aviso:
                creadas.append((usuario, aviso, entregar_push))

        for conjunto in conjuntos:
            cid = conjunto.id

            if ve("finanzas"):
                movs = (
                    db.query(models.MovimientoFinanciero)
                    .filter(
                        models.MovimientoFinanciero.id_conjunto == cid,
                        models.MovimientoFinanciero.estado.in_(["pendiente", "vencido"]),
                    )
                    .all()
                )
                # Un solo aviso RESUMEN por conjunto y tipo: 40 pagos vencidos
                # no deben convertirse en 40 notificaciones idénticas. El
                # recuento y el importe forman parte de la referencia, así
                # cuando cambian las cifras nace un aviso nuevo.
                vencidos = [m for m in movs if m.estado == "vencido"
                            or (m.fecha_vencimiento and m.fecha_vencimiento < hoy)]
                proximos = [m for m in movs if m not in vencidos
                            and m.fecha_vencimiento
                            and 0 <= (m.fecha_vencimiento - hoy).days <= 7]
                if vencidos:
                    total = sum(float(m.monto or 0) for m in vencidos)
                    add("mora", "Pagos vencidos",
                        f"Hay {len(vencidos)} {'pago vencido' if len(vencidos) == 1 else 'pagos vencidos'} "
                        f"por {_money(total)} en {conjunto.nombre}. Revisa la cartera en Finanzas.",
                        f"resumen:{len(vencidos)}:{int(total)}", "alta", cid, hoy)
                if proximos:
                    total = sum(float(m.monto or 0) for m in proximos)
                    add("proximo", "Pagos por vencer",
                        f"{len(proximos)} {'pago vence' if len(proximos) == 1 else 'pagos vencen'} "
                        f"en los próximos 7 días en {conjunto.nombre} ({_money(total)}).",
                        f"resumen:{len(proximos)}:{int(total)}", "media", cid, hoy)

            if ve("eventos"):
                eventos = (
                    db.query(models.Evento)
                    .filter(
                        models.Evento.id_conjunto == cid,
                        models.Evento.fecha >= hoy,
                        models.Evento.fecha <= hoy + timedelta(days=7),
                    )
                    .all()
                )
                # Los eventos sí se notifican uno a uno: son pocos y cada uno
                # tiene fecha y lugar propios.
                for ev in eventos:
                    add("evento", "Evento próximo",
                        f"{ev.titulo} — {ev.fecha.strftime('%d/%m/%Y')}" + (f" en {ev.lugar}" if ev.lugar else ""),
                        f"{ev.id}:{ev.fecha}", "baja", cid, ev.fecha)

            if ve("mantenimiento"):
                criticas = (
                    db.query(models.TareaMantenimiento)
                    .filter(
                        models.TareaMantenimiento.id_conjunto == cid,
                        models.TareaMantenimiento.prioridad == "critica",
                        models.TareaMantenimiento.estado != "completada",
                    )
                    .all()
                )
                if criticas:
                    nombres = ", ".join(t.titulo for t in criticas[:3])
                    if len(criticas) > 3:
                        nombres += "…"
                    ids = ",".join(str(t.id) for t in criticas[:20])
                    add("mantenimiento", "Mantenimientos críticos",
                        f"{len(criticas)} "
                        f"{'tarea crítica' if len(criticas) == 1 else 'tareas críticas'} "
                        f"sin resolver en {conjunto.nombre}: {nombres}.",
                        f"resumen:{len(criticas)}:{ids}", "alta", cid)

        if creadas:
            # Los recordatorios no se mandan por correo (evita spam); sí por
            # push cuando son nuevos y no es la primera carga de este usuario.
            entregas = [(aviso.id, False, con_push) for _, aviso, con_push in creadas]
            db.commit()
            _programar_entrega(entregas)
    except Exception:  # noqa: BLE001 - la campana nunca debe tumbar la API
        logger.exception("[notif] error al sincronizar recordatorios")
        db.rollback()


def serializar(db: Session, n: models.Notificacion) -> dict:
    nombre = None
    if n.id_conjunto:
        c = db.query(models.Conjunto.nombre).filter(models.Conjunto.id == n.id_conjunto).first()
        nombre = c[0] if c else None
    return {
        "id": n.id,
        "tipo": n.tipo,
        "severidad": n.severidad,
        "titulo": n.titulo,
        "mensaje": n.mensaje or "",
        "url": n.url,
        "fecha": n.fecha.isoformat() if n.fecha else None,
        # Se guarda con datetime.utcnow(): se marca Z para que el navegador
        # lo interprete como UTC y no como hora local.
        "fecha_creacion": (n.fecha_creacion.isoformat() + "Z") if n.fecha_creacion else None,
        "leida": bool(n.leida),
        "id_conjunto": n.id_conjunto,
        "nombre_conjunto": nombre,
    }


def listar_para(db: Session, usuario: models.Usuario, limite: int = 200) -> list[dict]:
    """Avisos visibles para el usuario, aplicando RBAC también en la lectura."""
    filas = (
        db.query(models.Notificacion)
        .filter(
            models.Notificacion.usuario_id == usuario.id,
            models.Notificacion.descartada.is_(False),
        )
        .order_by(models.Notificacion.leida.asc(), models.Notificacion.fecha_creacion.desc())
        .limit(limite)
        .all()
    )
    visibles = []
    for n in filas:
        permiso = permiso_para(n.tipo)
        if permiso and not usuario_tiene_permiso(db, usuario, permiso):
            continue
        visibles.append(serializar(db, n))
    orden = {"alta": 0, "media": 1, "baja": 2}
    visibles.sort(key=lambda x: (x["leida"], orden.get(x["severidad"], 3)))
    return visibles


def resumen_canales() -> dict:
    return {
        "correo_configurado": bool(mail_configurado() and canal_habilitado()),
        "push_configurado": bool(push_configurado()),
    }


def enviar_prueba(db: Session, usuario: models.Usuario, canal: str = "todos") -> dict:
    """Crea un aviso de prueba y lo entrega por los canales pedidos.

    Devuelve el detalle de cada entrega para que la interfaz pueda decirle al
    usuario si el correo salió, si hay suscripciones push, etc.
    """
    import uuid

    clave = uuid.uuid4().hex[:12]
    aviso = _insertar(
        db, usuario,
        tipo="prueba",
        titulo="Notificación de prueba",
        mensaje="Si estás viendo esto, tus notificaciones reales funcionan. "
                "Puedes marcarlas como leídas o descartarlas.",
        referencia=f"prueba:0:{clave}",
        severidad="media",
    )
    if not aviso:
        raise RuntimeError("No se pudo crear el aviso de prueba.")
    db.commit()

    resultado: dict = {"id": aviso.id, "correo": {"enviado": False}, "push": 0, "suscripciones": 0}

    if canal in ("todos", "correo"):
        if getattr(usuario, "notificaciones_correo", True):
            r = enviar_correo_notificacion(
                usuario.correo, usuario.nombre, aviso.titulo, aviso.mensaje or "", aviso.url
            )
            resultado["correo"] = r
            if r.get("enviado"):
                aviso.enviada_correo = True
        else:
            resultado["correo"] = {"enviado": False, "error": "desactivado por el usuario"}

    if canal in ("todos", "push"):
        total = (
            db.query(models.PushSuscripcion)
            .filter(models.PushSuscripcion.usuario_id == usuario.id,
                    models.PushSuscripcion.activa.is_(True))
            .count()
        )
        resultado["suscripciones"] = total
        if getattr(usuario, "notificaciones_push", True) and push_configurado() and total:
            enviados = enviar_push(
                db, usuario.id, aviso.titulo, aviso.mensaje or "", aviso.url, aviso.id
            )
            resultado["push"] = enviados
            if enviados:
                aviso.enviada_push = True

    db.commit()
    return resultado
