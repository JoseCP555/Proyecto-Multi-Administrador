"""
Suite de pruebas funcionales (pytest) para la API de Multi-Administrador.

Se ejecuta contra la instancia REAL de la API (http://localhost:8041)
que está conectada a PostgreSQL + Redis. Gracias a esto no se necesita
una BD aparte y se valida el stack completo.

Ejecución:
    cd backend
    python -m pytest tests/ -v
"""
import os
import httpx
import pytest

BASE = os.getenv("TEST_API_URL", "http://localhost:8041")
client = httpx.Client(base_url=BASE, timeout=20)

ADMIN_EMAIL = "admin@multiadmin.com"
ADMIN_PASS = "Admin2026!"


# --------------------------------------------------------------------------
# 1. Salud del servicio
# --------------------------------------------------------------------------
def test_health():
    r = client.get("/health")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok"


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "funcionando" in r.json()["mensaje"]


# --------------------------------------------------------------------------
# 2. Autenticación
# --------------------------------------------------------------------------
def test_roles():
    r = client.get("/roles")
    assert r.status_code == 200
    nombres = {x["nombre"] for x in r.json()}
    assert {"super_admin", "admin", "residente"}.issubset(nombres)


def test_login_correcto():
    r = client.post("/login", json={"correo": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["access_token"]
    assert data["usuario"]["correo"] == ADMIN_EMAIL


def test_login_incorrecto():
    r = client.post("/login", json={"correo": ADMIN_EMAIL, "password": "mal12345"})
    assert r.status_code == 200
    assert r.json()["ok"] is False


def test_register_duplicado():
    # Un correo que ya existe debe fallar (no lo crea de nuevo).
    r = client.post("/register", json={
        "nombre": "Otro", "correo": ADMIN_EMAIL, "contrasena": "12345678", "rol_id": 3,
    })
    assert r.status_code == 400


def test_logout_revoca_token():
    # login -> logout -> el token revocado no debe volver a autenticar.
    tok = client.post("/login", json={"correo": ADMIN_EMAIL, "password": ADMIN_PASS}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    r = client.post("/logout", headers=h)
    assert r.status_code == 200
    # Reusar el mismo token en un endpoint protegido -> 401
    r2 = client.post("/logout", headers=h)
    assert r2.status_code == 401


# --------------------------------------------------------------------------
# 3. Datos del dashboard y reportes (datos sembrados)
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def token():
    return client.post("/login", json={"correo": ADMIN_EMAIL, "password": ADMIN_PASS}).json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_stats(token):
    r = client.get("/reportes/dashboard", headers=auth(token))
    assert r.status_code == 200
    d = r.json()
    assert d["residentes"] > 0
    assert d["propiedades"] > 0
    assert d["documentos"] > 0
    assert "saldo" in d


def test_finanzas_resumen(token):
    r = client.get("/finanzas/resumen", headers=auth(token))
    assert r.status_code == 200
    d = r.json()
    assert "ingresos" in d and "gastos" in d and "saldo" in d


def test_finanzas_por_mes(token):
    r = client.get("/reportes/finanzas-por-mes", headers=auth(token))
    assert r.status_code == 200
    serie = r.json()
    assert isinstance(serie, list)
    assert all({"mes", "valor"}.issubset(x.keys()) for x in serie)


# --------------------------------------------------------------------------
# 4. Módulos CRUD
# --------------------------------------------------------------------------
def test_listar_propiedades(token):
    r = client.get("/propiedades", headers=auth(token))
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_listar_residentes(token):
    r = client.get("/residentes", headers=auth(token))
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_crear_y_eliminar_propiedad(token):
    import time
    payload = {"bloque": "T", "torre": "T9", "apartamento": f"TEST-{int(time.time())}", "estado": "vacio", "estrato": 2, "area": 70}
    r = client.post("/propiedades", json=payload, headers=auth(token))
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    # Eliminarla
    r2 = client.delete(f"/propiedades/{pid}", headers=auth(token))
    assert r2.status_code == 204


def test_mantenimiento_listar(token):
    r = client.get("/mantenimiento", headers=auth(token))
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_documentos_listar(token):
    r = client.get("/documentos", headers=auth(token))
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_eventos_listar(token):
    r = client.get("/eventos", headers=auth(token))
    assert r.status_code == 200


def test_usuarios_listar(token):
    r = client.get("/usuarios", headers=auth(token))
    assert r.status_code == 200
    assert any(u["correo"] == ADMIN_EMAIL for u in r.json())


# --------------------------------------------------------------------------
# 5. Chatbot (usa la BD real)
# --------------------------------------------------------------------------
def test_chatbot_respuesta(token):
    r = client.post("/chat/ask", json={"mensaje": "¿Cuál es el saldo?"}, headers=auth(token))
    assert r.status_code == 200, r.text
    data = r.json()
    assert "sesion_id" in data
    assert "respuesta" in data
    assert data["respuesta"]


def test_chatbot_persiste_historial(token):
    sid = client.post("/chat/ask", json={"mensaje": "hola"}, headers=auth(token)).json()["sesion_id"]
    r = client.get(f"/chat/sesiones/{sid}/mensajes", headers=auth(token))
    assert r.status_code == 200
    m = r.json()
    assert len(m) >= 2  # usuario + asistente
    assert any(x["rol"] == "asistente" for x in m)


def test_chatbot_conceptos(token):
    r = client.post("/chat/ask", json={"mensaje": "¿cuántas propiedades hay?"}, headers=auth(token))
    assert r.status_code == 200
    assert "propiedades" in r.json()["respuesta"].lower()
