from sqlalchemy.orm import Session
import crud
import schemas


def crear_usuario(db: Session, usuario: schemas.UsuarioCreate):
    return crud.crear_usuario(db, usuario)


def obtener_usuarios(db: Session):
    return crud.obtener_usuarios(db)