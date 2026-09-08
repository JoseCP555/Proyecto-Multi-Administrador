"""Prueba E2E de RBAC en la interfaz: entra como cada rol, revisa el menú,
los botones de acción y las rutas bloqueadas. Genera capturas en ../capturas_rbac/.

    python tests_ui_rbac.py   (requiere frontend :3000 y backend :8041 arriba)
"""
import os, sys, json
from playwright.sync_api import sync_playwright

URL = os.getenv("UI_URL", "http://localhost:3000")
PASS = "Prueba2026!"
OUT = os.path.join(os.path.dirname(__file__), "..", "capturas_rbac")
os.makedirs(OUT, exist_ok=True)

MENU_TODO = ["Dashboard", "Usuarios", "Residentes", "Propiedades", "Finanzas",
             "Mantenimiento", "Documentos", "Eventos", "Chat asistente", "Configuración"]

ESPERADO = {
    "super_admin": {
        "menu": MENU_TODO,
        "ruta_ok": "/dashboard/usuarios", "ruta_bloqueada": None,
        "ve_boton": [("/dashboard/usuarios", "Nuevo usuario"), ("/dashboard/configuracion", "Respaldar BD")],
        "no_ve_boton": [],
    },
    "admin": {
        "menu": MENU_TODO,
        "ruta_ok": "/dashboard/finanzas", "ruta_bloqueada": None,
        "ve_boton": [("/dashboard/usuarios", "Nuevo usuario"), ("/dashboard/finanzas", "Nuevo")],
        "no_ve_boton": [("/dashboard/configuracion", "Respaldar BD")],
    },
    "tesoreria": {
        "menu": ["Dashboard", "Residentes", "Propiedades", "Finanzas", "Documentos", "Chat asistente"],
        "ruta_ok": "/dashboard/finanzas", "ruta_bloqueada": "/dashboard/usuarios",
        "ve_boton": [("/dashboard/finanzas", "Nuevo"), ("/dashboard/finanzas", "Exportar")],
        "no_ve_boton": [("/dashboard/residentes", "Nuevo residente"), ("/dashboard/documentos", "Subir documento")],
    },
    "residente": {
        "menu": ["Dashboard", "Propiedades", "Mantenimiento", "Documentos", "Eventos", "Chat asistente"],
        "ruta_ok": "/dashboard/mantenimiento", "ruta_bloqueada": "/dashboard/finanzas",
        "ve_boton": [("/dashboard/mantenimiento", "Nueva tarea")],
        "no_ve_boton": [("/dashboard/mantenimiento", "Completar"), ("/dashboard/eventos", "Nuevo"),
                        ("/dashboard/propiedades", "Nueva")],
    },
    "seguridad": {
        "menu": ["Dashboard", "Residentes", "Propiedades", "Mantenimiento", "Documentos", "Eventos", "Chat asistente"],
        "ruta_ok": "/dashboard/residentes", "ruta_bloqueada": "/dashboard/finanzas",
        "ve_boton": [("/dashboard/mantenimiento", "Nueva tarea"), ("/dashboard/mantenimiento", "Completar")],
        "no_ve_boton": [("/dashboard/residentes", "Nuevo residente"), ("/dashboard/eventos", "Nuevo")],
    },
}

fallos = []

def check(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        fallos.append(msg)

with sync_playwright() as p:
    browser = p.chromium.launch()
    for rol, exp in ESPERADO.items():
        print(f"\n=== {rol} ===")
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        page.set_default_navigation_timeout(60000)
        _goto = page.goto
        page.goto = lambda u, **k: _goto(u, wait_until="domcontentloaded", **k)
        page.goto(f"{URL}/login")
        page.fill("input[type=email]", f"rbac.{rol}@test.com")
        page.fill("input[type=password]", PASS)
        page.keyboard.press("Enter")
        page.wait_for_url("**/dashboard**", timeout=15000)
        page.wait_for_timeout(1200)
        page.screenshot(path=f"{OUT}/{rol}_dashboard.png", full_page=True)

        # Menú lateral
        nav = page.locator("aside nav")
        items = [t.strip() for t in nav.locator("a span").all_inner_texts()]
        check(items == exp["menu"], f"menú = {items}")

        # Rutas
        page.goto(f"{URL}{exp['ruta_ok']}"); page.wait_for_timeout(900)
        check("Acceso restringido" not in page.content(), f"ruta permitida {exp['ruta_ok']}")
        if exp["ruta_bloqueada"]:
            page.goto(f"{URL}{exp['ruta_bloqueada']}"); page.wait_for_timeout(900)
            check("Acceso restringido" in page.content(), f"ruta bloqueada {exp['ruta_bloqueada']} muestra 'Acceso restringido'")
            page.screenshot(path=f"{OUT}/{rol}_bloqueado.png")

        # Botones
        for ruta, texto in exp["ve_boton"]:
            page.goto(f"{URL}{ruta}"); page.wait_for_timeout(1000)
            check(page.get_by_text(texto, exact=False).count() > 0, f"VE botón '{texto}' en {ruta}")
        for ruta, texto in exp["no_ve_boton"]:
            page.goto(f"{URL}{ruta}"); page.wait_for_timeout(1000)
            check(page.get_by_role("button", name=texto).count() == 0, f"NO ve botón '{texto}' en {ruta}")

        # Dashboard: sin datos financieros para roles sin reportes
        page.goto(f"{URL}/dashboard"); page.wait_for_timeout(1000)
        html = page.content()
        if "reportes.ver" not in exp and rol in ("residente", "seguridad"):
            check("Resumen financiero" not in html and "Ingresos por mes" not in html, "dashboard sin datos financieros")
        if rol in ("super_admin", "admin", "tesoreria"):
            check("Resumen financiero" in html, "dashboard con resumen financiero")
        ctx.close()
    browser.close()

print("\n" + ("TODO OK ✅" if not fallos else f"{len(fallos)} FALLOS ❌"))
sys.exit(1 if fallos else 0)
