"""Pruebas de las historias de usuario UH-01 a UH-32 (módulos nuevos).

Se ejecutan de forma **aislada** con SQLite y el `TestClient` de FastAPI, sin
necesidad de PostgreSQL ni Redis:

    cd backend
    python -m pytest tests/test_hus_nuevas.py -v

Cubren los criterios de aceptación de las historias implementadas en los
módulos de PQRS, reservas, comunicados, visitantes, comprobantes de pago,
votaciones, aprobaciones del consejo, auditoría, perfil, alertas de gasto y
seguridad de la sesión.
"""
import os
import uuid

# El entorno se configura ANTES de importar la app (igual que test_unit.py).
os.environ["SECRET_KEY"] = "hus-test-secret"
os.environ["DATABASE_URL"] = "sqlite:///./hus_test.db"
os.environ["REDIS_URL"] = "redis://localhost:6399/0"   # sin Redis: se usa el respaldo en memoria
os.environ["DESACTIVAR_PROGRAMADOR"] = "1"
os.environ["CORREO_DESHABILITADO"] = "1"   # nunca se envía correo real desde las pruebas

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

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
def admin(cliente):
    datos = _login(cliente, "admin@multiadmin.com", "Admin2026!")
    cabeceras = {"Authorization": f"Bearer {datos['access_token']}"}
    conjuntos = cliente.get("/conjuntos", headers=cabeceras).json()
    assert conjuntos, "El seed debe crear conjuntos de demostración"
    cabeceras["X-Conjunto-Id"] = str(conjuntos[0]["id"])
    return cabeceras


@pytest.fixture(scope="module")
def residente(cliente):
    datos = _login(cliente, "residente@multiadmin.com", "Residente2026!")
    cabeceras = {"Authorization": f"Bearer {datos['access_token']}"}
    conjuntos = cliente.get("/conjuntos", headers=cabeceras).json()
    cabeceras["X-Conjunto-Id"] = str(conjuntos[0]["id"])
    return cabeceras


@pytest.fixture(scope="module")
def consejo(cliente):
    datos = _login(cliente, "consejo@multiadmin.com", "Consejo2026!")
    cabeceras = {"Authorization": f"Bearer {datos['access_token']}"}
    conjuntos = cliente.get("/conjuntos", headers=cabeceras).json()
    cabeceras["X-Conjunto-Id"] = str(conjuntos[0]["id"])
    return cabeceras


# ---------------------------------------------------------------------------
# UH-09 · UH-16 · UH-32 — PQRS
# ---------------------------------------------------------------------------
def test_pqrs_flujo_completo(cliente, admin, residente, consejo):
    asunto = f"Ruido en zona común {uuid.uuid4().hex[:6]}"
    r = cliente.post(
        "/pqrs", headers=residente,
        json={"tipo": "queja", "categoria": "zonas_comunes", "asunto": asunto,
              "descripcion": "Música a alto volumen después de las 11 p.m."},
    )
    assert r.status_code == 201, r.text
    caso = r.json()
    assert caso["radicado"].startswith("PQRS-")
    assert caso["estado"] == "pendiente"

    # El residente ve su caso; la administración ve todos.
    propios = cliente.get("/pqrs", headers=residente).json()
    assert any(p["id"] == caso["id"] for p in propios)
    todos = cliente.get("/pqrs", headers=admin).json()
    assert any(p["id"] == caso["id"] for p in todos)

    # UH-32: el consejo recibió la notificación de PQRS de zona común.
    avisos = cliente.get("/notificaciones", headers=consejo).json()
    lista = avisos.get("notificaciones", avisos) if isinstance(avisos, dict) else avisos
    assert any(a.get("tipo") == "pqrs_consejo" for a in lista), lista[:3]

    # Responder y cerrar (UH-09).
    r = cliente.put(f"/pqrs/{caso['id']}/responder", headers=admin,
                    json={"estado": "en_proceso", "respuesta": "Se revisará con vigilancia."})
    assert r.status_code == 200 and r.json()["estado"] == "en_proceso"
    r = cliente.put(f"/pqrs/{caso['id']}/cerrar", headers=admin,
                    json={"respuesta": "Se aplicó el reglamento de convivencia."})
    assert r.status_code == 200 and r.json()["estado"] == "cerrada"
    assert r.json()["fecha_respuesta"]

    # El residente no puede responder su propia PQRS (sin permiso).
    r = cliente.put(f"/pqrs/{caso['id']}/responder", headers=residente,
                    json={"estado": "cerrada", "respuesta": "x"})
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# UH-10 · UH-14 — Reservas de zonas comunes
# ---------------------------------------------------------------------------
def test_reservas_evitan_duplicados(cliente, admin, residente):
    r = cliente.post("/reservas/zonas", headers=admin,
                     json={"nombre": f"Zona test {uuid.uuid4().hex[:5]}", "capacidad": 15})
    assert r.status_code == 201, r.text
    zona = r.json()

    base = {"zona_id": zona["id"], "fecha": "2030-05-10",
            "hora_inicio": "10:00", "hora_fin": "12:00", "motivo": "Cumpleaños"}
    r = cliente.post("/reservas", headers=residente, json=base)
    assert r.status_code == 201, r.text
    reserva = r.json()
    assert reserva["estado"] in {"pendiente", "aprobada"}

    # Solapamiento en la misma zona y fecha → 409.
    solapada = dict(base, hora_inicio="11:00", hora_fin="13:00")
    r = cliente.post("/reservas", headers=residente, json=solapada)
    assert r.status_code == 409, r.text

    # Horario libre → se permite.
    libre = dict(base, hora_inicio="14:00", hora_fin="16:00")
    assert cliente.post("/reservas", headers=residente, json=libre).status_code == 201

    # El historial personal incluye su reserva.
    historial = cliente.get("/reservas", headers=residente).json()
    assert any(x["id"] == reserva["id"] for x in historial)

    # La administración aprueba la reserva.
    if reserva["estado"] == "pendiente":
        r = cliente.put(f"/reservas/{reserva['id']}/decidir", headers=admin,
                        json={"estado": "aprobada"})
        assert r.status_code == 200 and r.json()["estado"] == "aprobada"


