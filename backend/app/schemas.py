"""Schemas Pydantic v2 para validación y serialización de la API."""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator

from app.colores import normalizar_color


# ---------------------------------------------------------------------------
# CONJUNTOS (COPROPIEDADES)
# ---------------------------------------------------------------------------
class ConjuntoBase(BaseModel):
    nombre: str
    nit: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    administrador: Optional[str] = None
    habitantes: Optional[int] = 0
    cuota: Optional[float] = 0
    dia_cobro: Optional[int] = None
    reunion: Optional[str] = None
    silencio: Optional[str] = None
    logo: Optional[str] = None
    # Id de paleta o #RRGGBB. None / "" = color automático.
    color: Optional[str] = None
    # UH-26: umbral de gasto que dispara la alerta al consejo.
    umbral_gasto: Optional[float] = 2000000
    activo: bool = True

    @field_validator("color")
    @classmethod
    def validar_color(cls, v):
        return normalizar_color(v, estricto=True)


class ConjuntoCreate(ConjuntoBase):
    pass


class ConjuntoUpdate(BaseModel):
    """Actualización parcial de un conjunto (todos los campos opcionales)."""

    nombre: Optional[str] = None
    nit: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    administrador: Optional[str] = None
    habitantes: Optional[int] = None
    cuota: Optional[float] = None
    dia_cobro: Optional[int] = None
    reunion: Optional[str] = None
    silencio: Optional[str] = None
    logo: Optional[str] = None
    color: Optional[str] = None
    umbral_gasto: Optional[float] = None
    activo: Optional[bool] = None

    @field_validator("color")
    @classmethod
    def validar_color(cls, v):
        return normalizar_color(v, estricto=True)


class ConjuntoSimple(BaseModel):
    """Conjunto reducido (id + nombre) para listados públicos (registro)."""

    id: int
    nombre: str


