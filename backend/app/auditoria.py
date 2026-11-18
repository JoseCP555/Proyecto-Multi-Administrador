"""Historial de auditoría de todas las acciones (UH-29).

Dos formas de registrar:

1. **Automática** (`AuditoriaMiddleware`): toda petición que modifica datos
   (POST / PUT / PATCH / DELETE) queda registrada con usuario, acción, ruta,
   módulo, IP, estado HTTP y fecha/hora. No hay que acordarse de llamar a nada
   en cada endpoint, así que ninguna acción "relevante" se queda sin traza.
2. **Manual** (`registrar()`): los routers añaden detalle de negocio (por
   ejemplo «aprobó la reserva 12 del salón comunal»). El middleware evita
   duplicar la fila cuando ya se registró manualmente (`request.state`).

El historial es **inmutable desde la aplicación**: no existe endpoint de
actualización ni de borrado, y ningún rol distinto del administrador puede
consultarlo (`auditoria.ver`).
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app import models

logger = logging.getLogger("app.auditoria")

# Métodos que no modifican datos: no generan filas de auditoría.
METODOS_IGNORADOS = {"GET", "HEAD", "OPTIONS", "TRACE"}

# Rutas que no aportan valor de auditoría (ruido de la campana de avisos).
RUTAS_IGNORADAS = {
    "/notificaciones/leer",
    "/notificaciones/leer-todas",
    "/notificaciones/preferencias",
    "/notificaciones/push/suscribir",
    "/notificaciones/push/desuscribir",
    "/me/actividad",
}

_ACCION_POR_METODO = {
    "POST": "crear",
    "PUT": "editar",
    "PATCH": "editar",
    "DELETE": "eliminar",
}

# Nombre legible del módulo a partir del primer segmento de la ruta.
_MODULOS = {
    "pqrs": "PQRS",
    "zonas": "Zonas comunes",
    "reservas": "Reservas",
    "comunicados": "Comunicados",
    "visitantes": "Visitantes",
    "pagos": "Comprobantes de pago",
    "votaciones": "Votaciones",
    "aprobaciones": "Aprobaciones del consejo",
    "auditoria": "Auditoría",
    "perfil": "Perfil",
    "eventos": "Eventos",
    "finanzas": "Finanzas",
    "documentos": "Documentos",
    "mantenimiento": "Mantenimiento",
    "residentes": "Residentes",
    "usuarios": "Usuarios",
    "auth": "Autenticación",
    "login": "Autenticación",
    "logout": "Autenticación",
    "register": "Autenticación",
    "conjuntos": "Conjuntos",
    "mensajes": "Chat residentes",
}


def _modulo_de(ruta: str) -> str:
    primer = ruta.strip("/").split("/")[0].lower() if ruta.strip("/") else "sistema"
    return _MODULOS.get(primer, primer or "sistema")


def registrar(
    db,
    usuario: Optional[models.Usuario] = None,
    *,
    accion: str,
    modulo: Optional[str] = None,
    entidad: Optional[str] = None,
    entidad_id: Optional[int] = None,
    detalle: Optional[str] = None,
    request: Optional[Request] = None,
    id_conjunto: Optional[int] = None,
    estado_http: int = 200,
    metodo: Optional[str] = None,
    ruta: Optional[str] = None,
    ip: Optional[str] = None,
    usuario_nombre: Optional[str] = None,
    usuario_rol: Optional[str] = None,
) -> Optional[models.Auditoria]:
    """Inserta una fila de auditoría. No hace commit (lo hace el llamador)."""
    try:
        if request is not None:
            if ruta is None:
                ruta = request.url.path
            if ip is None and request.client is not None:
                ip = request.client.host
            if metodo is None:
                metodo = request.method
            if id_conjunto is None:
                cabecera = request.headers.get("X-Conjunto-Id")
                if cabecera and cabecera.strip().isdigit():
                    id_conjunto = int(cabecera)
            if modulo is None:
                modulo = _modulo_de(ruta or "")

        if usuario is not None:
            usuario_id = usuario.id
            usuario_nombre = usuario_nombre or usuario.nombre
            usuario_rol = usuario_rol or str(usuario.rol_id)

        fila = models.Auditoria(
            usuario_id=getattr(usuario, "id", None),
            usuario_nombre=usuario_nombre,
            usuario_rol=usuario_rol,
            accion=accion,
            modulo=modulo or "sistema",
            metodo=metodo,
            ruta=ruta,
            entidad=entidad,
            entidad_id=entidad_id,
            detalle=detalle,
            ip=ip,
            estado_http=estado_http,
            id_conjunto=id_conjunto,
            fecha_creacion=datetime.utcnow(),
        )
        db.add(fila)
        db.commit()
        if request is not None:
            # Evita que el middleware vuelva a registrar la misma acción.
            try:
                request.state.auditado = True
            except Exception:  # noqa: BLE001
                pass
        return fila
    except Exception:  # noqa: BLE001 - la auditoría nunca debe tumbar la petición
        logger.exception("[auditoria] no se pudo registrar la acción %s", accion)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return None


def registrar_seguro(**kwargs) -> None:
    """`registrar()` sin devolver nada: para llamar desde un router."""
    registrar(**kwargs)


class AuditoriaMiddleware(BaseHTTPMiddleware):
    """Registra automáticamente cada operación que modifica datos."""

    async def dispatch(self, request: Request, call_next):
        if (
            request.method.upper() in METODOS_IGNORADOS
            or request.url.path in RUTAS_IGNORADAS
            or request.url.path.endswith("/leer")
        ):
            return await call_next(request)

        respuesta = await call_next(request)

        try:
            if getattr(request.state, "auditado", False):
                return respuesta

            from app.auth_jwt import verificar_token
            from app.database import SessionLocal

            autorizacion = request.headers.get("Authorization") or ""
            payload = None
            if autorizacion.startswith("Bearer "):
                payload = verificar_token(autorizacion.split(" ", 1)[1].strip())

            db = SessionLocal()
            try:
                usuario = None
                if payload and payload.get("sub"):
                    usuario = db.query(models.Usuario).get(int(payload["sub"]))
                ruta = request.url.path
                accion = _ACCION_POR_METODO.get(request.method.upper(), "otro")
                if ruta.endswith("/login"):
                    accion = "login"
                elif ruta.endswith("/logout"):
                    accion = "logout"

                cabecera = request.headers.get("X-Conjunto-Id")
                id_conjunto = int(cabecera) if cabecera and cabecera.strip().isdigit() else None

                detalle = f"{request.method.upper()} {ruta} → {respuesta.status_code}"
                db.add(models.Auditoria(
                    usuario_id=getattr(usuario, "id", None),
                    usuario_nombre=getattr(usuario, "nombre", None) or "Sistema",
                    usuario_rol=str(getattr(usuario, "rol_id", "")) or None,
                    accion=accion,
                    modulo=_modulo_de(ruta),
                    metodo=request.method.upper(),
                    ruta=ruta[:255],
                    detalle=detalle,
                    ip=(request.client.host if request.client else None),
                    estado_http=respuesta.status_code,
                    id_conjunto=id_conjunto,
                    fecha_creacion=datetime.utcnow(),
                ))
                db.commit()
            finally:
                db.close()
        except Exception:  # noqa: BLE001 - auditar jamás rompe la respuesta
            logger.exception("[auditoria] middleware: no se pudo registrar la petición")

        return respuesta
