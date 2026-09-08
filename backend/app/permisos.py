"""Fuente única de verdad del RBAC: catálogo de permisos y matriz rol → permisos.

`sincronizar_permisos()` se ejecuta al arrancar la API y deja la BD alineada con
esta matriz (idempotente): crea los permisos que falten y ajusta `rol_permisos`
de los 5 roles del sistema. Así `db/init.sql` y el backend nunca divergen.

Roles (IDs fijos): 1 = super_admin · 2 = admin · 3 = residente · 4 = tesoreria · 5 = seguridad
"""
import logging
from sqlalchemy.orm import Session

from app.models import Rol, Permiso, RolPermiso

logger = logging.getLogger(__name__)

SUPER_ADMIN, ADMIN, RESIDENTE, TESORERIA, SEGURIDAD = 1, 2, 3, 4, 5

ROLES = {
    SUPER_ADMIN: ("super_admin", "Acceso total al sistema"),
    ADMIN: ("admin", "Administrador del conjunto"),
    RESIDENTE: ("residente", "Residente propietario o inquilino"),
    TESORERIA: ("tesoreria", "Encargado de finanzas"),
    SEGURIDAD: ("seguridad", "Personal de vigilancia"),
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
    ("chat.usar", "chat", "usar", "Usar el chatbot / asistente"),
    ("sistema.respaldar", "sistema", "respaldar", "Generar respaldo de la base de datos"),
]

TODOS = [c[0] for c in CATALOGO]

# Exclusivos del super_admin (el admin del conjunto no los tiene).
SOLO_SUPER_ADMIN = {"usuarios.eliminar", "sistema.respaldar"}

MATRIZ: dict[int, set[str]] = {
    SUPER_ADMIN: set(TODOS),
    ADMIN: set(TODOS) - SOLO_SUPER_ADMIN,
    # Tesorería: finanzas completas, reportes, documentos (lectura), chatbot.
    TESORERIA: {
        "dashboard.ver", "reportes.ver",
        "finanzas.ver", "finanzas.crear", "finanzas.editar", "finanzas.eliminar",
        "propiedades.ver", "residentes.ver",
        "documentos.ver", "documentos.descargar",
        "chat.usar",
    },
    # Residente: lectura de su conjunto, crear solicitudes de mantenimiento, chatbot.
    RESIDENTE: {
        "dashboard.ver",
        "propiedades.ver",
        "documentos.ver", "documentos.descargar",
        "eventos.ver",
        "mantenimiento.ver", "mantenimiento.crear",
        "chat.usar",
    },
    # Seguridad: lectura operativa + puede actualizar estado de mantenimientos.
    SEGURIDAD: {
        "dashboard.ver",
        "propiedades.ver", "residentes.ver",
        "mantenimiento.ver", "mantenimiento.crear", "mantenimiento.editar",
        "eventos.ver",
        "documentos.ver", "documentos.descargar",
        "chat.usar",
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
