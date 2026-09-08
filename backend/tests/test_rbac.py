"""
Pruebas de RBAC: inicia sesión como CADA rol (super_admin, admin, residente,
tesorería, seguridad) y verifica que la API concede/niega cada acción según la
matriz de permisos (backend/app/permisos.py).

Se ejecuta contra la API real (PostgreSQL + Redis):
    cd backend && python -m pytest tests/test_rbac.py -v
"""
import os
import time

import httpx
import pytest

BASE = os.getenv("TEST_API_URL", "http://localhost:8041")
c = httpx.Client(base_url=BASE, timeout=30)

ADMIN_EMAIL, ADMIN_PASS = "admin@multiadmin.com", "Admin2026!"
PASS = "Prueba2026!"
ROLES = {"super_admin": 1, "admin": 2, "residente": 3, "tesoreria": 4, "seguridad": 5}

# Matriz esperada (espejo de app/permisos.py). Si cambia la matriz, cambia aquí.
ESPERADO = {
    "super_admin": None,  # todos
    "admin": None,        # todos menos SOLO_SUPER
    "tesoreria": {
        "dashboard.ver", "reportes.ver", "finanzas.ver", "finanzas.crear", "finanzas.editar",
        "finanzas.eliminar", "propiedades.ver", "residentes.ver", "documentos.ver",
        "documentos.descargar", "chat.usar",
    },
    "residente": {
        "dashboard.ver", "propiedades.ver", "documentos.ver", "documentos.descargar",
        "eventos.ver", "mantenimiento.ver", "mantenimiento.crear", "chat.usar",
    },
    "seguridad": {
        "dashboard.ver", "propiedades.ver", "residentes.ver", "mantenimiento.ver",
        "mantenimiento.crear", "mantenimiento.editar", "eventos.ver", "documentos.ver",
        "documentos.descargar", "chat.usar",
    },
}
SOLO_SUPER = {"usuarios.eliminar", "sistema.respaldar"}


# ---------------------------------------------------------------------------
# Fixtures: un usuario real por rol (creados por el super_admin)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def sesiones():
    """Devuelve {rol: (headers, usuario_json)} para los 5 roles."""
    seed = c.post("/login", json={"correo": ADMIN_EMAIL, "password": ADMIN_PASS}).json()
    assert seed["ok"], "el admin sembrado debe poder iniciar sesión"
    seed_h = {"Authorization": f"Bearer {seed['access_token']}"}

    # Aseguramos un super_admin real (el seed crea un 'admin'); lo promovemos vía BD-API:
    # si el usuario sembrado ya es super_admin no pasa nada.
    correo_super = "rbac.super_admin@test.com"
    r = c.post("/register", headers=seed_h, json={
        "nombre": "RBAC super", "correo": correo_super, "contrasena": PASS, "rol_id": 1,
    })
    if r.status_code == 403:
        # El seed es admin (rol 2) y no puede crear super_admin. Lo elevamos por SQL directo
        # solo para el test (no hay endpoint que lo permita, y así debe ser).
        _promover_por_sql(ADMIN_EMAIL)
        seed = c.post("/login", json={"correo": ADMIN_EMAIL, "password": ADMIN_PASS}).json()
        seed_h = {"Authorization": f"Bearer {seed['access_token']}"}
        c.post("/register", headers=seed_h, json={
            "nombre": "RBAC super", "correo": correo_super, "contrasena": PASS, "rol_id": 1,
        })

    out = {}
    for rol, rid in ROLES.items():
        correo = f"rbac.{rol}@test.com"
        c.post("/register", headers=seed_h, json={
            "nombre": f"RBAC {rol}", "correo": correo, "contrasena": PASS, "rol_id": rid,
        })
        lg = c.post("/login", json={"correo": correo, "password": PASS}).json()
        assert lg["ok"], f"login {rol}: {lg}"
        out[rol] = ({"Authorization": f"Bearer {lg['access_token']}"}, lg["usuario"])
    return out


def _db_url() -> str:
    """DATABASE_URL del .env del backend (sin depender del entorno del proceso,
    que otros tests —test_unit— pueden sobrescribir con sqlite)."""
    from dotenv import dotenv_values
    valores = dotenv_values(os.path.join(os.path.dirname(__file__), "..", ".env"))
    url = valores.get("DATABASE_URL") or os.getenv("DATABASE_URL", "")
    assert url.startswith("postgresql"), f"DATABASE_URL no es PostgreSQL: {url}"
    return url


