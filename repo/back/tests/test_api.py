from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200


def test_login_credenciales_invalidas():
    response = client.post("/login", json={"correo": "no-existe@example.com", "password": "algo"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
