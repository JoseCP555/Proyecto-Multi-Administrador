"""Utilidades de exportación de reportes a Excel (.xlsx) y PDF.

Se usan openpyxl (Excel real) y reportlab (PDF), ambos en requirements.txt.
"""
import calendar
from datetime import date
from io import BytesIO
from xml.sax.saxutils import escape as xml_escape

from sqlalchemy.orm import Session
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle

from app import models


def resolver_rango_periodo(
    desde: date | None = None,
    hasta: date | None = None,
    periodo: str | None = None,
) -> tuple[date | None, date | None, str]:
    """Normaliza un período (`YYYY-MM` o rango `desde`/`hasta`) en fechas y etiqueta legible."""
    if periodo and not desde and not hasta:
        limpio = periodo.strip()
        partes = limpio.split("-")
        if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
            y, m = int(partes[0]), int(partes[1])
            if 1 <= m <= 12:
                ultimo = calendar.monthrange(y, m)[1]
                desde = date(y, m, 1)
                hasta = date(y, m, ultimo)
                return desde, hasta, limpio
    if desde and hasta:
        return desde, hasta, f"{desde.strftime('%d/%m/%Y')} al {hasta.strftime('%d/%m/%Y')}"
    if desde:
        return desde, None, f"Desde {desde.strftime('%d/%m/%Y')}"
    if hasta:
        return None, hasta, f"Hasta {hasta.strftime('%d/%m/%Y')}"
    return None, None, "Histórico completo"