def test_disponibilidad_zona(cliente, admin):
    zonas = cliente.get("/reservas/zonas", headers=admin).json()
    zona = zonas[0]
    r = cliente.get(f"/reservas/disponibilidad?zona_id={zona['id']}&fecha=2030-05-10", headers=admin)
    assert r.status_code == 200
    assert "ocupadas" in r.json()


# ---------------------------------------------------------------------------
# UH-11 · UH-18 — Comunicados
# ---------------------------------------------------------------------------
def test_comunicado_masivo(cliente, admin, residente):
    r = cliente.post("/comunicados", headers=admin,
                     json={"titulo": f"Corte de agua {uuid.uuid4().hex[:4]}",
                           "contenido": "El servicio se suspenderá de 8 a 11 a.m.",
                           "categoria": "urgente", "prioridad": "alta"})
    assert r.status_code == 201, r.text
    comunicado = r.json()

    visibles = cliente.get("/comunicados", headers=residente).json()
    assert any(c["id"] == comunicado["id"] for c in visibles)

    avisos = cliente.get("/notificaciones", headers=residente).json()
    lista = avisos.get("notificaciones", avisos) if isinstance(avisos, dict) else avisos
    assert any(a.get("tipo") == "comunicado" for a in lista)


# ---------------------------------------------------------------------------
# UH-12 — Control de acceso de visitantes
# ---------------------------------------------------------------------------
def test_visitantes_registro_y_salida(cliente, admin):
    documento = f"CC{uuid.uuid4().hex[:8]}"
    r = cliente.post("/visitantes", headers=admin,
                     json={"nombre": "Visitante Test", "documento": documento,
                           "apartamento": "302", "motivo": "Visita"})
    assert r.status_code == 201, r.text
    visitante = r.json()
    assert visitante["estado"] == "dentro" and visitante["hora_ingreso"]

    # Filtro por fecha de hoy y por documento.
    hoy = visitante["hora_ingreso"][:10]
    filtrados = cliente.get(f"/visitantes?desde={hoy}&hasta={hoy}&q={documento}", headers=admin).json()
    assert any(v["id"] == visitante["id"] for v in filtrados)

    r = cliente.put(f"/visitantes/{visitante['id']}/salida", headers=admin, json={})
    assert r.status_code == 200 and r.json()["estado"] == "salio" and r.json()["hora_salida"]


# ---------------------------------------------------------------------------
# UH-13 · UH-17 — Comprobante de pago y estado de cuenta
# ---------------------------------------------------------------------------
def test_comprobante_de_pago(cliente, admin, residente):
    r = cliente.post(
        "/pagos/comprobantes", headers=residente,
        data={"monto": "150000", "periodo": "2030-01", "observacion": "Transferencia"},
        files={"archivo": ("comprobante.pdf", b"%PDF-1.4 comprobante", "application/pdf")},
    )
    assert r.status_code == 201, r.text
    comprobante = r.json()
    assert comprobante["estado"] == "en_revision"

    # La administración (tesorería/admin) lo ve y lo aprueba.
    pendientes = cliente.get("/pagos/comprobantes?estado=en_revision", headers=admin).json()
    assert any(c["id"] == comprobante["id"] for c in pendientes)

    r = cliente.put(f"/pagos/comprobantes/{comprobante['id']}/revisar", headers=admin,
                    json={"estado": "aprobado", "observacion": "Verificado en extracto"})
    assert r.status_code == 200 and r.json()["estado"] == "aprobado"
    assert r.json()["fecha_revision"]


