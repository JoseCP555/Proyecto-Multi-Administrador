"""Motor del chatbot: Ollama (v0.40+) con contexto real de la BD + respaldo local.

Por defecto utiliza **Ollama** (`CHATBOT_ENGINE=ollama`) a través de su API
nativa `/api/chat`, inyectando únicamente los datos reales del conjunto activo
(`id_conjunto`) y los módulos autorizados por el rol del usuario (RBAC).

Si `CHATBOT_ENGINE=local`, o si Ollama no está disponible / aún está
descargando el modelo, responde automáticamente con el motor local basado en
reglas + datos reales de la base de datos, garantizando disponibilidad 100 %.
"""
from __future__ import annotations

import difflib
import logging
import os
import unicodedata
from datetime import date
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app import models
from app.ollama_client import chatear_ollama, ollama_modelo_defecto

logger = logging.getLogger("app.chatbot")

# Conjunto activo mientras se genera la respuesta (None = todos los datos).
_CONJUNTO_ACTIVO: int | None = None


def _ctx(consulta, modelo, id_conjunto: int | None = None):
    """Aplica el filtro del conjunto activo si el modelo lo soporta."""
    cid = id_conjunto if id_conjunto is not None else _CONJUNTO_ACTIVO
    if cid is None:
        return consulta
    columna = getattr(modelo, "id_conjunto", None)
    return consulta.filter(columna == cid) if columna is not None else consulta


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return t.lower()


# Catálogo de intents (palabras clave). Se normaliza a minúsculas y sin tildes.
INTENTS = {
    "saludo": ["hola", "buenos dias", "buenas tardes", "buenas noches", "hey", "saludos", "que tal"],
    "balance": ["balance", "saldo", "cuanto tengo", "cuanto debo", "deuda", "estado cuenta", "estado de cuenta"],
    "ingresos": ["ingresos", "ingreso", "cuanto entra", "recaudado", "recaudacion"],
    "gastos": ["gastos", "gasto", "egresos", "cuanto sale", "erogacion"],
    "pagos_pendientes": ["pago pendiente", "pagos", "pendiente", "sin pagar", "mora", "morosos"],
    "mantenimiento": ["mantenimiento", "tarea", "reparacion", "averia", "arreglo", "falla"],
    "propiedades": ["propiedades", "inmuebles", "apartamento", "unidades", "bloque", "torre"],
    "residentes": ["residente", "residentes", "propietario", "inquilino"],
    "documentos": ["documento", "documentos", "reglamento", "acta", "manual", "archivo"],
    "eventos": ["evento", "reunion", "asamblea", "agenda", "actividad"],
    "ayuda": ["ayuda", "que puedes hacer", "funciones", "como usar", "help"],
    "gracias": ["gracias", "genial", "perfecto", "excelente", "ok"],
}


def detectar_intent(mensaje: str) -> str:
    n = _norm(mensaje)
    for intent, palabras in INTENTS.items():
        if any(palabra in n for palabra in palabras):
            return intent
    return "general"


def _format_money(v) -> str:
    number = float(v or 0)
    return f"${number:,.0f}".replace(",", ".")


# Módulo (permiso `<modulo>.ver`) que requiere cada intent con datos reales.
INTENT_MODULO = {
    "balance": "finanzas", "ingresos": "finanzas", "gastos": "finanzas",
    "pagos_pendientes": "finanzas", "mantenimiento": "mantenimiento",
    "propiedades": "propiedades", "residentes": "residentes",
    "documentos": "documentos", "eventos": "eventos",
}

SIN_PERMISO = (
    "Esa información pertenece al módulo de {modulo}, al que tu rol no tiene acceso. "
    "Si la necesitas, comunícate con la administración del conjunto. 🔒"
)


