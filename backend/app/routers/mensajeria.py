"""Mensajería directa en tiempo real entre residentes y administración.

Permite que cada residente de un conjunto converse directamente con el equipo
de administración (`admin` / `super_admin`):

* **Residente** (`mensajes.ver`, `mensajes.enviar`): sólo ve y escribe en su
  propia conversación con la administración de su conjunto.
* **Administrador** (`mensajes.ver`, `mensajes.enviar`, `mensajes.gestionar`):
  ve la bandeja de entrada con todos los residentes del conjunto activo, puede
  iniciar chats nuevos con cualquier residente, responder, enviar adjuntos y
  marcar conversaciones como resueltas o reabrirlas.
* **Tiempo real**: incluye endpoint WebSocket (`/mensajes/ws`) para entrega
  instantánea de mensajes, confirmaciones de lectura e indicador de escritura.
"""
from __future__ import annotations

import os
import secrets
import shutil
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import notificaciones_servicio as notif
from app import schemas
from app.auditoria import registrar_seguro
from app.auth_jwt import verificar_token
from app.chat_ws import ConexionChat, gestor_chat
from app.conjunto_ctx import (
    conjunto_activo,
    conjunto_por_defecto,
    filtrar,
    ids_conjuntos_usuario,
    ve_todos_los_conjuntos,
)
from app.database import SessionLocal, get_db
from app.deps import get_current_user, require_permiso, usuario_tiene_permiso
from app.models import (
    Conjunto,
    ConversacionDirecta,
    MensajeDirecto,
    Propiedad,
    Residente,
    Usuario,
    UsuarioConjunto,
)
from app.permisos import ADMIN, RESIDENTE, SUPER_ADMIN
from app.redis_client import token_revocado

router = APIRouter(prefix="/mensajes", tags=["Mensajería directa"])

ARCHIVOS_DIR = os.getenv("ARCHIVOS_DIR", "./archivos_documentos")
os.makedirs(ARCHIVOS_DIR, exist_ok=True)

