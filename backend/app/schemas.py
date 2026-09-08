"""Schemas Pydantic v2 para validación y serialización de la API."""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator


# ---------------------------------------------------------------------------
# USUARIOS
# ---------------------------------------------------------------------------
class UsuarioCreate(BaseModel):
    nombre: str
    telefono: Optional[str] = ""
    correo: EmailStr
    contrasena: str
    rol_id: int = 3  # por defecto 'residente'
    id_copropiedad: Optional[int] = None

    @field_validator("contrasena")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        return v


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    telefono: Optional[str]
    correo: str
    rol_id: int
    nombre_rol: Optional[str] = None
    activo: bool
    id_copropiedad: Optional[int] = None
    correo_verificado: bool = True
    permisos: Optional[List[str]] = []

    class Config:
        from_attributes = True


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[EmailStr] = None
    rol_id: Optional[int] = None
    activo: Optional[bool] = None


class Login(BaseModel):
    correo: EmailStr
    password: str


class RecuperarPassword(BaseModel):
    correo: EmailStr


class NuevaPassword(BaseModel):
    token: str
    nueva_password: str

    @field_validator("nueva_password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        return v


class ReenviarVerificacion(BaseModel):
    correo: EmailStr


class CodigoCorreo(BaseModel):
    """Correo + código de 6 dígitos (verificación de cuenta o recuperación)."""
    correo: EmailStr
    codigo: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class RolResponse(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# RESIDENTES Y PROPIEDADES
# ---------------------------------------------------------------------------
class ResidenteCreate(BaseModel):
    usuario_id: Optional[int] = None
    tipo: str = "propietario"
    identificacion: str
    telefono_adicional: Optional[str] = None
    contacto_emergencia: Optional[str] = None
    telefono_emergencia: Optional[str] = None
    activo: bool = True


class ResidenteResponse(BaseModel):
    id: int
    usuario_id: Optional[int]
    tipo: str
    identificacion: str
    telefono_adicional: Optional[str]
    contacto_emergencia: Optional[str]
    telefono_emergencia: Optional[str]
    activo: bool
    nombre: Optional[str] = None

    class Config:
        from_attributes = True


class PropiedadCreate(BaseModel):
    residencial: str = "Conjunto Central"
    bloque: Optional[str] = None
    torre: Optional[str] = None
    apartamento: str
    piso: Optional[int] = None
    area: Optional[float] = None
    habitaciones: int = 0
    banos: int = 0
    parqueaderos: int = 0
    estado: str = "ocupado"
    estrato: Optional[int] = None
    residente_id: Optional[int] = None


class PropiedadResponse(BaseModel):
    id: int
    residencial: str
    bloque: Optional[str]
    torre: Optional[str]
    apartamento: str
    piso: Optional[int]
    area: Optional[float]
    habitaciones: int
    banos: int
    parqueaderos: int
    estado: str
    estrato: Optional[int]
    residente_id: Optional[int]
    residente_nombre: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# FINANZAS
# ---------------------------------------------------------------------------
class ConceptoResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    tipo: str
    monto_default: Optional[float]
    recurrente: bool
    descripcion: Optional[str]

    class Config:
        from_attributes = True


class MovimientoCreate(BaseModel):
    propiedad_id: Optional[int] = None
    concepto_id: int
    monto: float
    fecha_vencimiento: date
    fecha_pago: Optional[date] = None
    estado: str = "pendiente"
    numero_recibo: Optional[str] = None
    metodo_pago: Optional[str] = None
    referencia: Optional[str] = None
    notas: Optional[str] = None


class MovimientoResponse(BaseModel):
    id: int
    propiedad_id: Optional[int]
    propiedad_desc: Optional[str] = None
    concepto_id: int
    concepto_nombre: str = ""
    monto: float
    fecha_vencimiento: date
    fecha_pago: Optional[date]
    estado: str
    numero_recibo: Optional[str]
    metodo_pago: Optional[str]
    referencia: Optional[str]
    notas: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# MANTENIMIENTO
# ---------------------------------------------------------------------------
class TareaCreate(BaseModel):
    propiedad_id: Optional[int] = None
    residente_id: Optional[int] = None
    titulo: str
    descripcion: str
    prioridad: str = "media"
    estado: str = "pendiente"
    asignado_a: Optional[int] = None
    costo_estimado: Optional[float] = None
    fecha_programada: Optional[date] = None


class TareaResponse(BaseModel):
    id: int
    propiedad_id: Optional[int]
    residente_id: Optional[int]
    titulo: str
    descripcion: str
    prioridad: str
    estado: str
    asignado_a: Optional[int]
    costo_estimado: Optional[float]
    fecha_programada: Optional[date]
    fecha_completada: Optional[datetime]
    fecha_creacion: datetime
    propiedad_desc: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# DOCUMENTOS
# ---------------------------------------------------------------------------
class DocumentoCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    ruta_archivo: str
    tipo_documento: Optional[str] = None
    mime: Optional[str] = None
    tamano: Optional[int] = None
    propiedad_id: Optional[int] = None
    publico: bool = False


class DocumentoResponse(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str]
    ruta_archivo: str
    tipo_documento: Optional[str]
    mime: Optional[str]
    tamano: Optional[int]
    propiedad_id: Optional[int]
    subido_por: Optional[int]
    publico: bool
    version: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# EVENTOS
# ---------------------------------------------------------------------------
class EventoCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    fecha: date
    lugar: Optional[str] = None


class EventoResponse(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str]
    fecha: date
    lugar: Optional[str]
    creado_por: Optional[int]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------
class ConfigSchema(BaseModel):
    clave: str
    valor: str
    descripcion: Optional[str]


class ConfigResponse(BaseModel):
    id: int
    clave: str
    valor: str
    descripcion: Optional[str]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# CHATBOT
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    mensaje: str
    sesion_id: Optional[int] = None


class ChatMessageResponse(BaseModel):
    id: int
    sesion_id: int
    rol: str
    contenido: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: int
    usuario_id: Optional[int]
    titulo: str
    estado: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# REPORTES / DASHBOARD
# ---------------------------------------------------------------------------
class DashboardStats(BaseModel):
    usuarios: int
    residentes: int
    propiedades: int
    pagos_pendientes: int
    pagos_pagados: int
    ingresos: float
    gastos: float
    saldo: float
    mantenimientos_pendientes: int
    mantenimientos_completados: int
    documentos: int