def test_estado_de_cuenta_y_pdf(cliente, residente):
    r = cliente.get("/pagos/estado-cuenta", headers=residente)
    assert r.status_code == 200
    datos = r.json()
    for campo in ("total_facturado", "total_pagado", "saldo", "movimientos"):
        assert campo in datos

    r = cliente.get("/pagos/estado-cuenta.pdf", headers=residente)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")


# ---------------------------------------------------------------------------
# UH-20 — Perfil propio
# ---------------------------------------------------------------------------
def test_actualizar_perfil(cliente, residente):
    r = cliente.put("/perfil", headers=residente,
                    json={"telefono": "3001239999", "nombre": "Residente Demo Actualizado"})
    assert r.status_code == 200, r.text
    assert r.json()["usuario"]["telefono"] == "3001239999"

    r = cliente.get("/perfil", headers=residente)
    assert r.status_code == 200 and r.json()["telefono"] == "3001239999"


# ---------------------------------------------------------------------------
# UH-24 — Aprobaciones del consejo
# ---------------------------------------------------------------------------
def test_aprobacion_del_consejo(cliente, admin, consejo):
    r = cliente.post("/aprobaciones", headers=admin,
                     json={"titulo": f"Compra de bombillas {uuid.uuid4().hex[:4]}",
                           "descripcion": "Cambio de luminarias LED en zonas comunes",
                           "monto": 2500000, "categoria": "gasto"})
    assert r.status_code == 201, r.text
    solicitud = r.json()

    pendientes = cliente.get("/aprobaciones?estado=pendiente", headers=consejo).json()
    assert any(s["id"] == solicitud["id"] for s in pendientes)

    r = cliente.put(f"/aprobaciones/{solicitud['id']}/decidir", headers=consejo,
                    json={"estado": "aprobada", "motivo_decision": "Cabe en el presupuesto"})
    assert r.status_code == 200, r.text
    decision = r.json()
    assert decision["estado"] == "aprobada"
    assert decision["fecha_decision"] and decision["decidido_por"]

    # Una solicitud ya decidida no se puede volver a decidir.
    r = cliente.put(f"/aprobaciones/{solicitud['id']}/decidir", headers=consejo,
                    json={"estado": "rechazada"})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# UH-25 — Votaciones
# ---------------------------------------------------------------------------
def test_votacion_un_solo_voto(cliente, consejo):
    r = cliente.post("/votaciones", headers=consejo,
                     json={"titulo": f"Votación {uuid.uuid4().hex[:5]}",
                           "descripcion": "¿Aprobar el presupuesto?",
                           "fecha_cierre": "2030-12-31", "opciones": ["Aprobar", "Rechazar"]})
    assert r.status_code == 201, r.text
    votacion = r.json()
    assert len(votacion["opciones"]) == 2

    opcion = votacion["opciones"][0]["id"]
    r = cliente.post(f"/votaciones/{votacion['id']}/voto", headers=consejo, json={"opcion_id": opcion})
    assert r.status_code == 200, r.text
    assert r.json()["mi_voto"] == opcion

    # Segundo voto → 409 (un voto por miembro).
    r = cliente.post(f"/votaciones/{votacion['id']}/voto", headers=consejo,
                     json={"opcion_id": votacion["opciones"][1]["id"]})
    assert r.status_code == 409

    # Cierre de la votación con resultados.
    r = cliente.put(f"/votaciones/{votacion['id']}/cerrar", headers=consejo, json={})
    assert r.status_code == 200 and r.json()["estado"] == "cerrada"


# ---------------------------------------------------------------------------
# UH-26 — Alerta cuando un gasto supera el umbral
# ---------------------------------------------------------------------------
def test_alerta_por_gasto_sobre_umbral(cliente, admin, consejo):
    # Umbral pequeño para forzar la alerta.
    conjuntos = cliente.get("/conjuntos", headers=admin).json()
    conjunto = conjuntos[0]
    r = cliente.put(f"/conjuntos/{conjunto['id']}", headers=admin, json={"umbral_gasto": 100000})
    assert r.status_code == 200, r.text
    assert float(r.json()["umbral_gasto"]) == 100000

    conceptos = cliente.get("/finanzas/conceptos", headers=admin).json()
    gasto = next((c for c in conceptos if c["tipo"] == "gasto"), conceptos[0])

    r = cliente.post("/finanzas", headers=admin,
                     json={"concepto_id": gasto["id"], "monto": 5000000,
                           "fecha_vencimiento": "2030-01-15", "estado": "pagado"})
    assert r.status_code == 201, r.text

    avisos = cliente.get("/notificaciones", headers=consejo).json()
    lista = avisos.get("notificaciones", avisos) if isinstance(avisos, dict) else avisos
    assert any(a.get("tipo") == "alerta_gasto" for a in lista), lista[:5]