EXTENSIONES_PERMITIDAS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf"}
MAX_TAMANO_ADJUNTO = 10 * 1024 * 1024  # 10 MB
ESTADOS_VALIDOS = {"abierta", "resuelta"}


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------
def _iso_utc(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    s = dt.isoformat()
    return s if s.endswith("Z") or "+" in s else s + "Z"


def _es_admin_chat(db: Session, usuario: Usuario) -> bool:
    return usuario_tiene_permiso(db, usuario, "mensajes.gestionar")


def _apartamento_de_usuario(db: Session, usuario_id: int, cid: Optional[int]) -> Optional[str]:
    q = db.query(Residente).filter(Residente.usuario_id == usuario_id)
    if cid is not None:
        q = q.filter(Residente.id_conjunto == cid)
    residente = q.first() or db.query(Residente).filter(Residente.usuario_id == usuario_id).first()
    if not residente:
        return None
    pq = db.query(Propiedad).filter(Propiedad.residente_id == residente.id)
    if cid is not None:
        pq = pq.filter(Propiedad.id_conjunto == cid)
    prop = pq.first() or db.query(Propiedad).filter(Propiedad.residente_id == residente.id).first()
    if not prop:
        return None
    return prop.apartamento


def _conjunto_del_residente(db: Session, usuario: Usuario, cid: Optional[int]) -> Optional[int]:
    if cid is not None:
        return cid
    propio = getattr(usuario, "id_conjunto", None) or getattr(usuario, "id_copropiedad", None)
    if propio:
        return propio
    asig = (
        db.query(UsuarioConjunto.conjunto_id)
        .filter(UsuarioConjunto.usuario_id == usuario.id)
        .first()
    )
    if asig:
        return asig[0]
    primero = db.query(Conjunto.id).filter(Conjunto.activo.is_(True)).order_by(Conjunto.id).first()
    return primero[0] if primero else None


def _usuario_en_conjunto(db: Session, usuario: Usuario, cid: Optional[int]) -> bool:
    if cid is None:
        return True
    if getattr(usuario, "id_conjunto", None) == cid or getattr(usuario, "id_copropiedad", None) == cid:
        return True
    asig = (
        db.query(UsuarioConjunto.id)
        .filter(UsuarioConjunto.usuario_id == usuario.id, UsuarioConjunto.conjunto_id == cid)
        .first()
    )
    return asig is not None


def _obtener_conversacion(
    db: Session, conv_id: int, usuario: Usuario, cid: Optional[int]
) -> ConversacionDirecta:
    conv = db.get(ConversacionDirecta, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    if cid is not None and conv.id_conjunto not in (None, cid):
        raise HTTPException(status_code=404, detail="Conversación no encontrada en este conjunto.")
    if not _es_admin_chat(db, usuario) and conv.residente_usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="Solo puedes acceder a tu propia conversación.")
    return conv


def _serializar_mensaje(db: Session, m: MensajeDirecto) -> dict:
    remitente = db.get(Usuario, m.remitente_id) if m.remitente_id else None
    return {
        "id": m.id,
        "conversacion_id": m.conversacion_id,
        "remitente_id": m.remitente_id,
        "remitente_nombre": remitente.nombre if remitente else (
            "Administración" if m.rol_remitente == "admin" else "Residente"
        ),
        "remitente_foto": getattr(remitente, "foto", None) if remitente else None,
        "rol_remitente": m.rol_remitente,
        "contenido": m.contenido,
        "adjunto": m.adjunto,
        "adjunto_nombre": m.adjunto_nombre,
        "adjunto_mime": m.adjunto_mime,
        "leido": bool(m.leido),
        "fecha_lectura": _iso_utc(m.fecha_lectura),
        "fecha_creacion": _iso_utc(m.fecha_creacion) or _iso_utc(datetime.utcnow()),
    }


def _serializar_conversacion(db: Session, conv: ConversacionDirecta, es_admin: bool) -> dict:
    residente_u = db.get(Usuario, conv.residente_usuario_id)
    conjunto = db.get(Conjunto, conv.id_conjunto) if conv.id_conjunto else None
    rol_ajeno = "residente" if es_admin else "admin"

    no_leidos = (
        db.query(func.count(MensajeDirecto.id))
        .filter(
            MensajeDirecto.conversacion_id == conv.id,
            MensajeDirecto.rol_remitente == rol_ajeno,
            MensajeDirecto.leido.is_(False),
        )
        .scalar()
        or 0
    )
    total = (
        db.query(func.count(MensajeDirecto.id))
        .filter(MensajeDirecto.conversacion_id == conv.id)
        .scalar()
        or 0
    )

    return {
        "id": conv.id,
        "residente_usuario_id": conv.residente_usuario_id,
        "residente_nombre": residente_u.nombre if residente_u else "Residente",
        "residente_correo": residente_u.correo if residente_u else None,
        "residente_telefono": residente_u.telefono if residente_u else None,
        "residente_foto": getattr(residente_u, "foto", None) if residente_u else None,
        "apartamento": _apartamento_de_usuario(db, conv.residente_usuario_id, conv.id_conjunto),
        "id_conjunto": conv.id_conjunto,
        "nombre_conjunto": conjunto.nombre if conjunto else None,
        "asunto": conv.asunto or "Chat con Administración",
        "estado": conv.estado,
        "ultimo_mensaje": conv.ultimo_mensaje,
        "ultimo_mensaje_en": _iso_utc(conv.ultimo_mensaje_en),
        "ultimo_remitente_rol": conv.ultimo_remitente_rol,
        "no_leidos": int(no_leidos),
        "total_mensajes": int(total),
        "fecha_creacion": _iso_utc(conv.fecha_creacion) or _iso_utc(datetime.utcnow()),
    }


def _buscar_o_crear_conversacion(
    db: Session,
    *,
    residente_usuario_id: int,
    id_conjunto: Optional[int],
    asunto: Optional[str] = None,
) -> tuple[ConversacionDirecta, bool]:
    q = db.query(ConversacionDirecta).filter(
        ConversacionDirecta.residente_usuario_id == residente_usuario_id
    )
    if id_conjunto is not None:
        q = q.filter(ConversacionDirecta.id_conjunto == id_conjunto)
    else:
        q = q.filter(ConversacionDirecta.id_conjunto.is_(None))
    existente = q.first()
    if existente:
        return existente, False

    conv = ConversacionDirecta(
        residente_usuario_id=residente_usuario_id,
        id_conjunto=id_conjunto,
        asunto=(asunto or "").strip() or "Chat con Administración",
        estado="abierta",
        fecha_creacion=datetime.utcnow(),
    )
    db.add(conv)
    db.flush()
    return conv, True


async def _crear_y_difundir_mensaje(
    db: Session,
    *,
    conv: ConversacionDirecta,
    usuario: Usuario,
    es_admin: bool,
    contenido: str,
    adjunto: Optional[str] = None,
    adjunto_nombre: Optional[str] = None,
    adjunto_mime: Optional[str] = None,
) -> dict:
    ahora = datetime.utcnow()
    rol_remitente = "admin" if es_admin else "residente"
    texto_limpio = contenido.strip()
    vista_previa = texto_limpio or (f"📎 {adjunto_nombre}" if adjunto_nombre else "Archivo adjunto")

    msg = MensajeDirecto(
        conversacion_id=conv.id,
        remitente_id=usuario.id,
        rol_remitente=rol_remitente,
        contenido=texto_limpio,
        adjunto=adjunto,
        adjunto_nombre=adjunto_nombre,
        adjunto_mime=adjunto_mime,
        leido=False,
        fecha_creacion=ahora,
    )
    db.add(msg)

    conv.ultimo_mensaje = vista_previa[:240]
    conv.ultimo_mensaje_en = ahora
    conv.ultimo_remitente_id = usuario.id
    conv.ultimo_remitente_rol = rol_remitente
    # Si estaba resuelta y cualquiera escribe de nuevo, se reabre automáticamente.
    if conv.estado == "resuelta":
        conv.estado = "abierta"

    db.commit()
    db.refresh(msg)
    db.refresh(conv)

    msg_json = _serializar_mensaje(db, msg)

    # Notificación en tiempo real por WebSocket.
    await gestor_chat.difundir_conversacion(
        residente_usuario_id=conv.residente_usuario_id,
        id_conjunto=conv.id_conjunto,
        payload={
            "tipo": "nuevo_mensaje",
            "conversacion_id": conv.id,
            "id_conjunto": conv.id_conjunto,
            "estado": conv.estado,
            "mensaje": msg_json,
        },
    )

    # Notificación persistente en la campana (y push si está activo; sin correo para no saturar).
    resumen_texto = vista_previa[:160]
    if es_admin:
        notif.notificar_seguro(
            db=db,
            id_conjunto=conv.id_conjunto,
            tipo="mensaje_chat",
            autor_id=usuario.id,
            titulo="Nuevo mensaje de la administración",
            mensaje=f"{usuario.nombre}: {resumen_texto}",
            clave=f"msg:{msg.id}",
            severidad="media",
            url="/dashboard/mensajes",
            correo=False,
            push=True,
            solo_usuario_id=conv.residente_usuario_id,
        )
    else:
        apto = _apartamento_de_usuario(db, usuario.id, conv.id_conjunto)
        etiqueta = f"{usuario.nombre} ({apto})" if apto else usuario.nombre
        notif.notificar_seguro(
            db=db,
            id_conjunto=conv.id_conjunto,
            tipo="mensaje_chat",
            autor_id=usuario.id,
            titulo=f"Mensaje de {etiqueta}",
            mensaje=resumen_texto,
            clave=f"msg:{msg.id}",
            severidad="media",
            url="/dashboard/mensajes",
            correo=False,
            push=True,
            solo_roles=[SUPER_ADMIN, ADMIN],
        )

    return msg_json


# ---------------------------------------------------------------------------
# Endpoints REST (rutas estáticas primero)
# ---------------------------------------------------------------------------
@router.get(
    "/no-leidos",
    response_model=schemas.ResumenNoLeidosResponse,
    dependencies=[Depends(require_permiso("mensajes.ver"))],
)
def resumen_no_leidos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: Optional[int] = Depends(conjunto_activo),
):
    """Contador ligero de mensajes sin leer para badges del menú y topbar."""
    es_admin = _es_admin_chat(db, usuario)
    q = filtrar(db.query(ConversacionDirecta.id), ConversacionDirecta, cid)
    if not es_admin:
        q = q.filter(ConversacionDirecta.residente_usuario_id == usuario.id)
    conv_ids = [fila[0] for fila in q.all()]
    if not conv_ids:
        return {"no_leidos": 0, "conversaciones_sin_leer": 0}

    rol_ajeno = "residente" if es_admin else "admin"
    filas = (
        db.query(MensajeDirecto.conversacion_id, func.count(MensajeDirecto.id))
        .filter(
            MensajeDirecto.conversacion_id.in_(conv_ids),
            MensajeDirecto.rol_remitente == rol_ajeno,
            MensajeDirecto.leido.is_(False),
        )
        .group_by(MensajeDirecto.conversacion_id)
        .all()
    )
    total = sum(int(c) for _, c in filas)
    return {"no_leidos": total, "conversaciones_sin_leer": len(filas)}