def _promover_por_sql(correo: str):
    import psycopg2
    conn = psycopg2.connect(_db_url())
    with conn, conn.cursor() as cur:
        cur.execute("UPDATE usuarios SET rol_id = 1 WHERE correo = %s", (correo,))
    conn.close()


def h(sesiones, rol):
    return sesiones[rol][0]


# ---------------------------------------------------------------------------
# 1. La lista de permisos que entrega /login coincide con la matriz
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("rol", list(ROLES))
def test_permisos_del_rol_coinciden_con_matriz(sesiones, rol):
    permisos = set(sesiones[rol][1]["permisos"])
    todos = set(c.get("/me", headers=h(sesiones, "super_admin")).json()["permisos"])
    assert "sistema.respaldar" in todos and "usuarios.eliminar" in todos
    if rol == "super_admin":
        assert permisos == todos
    elif rol == "admin":
        assert permisos == todos - SOLO_SUPER
    else:
        assert permisos == ESPERADO[rol], f"{rol}: {permisos ^ ESPERADO[rol]}"


# ---------------------------------------------------------------------------
# 2. Matriz de acceso a endpoints por rol
#    (rol, método, ruta, body, debe_permitir)
# ---------------------------------------------------------------------------
def _ok(status):        # permitido = cualquier cosa que no sea 401/403
    return status not in (401, 403)


CASOS = [
    # --- residente -------------------------------------------------------
    ("residente", "GET", "/usuarios", None, False),
    ("residente", "GET", "/residentes", None, False),
    ("residente", "GET", "/finanzas", None, False),
    ("residente", "GET", "/finanzas/resumen", None, False),
    ("residente", "GET", "/reportes/dashboard", None, False),
    ("residente", "GET", "/reportes/exportar/finanzas.xlsx", None, False),
    ("residente", "GET", "/reportes/exportar/mantenimiento.xlsx", None, True),
    ("residente", "GET", "/reportes/resumen-basico", None, True),
    ("residente", "GET", "/configuracion", None, False),
    ("residente", "GET", "/admin/backup", None, False),
    ("residente", "GET", "/propiedades", None, True),
    ("residente", "POST", "/propiedades", {}, False),
    ("residente", "GET", "/documentos", None, True),
    ("residente", "POST", "/documentos", {}, False),
    ("residente", "GET", "/eventos", None, True),
    ("residente", "POST", "/eventos", {}, False),
    ("residente", "GET", "/mantenimiento", None, True),
    ("residente", "POST", "/mantenimiento", {"titulo": "Gotera", "descripcion": "Baño", "prioridad": "media"}, True),
    ("residente", "PUT", "/mantenimiento/1", {"titulo": "x"}, False),
    ("residente", "DELETE", "/mantenimiento/1", None, False),
    ("residente", "GET", "/chat/sesiones", None, True),
    ("residente", "GET", "/notificaciones", None, True),
    # --- tesoreria -------------------------------------------------------
    ("tesoreria", "GET", "/finanzas", None, True),
    ("tesoreria", "POST", "/finanzas", {}, True),          # 422 por body vacío, pero autorizado
    ("tesoreria", "DELETE", "/finanzas/999999", None, True),  # 404, autorizado
    ("tesoreria", "GET", "/reportes/dashboard", None, True),
    ("tesoreria", "GET", "/reportes/exportar/finanzas.xlsx", None, True),
    ("tesoreria", "GET", "/reportes/exportar/pagos.pdf", None, True),
    ("tesoreria", "GET", "/propiedades", None, True),
    ("tesoreria", "GET", "/residentes", None, True),
    ("tesoreria", "POST", "/residentes", {}, False),
    ("tesoreria", "GET", "/usuarios", None, False),
    ("tesoreria", "GET", "/mantenimiento", None, False),
    ("tesoreria", "GET", "/eventos", None, False),
    ("tesoreria", "GET", "/configuracion", None, False),
    ("tesoreria", "GET", "/admin/backup", None, False),
    # --- seguridad -------------------------------------------------------
    ("seguridad", "GET", "/residentes", None, True),
    ("seguridad", "POST", "/residentes", {}, False),
    ("seguridad", "GET", "/propiedades", None, True),
    ("seguridad", "GET", "/mantenimiento", None, True),
    ("seguridad", "POST", "/mantenimiento", {"titulo": "Luz", "descripcion": "Portería", "prioridad": "alta"}, True),
    ("seguridad", "DELETE", "/mantenimiento/999999", None, False),
    ("seguridad", "GET", "/eventos", None, True),
    ("seguridad", "GET", "/documentos", None, True),
    ("seguridad", "POST", "/documentos", {}, False),
    ("seguridad", "GET", "/finanzas", None, False),
    ("seguridad", "GET", "/reportes/dashboard", None, False),
    ("seguridad", "GET", "/usuarios", None, False),
    ("seguridad", "GET", "/configuracion", None, False),
    # --- admin -----------------------------------------------------------
    ("admin", "GET", "/usuarios", None, True),
    ("admin", "GET", "/finanzas", None, True),
    ("admin", "GET", "/reportes/dashboard", None, True),
    ("admin", "GET", "/configuracion", None, True),
    ("admin", "PUT", "/configuracion", [], True),
    ("admin", "GET", "/admin/backup", None, False),          # solo super_admin
    ("admin", "DELETE", "/usuarios/999999", None, False),    # solo super_admin
    # --- super_admin -----------------------------------------------------
    ("super_admin", "GET", "/usuarios", None, True),
    ("super_admin", "DELETE", "/usuarios/999999", None, True),   # 404, autorizado
    ("super_admin", "GET", "/admin/backup", None, True),         # 200 o 500 sin pg_dump, pero autorizado
    ("super_admin", "GET", "/configuracion", None, True),
]


