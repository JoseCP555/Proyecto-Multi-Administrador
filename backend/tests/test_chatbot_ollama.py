"""Pruebas de integración del chatbot con Ollama (API nativa v0.40+).

Levanta un servidor HTTP local real que implementa los endpoints de Ollama
(`/api/version`, `/api/tags`, `/api/chat`) para verificar de extremo a extremo:
  1. Diagnóstico `/chat/estado` (versión de Ollama y detección del modelo).
  2. Respuesta vía Ollama con contexto real del conjunto + historial multi-turno.
  3. Aislamiento RBAC: un residente nunca obtiene ni filtra datos de finanzas a Ollama.
  4. Compatibilidad con modelos razonadores (`think: false` y limpieza de `<think>`).
  5. Respaldo automático al motor local cuando Ollama no está disponible.
  6. Cambio dinámico desde la tabla `configuraciones` (`chatbot_engine`, `ollama_model`).
"""
from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SECRET_KEY", "test-secret-ollama-0123456789")
os.environ.setdefault("CORREO_DESHABILITADO", "1")
os.environ.setdefault("DATABASE_URL", "")

from app.main import app  # noqa: E402
from app.ollama_client import ollama_base_url, _limpiar_respuesta  # noqa: E402


class _FakeOllamaState:
    def __init__(self) -> None:
        self.version = "0.40.16"
        self.models = ["llama3.2:3b", "qwen3:4b"]
        self.requests: list[dict] = []
        self.next_reply = "Respuesta generada por Ollama con datos reales del conjunto."
        self.status_code = 200


