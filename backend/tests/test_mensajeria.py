"""Pruebas del módulo de mensajería directa (chat residente <-> administrador).

Se ejecutan de forma aislada con SQLite y TestClient (incluye pruebas reales
de WebSocket en tiempo real):

    cd backend
    python -m pytest tests/test_mensajeria.py -v
"""
import io
import os
import uuid

os.environ.setdefault("SECRET_KEY", "mensajeria-test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///./mensajeria_test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6399/0")
os.environ.setdefault("DESACTIVAR_PROGRAMADOR", "1")
os.environ.setdefault("CORREO_DESHABILITADO", "1")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from starlette.websockets import WebSocketDisconnect  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def cliente():
    with TestClient(app) as c:
        yield c


def _login(c: TestClient, correo: str, password: str) -> dict:
    r = c.post("/login", json={"correo": correo, "password": password})
    assert r.status_code == 200, r.text
    datos = r.json()
    assert datos.get("ok") is True, datos
    return datos


@pytest.fixture(scope="module")
def contextos(cliente):
    admin_login = _login(cliente, "admin@multiadmin.com", "Admin2026!")
    admin_hdr_base = {"Authorization": f"Bearer {admin_login['access_token']}"}
    conjuntos = cliente.get("/conjuntos", headers=admin_hdr_base).json()
    assert len(conjuntos) >= 2, "Se esperan al menos 2 conjuntos de demo"
    c1, c2 = conjuntos[0]["id"], conjuntos[1]["id"]

    admin_c1 = {**admin_hdr_base, "X-Conjunto-Id": str(c1)}
    admin_c2 = {**admin_hdr_base, "X-Conjunto-Id": str(c2)}

    # Dos residentes en conjunto 1 + uno en conjunto 2 + un usuario de tesorería.
    def crear_usuario(nombre: str, rol_id: int, cid: int) -> dict:
        correo = f"chat.{uuid.uuid4().hex[:8]}@test.com"
        pwd = "ChatUser2026!"
        r = cliente.post(
            "/register",
            headers={**admin_hdr_base, "X-Conjunto-Id": str(cid)},
            json={
                "nombre": nombre,
                "correo": correo,
                "contrasena": pwd,
                "rol_id": rol_id,
                "id_conjunto": cid,
            },
        )
        assert r.status_code == 200, r.text
        lg = _login(cliente, correo, pwd)
        hdr = {"Authorization": f"Bearer {lg['access_token']}", "X-Conjunto-Id": str(cid)}
        return {"id": lg["usuario"]["id"], "token": lg["access_token"], "headers": hdr, "usuario": lg["usuario"]}

    res1 = crear_usuario("Residente Uno", 3, c1)
    res2 = crear_usuario("Residente Dos", 3, c1)
    res_c2 = crear_usuario("Residente Otro Conjunto", 3, c2)
    teso = crear_usuario("Tesoreria Test", 4, c1)
    seg = crear_usuario("Seguridad Test", 5, c1)
    consejo = crear_usuario("Consejo Test", 6, c1)

    return {
        "c1": c1,
        "c2": c2,
        "admin_token": admin_login["access_token"],
        "admin_c1": admin_c1,
        "admin_c2": admin_c2,
        "res1": res1,
        "res2": res2,
        "res_c2": res_c2,
        "teso": teso,
        "seg": seg,
        "consejo": consejo,
    }


def test_rbac_solo_residente_y_admin_acceden(cliente, contextos):
    for rol_key in ("teso", "seg", "consejo"):
        hdr = contextos[rol_key]["headers"]
        assert cliente.get("/mensajes/conversaciones", headers=hdr).status_code == 403
        assert cliente.get("/mensajes/no-leidos", headers=hdr).status_code == 403
        assert cliente.post("/mensajes/conversaciones", headers=hdr, json={}).status_code == 403

    # Sin token -> 401
    assert cliente.get("/mensajes/conversaciones").status_code == 401