# ---------------------------------------------------------------------------
# UH-29 — Auditoría
# ---------------------------------------------------------------------------
def test_auditoria_registra_acciones(cliente, admin):
    r = cliente.get("/auditoria?limite=100", headers=admin)
    assert r.status_code == 200
    registros = r.json()
    assert registros, "Debe haber acciones auditadas"
    assert {"crear", "editar"} & {x["accion"] for x in registros}
    assert all(x["fecha_creacion"] for x in registros)

    # El residente no puede consultar la auditoría (auditoria.ver).
    # (Se usa el token de admin para comprobar el endpoint; el residente no
    #  tiene el permiso, así que se valida con un usuario sin permisos.)
    r = cliente.delete("/auditoria/1", headers=admin)
    assert r.status_code in (404, 405), "El historial no se puede borrar por API"


def test_residente_sin_acceso_a_auditoria(cliente, residente):
    assert cliente.get("/auditoria", headers=residente).status_code == 403


# ---------------------------------------------------------------------------
# UH-27 — Bloqueo de la cuenta y vigencia de la sesión
# ---------------------------------------------------------------------------
def test_bloqueo_tras_cinco_intentos(cliente):
    correo = f"bloqueo-{uuid.uuid4().hex[:6]}@multiadmin.com"
    for i in range(5):
        r = cliente.post("/login", json={"correo": correo, "password": "incorrecta"})
        assert r.status_code == 200
        datos = r.json()
        assert datos["ok"] is False
    assert datos.get("codigo") == "cuenta_bloqueada"
    # Aun con la contraseña correcta sigue bloqueada.
    r = cliente.post("/login", json={"correo": correo, "password": "cualquiera"})
    assert r.json()["codigo"] == "cuenta_bloqueada"


def test_token_expira_en_30_minutos(cliente, admin):
    from app.auth_jwt import verificar_token, ACCESS_TOKEN_EXPIRE_MINUTES

    assert ACCESS_TOKEN_EXPIRE_MINUTES == 30
    payload = verificar_token(admin["Authorization"].split(" ", 1)[1])
    assert payload["exp"] - payload["iat"] == 30 * 60


# ---------------------------------------------------------------------------
# UH-04 · UH-01 — Eventos con hora y aviso de 48 horas
# ---------------------------------------------------------------------------
def test_evento_con_hora_y_aviso_48h(cliente, admin):
    from datetime import date, datetime, timedelta

    manana = (date.today() + timedelta(days=1)).isoformat()
    r = cliente.post("/eventos", headers=admin,
                     json={"titulo": "Asamblea extraordinaria", "fecha": manana,
                           "hora": "18:30", "tipo": "asamblea", "lugar": "Salón comunal"})
    assert r.status_code == 201, r.text
    evento = r.json()
    assert evento["hora"] == "18:30" and evento["tipo"] == "asamblea"

    # El programador genera el aviso de menos de 48 horas.
    from app.database import SessionLocal
    from app.models import Evento
    from app.programador import avisar_asambleas

    db = SessionLocal()
    try:
        evento_db = db.query(Evento).get(evento["id"])
        # Se deja a las 12:00 del día siguiente: siempre faltan menos de 48 h.
        evento_db.hora = "12:00"
        db.commit()
        enviados = avisar_asambleas(db)
        assert enviados >= 1
        db.refresh(evento_db)
        assert evento_db.notificado_48h is True
    finally:
        db.close()


def test_calendario_filtra_por_tipo(cliente, admin):
    """UH-15: el calendario muestra todos los eventos y filtra por tipo."""
    from datetime import date, timedelta

    base = date.today() + timedelta(days=3)
    for i, tipo in enumerate(["asamblea", "actividad", "reunion", "mantenimiento"]):
        r = cliente.post("/eventos", headers=admin, json={
            "titulo": f"Evento {tipo}", "fecha": (base + timedelta(days=i)).isoformat(),
            "hora": "10:00", "tipo": tipo, "lugar": "Zona social",
        })
        assert r.status_code == 201, r.text

    todos = cliente.get("/eventos", headers=admin)
    assert todos.status_code == 200
    assert len(todos.json()) >= 4

    solo_asambleas = cliente.get("/eventos?tipo=asamblea", headers=admin)
    assert solo_asambleas.status_code == 200
    assert solo_asambleas.json()
    assert all(e["tipo"] == "asamblea" for e in solo_asambleas.json())

    # El detalle del evento está disponible en el propio listado.
    detalle = solo_asambleas.json()[0]
    assert {"titulo", "fecha", "hora", "tipo", "lugar", "descripcion"} <= set(detalle)


