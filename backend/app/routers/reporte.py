"""Reportes y estadísticas del dashboard."""
from fastapi import APIRouter, Depends, Response
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
def finanzas_por_mes(db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    """Ingresos y gastos agrupados por mes (para las gráficas)."""
    cacheado = cache_get(f"finanzas_por_mes:{cid}")
    if cacheado:
        return cacheado

    desde = None
    from datetime import date
    # Tomar los últimos 6 meses
    movs = filtrar(db.query(MovimientoFinanciero, ConceptoFinanciero).join(
        ConceptoFinanciero, MovimientoFinanciero.concepto_id == ConceptoFinanciero.id
    ).filter(MovimientoFinanciero.estado == "pagado"), MovimientoFinanciero, cid).all()

    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    por_mes = {}
    for m, c in movs:
        if c.tipo != "ingreso":
            continue
        clave = m.fecha_vencimiento.strftime("%Y-%m")
        por_mes.setdefault(clave, 0)
        por_mes[clave] += float(m.monto)

    # Ordenar y tomar últimos 6
    series = []
    for clave in sorted(por_mes.keys())[-6:]:
        y, mo = clave.split("-")
        series.append({"mes": f"{meses[int(mo) - 1]}", "valor": round(por_mes[clave], 2)})

    cache_set(f"finanzas_por_mes:{cid}", series, ttl=60)
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
def exportar_pagos(db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    contenido = exportar.pagos_xlsx(db, cid)
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
def exportar_pagos_pdf(db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    contenido = exportar.pagos_pdf(db, cid)
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="pagos_mora.pdf"'},
    )