@pytest.fixture()
def fake_ollama(monkeypatch):
    """Servidor HTTP local que emula la API nativa de Ollama v0.40.16."""
    state = _FakeOllamaState()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A002
            return

        def _send_json(self, code: int, payload: dict):
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):  # noqa: N802
            if self.path == "/api/version":
                self._send_json(200, {"version": state.version})
            elif self.path == "/api/tags":
                self._send_json(200, {"models": [{"name": m} for m in state.models]})
            else:
                self._send_json(404, {"error": "not found"})

        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            if self.path == "/api/chat":
                state.requests.append(body)
                if state.status_code != 200:
                    self._send_json(state.status_code, {"error": "simulated error"})
                    return
                self._send_json(
                    200,
                    {
                        "model": body.get("model"),
                        "message": {"role": "assistant", "content": state.next_reply},
                        "done": True,
                    },
                )
            else:
                self._send_json(404, {"error": "not found"})

    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    monkeypatch.setenv("CHATBOT_ENGINE", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", f"http://127.0.0.1:{port}")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")
    monkeypatch.setenv("OLLAMA_TIMEOUT", "10")

    try:
        yield state, f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()


def _login(client: TestClient, correo: str, contrasena: str) -> dict[str, str]:
    r = client.post("/login", json={"correo": correo, "password": contrasena})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _set_config(client: TestClient, headers: dict, clave: str, valor: str):
    r = client.put(
        "/configuracion",
        headers=headers,
        json=[{"clave": clave, "valor": valor, "descripcion": ""}],
    )
    assert r.status_code == 200, r.text


def test_ollama_estado_y_chat_con_historial(fake_ollama):
    state, url = fake_ollama
    with TestClient(app) as client:
        h_admin = _login(client, "admin@multiadmin.com", "Admin2026!")
        _set_config(client, h_admin, "chatbot_engine", "ollama")
        _set_config(client, h_admin, "ollama_model", "llama3.2:3b")

        # 1. Diagnóstico /chat/estado
        est = client.get("/chat/estado", headers=h_admin)
        assert est.status_code == 200
        d = est.json()
        assert d["motor_configurado"] == "ollama"
        assert d["ollama_disponible"] is True
        assert d["ollama_version"] == "0.40.16"
        assert d["modelo"] == "llama3.2:3b"
        assert d["modelo_instalado"] is True
        assert d["ollama_url"] == url

        # 2. Primera pregunta: debe inyectar contexto real del conjunto (incluye FINANZAS para admin)
        r1 = client.post(
            "/chat/ask",
            headers=h_admin,
            json={"mensaje": "Dame un resumen general del estado del conjunto"},
        )
        assert r1.status_code == 200, r1.text
        b1 = r1.json()
        assert b1["motor_usado"] == "ollama"
        assert b1["modelo"] == "llama3.2:3b"
        assert b1["respuesta"] == state.next_reply
        assert len(state.requests) == 1

        req1 = state.requests[0]
        assert req1["model"] == "llama3.2:3b"
        assert req1["stream"] is False
        assert req1["messages"][0]["role"] == "system"
        assert "[FINANZAS]" in req1["messages"][0]["content"]
        assert "[PROPIEDADES]" in req1["messages"][0]["content"]
        assert req1["messages"][-1] == {
            "role": "user",
            "content": "Dame un resumen general del estado del conjunto",
        }

        # 3. Segunda pregunta en la misma sesión: debe incluir el historial previo
        state.next_reply = "Claro, aquí tienes el seguimiento."
        r2 = client.post(
            "/chat/ask",
            headers=h_admin,
            json={"mensaje": "¿Y cuál es el próximo evento?", "sesion_id": b1["sesion_id"]},
        )
        assert r2.status_code == 200
        assert r2.json()["respuesta"] == "Claro, aquí tienes el seguimiento."
        req2_msgs = state.requests[1]["messages"]
        roles = [m["role"] for m in req2_msgs]
        assert roles == ["system", "user", "assistant", "user"]


def test_ollama_respeta_rbac_residente(fake_ollama):
    state, _ = fake_ollama
    with TestClient(app) as client:
        h_admin = _login(client, "admin@multiadmin.com", "Admin2026!")
        _set_config(client, h_admin, "chatbot_engine", "ollama")
        _set_config(client, h_admin, "ollama_model", "llama3.2:3b")

        h_res = _login(client, "residente@multiadmin.com", "Residente2026!")

        # 1. Pregunta de finanzas -> bloqueada por RBAC ANTES de llamar a Ollama
        r_block = client.post("/chat/ask", headers=h_res, json={"mensaje": "¿cuál es el saldo?"})
        assert r_block.status_code == 200
        data_block = r_block.json()
        assert data_block["motor_usado"] == "rbac"
        assert "no tiene acceso" in data_block["respuesta"].lower()
        assert "$" not in data_block["respuesta"]
        assert len(state.requests) == 0

        # 2. Pregunta general permitida -> llama a Ollama SIN inyectar [FINANZAS]
        state.next_reply = "Puedes usar el módulo Chat con Admin para escribirle a la administración."
        r_ok = client.post(
            "/chat/ask",
            headers=h_res,
            json={"mensaje": "¿Cómo puedo hablar con la administración?"},
        )
        assert r_ok.status_code == 200
        assert r_ok.json()["motor_usado"] == "ollama"
        assert len(state.requests) == 1
        sys_prompt = state.requests[0]["messages"][0]["content"]
        assert "[FINANZAS]" not in sys_prompt
        assert "MÓDULOS RESTRINGIDOS" in sys_prompt
        assert "finanzas" in sys_prompt


def test_ollama_modelo_thinking_envia_think_false_y_limpia_etiquetas(fake_ollama):
    state, _ = fake_ollama
    state.next_reply = "<think>razonamiento interno oculto</think>\nEl horario de silencio es 22:00 - 06:00."
    with TestClient(app) as client:
        h_admin = _login(client, "admin@multiadmin.com", "Admin2026!")
        _set_config(client, h_admin, "chatbot_engine", "ollama")
        _set_config(client, h_admin, "ollama_model", "qwen3:4b")

        r = client.post("/chat/ask", headers=h_admin, json={"mensaje": "¿Cuál es el horario de silencio?"})
        assert r.status_code == 200
        body = r.json()
        assert body["motor_usado"] == "ollama"
        assert body["modelo"] == "qwen3:4b"
        assert "<think>" not in body["respuesta"]
        assert body["respuesta"] == "El horario de silencio es 22:00 - 06:00."
        assert state.requests[0].get("think") is False

        # Restaurar modelo por defecto
        _set_config(client, h_admin, "ollama_model", "llama3.2:3b")


def test_ollama_caido_hace_fallback_a_motor_local(monkeypatch):
    monkeypatch.setenv("CHATBOT_ENGINE", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("OLLAMA_TIMEOUT", "5")

    with TestClient(app) as client:
        h_admin = _login(client, "admin@multiadmin.com", "Admin2026!")
        _set_config(client, h_admin, "chatbot_engine", "ollama")

        est = client.get("/chat/estado", headers=h_admin)
        assert est.status_code == 200
        assert est.json()["ollama_disponible"] is False

        r = client.post("/chat/ask", headers=h_admin, json={"mensaje": "¿cuál es el saldo?"})
        assert r.status_code == 200
        body = r.json()
        assert body["motor_usado"] == "local"
        assert "saldo" in body["respuesta"].lower()


def test_helpers_ollama_url_y_limpieza(monkeypatch):
    assert _limpiar_respuesta("<think>abc</think>Hola") == "Hola"
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    if not os.path.exists("/.dockerenv"):
        assert ollama_base_url() == "http://localhost:11434"
