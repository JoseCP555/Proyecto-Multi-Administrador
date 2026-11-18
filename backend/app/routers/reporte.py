"""Reportes y estadísticas del dashboard."""
from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import schemas, exportar
from app.models import (
    Usuario, Residente, Propiedad, MovimientoFinanciero,
    ConceptoFinanciero, TareaMantenimiento, Documento,
)
from app.database import get_db
from app.deps import require_permiso, require_alguno, usuario_tiene_permiso
from app.models import Evento
from app.redis_client import cache_get, cache_set, cache_del
from app.conjunto_ctx import conjunto_activo, filtrar

# Los reportes generales exigen `reportes.ver`; las exportaciones de un módulo
# concreto se autorizan además con el permiso `<modulo>.ver` correspondiente.
router = APIRouter(prefix="/reportes", tags=["Reportes"])
_REPORTES = [Depends(require_permiso("reportes.ver"))]
_FINANZAS = [Depends(require_alguno("reportes.ver", "finanzas.ver"))]
_MANTENIMIENTO = [Depends(require_alguno("reportes.ver", "mantenimiento.ver"))]


@router.get("/dashboard", response_model=schemas.DashboardStats, dependencies=_REPORTES)
def dashboard(db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    """Estadísticas agregadas del dashboard (cacheadas en Redis 60s)."""
    # La caché se guarda por conjunto: cada uno tiene sus propias cifras.
    cacheado = cache_get(f"dashboard_stats:{cid}")
    if cacheado:
        return cacheado

    usuarios = filtrar(db.query(Usuario), Usuario, cid).count()
    residentes = filtrar(db.query(Residente).filter(Residente.activo == True), Residente, cid).count()
    propiedades = filtrar(db.query(Propiedad), Propiedad, cid).count()

    concepto = {c.id: c for c in db.query(ConceptoFinanciero).all()}
    ingresos = gastos = 0.0
    pagos_pendientes = pagos_pagados = 0
    for m in filtrar(db.query(MovimientoFinanciero), MovimientoFinanciero, cid).all():
        c = concepto.get(m.concepto_id)
        tipo = c.tipo if c else "gasto"
        if m.estado == "pagado":
            if tipo == "ingreso":
                ingresos += float(m.monto)
            else:
                gastos += float(m.monto)
            pagos_pagados += 1
        elif m.estado in ("pendiente", "vencido"):
            pagos_pendientes += 1

    mant_pend = filtrar(db.query(TareaMantenimiento).filter(
        TareaMantenimiento.estado.in_(["pendiente", "en_proceso"])
    ), TareaMantenimiento, cid).count()
    mant_comp = filtrar(db.query(TareaMantenimiento).filter(
        TareaMantenimiento.estado == "completada"
    ), TareaMantenimiento, cid).count()
    documentos = filtrar(db.query(Documento), Documento, cid).count()

    resultado = {
        "usuarios": usuarios, "residentes": residentes, "propiedades": propiedades,
        "pagos_pendientes": pagos_pendientes, "pagos_pagados": pagos_pagados,
        "ingresos": round(ingresos, 2), "gastos": round(gastos, 2),
        "saldo": round(ingresos - gastos, 2),
        "mantenimientos_pendientes": mant_pend, "mantenimientos_completados": mant_comp,
        "documentos": documentos,
    }
    cache_set(f"dashboard_stats:{cid}", resultado, ttl=60)
    return resultado


@router.get("/resumen-basico")
def resumen_basico(
    usuario=Depends(require_permiso("dashboard.ver")),
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
):
    """Contadores NO financieros para el panel de roles sin `reportes.ver`.
    Solo incluye los módulos que el rol puede ver (RBAC)."""
    from datetime import date
    ve = lambda m: usuario_tiene_permiso(db, usuario, f"{m}.ver")  # noqa: E731
    out: dict = {}
    if ve("propiedades"):
        out["propiedades"] = filtrar(db.query(Propiedad), Propiedad, cid).count()
    if ve("residentes"):
        out["residentes"] = filtrar(db.query(Residente).filter(Residente.activo == True), Residente, cid).count()
    if ve("mantenimiento"):
        out["mantenimientos_pendientes"] = filtrar(db.query(TareaMantenimiento).filter(
            TareaMantenimiento.estado.in_(["pendiente", "en_proceso"])
        ), TareaMantenimiento, cid).count()
    if ve("documentos"):
        out["documentos"] = filtrar(db.query(Documento), Documento, cid).count()
    if ve("eventos"):
        out["eventos_proximos"] = filtrar(db.query(Evento).filter(Evento.fecha >= date.today()), Evento, cid).count()
    return out


@router.get("/finanzas-por-mes", dependencies=_REPORTES)
def finanzas_por_mes(
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
    desde: date | None = Query(None, description="Fecha inicial del período (UH-23)"),
    hasta: date | None = Query(None, description="Fecha final del período (UH-23)"),
):
    """Ingresos agrupados por mes para las gráficas, filtrable por período (UH-23)."""
    clave_cache = f"finanzas_por_mes:{cid}:{desde}:{hasta}"
    cacheado = cache_get(clave_cache)
    if cacheado:
        return cacheado

    consulta = filtrar(db.query(MovimientoFinanciero, ConceptoFinanciero).join(
        ConceptoFinanciero, MovimientoFinanciero.concepto_id == ConceptoFinanciero.id
    ).filter(MovimientoFinanciero.estado == "pagado"), MovimientoFinanciero, cid)
    if desde:
        consulta = consulta.filter(MovimientoFinanciero.fecha_vencimiento >= desde)
    if hasta:
        consulta = consulta.filter(MovimientoFinanciero.fecha_vencimiento <= hasta)
    movs = consulta.all()
    limite = 12 if (desde or hasta) else 6

    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    por_mes: dict[str, dict[str, float]] = {}
    for m, c in movs:
        clave = m.fecha_vencimiento.strftime("%Y-%m")
        d = por_mes.setdefault(clave, {"ingresos": 0.0, "gastos": 0.0})
        if c.tipo == "ingreso":
            d["ingresos"] += float(m.monto)
        else:
            d["gastos"] += float(m.monto)

    # Ordenar y tomar últimos meses (mantiene `valor` = ingresos para compatibilidad con gráficos existentes).
    series = []
    for clave in sorted(por_mes.keys())[-limite:]:
        y, mo = clave.split("-")
        d = por_mes[clave]
        series.append({
            "mes": f"{meses[int(mo) - 1]}",
            "valor": round(d["ingresos"], 2),
            "ingresos": round(d["ingresos"], 2),
            "gastos": round(d["gastos"], 2),
        })

    cache_set(clave_cache, series, ttl=60)
    return series


# ---------------------------------------------------------------------------
# EXPORTACIÓN DE REPORTES (Excel / PDF)
# ---------------------------------------------------------------------------
@router.get("/exportar/finanzas.xlsx", dependencies=_FINANZAS)
def exportar_finanzas(db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    contenido = exportar.finanzas_xlsx(db, cid)
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="finanzas.xlsx"'},
    )


@router.get("/exportar/pagos.xlsx", dependencies=_FINANZAS)
def exportar_pagos(
    desde: date | None = None,
    hasta: date | None = None,
    periodo: str | None = None,
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
):
    contenido = exportar.pagos_xlsx(db, cid, desde, hasta, periodo)
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="pagos_mora.xlsx"'},
    )