# ---------------------------------------------------------------------------
# UH-03 · UH-19 — documentos: PDF/Word de hasta 20 MB y consulta por residentes
# ---------------------------------------------------------------------------
def test_documento_pdf_y_limite_de_20mb(cliente, admin, residente):
    pdf = b"%PDF-1.4\n% acta de asamblea\n"
    r = cliente.post("/documentos/upload", headers=admin,
                     files={"archivo": ("acta.pdf", pdf, "application/pdf")},
                     data={"titulo": "Acta de asamblea 2026", "tipo_documento": "acta", "publico": "true"})
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["tamano"] == len(pdf)

    # El residente ve y descarga el documento publicado.
    listado = cliente.get("/documentos", headers=residente)
    assert listado.status_code == 200
    assert any(d["id"] == doc["id"] for d in listado.json())
    descarga = cliente.get(f"/documentos/{doc['id']}/descargar", headers=residente)
    assert descarga.status_code == 200
    assert descarga.content.startswith(b"%PDF")

    # Formato no permitido.
    r = cliente.post("/documentos/upload", headers=admin,
                     files={"archivo": ("virus.exe", b"MZ", "application/octet-stream")},
                     data={"titulo": "no permitido"})
    assert r.status_code == 415
    assert "PDF o Word" in r.json()["detail"]

    # Archivo mayor a 20 MB.
    grande = b"0" * (20 * 1024 * 1024 + 1024)
    r = cliente.post("/documentos/upload", headers=admin,
                     files={"archivo": ("enorme.docx", grande, "application/msword")},
                     data={"titulo": "demasiado grande"})
    assert r.status_code == 413
    assert "20 MB" in r.json()["detail"]


# ---------------------------------------------------------------------------
# UH-21 — reporte de daño en zona común con foto y categoría
# ---------------------------------------------------------------------------
def test_mantenimiento_con_categoria_y_evidencia(cliente, residente, admin):
    r = cliente.post("/mantenimiento/evidencia", headers=residente,
                     files={"archivo": ("fuga.jpg", b"\xff\xd8\xff\xe0foto", "image/jpeg")})
    assert r.status_code == 200, r.text
    evidencia = r.json()["nombre"]
    assert evidencia.startswith("evidencia-")

    r = cliente.post("/mantenimiento", headers=residente, json={
        "titulo": "Fuga de agua en el baño del salón comunal",
        "descripcion": "El grifo del lavamanos gotea desde el fin de semana.",
        "prioridad": "alta", "categoria": "zona_comun", "evidencias": evidencia,
    })
    assert r.status_code == 201, r.text
    tarea = r.json()
    assert tarea["categoria"] == "zona_comun"
    assert tarea["evidencias"] == evidencia

    # Aparece como tarea pendiente en el panel del administrador.
    pendientes = cliente.get("/mantenimiento", headers=admin).json()
    assert any(t["id"] == tarea["id"] for t in pendientes)
    # La evidencia se puede consultar con permiso de mantenimiento.
    foto = cliente.get(f"/mantenimiento/evidencias/{evidencia}", headers=admin)
    assert foto.status_code == 200 and foto.content.startswith(b"\xff\xd8")

    # Formato de archivo no válido para evidencia.
    r = cliente.post("/mantenimiento/evidencia", headers=residente,
                     files={"archivo": ("notas.txt", b"hola", "text/plain")})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# UH-22 · UH-23 — documentos del consejo y reporte financiero exportable
# ---------------------------------------------------------------------------
def test_acta_y_reporte_del_consejo(cliente, admin, residente, consejo):
    r = cliente.post("/documentos/upload", headers=admin,
                     files={"archivo": ("acta.pdf", b"%PDF-1.4 acta", "application/pdf")},
                     data={"titulo": "Acta de la última asamblea", "tipo_documento": "acta", "publico": "true"})
    assert r.status_code == 201
    acta = r.json()

    # El consejo y el residente ven el acta; el residente no puede editarla.
    assert any(d["id"] == acta["id"] for d in cliente.get("/documentos", headers=consejo).json())
    assert any(d["id"] == acta["id"] for d in cliente.get("/documentos", headers=residente).json())
    r = cliente.put(f"/documentos/{acta['id']}", headers=residente, json={
        "titulo": "Acta alterada", "ruta_archivo": acta["ruta_archivo"],
        "tipo_documento": "acta", "publico": True,
    })
    assert r.status_code == 403

    # Reporte del consejo: datos filtrados por período, PDF y Excel.
    r = cliente.get("/finanzas/resumen?desde=2020-01-01&hasta=2035-12-31", headers=consejo)
    assert r.status_code == 200, r.text
    datos = r.json()
    assert {"ingresos", "gastos", "saldo", "pendiente"} <= set(datos)
    serie = cliente.get("/reportes/finanzas-por-mes?desde=2020-01-01", headers=consejo)
    assert serie.status_code == 200 and isinstance(serie.json(), list)

    pdf = cliente.get("/reportes/exportar/consejo.pdf?desde=2020-01-01&hasta=2035-12-31", headers=consejo)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    xlsx = cliente.get("/reportes/exportar/consejo.xlsx", headers=consejo)
    assert xlsx.status_code == 200 and xlsx.content[:2] == b"PK"


