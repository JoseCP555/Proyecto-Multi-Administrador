from pydantic import BaseModel

class UsuarioCreate(BaseModel):
    nombre: str
    telefono: str
    correo: str
    contrasena_hash: str
    id_rol: int
    activo: bool = True
    id_copropiedad: int | None = None


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