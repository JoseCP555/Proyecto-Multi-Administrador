"""Modelos ORM de la base de datos (SQLAlchemy 2.0)."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey,
    Numeric, Date, UniqueConstraint, Index, text as sa_text,
)
from sqlalchemy.orm import relationship
from app.database import Base


# ---------------------------------------------------------------------------
# CONJUNTOS (COPROPIEDADES) Y USUARIOS DE CADA CONJUNTO
# ---------------------------------------------------------------------------
class Conjunto(Base):
    """Cada copropiedad / conjunto residencial gestionado por la plataforma.

    Todos los datos operativos (residentes, propiedades, finanzas,
    mantenimientos, documentos y eventos) quedan ligados a un conjunto
    mediante la columna `id_conjunto`, de modo que cambiar de conjunto
    cambia el contexto de trabajo sin cerrar sesión (HU-07).
    """

    __tablename__ = "conjuntos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), unique=True, nullable=False)
    nit = Column(String(30))
    direccion = Column(String(200))
    ciudad = Column(String(80))
    telefono = Column(String(30))
    correo = Column(String(255))
    administrador = Column(String(150))
    # "habitantes" es el dato declarado por el conjunto (no se calcula).
    habitantes = Column(Integer, default=0)
    cuota = Column(Numeric(12, 2), default=0)
    dia_cobro = Column(Integer)
    reunion = Column(String(120))     # ej: "solo propietarios" | "todos los residentes"
    silencio = Column(String(60))     # ej: "22:00 - 06:00"
    logo = Column(String(500))
    # Color del tema: id de paleta ("azul", "verde", ...) o hexadecimal
    # "#RRGGBB". NULL = automático según la posición en la lista.
    color = Column(String(20))
    # UH-26: umbral de gasto que dispara la alerta al consejo.
    umbral_gasto = Column(Numeric(12, 2), default=2000000)
    activo = Column(Boolean, default=True, nullable=False, server_default="true")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class UsuarioConjunto(Base):
    """Asignación de un usuario a los conjuntos que tiene a su cargo."""

    __tablename__ = "usuario_conjuntos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    conjunto_id = Column(Integer, ForeignKey("conjuntos.id", ondelete="CASCADE"), nullable=False, index=True)


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
    id_copropiedad = Column(Integer, ForeignKey("conjuntos.id", ondelete="SET NULL"), nullable=True, index=True)  # heredado
    # Conjunto al que pertenece el usuario (contexto por defecto).
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id"), nullable=True, index=True)

    # Token de recuperación de contraseña
    token_recuperacion = Column(String(255), nullable=True)
    expira_token = Column(DateTime, nullable=True)
    codigo_recuperacion = Column(String(6), nullable=True)

    # Verificación de correo electrónico
    correo_verificado = Column(Boolean, default=False, nullable=False, server_default="false")
    token_verificacion = Column(String(255), nullable=True)
    expira_verificacion = Column(DateTime, nullable=True)
    codigo_verificacion = Column(String(6), nullable=True)

    # Preferencias de entrega de notificaciones (se pueden cambiar desde la
    # campana del dashboard). Por defecto ambos canales activados.
    notificaciones_correo = Column(Boolean, default=True, nullable=False, server_default="true")
    notificaciones_push = Column(Boolean, default=True, nullable=False, server_default="true")

    # Foto de perfil (data URI o URL) — UH-20.
    foto = Column(Text, nullable=True)

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
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id"), nullable=True, index=True)
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
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id"), nullable=True, index=True)
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
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id"), nullable=True, index=True)
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
    # UH-21: reportar daños/novedades en zonas comunes con fotos.
    categoria = Column(String(30), default="unidad")  # zona_comun | unidad | otro
    evidencias = Column(Text)                          # nombres de archivo separados por coma
    prioridad = Column(String(20), default="media")  # baja | media | alta | critica
    estado = Column(String(30), default="pendiente")  # pendiente | en_proceso | completada | rechazada
    asignado_a = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    costo_estimado = Column(Numeric(12, 2))
    fecha_programada = Column(Date)
    fecha_completada = Column(DateTime)
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id"), nullable=True, index=True)
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
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id"), nullable=True, index=True)
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
    hora = Column(String(5))            # HH:MM (UH-04)
    tipo = Column(String(30), default="actividad")  # asamblea | reunion | actividad | mantenimiento
    lugar = Column(String(150))
    # Evita repetir el aviso de "faltan menos de 48 horas" (UH-01).
    notificado_48h = Column(Boolean, default=False, nullable=False, server_default="false")
    creado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id"), nullable=True, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# CONFIGURACIÓN DEL SISTEMA
# ---------------------------------------------------------------------------
class Configuracion(Base):
    """Parámetro del sistema (clave/valor), global o por conjunto.

    * `categoria`   agrupa los parámetros en el panel (general, finanzas, ...).
    * `tipo`        texto | numero | booleano | json (cómo leer `valor`).
    * `id_conjunto` NULL = global; con valor = sobreescribe el global para ese conjunto.
    * `editable`    False = informativo, no se modifica desde el panel.
    """

    __tablename__ = "configuraciones"
    __table_args__ = (
        Index("uq_config_global", "clave", unique=True,
              postgresql_where=sa_text("id_conjunto IS NULL"),
              sqlite_where=sa_text("id_conjunto IS NULL")),
        Index("uq_config_conjunto", "clave", "id_conjunto", unique=True,
              postgresql_where=sa_text("id_conjunto IS NOT NULL"),
              sqlite_where=sa_text("id_conjunto IS NOT NULL")),
    )

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String(120), nullable=False)
    valor = Column(Text, nullable=False)
    descripcion = Column(String(255))
    categoria = Column(String(40), nullable=False, default="general", server_default="general")
    tipo = Column(String(20), nullable=False, default="texto", server_default="texto")
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id", ondelete="CASCADE"), nullable=True, index=True)
    editable = Column(Boolean, nullable=False, default=True, server_default="true")
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
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id"), nullable=True, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class MensajeChat(Base):
    __tablename__ = "mensajes_chat"

    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(Integer, ForeignKey("sesiones_chat.id"), nullable=False)
    rol = Column(String(20), nullable=False)  # usuario | asistente | sistema
    contenido = Column(Text, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# NOTIFICACIONES REALES
# ---------------------------------------------------------------------------
class Notificacion(Base):
    """Aviso persistente para un usuario concreto.

    A diferencia de los recordatorios calculados al vuelo, estas filas nacen
    cuando ocurre algo real en el sistema (o cuando el generador detecta una
    mora / vencimiento), se pueden marcar como leídas o descartar y registran
    por qué canal ya se entregaron. `referencia` evita duplicados: un mismo
    evento nunca genera dos avisos para la misma persona.
    """

    __tablename__ = "notificaciones"
    __table_args__ = (
        UniqueConstraint("usuario_id", "referencia", name="uq_notificacion_usuario_referencia"),
    )

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id", ondelete="CASCADE"), nullable=True, index=True)
    tipo = Column(String(40), nullable=False, index=True)  # mora | proximo | evento | mantenimiento | ...
    severidad = Column(String(10), default="media", nullable=False)  # alta | media | baja
    titulo = Column(String(200), nullable=False)
    mensaje = Column(Text)
    url = Column(String(200))            # ruta del frontend al hacer clic
    fecha = Column(Date)                 # fecha del hecho (opcional)
    referencia = Column(String(160), nullable=False)  # deduplicación
    leida = Column(Boolean, default=False, nullable=False, server_default="false")
    descartada = Column(Boolean, default=False, nullable=False, server_default="false")
    fecha_lectura = Column(DateTime)
    enviada_correo = Column(Boolean, default=False, nullable=False, server_default="false")
    enviada_push = Column(Boolean, default=False, nullable=False, server_default="false")
    fecha_creacion = Column(DateTime, default=datetime.utcnow, index=True)


class PushSuscripcion(Base):
    """Suscripción Web Push (VAPID) de un navegador para un usuario."""

    __tablename__ = "push_suscripciones"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(Text, nullable=False, unique=True)
    p256dh = Column(Text, nullable=False)
    auth = Column(Text, nullable=False)
    activa = Column(Boolean, default=True, nullable=False, server_default="true")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


# ===========================================================================
# MÓDULOS DE LAS HISTORIAS DE USUARIO UH-09 a UH-32
# ===========================================================================
# Todas las tablas llevan `id_conjunto` para respetar el aislamiento entre
# copropiedades (HU-07) y se crean de forma aditiva: `create_all` y las
# migraciones ligeras de `main.py` las añaden a una base ya existente.
# ---------------------------------------------------------------------------


class Pqrs(Base):
    """PQRS: petición, queja, reclamo o sugerencia (UH-09 / UH-16 / UH-32)."""

    __tablename__ = "pqrs"

    id = Column(Integer, primary_key=True, index=True)
    radicado = Column(String(30), unique=True, nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    residente_id = Column(Integer, ForeignKey("residentes.id", ondelete="SET NULL"), nullable=True)
    tipo = Column(String(20), nullable=False)          # peticion | queja | reclamo | sugerencia
    categoria = Column(String(40), nullable=False)     # zonas_comunes | administracion | convivencia | finanzas | otra
    asunto = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    adjunto = Column(String(500))                      # ruta del archivo opcional
    estado = Column(String(20), default="pendiente", nullable=False)  # pendiente | en_proceso | cerrada
    respuesta = Column(Text)
    respondido_por = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    fecha_respuesta = Column(DateTime)
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id", ondelete="SET NULL"), nullable=True, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ZonaComun(Base):
    """Zona común reservable: salón, BBQ, piscina, cancha, etc. (UH-10 / UH-14)."""

    __tablename__ = "zonas_comunes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    descripcion = Column(Text)
    capacidad = Column(Integer, default=20)
    hora_apertura = Column(String(5), default="08:00")   # HH:MM
    hora_cierre = Column(String(5), default="22:00")
    requiere_aprobacion = Column(Boolean, default=True, nullable=False, server_default="true")
    activo = Column(Boolean, default=True, nullable=False, server_default="true")
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id", ondelete="CASCADE"), nullable=True, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class ReservaZona(Base):
    """Reserva de una zona común por parte de un residente (UH-10 / UH-14)."""

    __tablename__ = "reservas_zonas"

    id = Column(Integer, primary_key=True, index=True)
    zona_id = Column(Integer, ForeignKey("zonas_comunes.id", ondelete="CASCADE"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    hora_inicio = Column(String(5), nullable=False)     # HH:MM
    hora_fin = Column(String(5), nullable=False)
    motivo = Column(String(255))
    asistentes = Column(Integer, default=1)
    estado = Column(String(20), default="pendiente", nullable=False)  # pendiente | aprobada | rechazada | cancelada
    motivo_decision = Column(String(255))
    decidido_por = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    fecha_decision = Column(DateTime)
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id", ondelete="SET NULL"), nullable=True, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class Comunicado(Base):
    """Comunicado o circular masiva para los residentes (UH-11 / UH-18)."""

    __tablename__ = "comunicados"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    contenido = Column(Text, nullable=False)
    categoria = Column(String(30), default="informativo")  # informativo | normas | evento | urgente
    prioridad = Column(String(10), default="media", nullable=False)  # alta | media | baja
    fijado = Column(Boolean, default=False, nullable=False, server_default="false")
    enviado_por = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id", ondelete="SET NULL"), nullable=True, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class Visitante(Base):
    """Registro y control de acceso de visitantes (UH-12)."""

    __tablename__ = "visitantes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    documento = Column(String(30), nullable=False, index=True)
    telefono = Column(String(30))
    apartamento = Column(String(30), nullable=False)
    residente_id = Column(Integer, ForeignKey("residentes.id", ondelete="SET NULL"), nullable=True)
    motivo = Column(String(200))
    observaciones = Column(Text)
    hora_ingreso = Column(DateTime, default=datetime.utcnow, nullable=False)
    hora_salida = Column(DateTime)
    estado = Column(String(20), default="dentro", nullable=False)  # dentro | salio
    registrado_por = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id", ondelete="SET NULL"), nullable=True, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class ComprobantePago(Base):
    """Comprobante de pago subido por el residente (UH-13)."""

    __tablename__ = "comprobantes_pago"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    movimiento_id = Column(Integer, ForeignKey("movimientos_financieros.id", ondelete="SET NULL"), nullable=True)
    periodo = Column(String(30))                       # ej. "2026-11"
    monto = Column(Numeric(12, 2), nullable=False)
    ruta_archivo = Column(String(500), nullable=False)
    nombre_archivo = Column(String(255))
    mime = Column(String(120))
    tamano = Column(Integer)
    estado = Column(String(20), default="en_revision", nullable=False)  # en_revision | aprobado | rechazado
    observacion = Column(Text)
    revisado_por = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    fecha_revision = Column(DateTime)
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id", ondelete="SET NULL"), nullable=True, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class Votacion(Base):
    """Votación del consejo de administración (UH-25)."""

    __tablename__ = "votaciones"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    fecha_cierre = Column(Date, nullable=False)
    estado = Column(String(20), default="abierta", nullable=False)  # abierta | cerrada
    creado_por = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id", ondelete="SET NULL"), nullable=True, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class VotacionOpcion(Base):
    __tablename__ = "votacion_opciones"

    id = Column(Integer, primary_key=True, index=True)
    votacion_id = Column(Integer, ForeignKey("votaciones.id", ondelete="CASCADE"), nullable=False, index=True)
    texto = Column(String(200), nullable=False)
    orden = Column(Integer, default=0)


class Voto(Base):
    """Un voto por miembro del consejo y votación (único)."""

    __tablename__ = "votos"
    __table_args__ = (
        UniqueConstraint("votacion_id", "usuario_id", name="uq_voto_votacion_usuario"),
    )

    id = Column(Integer, primary_key=True, index=True)
    votacion_id = Column(Integer, ForeignKey("votaciones.id", ondelete="CASCADE"), nullable=False, index=True)
    opcion_id = Column(Integer, ForeignKey("votacion_opciones.id", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class SolicitudAprobacion(Base):
    """Solicitud del administrador que el consejo aprueba o rechaza (UH-24)."""

    __tablename__ = "solicitudes_aprobacion"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    monto = Column(Numeric(12, 2), nullable=False, default=0)
    categoria = Column(String(40), default="gasto")   # gasto | contrato | presupuesto | otro
    estado = Column(String(20), default="pendiente", nullable=False)  # pendiente | aprobada | rechazada
    creado_por = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    decidido_por = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    fecha_decision = Column(DateTime)
    motivo_decision = Column(Text)
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id", ondelete="SET NULL"), nullable=True, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class Auditoria(Base):
    """Historial de auditoría de acciones (UH-29).

    Se escribe automáticamente desde `app.auditoria` para toda operación que
    modifica datos y no se puede eliminar desde la interfaz: sólo existe el
    endpoint de consulta (sin DELETE), de modo que un usuario común no puede
    borrar la trazabilidad.
    """

    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    usuario_nombre = Column(String(150))
    usuario_rol = Column(String(60))
    accion = Column(String(30), nullable=False, index=True)   # crear | editar | eliminar | login | logout | consultar
    modulo = Column(String(60), nullable=False, index=True)
    metodo = Column(String(10))
    ruta = Column(String(255))
    entidad = Column(String(80))
    entidad_id = Column(Integer)
    detalle = Column(Text)
    ip = Column(String(60))
    estado_http = Column(Integer)
    id_conjunto = Column(Integer, ForeignKey("conjuntos.id", ondelete="SET NULL"), nullable=True, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, index=True)


# ---------------------------------------------------------------------------
# MENSAJERÍA DIRECTA: CHAT RESIDENTE <-> ADMINISTRACIÓN
# ---------------------------------------------------------------------------
class ConversacionDirecta(Base):
    """Hilo de chat directo entre un residente y la administración de su conjunto.

    Cada residente tiene una conversación continua por conjunto con el equipo
    de administración (roles `admin` / `super_admin`). Respeta el aislamiento
    multi-conjunto (`id_conjunto`).
    """

    __tablename__ = "conversaciones_directas"

    id = Column(Integer, primary_key=True, index=True)
    residente_usuario_id = Column(
        Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    id_conjunto = Column(
        Integer, ForeignKey("conjuntos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    asunto = Column(String(200), default="Chat con Administración", nullable=False)
    estado = Column(String(20), default="abierta", nullable=False)  # abierta | resuelta
    ultimo_mensaje = Column(Text, nullable=True)
    ultimo_mensaje_en = Column(DateTime, nullable=True, index=True)
    ultimo_remitente_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    ultimo_remitente_rol = Column(String(20), nullable=True)  # residente | admin
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class MensajeDirecto(Base):
    """Mensaje individual dentro de una conversación directa residente <-> admin."""

    __tablename__ = "mensajes_directos"

    id = Column(Integer, primary_key=True, index=True)
    conversacion_id = Column(
        Integer, ForeignKey("conversaciones_directas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    remitente_id = Column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    rol_remitente = Column(String(20), nullable=False)  # residente | admin
    contenido = Column(Text, nullable=False)
    adjunto = Column(String(500), nullable=True)
    adjunto_nombre = Column(String(255), nullable=True)
    adjunto_mime = Column(String(120), nullable=True)
    leido = Column(Boolean, default=False, nullable=False, server_default="false")
    fecha_lectura = Column(DateTime, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, index=True)

