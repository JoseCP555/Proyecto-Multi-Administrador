"""Utilidades de exportación de reportes a Excel (.xlsx) y PDF.

Se usan openpyxl (Excel real) y reportlab (PDF), ambos en requirements.txt.
"""
from datetime import date
from io import BytesIO

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


# ---------------------------------------------------------------------------
# Finanzas -> Excel
# ---------------------------------------------------------------------------
def finanzas_xlsx(db: Session) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Movimientos"
    ws.append(["Fecha", "Concepto", "Tipo", "Propiedad", "Monto", "Estado", "Recibo"])
    _encabezado(ws, [])
    _autoancho(ws, [12, 24, 10, 16, 14, 12, 16])

    concepto = {c.id: c for c in db.query(models.ConceptoFinanciero).all()}
    movs = (
        db.query(models.MovimientoFinanciero)
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
def pagos_xlsx(db: Session) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Pagos"
    ws.append(["Concepto", "Propiedad", "Vencimiento", "Monto", "Estado", "Número"])
    _encabezado(ws, [])
    _autoancho(ws, [24, 16, 12, 14, 12, 16])

    concepto = {c.id: c for c in db.query(models.ConceptoFinanciero).all()}
    movs = (
        db.query(models.MovimientoFinanciero)
        .filter(models.MovimientoFinanciero.estado.in_(["pendiente", "vencido"]))
        .order_by(models.MovimientoFinanciero.fecha_vencimiento)
        .all()
    )
    for m in movs:
        c = concepto.get(m.concepto_id)
        ws.append([
            c.nombre if c else "",
            (m.propiedad_id or ""),
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
def mantenimiento_xlsx(db: Session) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Mantenimiento"
    ws.append(["Título", "Descripción", "Prioridad", "Estado", "F. programada", "Costo estimado"])
    _encabezado(ws, [])
    _autoancho(ws, [24, 30, 10, 12, 14, 14])

    tareas = db.query(models.TareaMantenimiento).order_by(models.TareaMantenimiento.fecha_creacion).all()
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
def reporte_finanzas_pdf(db: Session) -> bytes:
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
    movs = db.query(models.MovimientoFinanciero).filter(
        models.MovimientoFinanciero.estado == "pagado"
    ).order_by(models.MovimientoFinanciero.fecha_vencimiento).all()

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


def pagos_pdf(db: Session) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm)
    estilos = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=estilos["Title"], fontSize=16, textColor=colors.HexColor("#1a2332"))
    h2 = ParagraphStyle("h2", parent=estilos["Heading2"], fontSize=11, textColor=colors.HexColor("#3b82f6"))
    normal = ParagraphStyle("normal", parent=estilos["Normal"], fontSize=9)

    concepto = {c.id: c for c in db.query(models.ConceptoFinanciero).all()}
    movs = db.query(models.MovimientoFinanciero).filter(
        models.MovimientoFinanciero.estado.in_(["pendiente", "vencido"])
    ).order_by(models.MovimientoFinanciero.fecha_vencimiento).all()

    filas = [["Concepto", "Vencimiento", "Monto", "Estado"]]
    for m in movs:
        c = concepto.get(m.concepto_id)
        filas.append([
            c.nombre if c else "",
            m.fecha_vencimiento.strftime("%d/%m/%Y") if m.fecha_vencimiento else "",
            _money(m.monto),
            m.estado,
        ])
    total = sum(float(m.monto) for m in movs)
    filas.append(["TOTAL EN MORA", "", _money(total), ""])

    tabla = Table(filas, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2332")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d9d9d9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff4e5")]),
    ]))

    story = [
        Paragraph("Multi-Administrador", h1),
        Paragraph("Reporte de pagos en mora / pendientes", h2),
        Paragraph("Detalle de pagos pendientes y vencidos.", normal),
        Paragraph("", normal),
        tabla,
    ]
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