@router.get(
    "/contactos",
    dependencies=[Depends(require_permiso("mensajes.ver"))],
)
def listar_contactos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: Optional[int] = Depends(conjunto_activo),
):
    """Para admin: residentes del conjunto con quienes puede iniciar chat.
    Para residente: información de la administración de su conjunto."""
    es_admin = _es_admin_chat(db, usuario)
    if not es_admin:
        target_cid = _conjunto_del_residente(db, usuario, cid)
        conjunto = db.get(Conjunto, target_cid) if target_cid else None
        admins = (
            db.query(Usuario)
            .filter(Usuario.activo.is_(True), Usuario.rol_id.in_([SUPER_ADMIN, ADMIN]))
            .order_by(Usuario.rol_id.desc(), Usuario.nombre.asc())
            .all()
        )
        return {
            "modo": "residente",
            "conjunto": {
                "id": conjunto.id,
                "nombre": conjunto.nombre,
                "administrador": conjunto.administrador,
                "correo": conjunto.correo,
                "telefono": conjunto.telefono,
                "silencio": conjunto.silencio,
            } if conjunto else None,
            "admin_en_linea": gestor_chat.hay_admin_conectado(target_cid),
            "administradores": [
                {"id": a.id, "nombre": a.nombre, "correo": a.correo}
                for a in admins[:5]
            ],
        }

    # Admin: listar usuarios residentes activos del conjunto.
    residentes = (
        db.query(Usuario)
        .filter(Usuario.activo.is_(True), Usuario.rol_id == RESIDENTE)
        .order_by(Usuario.nombre.asc())
        .all()
    )
    if cid is not None:
        residentes = [u for u in residentes if _usuario_en_conjunto(db, u, cid)]

    conv_q = filtrar(db.query(ConversacionDirecta), ConversacionDirecta, cid)
    conv_por_residente = {c.residente_usuario_id: c.id for c in conv_q.all()}

    return {
        "modo": "admin",
        "contactos": [
            {
                "usuario_id": u.id,
                "nombre": u.nombre,
                "correo": u.correo,
                "telefono": u.telefono,
                "foto": getattr(u, "foto", None),
                "apartamento": _apartamento_de_usuario(db, u.id, cid),
                "conversacion_id": conv_por_residente.get(u.id),
            }
            for u in residentes
        ],
    }


