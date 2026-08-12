from pydantic import BaseModel, EmailStr, field_validator

class UsuarioCreate(BaseModel):
    nombre: str
    telefono: str
    correo: EmailStr
    contrasena_hash: str  # contraseña en texto plano recibida del cliente; se hashea en crud.crear_usuario
    id_rol: int
    activo: bool = True
    id_copropiedad: int | None = None

    @field_validator("contrasena_hash")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        return v


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    telefono: str
    correo: str
    id_rol: int
    activo: bool

    class Config:
        from_attributes = True
class RecuperarPassword(BaseModel):
    correo: str


class CambiarPassword(BaseModel):
    token: str
    nueva_password: str
    
class Login(BaseModel):
    correo: str
    password: str