@router.get("/exportar/mantenimiento.xlsx", dependencies=_MANTENIMIENTO)
def exportar_mantenimiento(db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    contenido = exportar.mantenimiento_xlsx(db, cid)
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="mantenimiento.xlsx"'},
    )


@router.get("/exportar/finanzas.pdf", dependencies=_FINANZAS)
def exportar_finanzas_pdf(db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    contenido = exportar.reporte_finanzas_pdf(db, cid)
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="finanzas.pdf"'},
    )


@router.get("/exportar/pagos.pdf", dependencies=_FINANZAS)
def exportar_pagos_pdf(
    desde: date | None = None,
    hasta: date | None = None,
    periodo: str | None = None,
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
):
    contenido = exportar.pagos_pdf(db, cid, desde, hasta, periodo)
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="pagos_mora.pdf"'},
    )


# ---------------------------------------------------------------------------
# Reportes del consejo y de los módulos nuevos (UH-23 · UH-06 · UH-09 · UH-10)
# ---------------------------------------------------------------------------
@router.get("/exportar/cartera.pdf", dependencies=_FINANZAS)
def exportar_cartera_pdf(
    desde: date | None = None,
    hasta: date | None = None,
    periodo: str | None = None,
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
):
    """Reporte descargable en PDF de pagos pendientes y al día por unidad (UH-06)."""
    contenido = exportar.cartera_pdf(db, cid, desde, hasta, periodo)
    sufijo = f"_{periodo}" if periodo else ""
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="cartera_unidades{sufijo}.pdf"'},
    )


@router.get("/exportar/cartera.xlsx", dependencies=_FINANZAS)
def exportar_cartera_xlsx(
    desde: date | None = None,
    hasta: date | None = None,
    periodo: str | None = None,
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
):
    """Reporte descargable en Excel de pagos pendientes y al día por unidad (UH-06)."""
    contenido = exportar.cartera_xlsx(db, cid, desde, hasta, periodo)
    sufijo = f"_{periodo}" if periodo else ""
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="cartera_unidades{sufijo}.xlsx"'},
    )


@router.get("/exportar/consejo.pdf", dependencies=_FINANZAS)
def exportar_consejo_pdf(desde: date | None = None, hasta: date | None = None,
                         db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    """Reporte de ingresos/egresos con gráfica para el consejo (UH-23)."""
    contenido = exportar.reporte_consejo_pdf(db, cid, desde, hasta)
    return Response(
        content=contenido, media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="reporte_consejo.pdf"'},
    )


@router.get("/exportar/consejo.xlsx", dependencies=_FINANZAS)
def exportar_consejo_xlsx(
    desde: date | None = None,
    hasta: date | None = None,
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
):
    contenido = exportar.reporte_consejo_xlsx(db, cid, desde, hasta)
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="reporte_consejo.xlsx"'},
    )


@router.get("/exportar/pqrs.xlsx", dependencies=[Depends(require_alguno("pqrs.ver", "reportes.ver"))])
def exportar_pqrs(db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    contenido = exportar.pqrs_xlsx(db, cid)
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="pqrs.xlsx"'},
    )


@router.get("/exportar/reservas.xlsx", dependencies=[Depends(require_alguno("reservas.ver", "reportes.ver"))])
def exportar_reservas(db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    contenido = exportar.reservas_xlsx(db, cid)
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="reservas.xlsx"'},
    )


@router.get("/cartera", dependencies=_FINANZAS)
def cartera(
    desde: date | None = None,
    hasta: date | None = None,
    periodo: str | None = None,
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
):
    """Cartera por unidad: pagos pendientes y al día para el período seleccionado (UH-06)."""
    return exportar.calcular_cartera(db, cid, desde, hasta, periodo)