def calcular_cartera(
    db: Session,
    id_conjunto: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    periodo: str | None = None,
) -> dict:
    """Calcula el estado de pago (al día / pendiente / en mora) de cada unidad (UH-06)."""
    f_desde, f_hasta, etiqueta = resolver_rango_periodo(desde, hasta, periodo)
    hoy = date.today()
    concepto = {c.id: c for c in db.query(models.ConceptoFinanciero).all()}
    residentes = {r.id: r for r in db.query(models.Residente).all()}
    usuarios = {u.id: u.nombre for u in db.query(models.Usuario).all()}

    filas: dict[int, dict] = {}
    for prop in _por_conjunto(db.query(models.Propiedad), models.Propiedad, id_conjunto).all():
        res = residentes.get(prop.residente_id) if prop.residente_id else None
        res_nombre = None
        if res:
            res_nombre = usuarios.get(res.usuario_id) if res.usuario_id else res.identificacion
        filas[prop.id] = {
            "propiedad_id": prop.id,
            "apartamento": prop.apartamento,
            "torre": prop.torre,
            "bloque": prop.bloque,
            "residente_id": prop.residente_id,
            "residente_nombre": res_nombre or "Sin asignar",
            "facturado": 0.0,
            "pagado": 0.0,
            "pendiente": 0.0,
            "vencido": 0.0,
            "estado_pago": "al_dia",
        }

    consulta = _por_conjunto(db.query(models.MovimientoFinanciero), models.MovimientoFinanciero, id_conjunto)
    if f_desde:
        consulta = consulta.filter(models.MovimientoFinanciero.fecha_vencimiento >= f_desde)
    if f_hasta:
        consulta = consulta.filter(models.MovimientoFinanciero.fecha_vencimiento <= f_hasta)

    for m in consulta.all():
        if not m.propiedad_id or m.propiedad_id not in filas:
            continue
        c = concepto.get(m.concepto_id)
        if c and c.tipo != "ingreso":
            continue
        monto = float(m.monto or 0)
        fila = filas[m.propiedad_id]
        fila["facturado"] += monto
        if m.estado == "pagado":
            fila["pagado"] += monto
        elif m.estado in ("pendiente", "vencido"):
            fila["pendiente"] += monto
            if m.estado == "vencido" or (m.fecha_vencimiento and m.fecha_vencimiento < hoy):
                fila["vencido"] += monto

    for fila in filas.values():
        fila["facturado"] = round(fila["facturado"], 2)
        fila["pagado"] = round(fila["pagado"], 2)
        fila["pendiente"] = round(fila["pendiente"], 2)
        fila["vencido"] = round(fila["vencido"], 2)
        if fila["pendiente"] <= 0:
            fila["estado_pago"] = "al_dia"
        elif fila["vencido"] > 0:
            fila["estado_pago"] = "en_mora"
        else:
            fila["estado_pago"] = "pendiente"

    unidades = sorted(filas.values(), key=lambda f: str(f["apartamento"]))
    return {
        "periodo": etiqueta,
        "desde": f_desde.isoformat() if f_desde else None,
        "hasta": f_hasta.isoformat() if f_hasta else None,
        "unidades": unidades,
        "al_dia": sum(1 for u in unidades if u["estado_pago"] == "al_dia"),
        "con_saldo": sum(1 for u in unidades if u["estado_pago"] != "al_dia"),
        "total_facturado": round(sum(u["facturado"] for u in unidades), 2),
        "total_pagado": round(sum(u["pagado"] for u in unidades), 2),
        "total_pendiente": round(sum(u["pendiente"] for u in unidades), 2),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _money(v) -> str:
    return f"${float(v or 0):,.0f}".replace(",", ".")


def _encabezado(ws, titulo):
    """Estilo para títulos de columna."""
    header_fill = PatternFill("solid", fgColor="1a2332")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
    ws.freeze_panes = "A2"


def _autoancho(ws, limites):
    for col, ancho in enumerate(limites, start=1):
        ws.column_dimensions[get_column_letter(col)].width = ancho


def _respuesta_xlsx(nombre: str, wb: Workbook) -> bytes:
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


def _por_conjunto(consulta, modelo, id_conjunto):
    """Filtra por conjunto si el modelo tiene la columna (multi-copropiedad)."""
    if id_conjunto is None:
        return consulta
    columna = getattr(modelo, "id_conjunto", None)
    return consulta.filter(columna == id_conjunto) if columna is not None else consulta


# ---------------------------------------------------------------------------
# Finanzas -> Excel
# ---------------------------------------------------------------------------
def finanzas_xlsx(db: Session, id_conjunto: int = None) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Movimientos"
    ws.append(["Fecha", "Concepto", "Tipo", "Propiedad", "Monto", "Estado", "Recibo"])
    _encabezado(ws, [])
    _autoancho(ws, [12, 24, 10, 16, 14, 12, 16])

    concepto = {c.id: c for c in db.query(models.ConceptoFinanciero).all()}
    movs = (
        _por_conjunto(db.query(models.MovimientoFinanciero), models.MovimientoFinanciero, id_conjunto)
        .order_by(models.MovimientoFinanciero.fecha_vencimiento)
        .all()
    )
    for m in movs:
        c = concepto.get(m.concepto_id)
        ws.append([
            m.fecha_vencimiento.strftime("%d/%m/%Y") if m.fecha_vencimiento else "",
            c.nombre if c else "",
            c.tipo if c else "",
            (m.propiedad_id or ""),
            float(m.monto),
            m.estado,
            m.numero_recibo or "",
        ])
    return _respuesta_xlsx("finanzas", wb)


# ---------------------------------------------------------------------------
# Pagos / mora -> Excel
# ---------------------------------------------------------------------------
def pagos_xlsx(
    db: Session,
    id_conjunto: int = None,
    desde: date | None = None,
    hasta: date | None = None,
    periodo: str | None = None,
) -> bytes:
    f_desde, f_hasta, _ = resolver_rango_periodo(desde, hasta, periodo)
    wb = Workbook()
    ws = wb.active
    ws.title = "Pagos"
    ws.append(["Concepto", "Unidad", "Vencimiento", "Monto", "Estado", "Número"])
    _encabezado(ws, [])
    _autoancho(ws, [24, 16, 12, 14, 12, 16])

    concepto = {c.id: c for c in db.query(models.ConceptoFinanciero).all()}
    props = {p.id: p.apartamento for p in db.query(models.Propiedad).all()}
    consulta = _por_conjunto(db.query(models.MovimientoFinanciero).filter(
        models.MovimientoFinanciero.estado.in_(["pendiente", "vencido"])
    ), models.MovimientoFinanciero, id_conjunto)
    if f_desde:
        consulta = consulta.filter(models.MovimientoFinanciero.fecha_vencimiento >= f_desde)
    if f_hasta:
        consulta = consulta.filter(models.MovimientoFinanciero.fecha_vencimiento <= f_hasta)
    movs = consulta.order_by(models.MovimientoFinanciero.fecha_vencimiento).all()
    for m in movs:
        c = concepto.get(m.concepto_id)
        ws.append([
            c.nombre if c else "",
            props.get(m.propiedad_id, m.propiedad_id or "General"),
            m.fecha_vencimiento.strftime("%d/%m/%Y") if m.fecha_vencimiento else "",
            float(m.monto),
            m.estado,
            m.numero_recibo or "",
        ])
    total = sum(float(m.monto) for m in movs)
    ws.append([])
    ws.append(["TOTAL EN MORA", "", "", round(total, 2), "", ""])
    ws["A" + str(ws.max_row)].font = Font(bold=True)
    return _respuesta_xlsx("pagos", wb)


# ---------------------------------------------------------------------------
# Mantenimiento -> Excel
# ---------------------------------------------------------------------------
def mantenimiento_xlsx(db: Session, id_conjunto: int = None) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Mantenimiento"
    ws.append(["Título", "Descripción", "Prioridad", "Estado", "F. programada", "Costo estimado"])
    _encabezado(ws, [])
    _autoancho(ws, [24, 30, 10, 12, 14, 14])

    tareas = _por_conjunto(db.query(models.TareaMantenimiento), models.TareaMantenimiento, id_conjunto).order_by(models.TareaMantenimiento.fecha_creacion).all()
    for t in tareas:
        ws.append([
            t.titulo,
            t.descripcion,
            t.prioridad,
            t.estado,
            t.fecha_programada.strftime("%d/%m/%Y") if t.fecha_programada else "",
            float(t.costo_estimado or 0),
        ])
    return _respuesta_xlsx("mantenimiento", wb)


# ---------------------------------------------------------------------------
# PDF: resumen financiero por mes (reporte ejecutivo)
# ---------------------------------------------------------------------------
def reporte_finanzas_pdf(db: Session, id_conjunto: int = None) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
    )
    estilos = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=estilos["Title"], fontSize=16, textColor=colors.HexColor("#1a2332"))
    h2 = ParagraphStyle("h2", parent=estilos["Heading2"], fontSize=11, textColor=colors.HexColor("#3b82f6"))
    normal = ParagraphStyle("normal", parent=estilos["Normal"], fontSize=9)

    concepto = {c.id: c for c in db.query(models.ConceptoFinanciero).all()}
    movs = _por_conjunto(db.query(models.MovimientoFinanciero).filter(
        models.MovimientoFinanciero.estado == "pagado"
    ), models.MovimientoFinanciero, id_conjunto).order_by(
        models.MovimientoFinanciero.fecha_vencimiento).all()

    # Agregar por mes (ingresos/gastos)
    por_mes = {}
    for m in movs:
        c = concepto.get(m.concepto_id)
        tipo = c.tipo if c else "gasto"
        clave = m.fecha_vencimiento.strftime("%Y-%m")
        d = por_mes.setdefault(clave, {"ingresos": 0.0, "gastos": 0.0})
        key = "ingresos" if tipo == "ingreso" else "gastos"
        d[key] += float(m.monto)

    filas = [["Mes", "Ingresos", "Gastos"]]
    for clave in sorted(por_mes.keys())[-6:]:
        año, mes = clave.split("-")
        import calendar
        d = por_mes[clave]
        filas.append([f"{calendar.month_name[int(mes)]} {año}", _money(d["ingresos"]), _money(d["gastos"])])

    t_in = 0.0
    t_ga = 0.0
    for m in movs:
        c = concepto.get(m.concepto_id)
        if c and c.tipo == "ingreso":
            t_in += float(m.monto)
        else:
            t_ga += float(m.monto)

    tabla = Table(filas, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2332")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d9d9d9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
    ]))

    story = [
        Paragraph("Multi-Administrador", h1),
        Paragraph(f"Reporte ejecutivo de finanzas — generado el {date.today().strftime('%d/%m/%Y')}", h2),
        Paragraph("Ingresos y gastos consolidados de los últimos meses.", normal),
        Paragraph("", normal),
        tabla,
        Paragraph("", normal),
        Paragraph(f"Total ingresos: <b>{_money(t_in)}</b>", normal),
        Paragraph(f"Total gastos: <b>{_money(t_ga)}</b>", normal),
        Paragraph(f"<b>Saldo: {_money(t_in - t_ga)}</b>", normal),
    ]
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


