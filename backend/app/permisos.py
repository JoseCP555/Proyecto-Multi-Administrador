"""Fuente única de verdad del RBAC: catálogo de permisos y matriz rol → permisos.

`sincronizar_permisos()` se ejecuta al arrancar la API y deja la BD alineada con
esta matriz (idempotente): crea los permisos que falten y ajusta `rol_permisos`
de los 5 roles del sistema. Así `db/init.sql` y el backend nunca divergen.

Roles (IDs fijos): 1 = super_admin · 2 = admin · 3 = residente · 4 = tesoreria
· 5 = seguridad · 6 = consejo

Los permisos de los módulos nuevos (PQRS, reservas, comunicados, visitantes,
comprobantes de pago, votaciones, aprobaciones y auditoría) corresponden a las
historias UH-09 a UH-32.
"""
import logging
from sqlalchemy.orm import Session

from app.models import Rol, Permiso, RolPermiso

logger = logging.getLogger(__name__)

SUPER_ADMIN, ADMIN, RESIDENTE, TESORERIA, SEGURIDAD, CONSEJO = 1, 2, 3, 4, 5, 6

ROLES = {
    SUPER_ADMIN: ("super_admin", "Acceso total al sistema"),
    ADMIN: ("admin", "Administrador del conjunto"),
    RESIDENTE: ("residente", "Residente propietario o inquilino"),
    TESORERIA: ("tesoreria", "Encargado de finanzas"),
    SEGURIDAD: ("seguridad", "Personal de vigilancia"),
    CONSEJO: ("consejo", "Miembro del consejo de administración"),
}

