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
