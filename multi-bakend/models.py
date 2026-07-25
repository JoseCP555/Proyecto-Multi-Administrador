from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)

    nombre = Column(String, nullable=False)
    telefono = Column(String)
    correo = Column(String, unique=True, nullable=False)
    contrasena_hash = Column(String, nullable=False)
    id_rol = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime)
    id_copropiedad = Column(Integer)

    # Campos para recuperación de contraseña
    token_recuperacion = Column(String, nullable=True)
    expira_token = Column(DateTime, nullable=True)