# (codigo, modulo, accion, descripcion)
CATALOGO = [
    ("dashboard.ver", "dashboard", "ver", "Ver el panel de control"),
    ("reportes.ver", "reportes", "ver", "Ver reportes, estadísticas y exportaciones"),
    ("usuarios.ver", "usuarios", "ver", "Ver usuarios"),
    ("usuarios.crear", "usuarios", "crear", "Crear usuarios con cualquier rol"),
    ("usuarios.editar", "usuarios", "editar", "Editar / activar-desactivar usuarios"),
    ("usuarios.eliminar", "usuarios", "eliminar", "Eliminar usuarios"),
    ("residentes.ver", "residentes", "ver", "Ver residentes"),
    ("residentes.crear", "residentes", "crear", "Crear residentes"),
    ("residentes.editar", "residentes", "editar", "Editar residentes"),
    ("residentes.eliminar", "residentes", "eliminar", "Eliminar residentes"),
    ("propiedades.ver", "propiedades", "ver", "Ver propiedades"),
    ("propiedades.crear", "propiedades", "crear", "Crear propiedades"),
    ("propiedades.editar", "propiedades", "editar", "Editar propiedades"),
    ("propiedades.eliminar", "propiedades", "eliminar", "Eliminar propiedades"),
    ("finanzas.ver", "finanzas", "ver", "Ver movimientos financieros"),
    ("finanzas.crear", "finanzas", "crear", "Registrar movimientos"),
    ("finanzas.editar", "finanzas", "editar", "Editar movimientos"),
    ("finanzas.eliminar", "finanzas", "eliminar", "Eliminar movimientos"),
    ("mantenimiento.ver", "mantenimiento", "ver", "Ver tareas de mantenimiento"),
    ("mantenimiento.crear", "mantenimiento", "crear", "Crear tareas / solicitudes"),
    ("mantenimiento.editar", "mantenimiento", "editar", "Editar / completar tareas"),
    ("mantenimiento.eliminar", "mantenimiento", "eliminar", "Eliminar tareas"),
    ("documentos.ver", "documentos", "ver", "Ver listado de documentos"),
    ("documentos.crear", "documentos", "crear", "Subir documentos"),
    ("documentos.editar", "documentos", "editar", "Editar documentos"),
    ("documentos.eliminar", "documentos", "eliminar", "Eliminar documentos"),
    ("documentos.descargar", "documentos", "descargar", "Descargar archivos"),
    ("eventos.ver", "eventos", "ver", "Ver eventos"),
    ("eventos.crear", "eventos", "crear", "Crear eventos"),
    ("eventos.editar", "eventos", "editar", "Editar eventos"),
    ("eventos.eliminar", "eventos", "eliminar", "Eliminar eventos"),
    ("config.ver", "config", "ver", "Ver configuración del sistema"),
    ("config.editar", "config", "editar", "Editar configuración"),
    ("conjuntos.ver", "conjuntos", "ver", "Ver el panel de conjuntos / copropiedades"),
    ("conjuntos.crear", "conjuntos", "crear", "Crear conjuntos"),
    ("conjuntos.editar", "conjuntos", "editar", "Editar conjuntos"),
    ("conjuntos.eliminar", "conjuntos", "eliminar", "Desactivar conjuntos"),
    ("conjuntos.gestionar", "conjuntos", "gestionar", "Administrar TODOS los conjuntos del sistema"),
    ("chat.usar", "chat", "usar", "Usar el chatbot / asistente"),
    ("sistema.respaldar", "sistema", "respaldar", "Generar respaldo de la base de datos"),
    # --- UH-09 / UH-16 / UH-32: PQRS -------------------------------------
    ("pqrs.ver", "pqrs", "ver", "Ver las PQRS del conjunto"),
    ("pqrs.crear", "pqrs", "crear", "Radicar una PQRS"),
    ("pqrs.responder", "pqrs", "responder", "Responder / poner en proceso una PQRS"),
    ("pqrs.cerrar", "pqrs", "cerrar", "Cerrar una PQRS"),
    ("pqrs.eliminar", "pqrs", "eliminar", "Eliminar una PQRS"),
    # --- UH-10 / UH-14: zonas comunes y reservas --------------------------
    ("zonas.ver", "zonas", "ver", "Ver las zonas comunes"),
    ("zonas.crear", "zonas", "crear", "Crear zonas comunes"),
    ("zonas.editar", "zonas", "editar", "Editar zonas comunes"),
    ("zonas.eliminar", "zonas", "eliminar", "Eliminar zonas comunes"),
    ("reservas.ver", "reservas", "ver", "Ver las reservas de zonas comunes"),
    ("reservas.crear", "reservas", "crear", "Solicitar una reserva"),
    ("reservas.gestionar", "reservas", "gestionar", "Aprobar, rechazar o cancelar reservas"),
    # --- UH-11 / UH-18: comunicados ---------------------------------------
    ("comunicados.ver", "comunicados", "ver", "Ver comunicados y circulares"),
    ("comunicados.crear", "comunicados", "crear", "Publicar comunicados"),
    ("comunicados.editar", "comunicados", "editar", "Editar comunicados"),
    ("comunicados.eliminar", "comunicados", "eliminar", "Eliminar comunicados"),
    # --- UH-12: visitantes ------------------------------------------------
    ("visitantes.ver", "visitantes", "ver", "Ver el historial de visitantes"),
    ("visitantes.crear", "visitantes", "crear", "Registrar el ingreso de visitantes"),
    ("visitantes.editar", "visitantes", "editar", "Registrar la salida / editar visitantes"),
    ("visitantes.eliminar", "visitantes", "eliminar", "Eliminar registros de visitantes"),
    # --- UH-13 / UH-17: comprobantes y estado de cuenta -------------------
    ("pagos.ver", "pagos", "ver", "Ver comprobantes de pago y estados de cuenta"),
    ("pagos.crear", "pagos", "crear", "Subir un comprobante de pago"),
    ("pagos.revisar", "pagos", "revisar", "Aprobar o rechazar comprobantes de pago"),
    # --- UH-25: votaciones del consejo ------------------------------------
    ("votaciones.ver", "votaciones", "ver", "Ver las votaciones"),
    ("votaciones.crear", "votaciones", "crear", "Crear votaciones"),
    ("votaciones.votar", "votaciones", "votar", "Votar en una votación abierta"),
    ("votaciones.cerrar", "votaciones", "cerrar", "Cerrar una votación"),
    # --- UH-24: aprobaciones del consejo ----------------------------------
    ("aprobaciones.ver", "aprobaciones", "ver", "Ver las solicitudes enviadas al consejo"),
    ("aprobaciones.crear", "aprobaciones", "crear", "Enviar una solicitud al consejo"),
    ("aprobaciones.decidir", "aprobaciones", "decidir", "Aprobar o rechazar solicitudes"),
    # --- UH-29: auditoría --------------------------------------------------
    ("auditoria.ver", "auditoria", "ver", "Consultar el historial de auditoría"),
    # --- UH-20: perfil propio ---------------------------------------------
    ("perfil.ver", "perfil", "ver", "Ver el perfil propio"),
    ("perfil.editar", "perfil", "editar", "Actualizar los datos personales"),
    # --- Chat directo residente <-> administrador -------------------------
    ("mensajes.ver", "mensajes", "ver", "Ver conversaciones del chat con la administración"),
    ("mensajes.enviar", "mensajes", "enviar", "Enviar mensajes en el chat con la administración"),
    ("mensajes.gestionar", "mensajes", "gestionar", "Ver y responder conversaciones de todos los residentes"),
]

TODOS = [c[0] for c in CATALOGO]

# Históricamente el rol admin no podía eliminar usuarios, respaldar la BD ni
# gestionar todos los conjuntos. Ahora **admin y super_admin son equivalentes**:
# el conjunto queda vacío para que la matriz le asigne TODOS los permisos.
SOLO_SUPER_ADMIN: set[str] = set()

# Roles con acceso total (se usan en comprobaciones puntuales donde no basta
# mirar un permiso, p. ej. "¿puede tocar cuentas super_admin?").
ROLES_ACCESO_TOTAL = {SUPER_ADMIN, ADMIN}