@pytest.mark.parametrize("rol,metodo,ruta,body,permitido", CASOS,
                         ids=[f"{r}-{m}-{p}" for r, m, p, _, _ in CASOS])
def test_matriz_endpoints(sesiones, rol, metodo, ruta, body, permitido):
    r = c.request(metodo, ruta, headers=h(sesiones, rol), json=body)
    assert _ok(r.status_code) == permitido, f"{rol} {metodo} {ruta} -> {r.status_code}: {r.text[:120]}"


def test_sin_token_401():
    for ruta in ["/usuarios", "/finanzas", "/reportes/dashboard", "/chat/sesiones", "/notificaciones"]:
        assert c.get(ruta).status_code == 401


# ---------------------------------------------------------------------------
# 3. Escalada de privilegios por /register
# ---------------------------------------------------------------------------
def test_registro_publico_no_permite_elegir_rol_admin():
    for rol_id in (1, 2, 4, 5):
        r = c.post("/register", json={
            "nombre": "Intruso", "correo": f"intruso{rol_id}.{int(time.time())}@x.com",
            "contrasena": "12345678", "rol_id": rol_id,
        })
        assert r.status_code == 403, r.text


def test_registro_publico_como_residente_si_funciona():
    correo = f"vecino.{int(time.time())}@x.com"
    r = c.post("/register", json={"nombre": "Vecino", "correo": correo, "contrasena": "12345678", "rol_id": 3})
    assert r.status_code == 200, r.text
    assert r.json()["rol_id"] == 3


def test_residente_autenticado_no_puede_crear_admins(sesiones):
    r = c.post("/register", headers=h(sesiones, "residente"), json={
        "nombre": "Intruso", "correo": f"i.{int(time.time())}@x.com", "contrasena": "12345678", "rol_id": 2,
    })
    assert r.status_code == 403


def test_admin_crea_tesoreria_pero_no_super_admin(sesiones):
    ok = c.post("/register", headers=h(sesiones, "admin"), json={
        "nombre": "Teso", "correo": f"teso.{int(time.time())}@x.com", "contrasena": "12345678", "rol_id": 4,
    })
    assert ok.status_code == 200, ok.text
    no = c.post("/register", headers=h(sesiones, "admin"), json={
        "nombre": "Super", "correo": f"sup.{int(time.time())}@x.com", "contrasena": "12345678", "rol_id": 1,
    })
    assert no.status_code == 403


# ---------------------------------------------------------------------------
# 4. Reglas de gestión de usuarios
# ---------------------------------------------------------------------------
def test_admin_no_puede_editar_ni_eliminar_super_admin(sesiones):
    super_id = sesiones["super_admin"][1]["id"]
    r = c.put(f"/usuarios/{super_id}", headers=h(sesiones, "admin"), json={"activo": False})
    assert r.status_code == 403
    r = c.delete(f"/usuarios/{super_id}", headers=h(sesiones, "admin"))
    assert r.status_code == 403


def test_admin_no_puede_ascender_a_nadie_a_super_admin(sesiones):
    res_id = sesiones["residente"][1]["id"]
    r = c.put(f"/usuarios/{res_id}", headers=h(sesiones, "admin"), json={"rol_id": 1})
    assert r.status_code == 403