@router.get(
    "/conversaciones",
    response_model=list[schemas.ConversacionDirectaResponse],
    dependencies=[Depends(require_permiso("mensajes.ver"))],
)
def listar_conversaciones(
    estado: Optional[str] = None,
    buscar: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: Optional[int] = Depends(conjunto_activo),
):
    """Lista las conversaciones visibles según el rol y el conjunto activo."""
    es_admin = _es_admin_chat(db, usuario)
    q = filtrar(db.query(ConversacionDirecta), ConversacionDirecta, cid)
    if not es_admin:
        q = q.filter(ConversacionDirecta.residente_usuario_id == usuario.id)
    if estado in ESTADOS_VALIDOS:
        q = q.filter(ConversacionDirecta.estado == estado)

    filas = q.order_by(
        ConversacionDirecta.ultimo_mensaje_en.desc(),
        ConversacionDirecta.fecha_creacion.desc(),
    ).all()

    resultado = [_serializar_conversacion(db, c, es_admin) for c in filas]

    if buscar and buscar.strip():
        termino = buscar.strip().lower()
        resultado = [
            item
            for item in resultado
            if termino in (item["residente_nombre"] or "").lower()
            or termino in (item["residente_correo"] or "").lower()
            or termino in (item["apartamento"] or "").lower()
            or termino in (item["ultimo_mensaje"] or "").lower()
        ]
    return resultado