def tiene_acceso_total(usuario) -> bool:
    """¿El usuario pertenece a un rol con acceso total (super_admin o admin)?"""
    return getattr(usuario, "rol_id", None) in ROLES_ACCESO_TOTAL


MATRIZ: dict[int, set[str]] = {
    SUPER_ADMIN: set(TODOS),
    ADMIN: set(TODOS) - SOLO_SUPER_ADMIN,  # = TODOS: igual que super_admin
    # Tesorería: finanzas completas, reportes, documentos (lectura), chatbot.
    TESORERIA: {
        "dashboard.ver", "reportes.ver", "conjuntos.ver",
        "finanzas.ver", "finanzas.crear", "finanzas.editar", "finanzas.eliminar",
        "propiedades.ver", "residentes.ver",
        "documentos.ver", "documentos.descargar",
        "chat.usar",
        "pagos.ver", "pagos.revisar",
        "comunicados.ver", "pqrs.ver",
        "perfil.ver", "perfil.editar",
    },
    # Residente: lectura de su conjunto, crear solicitudes de mantenimiento, chatbot.
    RESIDENTE: {
        "dashboard.ver", "conjuntos.ver",
        "propiedades.ver",
        "documentos.ver", "documentos.descargar",
        "eventos.ver",
        "mantenimiento.ver", "mantenimiento.crear",
        "chat.usar",
        # Módulos de autoservicio del residente (UH-13, UH-14, UH-16,
        # UH-17, UH-18, UH-20, UH-21, UH-25).
        "pqrs.ver", "pqrs.crear",
        "zonas.ver", "reservas.ver", "reservas.crear",
        "comunicados.ver",
        "pagos.ver", "pagos.crear",
        "votaciones.ver", "votaciones.votar",
        "perfil.ver", "perfil.editar",
        "mensajes.ver", "mensajes.enviar",
    },
    # Seguridad: lectura operativa + puede actualizar estado de mantenimientos
    # y gestionar el control de acceso de visitantes (UH-12).
    SEGURIDAD: {
        "dashboard.ver", "conjuntos.ver",
        "propiedades.ver", "residentes.ver",
        "mantenimiento.ver", "mantenimiento.crear", "mantenimiento.editar",
        "eventos.ver",
        "documentos.ver", "documentos.descargar",
        "chat.usar",
        "visitantes.ver", "visitantes.crear", "visitantes.editar",
        "zonas.ver", "reservas.ver", "comunicados.ver", "pqrs.ver",
        "perfil.ver", "perfil.editar",
    },
    # Consejo de administración (UH-22 a UH-26, UH-32): lectura amplia del
    # conjunto, votaciones, aprobación de solicitudes y alertas de gasto.
    CONSEJO: {
        "dashboard.ver", "conjuntos.ver", "reportes.ver",
        "propiedades.ver", "residentes.ver",
        "finanzas.ver", "pagos.ver",
        "documentos.ver", "documentos.descargar",
        "eventos.ver", "mantenimiento.ver",
        "pqrs.ver", "zonas.ver", "reservas.ver",
        "comunicados.ver", "visitantes.ver",
        "votaciones.ver", "votaciones.crear", "votaciones.votar", "votaciones.cerrar",
        "aprobaciones.ver", "aprobaciones.crear", "aprobaciones.decidir",
        "auditoria.ver", "chat.usar",
        "perfil.ver", "perfil.editar",
    },
}


def sincronizar_permisos(db: Session) -> None:
    """Deja `roles`, `permisos` y `rol_permisos` exactamente como dicta MATRIZ."""
    for rol_id, (nombre, desc) in ROLES.items():
        rol = db.query(Rol).get(rol_id)
        if not rol:
            db.add(Rol(id=rol_id, nombre=nombre, descripcion=desc))
    db.flush()

    existentes = {p.codigo: p for p in db.query(Permiso).all()}
    for codigo, modulo, accion, desc in CATALOGO:
        if codigo not in existentes:
            p = Permiso(codigo=codigo, modulo=modulo, accion=accion, descripcion=desc)
            db.add(p)
            existentes[codigo] = p
    db.flush()

    cambios = 0
    for rol_id, codigos in MATRIZ.items():
        deseados = {existentes[c].id for c in codigos}
        actuales = {
            rp.permiso_id for rp in db.query(RolPermiso).filter(RolPermiso.rol_id == rol_id).all()
        }
        for pid in deseados - actuales:
            db.add(RolPermiso(rol_id=rol_id, permiso_id=pid))
            cambios += 1
        if actuales - deseados:
            db.query(RolPermiso).filter(
                RolPermiso.rol_id == rol_id, RolPermiso.permiso_id.in_(actuales - deseados)
            ).delete(synchronize_session=False)
            cambios += len(actuales - deseados)
    db.commit()
    if cambios:
        logger.info("RBAC sincronizado: %d asignaciones ajustadas.", cambios)