def test_nadie_cambia_su_propio_rol_ni_se_desactiva(sesiones):
    for rol in ("super_admin", "admin"):
        yo = sesiones[rol][1]["id"]
        assert c.put(f"/usuarios/{yo}", headers=h(sesiones, rol), json={"rol_id": 3}).status_code == 400
        assert c.put(f"/usuarios/{yo}", headers=h(sesiones, rol), json={"activo": False}).status_code == 400
    yo = sesiones["super_admin"][1]["id"]
    assert c.delete(f"/usuarios/{yo}", headers=h(sesiones, "super_admin")).status_code == 400


def test_super_admin_elimina_usuario_y_admin_no(sesiones):
    correo = f"borrable.{int(time.time())}@x.com"
    nuevo = c.post("/register", headers=h(sesiones, "super_admin"), json={
        "nombre": "Borrable", "correo": correo, "contrasena": "12345678", "rol_id": 3,
    }).json()
    assert c.delete(f"/usuarios/{nuevo['id']}", headers=h(sesiones, "admin")).status_code == 403
    assert c.delete(f"/usuarios/{nuevo['id']}", headers=h(sesiones, "super_admin")).status_code == 204
    assert c.get(f"/usuarios/{nuevo['id']}", headers=h(sesiones, "super_admin")).status_code == 404


def test_usuario_desactivado_pierde_acceso(sesiones):
    correo = f"inactivo.{int(time.time())}@x.com"
    nuevo = c.post("/register", headers=h(sesiones, "admin"), json={
        "nombre": "Inactivo", "correo": correo, "contrasena": "12345678", "rol_id": 3,
    }).json()
    tok = c.post("/login", json={"correo": correo, "password": "12345678"}).json()["access_token"]
    assert c.get("/propiedades", headers={"Authorization": f"Bearer {tok}"}).status_code == 200
    c.put(f"/usuarios/{nuevo['id']}", headers=h(sesiones, "admin"), json={"activo": False})
    assert c.get("/propiedades", headers={"Authorization": f"Bearer {tok}"}).status_code == 401
    assert c.post("/login", json={"correo": correo, "password": "12345678"}).json()["ok"] is False


# ---------------------------------------------------------------------------
# 5. Chatbot: aislamiento de sesiones y filtrado por módulo
# ---------------------------------------------------------------------------
def test_chat_residente_no_ve_sesiones_de_otros(sesiones):
    # tesorería crea una conversación
    s = c.post("/chat/ask", headers=h(sesiones, "tesoreria"), json={"mensaje": "hola"}).json()
    sid = s["sesion_id"]
    # residente: no aparece en su lista, no puede leerla ni escribir en ella
    lista = c.get("/chat/sesiones", headers=h(sesiones, "residente")).json()
    assert all(x["id"] != sid for x in lista)
    assert c.get(f"/chat/sesiones/{sid}/mensajes", headers=h(sesiones, "residente")).status_code == 403
    assert c.post("/chat/ask", headers=h(sesiones, "residente"),
                  json={"mensaje": "hola", "sesion_id": sid}).status_code == 403
    # el admin (usuarios.ver) sí puede supervisarla
    assert c.get(f"/chat/sesiones/{sid}/mensajes", headers=h(sesiones, "admin")).status_code == 200


def test_chat_no_revela_finanzas_a_quien_no_tiene_permiso(sesiones):
    r = c.post("/chat/ask", headers=h(sesiones, "residente"), json={"mensaje": "¿cuál es el saldo?"}).json()
    assert "no tiene acceso" in r["respuesta"].lower()
    assert "$" not in r["respuesta"]
    r = c.post("/chat/ask", headers=h(sesiones, "seguridad"), json={"mensaje": "lista de residentes"}).json()
    assert "no tiene acceso" not in r["respuesta"].lower()  # seguridad sí ve residentes
    r = c.post("/chat/ask", headers=h(sesiones, "tesoreria"), json={"mensaje": "¿cuál es el saldo?"}).json()
    assert "saldo" in r["respuesta"].lower() and "no tiene acceso" not in r["respuesta"].lower()


# ---------------------------------------------------------------------------
# 6. Notificaciones filtradas por módulo
# ---------------------------------------------------------------------------
def test_notificaciones_filtradas_por_permisos(sesiones):
    tipos = lambda rol: {n["tipo"] for n in c.get("/notificaciones", headers=h(sesiones, rol)).json()}  # noqa: E731
    assert not tipos("residente") & {"mora", "proximo"}       # sin finanzas
    assert not tipos("seguridad") & {"mora", "proximo"}
    assert not tipos("tesoreria") & {"evento", "mantenimiento"}