@router.post(
    "/conversaciones",
    response_model=schemas.ConversacionDirectaResponse,
    dependencies=[Depends(require_permiso("mensajes.enviar"))],
)
async def crear_o_abrir_conversacion(
    data: schemas.ConversacionDirectaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: Optional[int] = Depends(conjunto_activo),
):
    """Obtiene o crea la conversación directa entre un residente y la administración."""
    es_admin = _es_admin_chat(db, usuario)

    if es_admin:
        if not data.residente_usuario_id:
            raise HTTPException(
                status_code=400,
                detail="Debes indicar el residente con quien iniciar la conversación.",
            )
        destino = db.get(Usuario, data.residente_usuario_id)
        if not destino or not destino.activo:
            raise HTTPException(status_code=404, detail="Residente no encontrado.")
        if destino.rol_id != RESIDENTE:
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden abrir conversaciones directas con usuarios de rol residente.",
            )
        if cid is not None and not _usuario_en_conjunto(db, destino, cid):
            raise HTTPException(
                status_code=403,
                detail="El residente seleccionado no pertenece al conjunto activo.",
            )
        target_uid = destino.id
        target_cid = _conjunto_del_residente(db, destino, cid)
    else:
        target_uid = usuario.id
        target_cid = _conjunto_del_residente(db, usuario, cid)

    conv, creada = _buscar_o_crear_conversacion(
        db,
        residente_usuario_id=target_uid,
        id_conjunto=target_cid,
        asunto=data.asunto,
    )
    db.commit()
    db.refresh(conv)

    if data.mensaje_inicial and data.mensaje_inicial.strip():
        await _crear_y_difundir_mensaje(
            db,
            conv=conv,
            usuario=usuario,
            es_admin=es_admin,
            contenido=data.mensaje_inicial,
        )
        db.refresh(conv)

    if creada:
        registrar_seguro(
            db=db,
            usuario=usuario,
            accion="crear",
            modulo="Chat residentes",
            entidad="conversacion_directa",
            entidad_id=conv.id,
            id_conjunto=conv.id_conjunto,
            detalle=f"Inició conversación directa #{conv.id}",
        )

    return _serializar_conversacion(db, conv, es_admin)


@router.get(
    "/conversaciones/{conv_id}/mensajes",
    response_model=list[schemas.MensajeDirectoResponse],
    dependencies=[Depends(require_permiso("mensajes.ver"))],
)
def listar_mensajes(
    conv_id: int,
    limite: int = Query(150, ge=1, le=500),
    antes_de: Optional[int] = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: Optional[int] = Depends(conjunto_activo),
):
    """Historial cronológico de mensajes de una conversación."""
    conv = _obtener_conversacion(db, conv_id, usuario, cid)
    q = db.query(MensajeDirecto).filter(MensajeDirecto.conversacion_id == conv.id)
    if antes_de is not None:
        q = q.filter(MensajeDirecto.id < antes_de)
    # Tomamos los últimos `limite` y los devolvemos en orden ascendente.
    recientes = q.order_by(MensajeDirecto.id.desc()).limit(limite).all()
    recientes.reverse()
    return [_serializar_mensaje(db, m) for m in recientes]


@router.post(
    "/conversaciones/{conv_id}/mensajes",
    response_model=schemas.MensajeDirectoResponse,
    status_code=201,
    dependencies=[Depends(require_permiso("mensajes.enviar"))],
)
async def enviar_mensaje(
    conv_id: int,
    data: schemas.MensajeDirectoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: Optional[int] = Depends(conjunto_activo),
):
    """Envía un mensaje de texto en la conversación."""
    contenido = data.contenido.strip()
    if not contenido:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")
    conv = _obtener_conversacion(db, conv_id, usuario, cid)
    es_admin = _es_admin_chat(db, usuario)
    return await _crear_y_difundir_mensaje(
        db, conv=conv, usuario=usuario, es_admin=es_admin, contenido=contenido
    )