def obtener_config_chatbot(db: Session) -> tuple[str, str]:
    """Devuelve `(motor, modelo_ollama)` leyendo tabla `configuraciones` y entorno.

    * Por defecto el motor es `"ollama"` (acepta `"ollama"` o `"local"`).
    * Si existe `chatbot_engine` en `configuraciones` con valor `"ollama"` o
      `"local"`, se respeta para que el administrador pueda cambiarlo desde el
      panel de Configuración.
    * Si existe `ollama_model` en `configuraciones` con valor no vacío, tiene
      prioridad sobre `OLLAMA_MODEL`.
    """
    motor_env = (os.getenv("CHATBOT_ENGINE") or "ollama").strip().lower()
    if motor_env not in ("ollama", "local"):
        motor_env = "ollama"
    modelo_env = ollama_modelo_defecto()

    motor = motor_env
    modelo = modelo_env
    try:
        filas = (
            db.query(models.Configuracion)
            .filter(
                models.Configuracion.clave.in_(["chatbot_engine", "ollama_model"]),
                models.Configuracion.id_conjunto.is_(None),
            )
            .all()
        )
        mapa = {f.clave: (f.valor or "").strip() for f in filas}
        if mapa.get("chatbot_engine") in ("ollama", "local"):
            motor = mapa["chatbot_engine"]
        if mapa.get("ollama_model"):
            modelo = mapa["ollama_model"]
    except Exception:  # noqa: BLE001
        pass

    return motor, modelo


def _tiene_permiso(permisos: Optional[Iterable[str]], codigo: str) -> bool:
    if permisos is None:
        return True
    return codigo in permisos