def pagos_pdf(
    db: Session,
    id_conjunto: int = None,
    desde: date | None = None,
    hasta: date | None = None,
    periodo: str | None = None,
) -> bytes:
    f_desde, f_hasta, etiqueta = resolver_rango_periodo(desde, hasta, periodo)
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm)
    estilos = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=estilos["Title"], fontSize=16, textColor=colors.HexColor("#1a2332"))
    h2 = ParagraphStyle("h2", parent=estilos["Heading2"], fontSize=11, textColor=colors.HexColor("#3b82f6"))
    normal = ParagraphStyle("normal", parent=estilos["Normal"], fontSize=9)

    concepto = {c.id: c for c in db.query(models.ConceptoFinanciero).all()}
    props = {p.id: p.apartamento for p in db.query(models.Propiedad).all()}
    consulta = _por_conjunto(db.query(models.MovimientoFinanciero).filter(
        models.MovimientoFinanciero.estado.in_(["pendiente", "vencido"])
    ), models.MovimientoFinanciero, id_conjunto)
    if f_desde:
        consulta = consulta.filter(models.MovimientoFinanciero.fecha_vencimiento >= f_desde)
    if f_hasta:
        consulta = consulta.filter(models.MovimientoFinanciero.fecha_vencimiento <= f_hasta)
    movs = consulta.order_by(models.MovimientoFinanciero.fecha_vencimiento).all()

    filas = [["Unidad", "Concepto", "Vencimiento", "Monto", "Estado"]]
    for m in movs:
        c = concepto.get(m.concepto_id)
        filas.append([
            str(props.get(m.propiedad_id, "General")),
            c.nombre if c else "",
            m.fecha_vencimiento.strftime("%d/%m/%Y") if m.fecha_vencimiento else "",
            _money(m.monto),
            m.estado,
        ])
    total = sum(float(m.monto) for m in movs)
    filas.append(["TOTAL EN MORA", "", "", _money(total), ""])

    tabla = Table(filas, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2332")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d9d9d9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff4e5")]),
    ]))

    story = [
        Paragraph("Multi-Administrador", h1),
        Paragraph("Reporte de pagos en mora / pendientes", h2),
        Paragraph(f"Período: {xml_escape(etiqueta)} — generado el {date.today().strftime('%d/%m/%Y')}", normal),
        Paragraph("", normal),
        tabla,
    ]
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Cartera por unidad (pagos pendientes y al día) -> PDF y Excel (UH-06)
# ---------------------------------------------------------------------------
_ETIQUETA_ESTADO_CARTERA = {
    "al_dia": "Al día",
    "pendiente": "Pendiente",
    "en_mora": "En mora",
}


