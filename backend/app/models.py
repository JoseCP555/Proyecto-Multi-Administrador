"""Modelos ORM de la base de datos (SQLAlchemy 2.0)."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey,
    Numeric, Date,
)
from sqlalchemy.orm import relationship
from app.database import Base


# ---------------------------------------------------------------------------
# USUARIOS Y ROLES
# ---------------------------------------------------------------------------
class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(60), unique=True, nullable=False)
    descripcion = Column(String(255))

    usuarios = relationship("Usuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    telefono = Column(String(30))
    correo = Column(String(255), unique=True, nullable=False, index=True)
    contrasena_hash = Column(String(255), nullable=False)
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    ultimo_acceso = Column(DateTime, nullable=True)
    id_copropiedad = Column(Integer, nullable=True)

    # Token de recuperación de contraseña
    token_recuperacion = Column(String(255), nullable=True)
    expira_token = Column(DateTime, nullable=True)
    codigo_recuperacion = Column(String(6), nullable=True)

    # Verificación de correo electrónico
    correo_verificado = Column(Boolean, default=False, nullable=False, server_default="false")
    token_verificacion = Column(String(255), nullable=True)
    expira_verificacion = Column(DateTime, nullable=True)
    codigo_verificacion = Column(String(6), nullable=True)

    rol = relationship("Rol", back_populates="usuarios")


# ---------------------------------------------------------------------------
# RBAC: PERMISOS Y PERMISOS POR ROL
# ---------------------------------------------------------------------------
class Permiso(Base):
    __tablename__ = "permisos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(120), unique=True, nullable=False, index=True)
    modulo = Column(String(60), nullable=False, index=True)
    accion = Column(String(30), nullable=False)
    descripcion = Column(String(255))


class RolPermiso(Base):
    __tablename__ = "rol_permisos"

    rol_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    permiso_id = Column(Integer, ForeignKey("permisos.id"), primary_key=True)


# ---------------------------------------------------------------------------
# RESIDENTES Y PROPIEDADES
# ---------------------------------------------------------------------------
class Residente(Base):
    __tablename__ = "residentes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    tipo = Column(String(20), default="propietario")  # propietario | inquilino
    identificacion = Column(String(30), unique=True, nullable=False)
    telefono_adicional = Column(String(30))
    contacto_emergencia = Column(String(150))
    telefono_emergencia = Column(String(30))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class Propiedad(Base):
    __tablename__ = "propiedades"

    id = Column(Integer, primary_key=True, index=True)
    residencial = Column(String(120), default="Conjunto Central")
    bloque = Column(String(30))
    torre = Column(String(30))
    apartamento = Column(String(30), nullable=False)
    piso = Column(Integer)
    area = Column(Numeric(10, 2))
    habitaciones = Column(Integer, default=0)
    banos = Column(Integer, default=0)
    parqueaderos = Column(Integer, default=0)
    estado = Column(String(30), default="ocupado")  # ocupado | vacio | mantenimiento | arrendado
    estrato = Column(Integer)
    residente_id = Column(Integer, ForeignKey("residentes.id"), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# FINANZAS
# ---------------------------------------------------------------------------
class ConceptoFinanciero(Base):
    __tablename__ = "conceptos_financieros"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(30), unique=True, nullable=False)
    nombre = Column(String(120), nullable=False)
    tipo = Column(String(20), nullable=False)  # ingreso | gasto
    monto_default = Column(Numeric(12, 2), default=0)
    recurrente = Column(Boolean, default=False)
    descripcion = Column(String(255))


class MovimientoFinanciero(Base):
    __tablename__ = "movimientos_financieros"

    id = Column(Integer, primary_key=True, index=True)
    propiedad_id = Column(Integer, ForeignKey("propiedades.id"), nullable=True)
    concepto_id = Column(Integer, ForeignKey("conceptos_financieros.id"), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    fecha_vencimiento = Column(Date, nullable=False)
    fecha_pago = Column(Date, nullable=True)
    estado = Column(String(20), default="pendiente")  # pendiente | pagado | vencido | cancelado
    numero_recibo = Column(String(50), unique=True, nullable=True)
    metodo_pago = Column(String(30))
    referencia = Column(String(100))
    notas = Column(Text)
    creado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# MANTENIMIENTO
# ---------------------------------------------------------------------------
class TareaMantenimiento(Base):
    __tablename__ = "tareas_mantenimiento"

    id = Column(Integer, primary_key=True, index=True)
    propiedad_id = Column(Integer, ForeignKey("propiedades.id"), nullable=True)
    residente_id = Column(Integer, ForeignKey("residentes.id"), nullable=True)
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=False)
    prioridad = Column(String(20), default="media")  # baja | media | alta | critica
    estado = Column(String(30), default="pendiente")  # pendiente | en_proceso | completada | rechazada
    asignado_a = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    costo_estimado = Column(Numeric(12, 2))
    fecha_programada = Column(Date)
    fecha_completada = Column(DateTime)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# DOCUMENTOS
# ---------------------------------------------------------------------------
class Documento(Base):
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text)
    ruta_archivo = Column(String(500), nullable=False)
    tipo_documento = Column(String(60))
    mime = Column(String(120))
    tamano = Column(Integer)
    propiedad_id = Column(Integer, ForeignKey("propiedades.id"), nullable=True)
    subido_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    publico = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# EVENTOS / INICIO
# ---------------------------------------------------------------------------
class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text)
    fecha = Column(Date, nullable=False)
    lugar = Column(String(150))
    creado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# CONFIGURACIÓN DEL SISTEMA
# ---------------------------------------------------------------------------
class Configuracion(Base):
    __tablename__ = "configuraciones"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String(120), unique=True, nullable=False)
    valor = Column(Text, nullable=False)
    descripcion = Column(String(255))
    actualizado = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# CHATBOT
# ---------------------------------------------------------------------------
class SesionChat(Base):
    __tablename__ = "sesiones_chat"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    titulo = Column(String(255), default="Nueva conversación")
    estado = Column(String(20), default="activa")  # activa | cerrada
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class MensajeChat(Base):
    __tablename__ = "mensajes_chat"

    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(Integer, ForeignKey("sesiones_chat.id"), nullable=False)
    rol = Column(String(20), nullable=False)  # usuario | asistente | sistema
    contenido = Column(Text, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