def construir_contexto_bd(
    db: Session,
    permisos: Optional[Iterable[str]] = None,
    id_conjunto: Optional[int] = None,
    usuario=None,
) -> str:
    """Arma un resumen compacto con datos reales del conjunto para Ollama.

    Aplica estrictamente RBAC: únicamente consulta e incluye los módulos donde
    el usuario tiene `<modulo>.ver`. De esta forma Ollama nunca recibe datos
    privados fuera del rol del usuario.
    """
    perms = set(permisos) if permisos is not None else None
    secciones: list[str] = [f"Fecha actual: {date.today().isoformat()}."]

    if usuario is not None:
        rol_nombre = getattr(getattr(usuario, "rol", None), "nombre", None) or "usuario"
        secciones.append(f"Usuario actual: {usuario.nombre} (rol: {rol_nombre}).")

    # Metadatos generales del conjunto activo
    if id_conjunto is not None:
        conjunto = db.query(models.Conjunto).filter(models.Conjunto.id == id_conjunto).first()
    else:
        conjunto = (
            db.query(models.Conjunto)
            .filter(models.Conjunto.activo == True)  # noqa: E712
            .order_by(models.Conjunto.id.asc())
            .first()
        )
    if conjunto is not None:
        info = [f"Conjunto activo: {conjunto.nombre}"]
        if conjunto.direccion:
            info.append(
                f"Dirección: {conjunto.direccion}"
                + (f", {conjunto.ciudad}" if conjunto.ciudad else "")
            )
        if conjunto.administrador:
            info.append(f"Administrador: {conjunto.administrador}")
        if conjunto.telefono:
            info.append(f"Teléfono: {conjunto.telefono}")
        if conjunto.correo:
            info.append(f"Correo: {conjunto.correo}")
        if conjunto.cuota and float(conjunto.cuota) > 0:
            cuota_txt = f"Cuota base de administración: {_format_money(conjunto.cuota)}"
            if conjunto.dia_cobro:
                cuota_txt += f" (día de cobro: {conjunto.dia_cobro})"
            info.append(cuota_txt)
        if conjunto.silencio:
            info.append(f"Horario de silencio: {conjunto.silencio}")
        if conjunto.reunion:
            info.append(f"Norma de reuniones: {conjunto.reunion}")
        secciones.append(" | ".join(info))

    autorizados: list[str] = []
    restringidos: list[str] = []

    # Finanzas (solo si tiene finanzas.ver)
    if _tiene_permiso(perms, "finanzas.ver"):
        autorizados.append("finanzas")
        ingresos = (
            _ctx(db.query(models.MovimientoFinanciero), models.MovimientoFinanciero, id_conjunto)
            .join(models.ConceptoFinanciero)
            .filter(
                models.ConceptoFinanciero.tipo == "ingreso",
                models.MovimientoFinanciero.estado == "pagado",
            )
            .all()
        )
        gastos = (
            _ctx(db.query(models.MovimientoFinanciero), models.MovimientoFinanciero, id_conjunto)
            .join(models.ConceptoFinanciero)
            .filter(
                models.ConceptoFinanciero.tipo == "gasto",
                models.MovimientoFinanciero.estado == "pagado",
            )
            .all()
        )
        pendientes = (
            _ctx(db.query(models.MovimientoFinanciero), models.MovimientoFinanciero, id_conjunto)
            .filter(models.MovimientoFinanciero.estado.in_(["pendiente", "vencido"]))
            .all()
        )
        total_ing = sum(float(m.monto or 0) for m in ingresos)
        total_gas = sum(float(m.monto or 0) for m in gastos)
        total_pend = sum(float(m.monto or 0) for m in pendientes)
        secciones.append(
            f"[FINANZAS] Ingresos recaudados: {_format_money(total_ing)} ({len(ingresos)} mov.); "
            f"Gastos pagados: {_format_money(total_gas)} ({len(gastos)} mov.); "
            f"Saldo disponible: {_format_money(total_ing - total_gas)}; "
            f"Pagos pendientes o vencidos: {len(pendientes)} por {_format_money(total_pend)}."
        )
    else:
        restringidos.append("finanzas")

    # Propiedades
    if _tiene_permiso(perms, "propiedades.ver"):
        autorizados.append("propiedades")
        q_p = _ctx(db.query(models.Propiedad), models.Propiedad, id_conjunto)
        total = q_p.count()
        ocupadas = q_p.filter(models.Propiedad.estado == "ocupado").count()
        vacias = q_p.filter(models.Propiedad.estado == "vacio").count()
        mant = q_p.filter(models.Propiedad.estado == "mantenimiento").count()
        secciones.append(
            f"[PROPIEDADES] Total: {total} (ocupadas: {ocupadas}, vacías: {vacias}, mantenimiento: {mant})."
        )
    else:
        restringidos.append("propiedades")

    # Residentes
    if _tiene_permiso(perms, "residentes.ver"):
        autorizados.append("residentes")
        q_r = _ctx(db.query(models.Residente), models.Residente, id_conjunto)
        total = q_r.count()
        activos = q_r.filter(models.Residente.activo == True).count()  # noqa: E712
        propietarios = q_r.filter(models.Residente.tipo == "propietario").count()
        inquilinos = q_r.filter(models.Residente.tipo == "inquilino").count()
        secciones.append(
            f"[RESIDENTES] Total: {total} (activos: {activos}, propietarios: {propietarios}, inquilinos: {inquilinos})."
        )
    else:
        restringidos.append("residentes")

    # Mantenimiento
    if _tiene_permiso(perms, "mantenimiento.ver"):
        autorizados.append("mantenimiento")
        tareas = _ctx(db.query(models.TareaMantenimiento), models.TareaMantenimiento, id_conjunto).all()
        pend = [t for t in tareas if t.estado in ("pendiente", "en_proceso")]
        comp = [t for t in tareas if t.estado == "completada"]
        crit = [t for t in pend if t.prioridad == "critica"]
        muestra = "; ".join(f"{t.titulo} ({t.prioridad}, {t.estado})" for t in pend[:4])
        secciones.append(
            f"[MANTENIMIENTO] Pendientes/en proceso: {len(pend)} (críticas: {len(crit)}); "
            f"Completadas: {len(comp)}."
            + (f" Principales pendientes: {muestra}." if muestra else "")
        )
    else:
        restringidos.append("mantenimiento")

    # Documentos
    if _tiene_permiso(perms, "documentos.ver"):
        autorizados.append("documentos")
        docs = _ctx(db.query(models.Documento), models.Documento, id_conjunto).all()
        publicos = [d for d in docs if d.publico]
        visibles = docs if _tiene_permiso(perms, "documentos.crear") else publicos
        muestra = "; ".join(f"{d.titulo} ({d.tipo_documento or 'general'})" for d in visibles[:5])
        secciones.append(
            f"[DOCUMENTOS] Visibles: {len(visibles)} (públicos: {len(publicos)})."
            + (f" Ejemplos: {muestra}." if muestra else "")
        )
    else:
        restringidos.append("documentos")

    # Eventos próximos
    if _tiene_permiso(perms, "eventos.ver"):
        autorizados.append("eventos")
        eventos = (
            _ctx(db.query(models.Evento), models.Evento, id_conjunto)
            .filter(models.Evento.fecha >= date.today())
            .order_by(models.Evento.fecha.asc())
            .limit(5)
            .all()
        )
        if eventos:
            lista = "; ".join(
                f"{e.fecha.strftime('%d/%m/%Y')}"
                + (f" {e.hora}" if e.hora else "")
                + f" - {e.titulo}"
                + (f" ({e.lugar})" if e.lugar else "")
                for e in eventos
            )
            secciones.append(f"[EVENTOS PRÓXIMOS] {lista}.")
        else:
            secciones.append("[EVENTOS PRÓXIMOS] No hay eventos próximos programados.")
    else:
        restringidos.append("eventos")

    # Comunicados recientes
    if _tiene_permiso(perms, "comunicados.ver"):
        autorizados.append("comunicados")
        comunicados = (
            _ctx(db.query(models.Comunicado), models.Comunicado, id_conjunto)
            .order_by(models.Comunicado.fijado.desc(), models.Comunicado.fecha_creacion.desc())
            .limit(3)
            .all()
        )
        if comunicados:
            lista = "; ".join(f"{c.titulo} [{c.categoria}]" for c in comunicados)
            secciones.append(f"[COMUNICADOS RECIENTES] {lista}.")

    # Zonas comunes
    if _tiene_permiso(perms, "zonas.ver"):
        autorizados.append("zonas")
        zonas = (
            _ctx(db.query(models.ZonaComun), models.ZonaComun, id_conjunto)
            .filter(models.ZonaComun.activo == True)  # noqa: E712
            .all()
        )
        if zonas:
            lista = "; ".join(
                f"{z.nombre} ({z.hora_apertura}-{z.hora_cierre}, cap. {z.capacidad})"
                for z in zonas[:6]
            )
            secciones.append(f"[ZONAS COMUNES] {lista}.")

    # PQRS
    if _tiene_permiso(perms, "pqrs.ver"):
        autorizados.append("pqrs")
        q_pqrs = _ctx(db.query(models.Pqrs), models.Pqrs, id_conjunto)
        if usuario is not None and not _tiene_permiso(perms, "pqrs.responder"):
            q_pqrs = q_pqrs.filter(models.Pqrs.usuario_id == usuario.id)
        pqrs_list = q_pqrs.all()
        abiertas = sum(1 for p in pqrs_list if p.estado != "cerrada")
        secciones.append(f"[PQRS] Visibles: {len(pqrs_list)} (abiertas/en proceso: {abiertas}).")

    if restringidos:
        secciones.append(
            "MÓDULOS RESTRINGIDOS PARA ESTE USUARIO (NO revelar ni inventar datos): "
            + ", ".join(restringidos)
            + "."
        )
    if autorizados:
        secciones.append("Módulos autorizados: " + ", ".join(autorizados) + ".")

    return "\n".join(secciones)