def cartera_pdf(
    db: Session,
    id_conjunto: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    periodo: str | None = None,
) -> bytes:
    """Listado descargable en PDF con el estado de pago (pendientes y al día) de cada unidad (UH-06)."""
    datos = calcular_cartera(db, id_conjunto, desde, hasta, periodo)
    conjunto = db.query(models.Conjunto).get(id_conjunto) if id_conjunto else None

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
    )
    estilos = getSampleStyleSheet()
    h1 = ParagraphStyle("c_h1", parent=estilos["Title"], fontSize=16, textColor=colors.HexColor("#1a2332"))
    h2 = ParagraphStyle("c_h2", parent=estilos["Heading2"], fontSize=11, textColor=colors.HexColor("#3b82f6"))
    normal = ParagraphStyle("c_norm", parent=estilos["Normal"], fontSize=9)

    filas = [["Unidad", "Torre/Bloque", "Residente", "Facturado", "Pagado", "Pendiente", "Estado"]]
    for u in datos["unidades"]:
        ubic = " / ".join(x for x in (u.get("torre"), u.get("bloque")) if x) or "—"
        filas.append([
            str(u["apartamento"]),
            ubic,
            str(u.get("residente_nombre") or "—")[:26],
            _money(u["facturado"]),
            _money(u["pagado"]),
            _money(u["pendiente"]),
            _ETIQUETA_ESTADO_CARTERA.get(u["estado_pago"], u["estado_pago"]),
        ])
    if len(filas) == 1:
        filas.append(["Sin unidades registradas", "", "", "", "", "", ""])
    else:
        filas.append([
            "TOTAL",
            f"{len(datos['unidades'])} unid.",
            f"{datos['al_dia']} al día · {datos['con_saldo']} con saldo",
            _money(datos["total_facturado"]),
            _money(datos["total_pagado"]),
            _money(datos["total_pendiente"]),
            "",
        ])

    tabla = Table(filas, repeatRows=1, colWidths=[22 * mm, 24 * mm, 42 * mm, 24 * mm, 24 * mm, 24 * mm, 20 * mm])
    estilo_tabla = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2332")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (3, 0), (5, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d9d9d9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f5f7fa")]),
    ]
    if len(filas) > 2:
        estilo_tabla.extend([
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ])
    tabla.setStyle(TableStyle(estilo_tabla))

    titulo_conj = conjunto.nombre if conjunto else "Multi-Administrador"
    story = [
        Paragraph(xml_escape(titulo_conj), h1),
        Paragraph("Reporte de pagos pendientes y al día por unidad", h2),
        Paragraph(
            f"Período: <b>{xml_escape(datos['periodo'])}</b> · Generado el {date.today().strftime('%d/%m/%Y')}",
            normal,
        ),
        Paragraph(
            f"Unidades al día: <b>{datos['al_dia']}</b> · Con saldo pendiente/mora: <b>{datos['con_saldo']}</b> · "
            f"Total pendiente: <b>{_money(datos['total_pendiente'])}</b>",
            normal,
        ),
        Paragraph("", normal),
        tabla,
    ]
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