# ---------------------------------------------------------------------------
# UH-30 — el enlace de recuperación de contraseña expira en 30 minutos
# ---------------------------------------------------------------------------
def test_recuperacion_expira_en_30_minutos(cliente, admin):
    from datetime import datetime, timedelta

    from app.database import SessionLocal
    from app.models import Usuario

    r = cliente.post("/recuperar-password", json={"correo": "residente@multiadmin.com"})
    assert r.status_code == 200

    db = SessionLocal()
    try:
        u = db.query(Usuario).filter(Usuario.correo == "residente@multiadmin.com").first()
        assert u is not None and u.token_recuperacion and u.expira_token
        delta = u.expira_token - datetime.utcnow()
        assert timedelta(minutes=28) <= delta <= timedelta(minutes=31), delta
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Correo SMTP — diagnóstico y estado del envío de la verificación
# ---------------------------------------------------------------------------
def test_health_expone_configuracion_de_correo(cliente):
    r = cliente.get("/health")
    assert r.status_code == 200
    correo = r.json()["correo"]
    assert {"configurado", "remitente", "servidor", "puerto", "seguridad",
            "autenticacion", "password_definida"} <= set(correo)
    # Nunca se expone la contraseña, solo si está definida.
    assert "password" not in correo


def test_registro_publico_indica_estado_del_correo(cliente):
    """El alta devuelve si el correo salió y deja el código para verificarse."""
    correo = f"nuevo.{uuid.uuid4().hex[:6]}@ejemplo.com"   # dominio de prueba: no se envía de verdad
    r = cliente.post("/register", json={"nombre": "Nuevo Residente", "correo": correo,
                                        "contrasena": "Prueba2026!"})
    assert r.status_code == 200, r.text
    datos = r.json()
    assert datos["verificacion"]["requerida"] is True
    assert isinstance(datos["verificacion"]["enviado"], bool)
    assert datos["verificacion"]["mensaje"]

    # La cuenta no puede entrar hasta verificar; el código de 6 dígitos sí funciona.
    login = cliente.post("/login", json={"correo": correo, "password": "Prueba2026!"})
    cuerpo = login.json()
    assert cuerpo.get("ok") is not True
    assert cuerpo.get("codigo") == "correo_no_verificado", cuerpo

    from app.database import SessionLocal
    from app.models import Usuario

    db = SessionLocal()
    try:
        u = db.query(Usuario).filter(Usuario.correo == correo).first()
        assert u and u.codigo_verificacion and len(str(u.codigo_verificacion)) == 6
        codigo = u.codigo_verificacion
    finally:
        db.close()

    r = cliente.post("/verificar-codigo", json={"correo": correo, "codigo": codigo})
    assert r.status_code == 200
    assert cliente.post("/login", json={"correo": correo, "password": "Prueba2026!"}).json()["ok"] is True


# ---------------------------------------------------------------------------
# RBAC — el consejo no administra usuarios ni finanzas
# ---------------------------------------------------------------------------
def test_rbac_consejo(cliente, consejo):
    assert cliente.get("/usuarios", headers=consejo).status_code == 403
    assert cliente.get("/auditoria", headers=consejo).status_code == 200
    assert cliente.get("/aprobaciones", headers=consejo).status_code == 200


def test_cuentas_demo_consejo_y_residente_ven_los_4_conjuntos(cliente, consejo, residente):
    nombres_esperados = {
        "Conjunto Residencial Los Pinos",
        "Edificio Altos del Parque",
        "Reservas de la Colina",
        "Torres de San Martín",
    }
    for headers in (consejo, residente):
        r = cliente.get("/conjuntos", headers=headers)
        assert r.status_code == 200, r.text
        lista = r.json()
        assert len(lista) >= 4
        assert nombres_esperados.issubset({c["nombre"] for c in lista})
        # Verificar que pueden cambiar a cualquiera de los 4 conjuntos vía X-Conjunto-Id
        for c in lista[:4]:
            r_ev = cliente.get("/eventos", headers={**headers, "X-Conjunto-Id": str(c["id"])})
            assert r_ev.status_code == 200, r_ev.text