class ConjuntoResponse(BaseModel):
    id: int
    nombre: str
    nit: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    administrador: Optional[str] = None
    habitantes: Optional[int] = 0
    cuota: Optional[float] = 0
    dia_cobro: Optional[int] = None
    reunion: Optional[str] = None
    silencio: Optional[str] = None
    logo: Optional[str] = None
    color: Optional[str] = None
    umbral_gasto: Optional[float] = 2000000
    activo: bool = True
    fecha_creacion: Optional[datetime] = None
    # Métricas calculadas (no son columnas).
    propiedades: int = 0
    residentes: int = 0
    saldo: float = 0

    class Config:
        from_attributes = True


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
    id_conjunto: Optional[int] = None

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
    id_conjunto: Optional[int] = None
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
    identificacion: str = ""
    telefono_adicional: Optional[str] = None
    contacto_emergencia: Optional[str] = None
    telefono_emergencia: Optional[str] = None
    activo: bool = True
    # Campos integrados de UH-02 (todos opcionales para mantener compatibilidad):
    nombre: Optional[str] = None
    correo: Optional[EmailStr] = None
    contrasena: Optional[str] = None
    rol_id: Optional[int] = None
    apartamento: Optional[str] = None
    propiedad_id: Optional[int] = None


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
    correo: Optional[str] = None
    rol_id: Optional[int] = None
    nombre_rol: Optional[str] = None
    apartamento: Optional[str] = None
    propiedad_id: Optional[int] = None

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
    categoria: str = "unidad"              # zona_comun | unidad | otro (UH-21)
    evidencias: Optional[str] = None        # nombres de archivo separados por coma
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
    categoria: Optional[str] = "unidad"
    evidencias: Optional[str] = None
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
    hora: Optional[str] = None            # HH:MM (UH-04)
    tipo: str = "actividad"               # asamblea | reunion | actividad | mantenimiento
    lugar: Optional[str] = None

    @field_validator("hora")
    @classmethod
    def validar_hora(cls, v):
        if v in (None, ""):
            return None
        partes = str(v).split(":")
        if len(partes) != 2 or not all(p.isdigit() for p in partes):
            raise ValueError("La hora debe tener el formato HH:MM.")
        h, m = int(partes[0]), int(partes[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("La hora debe estar entre 00:00 y 23:59.")
        return f"{h:02d}:{m:02d}"


class EventoResponse(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str]
    fecha: date
    hora: Optional[str] = None
    tipo: Optional[str] = "actividad"
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
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    tipo: Optional[str] = None
    id_conjunto: Optional[int] = None


class ConfigResponse(BaseModel):
    id: int
    clave: str
    valor: str
    descripcion: Optional[str]
    categoria: str = "general"
    tipo: str = "texto"
    id_conjunto: Optional[int] = None
    editable: bool = True

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


# ---------------------------------------------------------------------------
# NOTIFICACIONES
# ---------------------------------------------------------------------------
class NotificacionResponse(BaseModel):
    id: int
    tipo: str
    severidad: str
    titulo: str
    mensaje: Optional[str] = None
    url: Optional[str] = None
    fecha: Optional[date] = None
    fecha_creacion: Optional[datetime] = None
    leida: bool = False
    id_conjunto: Optional[int] = None
    nombre_conjunto: Optional[str] = None

    class Config:
        from_attributes = True


class PreferenciasNotificacionResponse(BaseModel):
    correo: bool = True
    push: bool = True
    correo_configurado: bool = False
    push_configurado: bool = False
    vapid_publico: Optional[str] = None


class PreferenciasNotificacionUpdate(BaseModel):
    correo: Optional[bool] = None
    push: Optional[bool] = None


class PushSuscripcionCreate(BaseModel):
    endpoint: str
    keys: dict


class NotificacionPruebaCreate(BaseModel):
    canal: str = "todos"  # todos | correo | push | ninguno


# ---------------------------------------------------------------------------
# PQRS (UH-09 · UH-16 · UH-32)
# ---------------------------------------------------------------------------
class PqrsCreate(BaseModel):
    tipo: str = "peticion"                 # peticion | queja | reclamo | sugerencia
    categoria: str = "administracion"      # zonas_comunes | administracion | convivencia | finanzas | otra
    asunto: str = Field(min_length=3, max_length=200)
    descripcion: str = Field(min_length=5)
    adjunto: Optional[str] = None


class PqrsRespuesta(BaseModel):
    """Respuesta / cambio de estado que hace la administración."""

    estado: Optional[str] = None           # pendiente | en_proceso | cerrada
    respuesta: Optional[str] = None


class PqrsResponse(BaseModel):
    id: int
    radicado: str
    usuario_id: Optional[int]
    residente_id: Optional[int]
    tipo: str
    categoria: str
    asunto: str
    descripcion: str
    adjunto: Optional[str]
    estado: str
    respuesta: Optional[str]
    respondido_por: Optional[int]
    fecha_respuesta: Optional[datetime]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    solicitante: Optional[str] = None
    apartamento: Optional[str] = None
    respondido_por_nombre: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# ZONAS COMUNES Y RESERVAS (UH-10 · UH-14)
# ---------------------------------------------------------------------------
class ZonaComunCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    capacidad: int = 20
    hora_apertura: str = "08:00"
    hora_cierre: str = "22:00"
    requiere_aprobacion: bool = True
    activo: bool = True


class ZonaComunResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    capacidad: int
    hora_apertura: Optional[str]
    hora_cierre: Optional[str]
    requiere_aprobacion: bool
    activo: bool

    class Config:
        from_attributes = True


class ReservaCreate(BaseModel):
    zona_id: int
    fecha: date
    hora_inicio: str
    hora_fin: str
    motivo: Optional[str] = None
    asistentes: int = 1

    @field_validator("hora_inicio", "hora_fin")
    @classmethod
    def validar_hora(cls, v: str) -> str:
        partes = (v or "").split(":")
        if len(partes) != 2 or not all(p.isdigit() for p in partes):
            raise ValueError("La hora debe tener el formato HH:MM.")
        h, m = int(partes[0]), int(partes[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("Hora fuera de rango.")
        return f"{h:02d}:{m:02d}"


class ReservaResponse(BaseModel):
    id: int
    zona_id: int
    zona_nombre: Optional[str] = None
    usuario_id: Optional[int]
    solicitante: Optional[str] = None
    fecha: date
    hora_inicio: str
    hora_fin: str
    motivo: Optional[str]
    asistentes: Optional[int] = 1
    estado: str
    motivo_decision: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# COMUNICADOS (UH-11 · UH-18)
# ---------------------------------------------------------------------------
class ComunicadoCreate(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    contenido: str = Field(min_length=5)
    categoria: str = "informativo"
    prioridad: str = "media"
    fijado: bool = False


class ComunicadoResponse(BaseModel):
    id: int
    titulo: str
    contenido: str
    categoria: str
    prioridad: str
    fijado: bool
    enviado_por: Optional[int]
    autor: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# VISITANTES (UH-12)
# ---------------------------------------------------------------------------
class VisitanteCreate(BaseModel):
    nombre: str
    documento: str
    telefono: Optional[str] = None
    apartamento: str
    residente_id: Optional[int] = None
    motivo: Optional[str] = None
    observaciones: Optional[str] = None


class VisitanteResponse(BaseModel):
    id: int
    nombre: str
    documento: str
    telefono: Optional[str]
    apartamento: str
    residente_id: Optional[int]
    motivo: Optional[str]
    observaciones: Optional[str]
    hora_ingreso: datetime
    hora_salida: Optional[datetime]
    estado: str
    registrado_por: Optional[int]
    registrado_por_nombre: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# COMPROBANTES DE PAGO (UH-13 · UH-17)
# ---------------------------------------------------------------------------
class ComprobanteRevision(BaseModel):
    estado: str                              # aprobado | rechazado
    observacion: Optional[str] = None


class ComprobanteResponse(BaseModel):
    id: int
    usuario_id: int
    solicitante: Optional[str] = None
    movimiento_id: Optional[int]
    periodo: Optional[str]
    monto: float
    ruta_archivo: str
    nombre_archivo: Optional[str]
    mime: Optional[str]
    tamano: Optional[int]
    estado: str
    observacion: Optional[str]
    revisado_por: Optional[int]
    fecha_revision: Optional[datetime]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# VOTACIONES DEL CONSEJO (UH-25)
# ---------------------------------------------------------------------------
class VotacionCreate(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    descripcion: Optional[str] = None
    fecha_cierre: date
    opciones: List[str] = Field(min_length=2)


class VotoCreate(BaseModel):
    opcion_id: int


class VotacionResponse(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str]
    fecha_cierre: date
    estado: str
    creado_por: Optional[int]
    fecha_creacion: datetime
    opciones: List[dict] = []
    total_votos: int = 0
    mi_voto: Optional[int] = None
    puede_votar: bool = True
    resultados: List[dict] = []

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# APROBACIONES DEL CONSEJO (UH-24)
# ---------------------------------------------------------------------------
class AprobacionCreate(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    descripcion: str = Field(min_length=5)
    monto: float = 0
    categoria: str = "gasto"


class AprobacionDecision(BaseModel):
    estado: str                              # aprobada | rechazada
    motivo_decision: Optional[str] = None


class AprobacionResponse(BaseModel):
    id: int
    titulo: str
    descripcion: str
    monto: float
    categoria: str
    estado: str
    creado_por: Optional[int]
    creado_por_nombre: Optional[str] = None
    decidido_por: Optional[int]
    decidido_por_nombre: Optional[str] = None
    fecha_decision: Optional[datetime]
    motivo_decision: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# AUDITORÍA (UH-29)
# ---------------------------------------------------------------------------
class AuditoriaResponse(BaseModel):
    id: int
    usuario_id: Optional[int]
    usuario_nombre: Optional[str]
    usuario_rol: Optional[str]
    accion: str
    modulo: str
    metodo: Optional[str]
    ruta: Optional[str]
    entidad: Optional[str]
    entidad_id: Optional[int]
    detalle: Optional[str]
    ip: Optional[str]
    estado_http: Optional[int]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# PERFIL PROPIO (UH-20)
# ---------------------------------------------------------------------------
class PerfilUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[EmailStr] = None
    foto: Optional[str] = None       # data URI o URL de la imagen de perfil


class CambioPassword(BaseModel):
    actual: str
    nueva: str

    @field_validator("nueva")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        return v


# ---------------------------------------------------------------------------
# MENSAJERÍA DIRECTA: CHAT RESIDENTE <-> ADMINISTRACIÓN
# ---------------------------------------------------------------------------
class ConversacionDirectaCreate(BaseModel):
    residente_usuario_id: Optional[int] = None
    asunto: Optional[str] = Field(default=None, max_length=200)
    mensaje_inicial: Optional[str] = Field(default=None, max_length=4000)


class ConversacionEstadoUpdate(BaseModel):
    estado: str  # abierta | resuelta


class MensajeDirectoCreate(BaseModel):
    contenido: str = Field(min_length=1, max_length=4000)


class MensajeDirectoResponse(BaseModel):
    id: int
    conversacion_id: int
    remitente_id: Optional[int] = None
    remitente_nombre: Optional[str] = None
    remitente_foto: Optional[str] = None
    rol_remitente: str
    contenido: str
    adjunto: Optional[str] = None
    adjunto_nombre: Optional[str] = None
    adjunto_mime: Optional[str] = None
    leido: bool = False
    fecha_lectura: Optional[str] = None
    fecha_creacion: str


class ConversacionDirectaResponse(BaseModel):
    id: int
    residente_usuario_id: int
    residente_nombre: str
    residente_correo: Optional[str] = None
    residente_telefono: Optional[str] = None
    residente_foto: Optional[str] = None
    apartamento: Optional[str] = None
    id_conjunto: Optional[int] = None
    nombre_conjunto: Optional[str] = None
    asunto: str
    estado: str
    ultimo_mensaje: Optional[str] = None
    ultimo_mensaje_en: Optional[str] = None
    ultimo_remitente_rol: Optional[str] = None
    no_leidos: int = 0
    total_mensajes: int = 0
    fecha_creacion: str


class ContactoChatResponse(BaseModel):
    usuario_id: int
    nombre: str
    correo: str
    telefono: Optional[str] = None
    foto: Optional[str] = None
    apartamento: Optional[str] = None
    conversacion_id: Optional[int] = None


class ResumenNoLeidosResponse(BaseModel):
    no_leidos: int
    conversaciones_sin_leer: int

