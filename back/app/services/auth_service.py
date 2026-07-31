from sqlalchemy.orm import Session
import crud


def login(db: Session, correo: str, password: str):
    return crud.login_usuario(db, correo, password)


async def recuperar_password(db: Session, correo: str):
    return await crud.enviar_recuperacion(db, correo)


def cambiar_password(db: Session, token: str, nueva_password: str):
    return crud.cambiar_password(db, token, nueva_password)