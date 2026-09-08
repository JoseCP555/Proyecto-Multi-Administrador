"""Rutas del chatbot: sesiones, historial y generación de respuestas."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, chatbot, crud
from app.models import SesionChat, MensajeChat
from app.database import get_db
from app.deps import require_permiso, get_current_user, usuario_tiene_permiso

router = APIRouter(prefix="/chat", tags=["Chatbot"], dependencies=[Depends(require_permiso("chat.usar"))])


def _serializar_m(m: MensajeChat) -> dict:
    return {
        "id": m.id, "sesion_id": m.sesion_id, "rol": m.rol,
        "contenido": m.contenido, "fecha_creacion": m.fecha_creacion,
    }


def _puede_ver_sesion(db: Session, usuario, sesion: SesionChat) -> bool:
    """Cada usuario ve solo sus sesiones; quien gestiona usuarios ve todas."""
    return sesion.usuario_id == usuario.id or usuario_tiene_permiso(db, usuario, "usuarios.ver")


@router.get("/sesiones")
def listar_sesiones(
    usuario_id: int = None,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(SesionChat)
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
):
    """Recibe un mensaje, lo guarda y devuelve la respuesta del asistente."""
    if not data.mensaje.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    if data.sesion_id:
        sesion = db.query(SesionChat).get(data.sesion_id)
        if not sesion:
            raise HTTPException(status_code=404, detail="Sesión no encontrada.")
        if not _puede_ver_sesion(db, usuario, sesion):
            raise HTTPException(status_code=403, detail="No puedes escribir en esta conversación.")
    else:
        sesion = chatbot.crear_sesion(db, usuario_id=usuario.id)

    # Guardar mensaje del usuario
    chatbot.guardar_mensaje(db, sesion.id, "usuario", data.mensaje)

    # Generar respuesta (motor local basado en la BD)
    respuesta = chatbot.responder(db, data.mensaje, permisos=crud.obtener_permisos_rol(db, usuario.rol_id))
    chatbot.cambiar_titulo_si_necesario(db, sesion.id, data.mensaje)

    # Guardar respuesta del asistente
    mensaje_resp = chatbot.guardar_mensaje(db, sesion.id, "asistente", respuesta)

    return {
        "sesion_id": sesion.id,
        "respuesta": respuesta,
        "mensaje": _serializar_m(mensaje_resp),
    }
