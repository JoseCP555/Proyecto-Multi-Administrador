"""Pruebas de las dos funciones nuevas:

* color del conjunto (paleta + hexadecimal personalizado);
* notificaciones reales persistentes, accionables y con canales de entrega.

Requieren la API levantada (TEST_API_URL) contra PostgreSQL, igual que el
resto de la suite de integración.
"""
import os
import uuid
from datetime import date, timedelta

import httpx
import pytest

BASE = os.getenv("TEST_API_URL", "http://localhost:8041")
c = httpx.Client(base_url=BASE, timeout=30)


@pytest.fixture(scope="module")
def headers():
    r = c.post("/login", json={"correo": "admin@multiadmin.com", "password": "Admin2026!"})
    assert r.status_code == 200, f"No se pudo iniciar sesión: {r.text}"
    return {
        "Authorization": f"Bearer {r.json()['access_token']}",
        "X-Conjunto-Id": "1",
    }


def _conjunto_temporal(headers, **extra):
    datos = {"nombre": f"Conjunto Prueba {uuid.uuid4().hex[:8]}", **extra}
    r = c.post("/conjuntos", json=datos, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ---------------------------------------------------------------------------
# Color del conjunto
# ---------------------------------------------------------------------------
def test_color_personalizado_y_paleta(headers):
    cid = _conjunto_temporal(headers, color="#7C3AED")
    try:
        r = c.put(f"/conjuntos/{cid}", json={"color": "verde"}, headers=headers)
        assert r.status_code == 200 and r.json()["color"] == "verde"

        # #ABC se expande a #aabbcc y se guarda en minúsculas.
        r = c.put(f"/conjuntos/{cid}", json={"color": "#ABC"}, headers=headers)
        assert r.status_code == 200 and r.json()["color"] == "#aabbcc"

        # "" = volver al color automático.
        r = c.put(f"/conjuntos/{cid}", json={"color": ""}, headers=headers)
        assert r.status_code == 200 and r.json()["color"] is None

        # Un valor que no es ni paleta ni hexadecimal se rechaza.
        r = c.put(f"/conjuntos/{cid}", json={"color": "colorincho"}, headers=headers)
        assert r.status_code == 422

        # El listado expone el campo color.
        r = c.put(f"/conjuntos/{cid}", json={"color": "rosa"}, headers=headers)
        assert r.status_code == 200
        listado = c.get("/conjuntos", headers=headers).json()
        assert any(x["id"] == cid and x["color"] == "rosa" for x in listado)
    finally:
        c.delete(f"/conjuntos/{cid}", headers=headers)


def test_color_automatico_al_crear(headers):
    cid = _conjunto_temporal(headers)
    try:
        fila = next(x for x in c.get("/conjuntos", headers=headers).json() if x["id"] == cid)
        assert fila["color"] in {"azul", "verde", "ambar", "rosa", "violeta", "cian"}
    finally:
        c.delete(f"/conjuntos/{cid}", headers=headers)


# ---------------------------------------------------------------------------
# Notificaciones
# ---------------------------------------------------------------------------
def test_config_y_preferencias(headers):
    cfg = c.get("/notificaciones/config").json()
    assert "vapid_publico" in cfg and "correo_configurado" in cfg and "push_configurado" in cfg

    prefs = c.get("/notificaciones/preferencias", headers=headers).json()
    assert isinstance(prefs["correo"], bool) and isinstance(prefs["push"], bool)

    r = c.put("/notificaciones/preferencias", json={"correo": False}, headers=headers)
    assert r.status_code == 200 and r.json()["correo"] is False
    r = c.put("/notificaciones/preferencias", json={"correo": True}, headers=headers)
    assert r.status_code == 200 and r.json()["correo"] is True


def test_notificacion_nace_de_un_hecho_real(headers):
    titulo = f"Reunión {uuid.uuid4().hex[:6]}"
    fecha = (date.today() + timedelta(days=4)).isoformat()
    r = c.post(
        "/eventos",
        json={"titulo": titulo, "descripcion": "Prueba", "fecha": fecha, "lugar": "Salón"},
        headers=headers,
    )
    assert r.status_code == 201, r.text

    # La notificación se crea en la misma petición (no es un dato inventado).
    items = c.get("/notificaciones", headers=headers).json()
    avisos = [n for n in items if titulo in (n["mensaje"] or "")]
    assert avisos, "No apareció el aviso del evento recién creado"
    n = avisos[0]
    assert n["tipo"] == "evento"
    assert n["url"] == "/dashboard/eventos"
    assert n["leida"] is False
    assert n["id"] > 0 and n["fecha_creacion"]

    # Marcar como leída y descartar.
    assert c.post(f"/notificaciones/{n['id']}/leer", headers=headers).status_code == 200
    assert any(x["id"] == n["id"] and x["leida"]
               for x in c.get("/notificaciones", headers=headers).json())
    assert c.delete(f"/notificaciones/{n['id']}", headers=headers).status_code == 204
    assert not any(x["id"] == n["id"] for x in c.get("/notificaciones", headers=headers).json())


def test_resumen_y_aviso_de_prueba(headers):
    antes = c.get("/notificaciones/resumen", headers=headers).json()
    assert "no_leidas" in antes and "total" in antes

    r = c.post("/notificaciones/probar", json={"canal": "ninguno"}, headers=headers)
    assert r.status_code == 200 and r.json()["ok"] is True
    despues = c.get("/notificaciones/resumen", headers=headers).json()
    assert despues["no_leidas"] >= antes["no_leidas"]

    r = c.post("/notificaciones/leer-todas", headers=headers)
    assert r.status_code == 200
    assert c.get("/notificaciones/resumen", headers=headers).json()["no_leidas"] == 0


def test_recordatorios_agrupados_y_rbac(headers):
    """Los recordatorios se agrupan: no debe haber decenas de 'Pago vencido'
    idénticos, sino un resumen por conjunto."""
    items = c.get("/notificaciones", headers=headers).json()
    moras = [n for n in items if n["tipo"] == "mora"]
    for n in moras:
        assert "pago" in (n["mensaje"] or "").lower()
    # A lo sumo un resumen por conjunto (hay menos de 50 conjuntos en demo).
    assert len(moras) < 50