def _construir_mensajes_ollama(
    mensaje: str,
    contexto: str,
    historial: Optional[Iterable[tuple[str, str]]] = None,
) -> list[dict[str, str]]:
    """Prepara los mensajes para `POST /api/chat` de Ollama."""
    system_prompt = (
        "Eres el asistente virtual oficial de Multi-Administrador, una plataforma "
        "de gestión de conjuntos residenciales en Colombia (moneda COP, signo $).\n"
        "Reglas estrictas:\n"
        "1. Responde siempre en español claro, cordial, útil y conciso.\n"
        "2. Basa cualquier cifra, fecha, evento o documento ÚNICAMENTE en el bloque "
        "de CONTEXTO AUTORIZADO; jamás inventes montos ni registros.\n"
        "3. Si el usuario consulta sobre un módulo listado en MÓDULOS RESTRINGIDOS, "
        "indícale amablemente que su rol actual no tiene acceso a ese módulo y que "
        "debe solicitar la información a la administración.\n"
        "4. Si el usuario quiere hablar con una persona de la administración, recuérdale "
        "que puede usar el módulo 'Chat con Admin' o radicar una PQRS desde el panel.\n\n"
        f"CONTEXTO AUTORIZADO DEL CONJUNTO:\n{contexto}"
    )

    mensajes: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if historial:
        for rol, contenido in list(historial)[-10:]:
            rol_ollama = "user" if rol == "usuario" else "assistant"
            if contenido and contenido.strip():
                mensajes.append({"role": rol_ollama, "content": contenido.strip()})
    mensajes.append({"role": "user", "content": mensaje.strip()})
    return mensajes