def cartera_xlsx(
    db: Session,
    id_conjunto: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    periodo: str | None = None,
) -> bytes:
    """Listado descargable en Excel con el estado de pago (pendientes y al día) de cada unidad (UH-06)."""
    datos = calcular_cartera(db, id_conjunto, desde, hasta, periodo)
    wb = Workbook()
    ws = wb.active
    ws.title = "Cartera por unidad"
    ws.append(["Unidad", "Torre", "Bloque", "Residente", "Facturado", "Pagado", "Pendiente", "Estado", "Período"])
    _encabezado(ws, [])
    _autoancho(ws, [14, 12, 12, 26, 15, 15, 15, 14, 22])

    for u in datos["unidades"]:
        ws.append([
            u["apartamento"],
            u.get("torre") or "",
            u.get("bloque") or "",
            u.get("residente_nombre") or "",
            float(u["facturado"]),
            float(u["pagado"]),
            float(u["pendiente"]),
            _ETIQUETA_ESTADO_CARTERA.get(u["estado_pago"], u["estado_pago"]),
            datos["periodo"],
        ])
    ws.append([])
    ws.append([
        "TOTAL",
        "",
        "",
        f"{datos['al_dia']} al día / {datos['con_saldo']} con saldo",
        float(datos["total_facturado"]),
        float(datos["total_pagado"]),
        float(datos["total_pendiente"]),
        "",
        datos["periodo"],
    ])
    for col in range(1, 10):
        ws.cell(row=ws.max_row, column=col).font = Font(bold=True)
    return _respuesta_xlsx("cartera_unidades", wb)


# ---------------------------------------------------------------------------
# PQRS -> Excel (UH-09)
# ---------------------------------------------------------------------------
def pqrs_xlsx(db: Session, id_conjunto: int = None) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "PQRS"
    ws.append(["Radicado", "Fecha", "Tipo", "Categoría", "Asunto", "Estado", "Solicitante", "Respuesta"])
    _encabezado(ws, [])
    _autoancho(ws, [24, 12, 12, 16, 34, 12, 22, 40])

    filas = _por_conjunto(db.query(models.Pqrs), models.Pqrs, id_conjunto).order_by(
        models.Pqrs.fecha_creacion.desc()).all()
    for p in filas:
        u = db.query(models.Usuario).get(p.usuario_id) if p.usuario_id else None
        ws.append([
            p.radicado,
            p.fecha_creacion.strftime("%d/%m/%Y") if p.fecha_creacion else "",
            p.tipo,
            p.categoria,
            p.asunto,
            p.estado,
            u.nombre if u else "",
            p.respuesta or "",
        ])
    return _respuesta_xlsx("pqrs", wb)


