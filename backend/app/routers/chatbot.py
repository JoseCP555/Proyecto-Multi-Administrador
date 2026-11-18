"""Rutas del chatbot: estado de Ollama, sesiones, historial y respuestas."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, chatbot, crud
from app.models import SesionChat, MensajeChat
from app.database import get_db
from app.deps import require_permiso, get_current_user, usuario_tiene_permiso
from app.conjunto_ctx import conjunto_activo, filtrar
from app.ollama_client import estado_ollama

router = APIRouter(prefix="/chat", tags=["Chatbot"], dependencies=[Depends(require_permiso("chat.usar"))])


def _serializar_m(m: MensajeChat) -> dict:
    return {
        "id": m.id, "sesion_id": m.sesion_id, "rol": m.rol,
        "contenido": m.contenido, "fecha_creacion": m.fecha_creacion,
    }


def _puede_ver_sesion(db: Session, usuario, sesion: SesionChat) -> bool:
    """Cada usuario ve solo sus sesiones; quien gestiona usuarios ve todas."""
    return sesion.usuario_id == usuario.id or usuario_tiene_permiso(db, usuario, "usuarios.ver")


@router.get("/estado")
def estado_chatbot(db: Session = Depends(get_db)):
    """Informa el motor configurado (`ollama` o `local`) y el estado real de Ollama."""
    motor, modelo = chatbot.obtener_config_chatbot(db)
    if motor == "local":
        return {
            "motor_configurado": "local",
            "ollama_disponible": False,
            "ollama_version": None,
            "ollama_url": None,
            "modelo": None,
            "modelo_instalado": False,
            "modelos_disponibles": [],
            "detalle": "Motor local por reglas activo.",
        }

    info = estado_ollama(modelo=modelo)
    return {
        "motor_configurado": "ollama",
        "ollama_disponible": info["disponible"],
        "ollama_version": info["version"],
        "ollama_url": info["url"],
        "modelo": info["modelo"],
        "modelo_instalado": info["modelo_instalado"],
        "modelos_disponibles": info["modelos_disponibles"],
        "detalle": info["detalle"],
    }


@router.get("/sesiones")
def listar_sesiones(
    usuario_id: int = None,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
):
    q = filtrar(db.query(SesionChat), SesionChat, cid)
    if usuario_tiene_permiso(db, usuario, "usuarios.ver"):
        if usuario_id:
            q = q.filter(SesionChat.usuario_id == usuario_id)
    else:
        q = q.filter(SesionChat.usuario_id == usuario.id)
    return q.order_by(SesionChat.fecha_creacion.desc()).all()


@router.get("/sesiones/{sesion_id}/mensajes", response_model=list[schemas.ChatMessageResponse])
def mensajes(sesion_id: int, usuario=Depends(get_current_user), db: Session = Depends(get_db)):
    sesion = db.query(SesionChat).get(sesion_id)
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    if not _puede_ver_sesion(db, usuario, sesion):
        raise HTTPException(status_code=403, detail="No puedes ver esta conversación.")
    return db.query(MensajeChat).filter(MensajeChat.sesion_id == sesion_id).order_by(
        MensajeChat.fecha_creacion.asc()
    ).all()


@router.post("/ask")
def ask(
    data: schemas.ChatRequest,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
):
    """Recibe un mensaje, lo guarda y devuelve la respuesta del asistente (Ollama + respaldo local)."""
    if not data.mensaje.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    if data.sesion_id:
        sesion = db.query(SesionChat).get(data.sesion_id)
        if not sesion:
            raise HTTPException(status_code=404, detail="Sesión no encontrada.")
        if not _puede_ver_sesion(db, usuario, sesion):
            raise HTTPException(status_code=403, detail="No puedes escribir en esta conversación.")
        previos = (
            db.query(MensajeChat)
            .filter(MensajeChat.sesion_id == sesion.id)
            .order_by(MensajeChat.fecha_creacion.asc(), MensajeChat.id.asc())
            .all()
        )
        historial = [(m.rol, m.contenido) for m in previos[-10:]]
    else:
        sesion = chatbot.crear_sesion(db, usuario_id=usuario.id, id_conjunto=cid)
        historial = []

    # Guardar mensaje del usuario
    chatbot.guardar_mensaje(db, sesion.id, "usuario", data.mensaje)

    # Generar respuesta (Ollama con contexto RBAC del conjunto o respaldo local)
    resultado = chatbot.responder_con_detalle(
        db,
        data.mensaje,
        permisos=crud.obtener_permisos_rol(db, usuario.rol_id),
        id_conjunto=cid,
        historial=historial,
        usuario=usuario,
    )
    respuesta = resultado["respuesta"] or ""
    chatbot.cambiar_titulo_si_necesario(db, sesion.id, data.mensaje)

    # Guardar respuesta del asistente
    mensaje_resp = chatbot.guardar_mensaje(db, sesion.id, "asistente", respuesta)

    return {
        "sesion_id": sesion.id,
        "respuesta": respuesta,
        "motor_usado": resultado["motor_usado"],
        "modelo": resultado["modelo"],
        "mensaje": _serializar_m(mensaje_resp),
    }