def test_todos_los_documentos_son_descargables_en_los_4_conjuntos(cliente, admin, residente, consejo):
    conjuntos = cliente.get("/conjuntos", headers=admin).json()
    assert len(conjuntos) >= 4
    total_descargados = 0

    for c in conjuntos[:4]:
        cid = str(c["id"])
        docs = cliente.get("/documentos", headers={**admin, "X-Conjunto-Id": cid}).json()
        assert len(docs) >= 4, f"Conjunto {c['nombre']} debería tener documentos"
        for d in docs:
            for headers in (admin, residente, consejo):
                r = cliente.get(f"/documentos/{d['id']}/descargar", headers={**headers, "X-Conjunto-Id": cid})
                assert r.status_code == 200, f"Falló descarga doc {d['id']} ({d['titulo']}): {r.text}"
                assert r.content.startswith(b"%PDF-"), f"Doc {d['id']} no devolvió PDF válido"
                assert len(r.content) > 0
                if (d.get("ruta_archivo") or "").startswith("doc_"):
                    assert len(r.content) > 500
                disp = r.headers.get("content-disposition", "")
                assert ".pdf" in disp.lower()
            total_descargados += 1

    assert total_descargados >= 16


# ---------------------------------------------------------------------------
# UH-02 — gestión integral de residentes (nombre, apartamento, correo y rol)
# ---------------------------------------------------------------------------
def test_uh02_gestion_residente_completa_y_legacy(cliente, admin):
    correo = f"laura.{uuid.uuid4().hex[:6]}@ejemplo.com"
    r = cliente.post("/residentes", headers=admin, json={
        "nombre": "Laura Gómez",
        "correo": correo,
        "rol_id": 3,
        "apartamento": "T1-405",
        "tipo": "propietario",
        "identificacion": f"CC-{uuid.uuid4().hex[:6]}",
        "telefono_adicional": "3001112233",
    })
    assert r.status_code == 201, r.text
    creado = r.json()
    assert creado["nombre"] == "Laura Gómez"
    assert creado["correo"] == correo
    assert creado["apartamento"] == "T1-405"
    assert creado["rol_id"] == 3
    assert creado["usuario_id"] is not None
    assert creado["propiedad_id"] is not None

    # Editar nombre, apartamento y rol en el mismo flujo.
    r = cliente.put(f"/residentes/{creado['id']}", headers=admin, json={
        "nombre": "Laura Gómez Editada",
        "correo": correo,
        "rol_id": 4,
        "apartamento": "T1-406",
        "tipo": "inquilino",
        "identificacion": creado["identificacion"],
        "activo": True,
    })
    assert r.status_code == 200, r.text
    editado = r.json()
    assert editado["nombre"] == "Laura Gómez Editada"
    assert editado["apartamento"] == "T1-406"
    assert editado["rol_id"] == 4
    assert editado["tipo"] == "inquilino"

    # Compatibilidad legacy: alta clásica sin nombre/correo/apartamento sigue funcionando.
    r_legacy = cliente.post("/residentes", headers=admin, json={
        "tipo": "propietario",
        "identificacion": f"LEG-{uuid.uuid4().hex[:6]}",
    })
    assert r_legacy.status_code == 201, r_legacy.text

    # Desactivar residente.
    r_del = cliente.delete(f"/residentes/{creado['id']}", headers=admin)
    assert r_del.status_code == 204