def _responder_local(db: Session, mensaje: str, intent: str) -> str:
    """Motor local por reglas + datos reales (respaldo sin Ollama)."""
    respuestas = {
        "saludo": (
            "¡Hola! 👋 Soy el asistente virtual de Multi-Administrador. "
            "Puedo ayudarte con información sobre finanzas, pagos, mantenimiento, "
            "propiedades, residentes, documentos y eventos del conjunto. "
            "¿Qué deseas saber?"
        ),
        "ayuda": (
            "Puedo responderte sobre: \n"
            "• Finanzas: balance, ingresos, gastos\n"
            "• Pagos: pendientes / en mora\n"
            "• Mantenimiento: tareas y su estado\n"
            "• Propiedades y residentes\n"
            "• Documentos y eventos del conjunto\n"
            "Prueba con: \"¿Cuál es el saldo?\" o \"¿Hay pagos pendientes?\""
        ),
        "gracias": "¡Con gusto! Estoy aquí para lo que necesites. 😊",
    }

    if intent in respuestas:
        return respuestas[intent]

    if intent in ("balance", "ingresos", "gastos", "pagos_pendientes"):
        return _responder_finanzas(db, intent)
    if intent == "mantenimiento":
        return _responder_mantenimiento(db)
    if intent == "propiedades":
        return _responder_propiedades(db)
    if intent == "residentes":
        return _responder_residentes(db)
    if intent == "documentos":
        return _responder_documentos(db)
    if intent == "eventos":
        return _responder_eventos(db)

    sugerido = _sugerir_intent(mensaje)
    if sugerido:
        return (
            f"Creo que quieres saber sobre {sugerido}. Vuelve a preguntarme con "
            f"más detalle, por ejemplo: ¿Cuál es el saldo? o ¿Hay pagos pendientes?"
        )

    return (
        "No estoy seguro de haber entendido. Puedo ayudarte con finanzas, pagos, "
        "mantenimiento, propiedades, documentos y eventos. Escribe \"ayuda\" para ver opciones."
    )


def responder_con_detalle(
    db: Session,
    mensaje: str,
    permisos: list[str] | set[str] | None = None,
    id_conjunto: int | None = None,
    historial: Optional[Iterable[tuple[str, str]]] = None,
    usuario=None,
) -> dict[str, Optional[str]]:
    """Genera la respuesta y devuelve metadatos del motor utilizado.

    1. Barrera RBAC dura: bloquea de inmediato intents cuyo módulo no esté
       autorizado en `permisos`, sin llamar a Ollama.
    2. Si el motor activo es `ollama`, envía contexto RBAC del conjunto e
       historial a Ollama (`/api/chat`).
    3. Si Ollama no responde o el motor es `local`, usa el motor local.
    """
    global _CONJUNTO_ACTIVO
    _CONJUNTO_ACTIVO = id_conjunto
    try:
        intent = detectar_intent(mensaje)
        modulo = INTENT_MODULO.get(intent)
        if permisos is not None and modulo and f"{modulo}.ver" not in permisos:
            return {
                "respuesta": SIN_PERMISO.format(modulo=modulo),
                "motor_usado": "rbac",
                "modelo": None,
            }

        motor, modelo = obtener_config_chatbot(db)
        if motor == "ollama":
            contexto = construir_contexto_bd(
                db,
                permisos=permisos,
                id_conjunto=id_conjunto,
                usuario=usuario,
            )
            mensajes_ollama = _construir_mensajes_ollama(
                mensaje=mensaje,
                contexto=contexto,
                historial=historial,
            )
            respuesta_ia = chatear_ollama(mensajes_ollama, modelo=modelo)
            if respuesta_ia:
                return {
                    "respuesta": respuesta_ia,
                    "motor_usado": "ollama",
                    "modelo": modelo,
                }
            logger.info("[chatbot] Ollama no disponible; respondiendo con motor local.")

        return {
            "respuesta": _responder_local(db, mensaje, intent),
            "motor_usado": "local",
            "modelo": None,
        }
    finally:
        _CONJUNTO_ACTIVO = None