# ---------------------------------------------------------------------------
# 7. Eventos: solo fechas posteriores al día actual
# ---------------------------------------------------------------------------
def test_eventos_solo_fechas_futuras(sesiones):
    from datetime import date, timedelta
    hdr = h(sesiones, "admin")
    hoy = date.today()
    base = {"titulo": "Asamblea", "descripcion": "Prueba", "lugar": "Salón"}

    # hoy y ayer → 400
    for f in (hoy, hoy - timedelta(days=1)):
        r = c.post("/eventos", headers=hdr, json={**base, "fecha": f.isoformat()})
        assert r.status_code == 400, r.text
        assert "posterior" in r.json()["detail"]

    # mañana → 201
    r = c.post("/eventos", headers=hdr, json={**base, "fecha": (hoy + timedelta(days=1)).isoformat()})
    assert r.status_code == 201, r.text
    eid = r.json()["id"]

    # editar moviéndolo al pasado → 400; editar solo el título (misma fecha) → 200
    r = c.put(f"/eventos/{eid}", headers=hdr, json={**base, "fecha": hoy.isoformat()})
    assert r.status_code == 400
    r = c.put(f"/eventos/{eid}", headers=hdr, json={**base, "titulo": "Asamblea 2", "fecha": (hoy + timedelta(days=1)).isoformat()})
    assert r.status_code == 200 and r.json()["titulo"] == "Asamblea 2"

    c.delete(f"/eventos/{eid}", headers=hdr)


# ---------------------------------------------------------------------------
# 8. Verificación de correo y recuperación de contraseña
# ---------------------------------------------------------------------------
def _token_de(correo, campo):
    import psycopg2
    conn = psycopg2.connect(_db_url())
    with conn, conn.cursor() as cur:
        cur.execute(f"SELECT {campo} FROM usuarios WHERE correo = %s", (correo,))
        row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def test_registro_publico_requiere_verificar_correo():
    correo = f"nuevo.{int(time.time())}@x.com"
    r = c.post("/register", json={"nombre": "Nuevo", "correo": correo, "contrasena": "Prueba2026!", "rol_id": 3})
    assert r.status_code == 200, r.text
    assert r.json()["correo_verificado"] is False
    assert r.json()["verificacion"]["requerida"] is True

    # No puede iniciar sesión hasta verificar
    lg = c.post("/login", json={"correo": correo, "password": "Prueba2026!"}).json()
    assert lg["ok"] is False and lg.get("codigo") == "correo_no_verificado"

    # Token inválido → no verifica
    assert c.get("/verificar-correo/token-falso").json()["estado"] == "invalido"

    # Token real → verifica y ya puede entrar; reabrir el enlace sigue siendo 'ok' (idempotente)
    tok = _token_de(correo, "token_verificacion")
    assert tok
    assert c.get(f"/verificar-correo/{tok}").json()["estado"] == "ok"
    assert c.get(f"/verificar-correo/{tok}").json()["estado"] == "ok"
    lg = c.post("/login", json={"correo": correo, "password": "Prueba2026!"}).json()
    assert lg["ok"] is True and lg["usuario"]["correo_verificado"] is True


def test_reenviar_verificacion_no_revela_existencia():
    r1 = c.post("/reenviar-verificacion", json={"correo": "nadie.inexistente@x.com"})
    r2 = c.post("/reenviar-verificacion", json={"correo": ADMIN_EMAIL})
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["mensaje"] == r2.json()["mensaje"]


def test_usuarios_creados_por_admin_quedan_verificados(sesiones):
    correo = f"poradmin.{int(time.time())}@x.com"
    r = c.post("/register", headers=h(sesiones, "admin"), json={
        "nombre": "Por admin", "correo": correo, "contrasena": "Prueba2026!", "rol_id": 4,
    })
    assert r.status_code == 200 and r.json()["correo_verificado"] is True
    assert "verificacion" not in r.json()
    assert c.post("/login", json={"correo": correo, "password": "Prueba2026!"}).json()["ok"] is True