# ---------------------------------------------------------------------------
# Reservas -> Excel (UH-10)
# ---------------------------------------------------------------------------
def reservas_xlsx(db: Session, id_conjunto: int = None) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Reservas"
    ws.append(["Zona", "Fecha", "Inicio", "Fin", "Solicitante", "Asistentes", "Estado", "Motivo"])
    _encabezado(ws, [])
    _autoancho(ws, [24, 12, 10, 10, 22, 12, 12, 30])

    filas = _por_conjunto(db.query(models.ReservaZona), models.ReservaZona, id_conjunto).order_by(
        models.ReservaZona.fecha.desc()).all()
    for r in filas:
        zona = db.query(models.ZonaComun).get(r.zona_id)
        u = db.query(models.Usuario).get(r.usuario_id) if r.usuario_id else None
        ws.append([
            zona.nombre if zona else "",
            r.fecha.strftime("%d/%m/%Y") if r.fecha else "",
            r.hora_inicio, r.hora_fin,
            u.nombre if u else "",
            r.asistentes or 0,
            r.estado,
            r.motivo or "",
        ])
    return _respuesta_xlsx("reservas", wb)


# ---------------------------------------------------------------------------
# Visitantes -> Excel (UH-12)
# ---------------------------------------------------------------------------
def visitantes_xlsx(db: Session, id_conjunto: int = None, desde=None, hasta=None) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Visitantes"
    ws.append(["Nombre", "Documento", "Teléfono", "Apartamento", "Motivo", "Ingreso", "Salida", "Estado"])
    _encabezado(ws, [])
    _autoancho(ws, [26, 16, 14, 14, 26, 20, 20, 10])

    consulta = _por_conjunto(db.query(models.Visitante), models.Visitante, id_conjunto)
    if desde:
        consulta = consulta.filter(models.Visitante.hora_ingreso >= desde)
    if hasta:
        consulta = consulta.filter(models.Visitante.hora_ingreso <= hasta)
    for v in consulta.order_by(models.Visitante.hora_ingreso.desc()).all():
        ws.append([
            v.nombre, v.documento, v.telefono or "", v.apartamento, v.motivo or "",
            v.hora_ingreso.strftime("%d/%m/%Y %H:%M") if v.hora_ingreso else "",
            v.hora_salida.strftime("%d/%m/%Y %H:%M") if v.hora_salida else "",
            v.estado,
        ])
    return _respuesta_xlsx("visitantes", wb)


# ---------------------------------------------------------------------------
# Comprobantes de pago -> Excel (UH-13)
# ---------------------------------------------------------------------------
def comprobantes_xlsx(db: Session, id_conjunto: int = None) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Comprobantes"
    ws.append(["Fecha", "Residente", "Periodo", "Monto", "Estado", "Observación"])
    _encabezado(ws, [])
    _autoancho(ws, [16, 26, 12, 16, 14, 34])

    filas = _por_conjunto(db.query(models.ComprobantePago), models.ComprobantePago, id_conjunto).order_by(
        models.ComprobantePago.fecha_creacion.desc()).all()
    for c in filas:
        u = db.query(models.Usuario).get(c.usuario_id)
        ws.append([
            c.fecha_creacion.strftime("%d/%m/%Y") if c.fecha_creacion else "",
            u.nombre if u else "",
            c.periodo or "",
            float(c.monto or 0),
            c.estado,
            c.observacion or "",
        ])
    return _respuesta_xlsx("comprobantes", wb)


# ---------------------------------------------------------------------------
# Auditoría -> Excel (UH-29)
# ---------------------------------------------------------------------------
def auditoria_xlsx(db: Session, id_conjunto: int = None) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Auditoría"
    ws.append(["Fecha y hora", "Usuario", "Acción", "Módulo", "Detalle", "IP", "HTTP"])
    _encabezado(ws, [])
    _autoancho(ws, [20, 24, 12, 22, 50, 16, 8])

    filas = _por_conjunto(db.query(models.Auditoria), models.Auditoria, id_conjunto).order_by(
        models.Auditoria.fecha_creacion.desc()).limit(5000).all()
    for a in filas:
        ws.append([
            a.fecha_creacion.strftime("%d/%m/%Y %H:%M:%S") if a.fecha_creacion else "",
            a.usuario_nombre or "Sistema",
            a.accion,
            a.modulo,
            a.detalle or "",
            a.ip or "",
            a.estado_http or "",
        ])
    return _respuesta_xlsx("auditoria", wb)