def responder(
    db: Session,
    mensaje: str,
    permisos: list[str] | set[str] | None = None,
    id_conjunto: int | None = None,
    historial: Optional[Iterable[tuple[str, str]]] = None,
    usuario=None,
) -> str:
    """Genera la respuesta en texto plano (compatible con callers existentes)."""
    return responder_con_detalle(
        db,
        mensaje,
        permisos=permisos,
        id_conjunto=id_conjunto,
        historial=historial,
        usuario=usuario,
    )["respuesta"] or ""


# ---- Intents específicos (motor local) -------------------------------------
def _responder_finanzas(db: Session, intent: str) -> str:
    ingresos = (
        _ctx(db.query(models.MovimientoFinanciero), models.MovimientoFinanciero)
        .join(models.ConceptoFinanciero)
        .filter(models.ConceptoFinanciero.tipo == "ingreso", models.MovimientoFinanciero.estado == "pagado")
        .all()
    )
    gastos = (
        _ctx(db.query(models.MovimientoFinanciero), models.MovimientoFinanciero)
        .join(models.ConceptoFinanciero)
        .filter(models.ConceptoFinanciero.tipo == "gasto", models.MovimientoFinanciero.estado == "pagado")
        .all()
    )
    total_ing = sum(float(m.monto) for m in ingresos)
    total_gas = sum(float(m.monto) for m in gastos)
    saldo = total_ing - total_gas

    pendientes = (
        _ctx(db.query(models.MovimientoFinanciero), models.MovimientoFinanciero)
        .filter(models.MovimientoFinanciero.estado.in_(["pendiente", "vencido"]))
        .all()
    )
    total_pend = sum(float(m.monto) for m in pendientes)

    if intent == "ingresos":
        return (
            f"Los ingresos recaudados del periodo suman {_format_money(total_ing)} "
            f"en {len(ingresos)} movimientos registrados. 💰"
        )
    if intent == "gastos":
        return (
            f"Los gastos del periodo suman {_format_money(total_gas)} "
            f"en {len(gastos)} movimientos. 📉"
        )
    if intent == "pagos_pendientes":
        if not pendientes:
            return "¡Buenas noticias! No hay pagos pendientes ni en mora. ✅"
        return (
            f"Hay {len(pendientes)} pagos pendientes o en mora por un total de "
            f"{_format_money(total_pend)}. Revisa el módulo de Finanzas para gestionarlos."
        )

    # balance
    return (
        f"📊 Resumen financiero:\n"
        f"• Ingresos: {_format_money(total_ing)}\n"
        f"• Gastos: {_format_money(total_gas)}\n"
        f"• Saldo: {_format_money(saldo)}\n"
        f"• Pendientes/En mora: {_format_money(total_pend)}\n\n"
        "¿Quieres detalle de ingresos, gastos o pagos pendientes?"
    )