def test_flujo_completo_residente_y_admin(cliente, contextos):
    res1 = contextos["res1"]
    admin_c1 = contextos["admin_c1"]

    # 1) Residente inicia conversación con mensaje inicial.
    r = cliente.post(
        "/mensajes/conversaciones",
        headers=res1["headers"],
        json={"mensaje_inicial": "Hola admin, ¿cuándo fumigan la torre A?"},
    )
    assert r.status_code == 200, r.text
    conv = r.json()
    conv_id = conv["id"]
    assert conv["residente_usuario_id"] == res1["id"]
    assert conv["estado"] == "abierta"
    assert "fumigan" in (conv["ultimo_mensaje"] or "")

    # 2) El admin ve la conversación con 1 mensaje sin leer.
    lista_admin = cliente.get("/mensajes/conversaciones", headers=admin_c1).json()
    encontrada = next((x for x in lista_admin if x["id"] == conv_id), None)
    assert encontrada is not None
    assert encontrada["no_leidos"] == 1

    resumen_admin = cliente.get("/mensajes/no-leidos", headers=admin_c1).json()
    assert resumen_admin["no_leidos"] >= 1

    # 3) El admin marca como leídos y responde.
    r_leer = cliente.post(f"/mensajes/conversaciones/{conv_id}/leer", headers=admin_c1)
    assert r_leer.status_code == 200 and r_leer.json()["marcados"] == 1

    r_resp = cliente.post(
        f"/mensajes/conversaciones/{conv_id}/mensajes",
        headers=admin_c1,
        json={"contenido": "Hola, la fumigación está programada para el viernes a las 9 a.m."},
    )
    assert r_resp.status_code == 201, r_resp.text
    msg_admin = r_resp.json()
    assert msg_admin["rol_remitente"] == "admin"
    assert msg_admin["leido"] is False

    # 4) El residente ve 1 no leído y al abrir ve ambos mensajes con el suyo ya leído.
    resumen_res = cliente.get("/mensajes/no-leidos", headers=res1["headers"]).json()
    assert resumen_res["no_leidos"] == 1

    hist = cliente.get(f"/mensajes/conversaciones/{conv_id}/mensajes", headers=res1["headers"]).json()
    assert len(hist) == 2
    assert hist[0]["rol_remitente"] == "residente" and hist[0]["leido"] is True
    assert hist[1]["rol_remitente"] == "admin" and hist[1]["leido"] is False

    # Notificación creada para el residente.
    notifs = cliente.get("/notificaciones", headers=res1["headers"]).json()
    assert any(n.get("tipo") == "mensaje_chat" for n in notifs)

    # 5) El residente marca como leído y el contador queda en 0.
    r_leer_res = cliente.post(f"/mensajes/conversaciones/{conv_id}/leer", headers=res1["headers"])
    assert r_leer_res.status_code == 200 and r_leer_res.json()["marcados"] == 1
    assert cliente.get("/mensajes/no-leidos", headers=res1["headers"]).json()["no_leidos"] == 0


def test_aislamiento_entre_residentes_y_conjuntos(cliente, contextos):
    res1 = contextos["res1"]
    res2 = contextos["res2"]
    res_c2 = contextos["res_c2"]
    admin_c1 = contextos["admin_c1"]
    admin_c2 = contextos["admin_c2"]

    conv1 = cliente.post(
        "/mensajes/conversaciones",
        headers=res1["headers"],
        json={"mensaje_inicial": "Mensaje privado residente 1"},
    ).json()
    cid1 = conv1["id"]

    # Residente 2 NO ve la conversación de Residente 1 ni puede leer/escribir/marcar.
    lista_r2 = cliente.get("/mensajes/conversaciones", headers=res2["headers"]).json()
    assert all(c["id"] != cid1 for c in lista_r2)
    assert cliente.get(f"/mensajes/conversaciones/{cid1}/mensajes", headers=res2["headers"]).status_code == 403
    assert cliente.post(
        f"/mensajes/conversaciones/{cid1}/mensajes",
        headers=res2["headers"],
        json={"contenido": "Intruso"},
    ).status_code == 403
    assert cliente.post(f"/mensajes/conversaciones/{cid1}/leer", headers=res2["headers"]).status_code == 403

    # Aislamiento multi-conjunto: conversación del conjunto 2 no aparece en conjunto 1.
    conv2 = cliente.post(
        "/mensajes/conversaciones",
        headers=res_c2["headers"],
        json={"mensaje_inicial": "Consulta desde el conjunto 2"},
    ).json()
    lista_admin_c1 = cliente.get("/mensajes/conversaciones", headers=admin_c1).json()
    lista_admin_c2 = cliente.get("/mensajes/conversaciones", headers=admin_c2).json()
    assert any(c["id"] == conv2["id"] for c in lista_admin_c2)
    assert all(c["id"] != conv2["id"] for c in lista_admin_c1)


def test_estado_resuelta_y_reapertura_automatica(cliente, contextos):
    res2 = contextos["res2"]
    admin_c1 = contextos["admin_c1"]

    # Admin inicia conversación con Residente 2 desde contactos.
    contactos = cliente.get("/mensajes/contactos", headers=admin_c1).json()
    assert contactos["modo"] == "admin"
    assert any(c["usuario_id"] == res2["id"] for c in contactos["contactos"])

    conv = cliente.post(
        "/mensajes/conversaciones",
        headers=admin_c1,
        json={"residente_usuario_id": res2["id"], "mensaje_inicial": "Hola, te escribimos desde administración."},
    ).json()
    conv_id = conv["id"]

    # Residente NO puede cambiar estado manualmente (403).
    r_forbidden = cliente.put(
        f"/mensajes/conversaciones/{conv_id}/estado",
        headers=res2["headers"],
        json={"estado": "resuelta"},
    )
    assert r_forbidden.status_code == 403

    # Admin marca como resuelta.
    r_res = cliente.put(
        f"/mensajes/conversaciones/{conv_id}/estado",
        headers=admin_c1,
        json={"estado": "resuelta"},
    )
    assert r_res.status_code == 200 and r_res.json()["estado"] == "resuelta"

    # Al escribir el residente de nuevo, se reabre automáticamente.
    r_msg = cliente.post(
        f"/mensajes/conversaciones/{conv_id}/mensajes",
        headers=res2["headers"],
        json={"contenido": "Gracias, una pregunta adicional por favor."},
    )
    assert r_msg.status_code == 201
    convs_r2 = cliente.get("/mensajes/conversaciones", headers=res2["headers"]).json()
    actual = next(c for c in convs_r2 if c["id"] == conv_id)
    assert actual["estado"] == "abierta"