# ---------------------------------------------------------------------------
# Estado de cuenta del residente -> PDF (UH-17)
# ---------------------------------------------------------------------------
def estado_cuenta_pdf(datos: dict) -> bytes:
    """Genera el PDF del estado de cuenta a partir del dict de `_estado_cuenta`."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm)
    estilos = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=estilos["Title"], fontSize=16, textColor=colors.HexColor("#1a2332"))
    h2 = ParagraphStyle("h2", parent=estilos["Heading2"], fontSize=11, textColor=colors.HexColor("#3b82f6"))
    normal = ParagraphStyle("normal", parent=estilos["Normal"], fontSize=9)

    usuario = datos.get("usuario", {})
    unidades = ", ".join(u.get("apartamento") or "—" for u in datos.get("unidades", [])) or "—"

    filas = [["Concepto", "Unidad", "Vencimiento", "Monto", "Estado"]]
    for m in datos.get("movimientos", []):
        filas.append([
            m.get("concepto", ""),
            m.get("propiedad") or "—",
            m["fecha_vencimiento"].strftime("%d/%m/%Y") if m.get("fecha_vencimiento") else "",
            _money(m.get("monto", 0)),
            m.get("estado", ""),
        ])
    if len(filas) == 1:
        filas.append(["Sin movimientos registrados", "", "", "", ""])

    tabla = Table(filas, repeatRows=1, colWidths=[70 * mm, 25 * mm, 30 * mm, 30 * mm, 25 * mm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2332")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d9d9d9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
    ]))

    story = [
        Paragraph("Multi-Administrador", h1),
        Paragraph("Estado de cuenta del residente", h2),
        Paragraph(f"<b>{usuario.get('nombre', '')}</b> · {usuario.get('correo', '')}", normal),
        Paragraph(f"Unidad(es): {unidades}", normal),
        Paragraph(f"Generado el {date.today().strftime('%d/%m/%Y')}", normal),
        Paragraph("", normal),
        tabla,
        Paragraph("", normal),
        Paragraph(f"Total facturado: <b>{_money(datos.get('total_facturado', 0))}</b>", normal),
        Paragraph(f"Total pagado: <b>{_money(datos.get('total_pagado', 0))}</b>", normal),
        Paragraph(f"<b>Saldo pendiente: {_money(datos.get('saldo', 0))}</b>", normal),
    ]
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Reporte financiero del consejo con gráficas -> PDF (UH-23)
# ---------------------------------------------------------------------------
def reporte_consejo_pdf(db: Session, id_conjunto: int = None, desde=None, hasta=None) -> bytes:
    """Ingresos y egresos por periodo con una gráfica de barras resumen."""
    from reportlab.graphics.shapes import Drawing, Rect, String

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm)
    estilos = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=estilos["Title"], fontSize=16, textColor=colors.HexColor("#1a2332"))
    h2 = ParagraphStyle("h2", parent=estilos["Heading2"], fontSize=11, textColor=colors.HexColor("#3b82f6"))
    normal = ParagraphStyle("normal", parent=estilos["Normal"], fontSize=9)

    concepto = {c.id: c for c in db.query(models.ConceptoFinanciero).all()}
    consulta = _por_conjunto(db.query(models.MovimientoFinanciero).filter(
        models.MovimientoFinanciero.estado == "pagado"
    ), models.MovimientoFinanciero, id_conjunto)
    if desde:
        consulta = consulta.filter(models.MovimientoFinanciero.fecha_vencimiento >= desde)
    if hasta:
        consulta = consulta.filter(models.MovimientoFinanciero.fecha_vencimiento <= hasta)

    ingresos = gastos = 0.0
    por_mes: dict[str, dict] = {}
    for m in consulta.all():
        c = concepto.get(m.concepto_id)
        tipo = c.tipo if c else "gasto"
        d = por_mes.setdefault(m.fecha_vencimiento.strftime("%Y-%m"), {"i": 0.0, "g": 0.0})
        if tipo == "ingreso":
            d["i"] += float(m.monto)
            ingresos += float(m.monto)
        else:
            d["g"] += float(m.monto)
            gastos += float(m.monto)

    filas = [["Mes", "Ingresos", "Egresos", "Balance"]]
    for clave in sorted(por_mes.keys())[-12:]:
        d = por_mes[clave]
        año, mes = clave.split("-")
        import calendar
        filas.append([f"{calendar.month_name[int(mes)]} {año}", _money(d["i"]), _money(d["g"]), _money(d["i"] - d["g"])])

    tabla = Table(filas, repeatRows=1, colWidths=[50 * mm, 37 * mm, 37 * mm, 37 * mm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2332")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d9d9d9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
    ]))

    # Gráfica de barras: ingresos (azul) vs egresos (rojo) por mes.
    dibujo = Drawing(400, 150)
    meses = sorted(por_mes.keys())[-6:]
    maximo = max([por_mes[m]["i"] for m in meses] + [por_mes[m]["g"] for m in meses] + [1]) if meses else 1
    ancho = 40 if meses else 0
    for i, clave in enumerate(meses):
        d = por_mes[clave]
        x = 20 + i * 62
        hi = (d["i"] / maximo) * 100
        hg = (d["g"] / maximo) * 100
        dibujo.add(Rect(x, 30, ancho / 2, max(hi, 1), fillColor=colors.HexColor("#3b82f6"), strokeColor=None))
        dibujo.add(Rect(x + ancho / 2, 30, ancho / 2, max(hg, 1), fillColor=colors.HexColor("#ef4444"), strokeColor=None))
        dibujo.add(String(x, 18, clave[5:], fontSize=7, fillColor=colors.HexColor("#555555")))
    dibujo.add(String(20, 138, "Ingresos (azul) vs egresos (rojo)", fontSize=8, fillColor=colors.HexColor("#555555")))

    _, _, etiqueta_periodo = resolver_rango_periodo(desde, hasta)
    story = [
        Paragraph("Multi-Administrador", h1),
        Paragraph("Reporte financiero para el consejo de administración", h2),
        Paragraph(
            f"Ingresos y egresos consolidados · Período: <b>{xml_escape(etiqueta_periodo)}</b> (UH-23).",
            normal,
        ),
        Paragraph("", normal),
        tabla,
        Paragraph("", normal),
        dibujo,
        Paragraph("", normal),
        Paragraph(f"Total ingresos: <b>{_money(ingresos)}</b>", normal),
        Paragraph(f"Total egresos: <b>{_money(gastos)}</b>", normal),
        Paragraph(f"<b>Balance: {_money(ingresos - gastos)}</b>", normal),
    ]
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


def reporte_consejo_xlsx(
    db: Session,
    id_conjunto: int = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> bytes:
    """Resumen de ingresos y egresos por mes para el consejo, filtrable por período (UH-23)."""
    f_desde, f_hasta, etiqueta = resolver_rango_periodo(desde, hasta)
    wb = Workbook()
    ws = wb.active
    ws.title = "Resumen consejo"
    ws.append(["Mes", "Ingresos", "Egresos", "Balance", "Período"])
    _encabezado(ws, [])
    _autoancho(ws, [16, 18, 18, 18, 26])

    concepto = {c.id: c for c in db.query(models.ConceptoFinanciero).all()}
    consulta = _por_conjunto(db.query(models.MovimientoFinanciero).filter(
        models.MovimientoFinanciero.estado == "pagado"
    ), models.MovimientoFinanciero, id_conjunto)
    if f_desde:
        consulta = consulta.filter(models.MovimientoFinanciero.fecha_vencimiento >= f_desde)
    if f_hasta:
        consulta = consulta.filter(models.MovimientoFinanciero.fecha_vencimiento <= f_hasta)

    por_mes: dict[str, dict] = {}
    t_i = t_g = 0.0
    for m in consulta.all():
        c = concepto.get(m.concepto_id)
        clave = m.fecha_vencimiento.strftime("%Y-%m")
        d = por_mes.setdefault(clave, {"i": 0.0, "g": 0.0})
        if c and c.tipo == "ingreso":
            d["i"] += float(m.monto)
            t_i += float(m.monto)
        else:
            d["g"] += float(m.monto)
            t_g += float(m.monto)
    for clave in sorted(por_mes.keys()):
        d = por_mes[clave]
        ws.append([clave, round(d["i"], 2), round(d["g"], 2), round(d["i"] - d["g"], 2), etiqueta])
    ws.append([])
    ws.append(["TOTAL", round(t_i, 2), round(t_g, 2), round(t_i - t_g, 2), etiqueta])
    for col in range(1, 6):
        ws.cell(row=ws.max_row, column=col).font = Font(bold=True)
    return _respuesta_xlsx("reporte_consejo", wb)