@router.post(
    "/conversaciones/{conv_id}/adjunto",
    response_model=schemas.MensajeDirectoResponse,
    status_code=201,
    dependencies=[Depends(require_permiso("mensajes.enviar"))],
)
async def enviar_mensaje_con_adjunto(
    conv_id: int,
    contenido: str = Form(""),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: Optional[int] = Depends(conjunto_activo),
):
    """Envía un mensaje con una imagen o documento PDF adjunto (máx. 10 MB)."""
    conv = _obtener_conversacion(db, conv_id, usuario, cid)
    if not archivo or not archivo.filename:
        raise HTTPException(status_code=400, detail="Debes seleccionar un archivo para adjuntar.")

    nombre_original = os.path.basename(archivo.filename)
    ext = os.path.splitext(nombre_original)[1].lower()
    if ext not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail="Formato no permitido. Adjunta una imagen (PNG, JPG, WEBP, GIF) o un PDF.",
        )

    nombre_guardado = f"chat-{secrets.token_hex(8)}{ext}"
    destino = os.path.join(ARCHIVOS_DIR, nombre_guardado)
    with open(destino, "wb") as salida:
        shutil.copyfileobj(archivo.file, salida)

    if os.path.getsize(destino) > MAX_TAMANO_ADJUNTO:
        os.remove(destino)
        raise HTTPException(status_code=400, detail="El archivo supera el límite máximo de 10 MB.")

    mime = archivo.content_type or ("application/pdf" if ext == ".pdf" else f"image/{ext.lstrip('.')}")
    es_admin = _es_admin_chat(db, usuario)
    return await _crear_y_difundir_mensaje(
        db,
        conv=conv,
        usuario=usuario,
        es_admin=es_admin,
        contenido=contenido,
        adjunto=nombre_guardado,
        adjunto_nombre=nombre_original[:255],
        adjunto_mime=mime[:120],
    )


@router.get(
    "/adjunto/{mensaje_id}",
    dependencies=[Depends(require_permiso("mensajes.ver"))],
)
def descargar_adjunto(
    mensaje_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: Optional[int] = Depends(conjunto_activo),
):
    """Descarga o visualiza un archivo adjunto verificando permisos de la conversación."""
    msg = db.get(MensajeDirecto, mensaje_id)
    if not msg or not msg.adjunto:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado.")
    # Verifica pertenencia / permisos sobre la conversación dueña del mensaje.
    _obtener_conversacion(db, msg.conversacion_id, usuario, cid)
    ruta = os.path.join(ARCHIVOS_DIR, os.path.basename(msg.adjunto))
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="El archivo ya no existe en el servidor.")
    return FileResponse(
        ruta,
        media_type=msg.adjunto_mime or "application/octet-stream",
        filename=msg.adjunto_nombre or os.path.basename(msg.adjunto),
    )


@router.post(
    "/conversaciones/{conv_id}/leer",
    dependencies=[Depends(require_permiso("mensajes.ver"))],
)
async def marcar_como_leidos(
    conv_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: Optional[int] = Depends(conjunto_activo),
):
    """Marca como leídos los mensajes enviados por la otra parte."""
    conv = _obtener_conversacion(db, conv_id, usuario, cid)
    es_admin = _es_admin_chat(db, usuario)
    rol_ajeno = "residente" if es_admin else "admin"

    pendientes = (
        db.query(MensajeDirecto)
        .filter(
            MensajeDirecto.conversacion_id == conv.id,
            MensajeDirecto.rol_remitente == rol_ajeno,
            MensajeDirecto.leido.is_(False),
        )
        .all()
    )
    ahora = datetime.utcnow()
    for m in pendientes:
        m.leido = True
        m.fecha_lectura = ahora
    db.commit()

    if pendientes:
        await gestor_chat.difundir_conversacion(
            residente_usuario_id=conv.residente_usuario_id,
            id_conjunto=conv.id_conjunto,
            payload={
                "tipo": "mensajes_leidos",
                "conversacion_id": conv.id,
                "id_conjunto": conv.id_conjunto,
                "lector_rol": "admin" if es_admin else "residente",
                "fecha_lectura": _iso_utc(ahora),
            },
        )
    return {"ok": True, "marcados": len(pendientes)}