def test_adjuntos_validacion_y_permisos(cliente, contextos):
    res1 = contextos["res1"]
    res2 = contextos["res2"]
    admin_c1 = contextos["admin_c1"]

    conv = cliente.post("/mensajes/conversaciones", headers=res1["headers"], json={}).json()
    conv_id = conv["id"]

    # Extensión prohibida (.exe) -> 400
    r_bad = cliente.post(
        f"/mensajes/conversaciones/{conv_id}/adjunto",
        headers=res1["headers"],
        data={"contenido": "archivo raro"},
        files={"archivo": ("virus.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
    )
    assert r_bad.status_code == 400

    # PDF válido -> 201
    pdf_bytes = b"%PDF-1.4\n%Prueba chat\n"
    r_ok = cliente.post(
        f"/mensajes/conversaciones/{conv_id}/adjunto",
        headers=res1["headers"],
        data={"contenido": "Adjunto comprobante"},
        files={"archivo": ("comprobante.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert r_ok.status_code == 201, r_ok.text
    msg = r_ok.json()
    assert msg["adjunto"] and msg["adjunto_nombre"] == "comprobante.pdf"

    # Residente dueño y admin pueden descargarlo; residente 2 recibe 403.
    dl_owner = cliente.get(f"/mensajes/adjunto/{msg['id']}", headers=res1["headers"])
    assert dl_owner.status_code == 200 and dl_owner.content == pdf_bytes
    dl_admin = cliente.get(f"/mensajes/adjunto/{msg['id']}", headers=admin_c1)
    assert dl_admin.status_code == 200 and dl_admin.content == pdf_bytes
    dl_other = cliente.get(f"/mensajes/adjunto/{msg['id']}", headers=res2["headers"])
    assert dl_other.status_code == 403


def test_websocket_tiempo_real(cliente, contextos):
    res1 = contextos["res1"]
    admin_c1 = contextos["admin_c1"]
    admin_token = contextos["admin_token"]

    # Token inválido debe ser rechazado.
    with pytest.raises(WebSocketDisconnect):
        with cliente.websocket_connect("/mensajes/ws?token=invalido"):
            pass

    conv = cliente.post("/mensajes/conversaciones", headers=res1["headers"], json={}).json()
    conv_id = conv["id"]

    with cliente.websocket_connect(f"/mensajes/ws?token={res1['token']}") as ws_res, \
         cliente.websocket_connect(f"/mensajes/ws?token={admin_token}") as ws_admin:
        assert ws_res.receive_json()["tipo"] == "conectado"
        assert ws_admin.receive_json()["tipo"] == "conectado"

        # Ping/pong.
        ws_res.send_json({"tipo": "ping"})
        assert ws_res.receive_json()["tipo"] == "pong"

        # Indicador de escritura del residente llega al admin.
        ws_res.send_json({"tipo": "escribiendo", "conversacion_id": conv_id, "activo": True})
        ev_typing = ws_admin.receive_json()
        assert ev_typing["tipo"] == "escribiendo"
        assert ev_typing["conversacion_id"] == conv_id
        assert ev_typing["activo"] is True

        # Cuando el admin envía un mensaje por REST, ambos sockets reciben `nuevo_mensaje`.
        r_msg = cliente.post(
            f"/mensajes/conversaciones/{conv_id}/mensajes",
            headers=admin_c1,
            json={"contenido": "Mensaje en tiempo real por WebSocket"},
        )
        assert r_msg.status_code == 201
        ev_res = ws_res.receive_json()
        ev_adm = ws_admin.receive_json()
        assert ev_res["tipo"] == "nuevo_mensaje"
        assert ev_res["mensaje"]["contenido"] == "Mensaje en tiempo real por WebSocket"
        assert ev_adm["tipo"] == "nuevo_mensaje"

        # Cuando el residente marca como leído, el admin recibe `mensajes_leidos`.
        cliente.post(f"/mensajes/conversaciones/{conv_id}/leer", headers=res1["headers"])
        ev_leido = ws_admin.receive_json()
        assert ev_leido["tipo"] == "mensajes_leidos"
        assert ev_leido["lector_rol"] == "residente"