def test_recuperacion_password_flujo_completo(sesiones):
    correo = f"olvido.{int(time.time())}@x.com"
    c.post("/register", headers=h(sesiones, "admin"), json={
        "nombre": "Olvidadizo", "correo": correo, "contrasena": "Vieja2026!", "rol_id": 3,
    })
    # Solicitud: misma respuesta exista o no el correo
    r = c.post("/recuperar-password", json={"correo": correo})
    assert r.status_code == 200
    r2 = c.post("/recuperar-password", json={"correo": "no.existe.999@x.com"})
    assert r.json()["mensaje"] == r2.json()["mensaje"]

    tok = _token_de(correo, "token_recuperacion")
    assert tok
    assert c.get(f"/validar-token-recuperacion/{tok}").json()["valido"] is True
    assert c.get("/validar-token-recuperacion/falso").json()["valido"] is False

    # Contraseña corta → 422 ; token falso → ok False
    assert c.post("/restablecer-password", json={"token": tok, "nueva_password": "corta"}).status_code == 422
    assert c.post("/restablecer-password", json={"token": "falso", "nueva_password": "Nueva2026!"}).json()["ok"] is False

    # Restablecer de verdad
    assert c.post("/restablecer-password", json={"token": tok, "nueva_password": "Nueva2026!"}).json()["ok"] is True
    assert c.post("/login", json={"correo": correo, "password": "Vieja2026!"}).json()["ok"] is False
    assert c.post("/login", json={"correo": correo, "password": "Nueva2026!"}).json()["ok"] is True
    # El token se consume
    assert c.get(f"/validar-token-recuperacion/{tok}").json()["valido"] is False


# ---------------------------------------------------------------------------
# CÓDIGOS DE 6 DÍGITOS (verificación de cuenta y recuperación)
# ---------------------------------------------------------------------------
def test_verificacion_con_codigo_de_6_digitos():
    correo = f"codigo.{int(time.time())}@x.com"
    r = c.post("/register", json={"nombre": "Con Código", "correo": correo, "contrasena": "Prueba2026!", "rol_id": 3})
    assert r.status_code == 200 and "codigo" not in r.json().get("verificacion", {})

    codigo = _token_de(correo, "codigo_verificacion")
    assert codigo and len(codigo) == 6 and codigo.isdigit()

    # Formato inválido → 422; código incorrecto → invalido
    assert c.post("/verificar-codigo", json={"correo": correo, "codigo": "12"}).status_code == 422
    malo = "000000" if codigo != "000000" else "111111"
    assert c.post("/verificar-codigo", json={"correo": correo, "codigo": malo}).json()["estado"] == "invalido"
    lg = c.post("/login", json={"correo": correo, "password": "Prueba2026!"}).json()
    assert lg["ok"] is False

    # Código correcto → verificado; repetir sigue siendo ok; login funciona
    assert c.post("/verificar-codigo", json={"correo": correo, "codigo": codigo}).json()["estado"] == "ok"
    assert c.post("/verificar-codigo", json={"correo": correo, "codigo": codigo}).json()["estado"] == "ok"
    lg = c.post("/login", json={"correo": correo, "password": "Prueba2026!"}).json()
    assert lg["ok"] is True and lg["usuario"]["correo_verificado"] is True


def test_recuperacion_con_codigo_de_6_digitos(sesiones):
    correo = f"olvido.codigo.{int(time.time())}@x.com"
    admin = sesiones["admin"][0]
    r = c.post("/register", headers=admin, json={"nombre": "Olvido", "correo": correo, "contrasena": "Prueba2026!", "rol_id": 3})
    assert r.status_code == 200

    r = c.post("/recuperar-password", json={"correo": correo})
    assert r.status_code == 200 and "token" not in r.json() and "codigo" not in r.json()
    codigo = _token_de(correo, "codigo_recuperacion")
    token = _token_de(correo, "token_recuperacion")
    assert codigo and len(codigo) == 6 and token

    malo = "000000" if codigo != "000000" else "111111"
    assert c.post("/validar-codigo-recuperacion", json={"correo": correo, "codigo": malo}).json()["valido"] is False
    v = c.post("/validar-codigo-recuperacion", json={"correo": correo, "codigo": codigo}).json()
    assert v["valido"] is True and v["token"] == token

    ok = c.post("/restablecer-password", json={"token": v["token"], "nueva_password": "NuevaClave2026!"}).json()
    assert ok["ok"] is True
    # El código queda consumido
    assert c.post("/validar-codigo-recuperacion", json={"correo": correo, "codigo": codigo}).json()["valido"] is False
    assert c.post("/login", json={"correo": correo, "password": "NuevaClave2026!"}).json()["ok"] is True