@router.put(
    "/conversaciones/{conv_id}/estado",
    response_model=schemas.ConversacionDirectaResponse,
    dependencies=[Depends(require_permiso("mensajes.gestionar"))],
)
async def cambiar_estado(
    conv_id: int,
    data: schemas.ConversacionEstadoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: Optional[int] = Depends(conjunto_activo),
):
    """Permite al administrador marcar la conversación como resuelta o reabrirla."""
    if data.estado not in ESTADOS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Usa uno de: {', '.join(sorted(ESTADOS_VALIDOS))}.",
        )
    conv = _obtener_conversacion(db, conv_id, usuario, cid)
    conv.estado = data.estado
    db.commit()
    db.refresh(conv)

    await gestor_chat.difundir_conversacion(
        residente_usuario_id=conv.residente_usuario_id,
        id_conjunto=conv.id_conjunto,
        payload={
            "tipo": "conversacion_actualizada",
            "conversacion_id": conv.id,
            "id_conjunto": conv.id_conjunto,
            "estado": conv.estado,
        },
    )
    registrar_seguro(
        db=db,
        usuario=usuario,
        accion="editar",
        modulo="Chat residentes",
        entidad="conversacion_directa",
        entidad_id=conv.id,
        id_conjunto=conv.id_conjunto,
        detalle=f"Cambió el estado de la conversación #{conv.id} a '{conv.estado}'",
    )
    return _serializar_conversacion(db, conv, True)


# ---------------------------------------------------------------------------
# WebSocket en tiempo real: /mensajes/ws?token=<jwt>
# ---------------------------------------------------------------------------
@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket, token: Optional[str] = None):
    """Canal WebSocket autenticado para mensajería en tiempo real."""
    if not token:
        await websocket.close(code=4401)
        return

    payload = verificar_token(token)
    if not payload or token_revocado(token):
        await websocket.close(code=4401)
        return

    sub = payload.get("sub")
    if sub is None:
        await websocket.close(code=4401)
        return

    db = SessionLocal()
    try:
        usuario = db.get(Usuario, int(sub))
        if not usuario or not usuario.activo:
            await websocket.close(code=4401)
            return
        if not usuario_tiene_permiso(db, usuario, "mensajes.ver"):
            await websocket.close(code=4403)
            return

        es_admin = _es_admin_chat(db, usuario)
        ve_todos = ve_todos_los_conjuntos(db, usuario)
        permitidos = ids_conjuntos_usuario(db, usuario)
        uid = usuario.id
        nombre = usuario.nombre
    finally:
        db.close()

    conexion = ConexionChat(
        websocket=websocket,
        usuario_id=uid,
        es_admin=es_admin,
        ve_todos_conjuntos=ve_todos,
        conjuntos_permitidos=permitidos,
    )
    await gestor_chat.conectar(conexion)
    try:
        await websocket.send_json({"tipo": "conectado", "usuario_id": uid})
        while True:
            datos = await websocket.receive_json()
            if not isinstance(datos, dict):
                continue
            tipo = datos.get("tipo")
            if tipo == "ping":
                await websocket.send_json({"tipo": "pong"})
            elif tipo == "escribiendo":
                conv_id = datos.get("conversacion_id")
                if not isinstance(conv_id, int):
                    continue
                activo = bool(datos.get("activo", False))
                # Validar acceso a la conversación antes de difundir el indicador.
                db = SessionLocal()
                try:
                    conv = db.get(ConversacionDirecta, conv_id)
                    if not conv:
                        continue
                    if not es_admin and conv.residente_usuario_id != uid:
                        continue
                    if es_admin and not conexion.puede_ver_conjunto(conv.id_conjunto):
                        continue
                    res_uid = conv.residente_usuario_id
                    conv_cid = conv.id_conjunto
                finally:
                    db.close()

                await gestor_chat.difundir_conversacion(
                    residente_usuario_id=res_uid,
                    id_conjunto=conv_cid,
                    excluir_usuario_id=uid,
                    payload={
                        "tipo": "escribiendo",
                        "conversacion_id": conv_id,
                        "remitente_rol": "admin" if es_admin else "residente",
                        "remitente_nombre": nombre,
                        "activo": activo,
                    },
                )
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        pass
    finally:
        gestor_chat.desconectar(conexion)