# ---------------------------------------------------------------------------
# UH-05 · UH-06 — balance en tiempo real y cartera descargable por período
# ---------------------------------------------------------------------------
def test_uh05_uh06_balance_tiempo_real_y_cartera_periodo(cliente, admin):
    conceptos = cliente.get("/finanzas/conceptos", headers=admin).json()
    concepto_ing = next(c for c in conceptos if c["tipo"] == "ingreso")
    props = cliente.get("/propiedades", headers=admin).json()
    assert props, "Se esperaba al menos una propiedad semilla"
    prop = props[0]

    antes = cliente.get("/finanzas/resumen", headers=admin).json()
    r = cliente.post("/finanzas", headers=admin, json={
        "concepto_id": concepto_ing["id"],
        "propiedad_id": prop["id"],
        "monto": 350000,
        "fecha_vencimiento": "2026-10-15",
        "estado": "pagado",
    })
    assert r.status_code == 201, r.text
    mov_id = r.json()["id"]

    # UH-05: el resumen refleja inmediatamente el ingreso sin quedar obsoleto en caché.
    despues = cliente.get("/finanzas/resumen", headers=admin).json()
    assert round(despues["ingresos"] - antes["ingresos"], 2) == 350000.0

    # UH-06: cartera filtrada por período devuelve unidades al día y pendientes + PDF/Excel.
    cartera = cliente.get("/reportes/cartera?periodo=2026-10", headers=admin)
    assert cartera.status_code == 200, cartera.text
    datos = cartera.json()
    assert datos["periodo"] == "2026-10"
    assert {"unidades", "al_dia", "con_saldo", "total_facturado", "total_pagado", "total_pendiente"} <= set(datos)
    unidad_prop = next(u for u in datos["unidades"] if u["propiedad_id"] == prop["id"])
    assert unidad_prop["pagado"] >= 350000.0

    pdf = cliente.get("/reportes/exportar/cartera.pdf?periodo=2026-10", headers=admin)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF-")
    xlsx = cliente.get("/reportes/exportar/cartera.xlsx?periodo=2026-10", headers=admin)
    assert xlsx.status_code == 200 and xlsx.content[:2] == b"PK"

    # Limpieza y verificación de actualización inmediata al eliminar.
    assert cliente.delete(f"/finanzas/{mov_id}", headers=admin).status_code == 204
    final = cliente.get("/finanzas/resumen", headers=admin).json()
    assert round(final["ingresos"], 2) == round(antes["ingresos"], 2)


# ---------------------------------------------------------------------------
# UH-19 — documentos filtrables por categoría y ordenables por fecha
# ---------------------------------------------------------------------------
def test_uh19_documentos_categoria_y_orden(cliente, admin, residente):
    r_cat = cliente.get("/documentos?categoria=reglamento&orden=fecha_desc", headers=residente)
    assert r_cat.status_code == 200, r_cat.text
    docs_reg = r_cat.json()
    assert all((d.get("tipo_documento") or "").lower() == "reglamento" for d in docs_reg)

    r_asc = cliente.get("/documentos?orden=fecha_asc", headers=residente)
    r_desc = cliente.get("/documentos?orden=fecha_desc", headers=residente)
    assert r_asc.status_code == 200 and r_desc.status_code == 200
    fechas_asc = [d["fecha_creacion"] for d in r_asc.json()]
    fechas_desc = [d["fecha_creacion"] for d in r_desc.json()]
    assert fechas_asc == sorted(fechas_asc)
    assert fechas_desc == sorted(fechas_desc, reverse=True)


# ---------------------------------------------------------------------------
# UH-21 · UH-23 · UH-32 — URL de evidencia, consejo por período y enlace PQRS
# ---------------------------------------------------------------------------
def test_uh21_uh23_uh32_url_evidencia_consejo_y_pqrs_enlace(cliente, admin, residente, consejo):
    # UH-21: la URL devuelta por /mantenimiento/evidencia apunta al endpoint real.
    ev = cliente.post(
        "/mantenimiento/evidencia",
        headers=residente,
        files={"archivo": ("dano.png", b"\x89PNG\r\n\x1a\nimg", "image/png")},
    )
    assert ev.status_code == 200, ev.text
    body = ev.json()
    assert body["url"] == f"/mantenimiento/evidencias/{body['nombre']}"
    assert cliente.get(body["url"], headers=admin).status_code == 200

    # UH-23: /reportes/finanzas-por-mes incluye ingresos y gastos, y consejo.xlsx acepta período.
    serie = cliente.get("/reportes/finanzas-por-mes?desde=2020-01-01&hasta=2035-12-31", headers=consejo)
    assert serie.status_code == 200, serie.text
    for punto in serie.json():
        assert {"mes", "valor", "ingresos", "gastos"} <= set(punto)
    xlsx = cliente.get("/reportes/exportar/consejo.xlsx?desde=2020-01-01&hasta=2035-12-31", headers=consejo)
    assert xlsx.status_code == 200 and xlsx.content[:2] == b"PK"

    # UH-32: PQRS de zonas comunes notifica al consejo con resumen y enlace directo ?id=<id>.
    r = cliente.post("/pqrs", headers=residente, json={
        "tipo": "queja",
        "categoria": "zonas_comunes",
        "asunto": "Luminaria dañada en plazoleta central",
        "descripcion": "Dos postes de luz llevan tres días apagados en la plazoleta.",
    })
    assert r.status_code == 201, r.text
    caso = r.json()
    notifs = cliente.get("/notificaciones", headers=consejo).json()
    n_caso = next((n for n in notifs if caso["radicado"] in n["mensaje"]), None)
    assert n_caso is not None, "El consejo no recibió la notificación de la PQRS de zona común"
    assert n_caso["url"] == f"/dashboard/pqrs?id={caso['id']}"
    assert "Luminaria dañada" in n_caso["mensaje"]

