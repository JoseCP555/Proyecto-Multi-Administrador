"""
Pruebas unitarias de módulos internos del backend
(seguridad, JWT, chatbot) sin necesidad de red.
"""
import os
os.environ["SECRET_KEY"] = "unit-test-secret"
os.environ["DATABASE_URL"] = "sqlite:///./unit.db"
os.environ["REDIS_URL"] = "redis://localhost:6399/0"

from app.security import hashear_password, verificar_password  # noqa: E402
from app.auth_jwt import crear_token, verificar_token, segundos_restantes  # noqa: E402
from app.chatbot import detectar_intent, _norm, _format_money  # noqa: E402


# --------------------------- Seguridad ------------------------------------
def test_hash_verifica():
    h = hashear_password("Secret123!")
    assert h and isinstance(h, str)
    assert verificar_password("Secret123!", h) is True
    assert verificar_password("incorrecta", h) is False


def test_hash_distinto_cada_vez():
    # bcrypt genera salts aleatorios -> hashes distintos para la misma password.
    assert hashear_password("x") != hashear_password("x")


# --------------------------- JWT ------------------------------------------
def test_crear_verificar_token():
    t = crear_token({"sub": "5", "rol": 2})
    payload = verificar_token(t)
    assert payload is not None
    assert payload["sub"] == "5"
    assert payload["rol"] == 2


def test_token_invalido():
    assert verificar_token("no-es-un-token") is None
    assert verificar_token("") is None


def test_segundos_restantes():
    t = crear_token({"sub": "1"})
    s = segundos_restantes(t)
    assert s > 0


# --------------------------- Chatbot --------------------------------------
def test_detectar_intents():
    assert detectar_intent("Hola, buenos días") == "saludo"
    assert detectar_intent("¿cuál es el saldo?") == "balance"
    assert detectar_intent("hay pagos pendientes?") == "pagos_pendientes"
    assert detectar_intent("dame los gastos del mes") == "gastos"
    assert detectar_intent("no entiendo esto") == "general"


def test_detectar_intent_sin_tildes():
    # El normalizador quita tildes: 'mantenimiento' detecta 'tarea'.
    assert detectar_intent("¿cómo va el mantenimiento?") == "mantenimiento"


def test_format_money():
    assert "1.500" in _format_money(1500)
    assert "$" in _format_money(0)


# --------------------------- Enlaces de correos ---------------------------
def test_correo_notificacion_usa_origen_real_y_abre_en_navegador(monkeypatch):
    from app import correo
    from app.correo_notificaciones import construir_url_notificacion, _html

    monkeypatch.setenv("FRONTEND_URL", "http://localhost:3000")
    correo._ultimo_origen_publico = ""

    tok = correo.registrar_origen_frontend("http://192.168.1.34:3000")
    try:
        url = construir_url_notificacion("/dashboard/mensajes", id_conjunto=3)
        assert url == "http://192.168.1.34:3000/dashboard/mensajes?conjunto=3"
        html = _html("Sayeth", "Prueba", "Mensaje", url)
        assert 'target="_blank"' in html
        assert 'rel="noopener noreferrer"' in html
        assert "Ver en la aplicación" in html
        assert url in html
    finally:
        correo.restaurar_origen_frontend(tok)
        correo._ultimo_origen_publico = ""


def test_correo_respeta_frontend_url_publica_explicita(monkeypatch):
    from app import correo
    from app.correo_notificaciones import construir_url_notificacion

    monkeypatch.setenv("FRONTEND_URL", "https://mi-conjunto.com")
    tok = correo.registrar_origen_frontend("http://192.168.1.34:3000")
    try:
        assert construir_url_notificacion("/dashboard/inicio") == "https://mi-conjunto.com/dashboard/inicio"
    finally:
        correo.restaurar_origen_frontend(tok)
        correo._ultimo_origen_publico = ""