def _responder_mantenimiento(db: Session) -> str:
    pendientes = _ctx(db.query(models.TareaMantenimiento), models.TareaMantenimiento).filter(
        models.TareaMantenimiento.estado.in_(["pendiente", "en_proceso"])
    ).count()
    completadas = _ctx(db.query(models.TareaMantenimiento), models.TareaMantenimiento).filter(
        models.TareaMantenimiento.estado == "completada"
    ).count()
    criticas = _ctx(db.query(models.TareaMantenimiento), models.TareaMantenimiento).filter(
        models.TareaMantenimiento.prioridad == "critica",
        models.TareaMantenimiento.estado != "completada",
    ).count()
    return (
        f"🛠️ Mantenimiento:\n"
        f"• Tareas pendientes/en proceso: {pendientes}\n"
        f"• Completadas: {completadas}\n"
        f"• Críticas sin resolver: {criticas}\n\n"
        "Consulta el módulo de Mantenimiento para ver el detalle."
    )


def _responder_propiedades(db: Session) -> str:
    total = _ctx(db.query(models.Propiedad), models.Propiedad).count()
    ocupadas = _ctx(db.query(models.Propiedad), models.Propiedad).filter(models.Propiedad.estado == "ocupado").count()
    vacias = _ctx(db.query(models.Propiedad), models.Propiedad).filter(models.Propiedad.estado == "vacio").count()
    return (
        f"🏢 El conjunto cuenta con {total} propiedades: "
        f"{ocupadas} ocupadas y {vacias} vacías. "
        "¿Quieres conocer el estado de alguna torre o bloque en particular?"
    )


def _responder_residentes(db: Session) -> str:
    total = _ctx(db.query(models.Residente), models.Residente).count()
    activos = _ctx(db.query(models.Residente), models.Residente).filter(models.Residente.activo == True).count()  # noqa: E712
    propietarios = _ctx(db.query(models.Residente), models.Residente).filter(models.Residente.tipo == "propietario").count()
    inquilinos = _ctx(db.query(models.Residente), models.Residente).filter(models.Residente.tipo == "inquilino").count()
    return (
        f"👥 Hay {total} residentes registrados ({activos} activos).\n"
        f"• Propietarios: {propietarios}\n"
        f"• Inquilinos: {inquilinos}\n\n"
        "Consulta el módulo de Residentes para el detalle completo."
    )


def _responder_documentos(db: Session) -> str:
    total = _ctx(db.query(models.Documento), models.Documento).count()
    publicos = _ctx(db.query(models.Documento), models.Documento).filter(models.Documento.publico == True).count()  # noqa: E712
    return (
        f"📄 Hay {total} documentos cargados, de los cuales {publicos} son de acceso público "
        "(reglamentos, actas, manuales). Consulta el módulo de Documentos."
    )


def _responder_eventos(db: Session) -> str:
    hoy = date.today()
    eventos = _ctx(db.query(models.Evento), models.Evento).filter(
        models.Evento.fecha >= hoy
    ).order_by(models.Evento.fecha).all()
    if not eventos:
        return "No hay eventos próximos programados. 📅"
    lineas = "\n".join(f"• {e.titulo} — {e.fecha.strftime('%d/%m/%Y')} ({e.lugar})" for e in eventos[:5])
    return f"📅 Próximos eventos del conjunto:\n{lineas}"


def _sugerir_intent(mensaje: str) -> str | None:
    """Recomienda una categoría por similitud de palabras."""
    n = _norm(mensaje)
    mejor = None
    mejor_score = 0.6
    for intent, claves in INTENTS.items():
        for clave in claves:
            score = difflib.SequenceMatcher(None, n, clave).ratio()
            if score > mejor_score:
                mejor_score = score
                mejor = intent
    return mejor


def crear_sesion(db: Session, usuario_id=None, id_conjunto: int | None = None) -> models.SesionChat:
    s = models.SesionChat(usuario_id=usuario_id, titulo="Chat asistente", id_conjunto=id_conjunto)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def guardar_mensaje(db: Session, sesion_id: int, rol: str, contenido: str) -> models.MensajeChat:
    m = models.MensajeChat(sesion_id=sesion_id, rol=rol, contenido=contenido)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def cambiar_titulo_si_necesario(db: Session, sesion_id: int, contenido: str) -> None:
    s = db.query(models.SesionChat).get(sesion_id)
    if s and s.titulo == "Chat asistente":
        s.titulo = contenido[:45]
        db.commit()
