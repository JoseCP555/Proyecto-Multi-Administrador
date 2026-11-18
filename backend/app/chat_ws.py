"""Gestor de conexiones WebSocket en tiempo real para el chat residente <-> admin.

Mantiene un registro ligero en memoria de las pestañas activas por usuario,
respetando los permisos y el aislamiento multi-conjunto (`id_conjunto`):

* Un evento de una conversación se entrega al residente dueño de esa
  conversación y a todos los administradores conectados con acceso al
  conjunto correspondiente.
* Si un usuario tiene varias pestañas abiertas, todas se mantienen
  sincronizadas.
* Las conexiones cerradas o caídas se limpian automáticamente sin afectar al
  resto de los clientes.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from fastapi import WebSocket

logger = logging.getLogger("app.chat_ws")


@dataclass(eq=False)
class ConexionChat:
    websocket: WebSocket
    usuario_id: int
    es_admin: bool
    ve_todos_conjuntos: bool
    conjuntos_permitidos: set[int] = field(default_factory=set)

    def puede_ver_conjunto(self, id_conjunto: Optional[int]) -> bool:
        if id_conjunto is None or self.ve_todos_conjuntos:
            return True
        return id_conjunto in self.conjuntos_permitidos


class GestorWebSocketChat:
    """Registro de clientes WebSocket conectados al módulo de mensajería."""

    def __init__(self) -> None:
        self._por_usuario: dict[int, set[ConexionChat]] = {}

    async def conectar(self, conexion: ConexionChat) -> None:
        await conexion.websocket.accept()
        self._por_usuario.setdefault(conexion.usuario_id, set()).add(conexion)

    def desconectar(self, conexion: ConexionChat) -> None:
        grupo = self._por_usuario.get(conexion.usuario_id)
        if not grupo:
            return
        grupo.discard(conexion)
        if not grupo:
            self._por_usuario.pop(conexion.usuario_id, None)

    def usuario_conectado(self, usuario_id: int) -> bool:
        return bool(self._por_usuario.get(usuario_id))

    def hay_admin_conectado(self, id_conjunto: Optional[int]) -> bool:
        for grupo in self._por_usuario.values():
            for conn in grupo:
                if conn.es_admin and conn.puede_ver_conjunto(id_conjunto):
                    return True
        return False

    async def _enviar(self, conn: ConexionChat, payload: dict[str, Any]) -> bool:
        try:
            await conn.websocket.send_json(payload)
            return True
        except Exception:  # noqa: BLE001 - socket desconectado
            return False

    async def difundir_conversacion(
        self,
        *,
        residente_usuario_id: int,
        id_conjunto: Optional[int],
        payload: dict[str, Any],
        excluir_usuario_id: Optional[int] = None,
    ) -> None:
        """Envía un evento en tiempo real al residente y a los admins del conjunto."""
        destinos: list[ConexionChat] = []
        for uid, grupo in list(self._por_usuario.items()):
            if excluir_usuario_id is not None and uid == excluir_usuario_id:
                continue
            for conn in list(grupo):
                if uid == residente_usuario_id:
                    destinos.append(conn)
                elif conn.es_admin and conn.puede_ver_conjunto(id_conjunto):
                    destinos.append(conn)

        rotas: list[ConexionChat] = []
        for conn in destinos:
            ok = await self._enviar(conn, payload)
            if not ok:
                rotas.append(conn)

        for conn in rotas:
            self.desconectar(conn)


gestor_chat = GestorWebSocketChat()
