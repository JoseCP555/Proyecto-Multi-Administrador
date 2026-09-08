"""Notificaciones / recordatorios calculados desde los datos reales."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, usuario_tiene_permiso
from app import models

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


def _money(v) -> str:
    return f"${float(v or 0):,.0f}".replace(",", ".")


@router.get("")
def listar_notificaciones(
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Devuelve recordatorios de: pagos vencidos/próximos, eventos próximos
    y mantenimientos críticos sin resolver. Cada bloque se incluye solo si
    el rol del usuario tiene permiso de ver ese módulo (RBAC)."""
    notificaciones = []
    hoy = date.today()
    ve = lambda modulo: usuario_tiene_permiso(db, usuario, f"{modulo}.ver")  # noqa: E731

    # 1) Pagos vencidos (mora) y próximos a vencer (7 días)
    concepto = {c.id: c for c in db.query(models.ConceptoFinanciero).all()}
    movs = db.query(models.MovimientoFinanciero).filter(
        models.MovimientoFinanciero.estado.in_(["pendiente", "vencido"])
    ).order_by(models.MovimientoFinanciero.fecha_vencimiento).all() if ve("finanzas") else []
    for m in movs:
        tipo = "mora" if m.estado == "vencido" or (m.fecha_vencimiento and m.fecha_vencimiento < hoy) else "proximo"
        monto = _money(m.monto)
        concepto_nombre = (concepto.get(m.concepto_id).nombre if concepto.get(m.concepto_id) else "pago")
        if tipo == "mora":
            notificaciones.append({
                "tipo": "mora", "severidad": "alta",
                "titulo": "Pago vencido",
                "mensaje": f"{concepto_nombre} por {monto} está vencido (propiedad {m.propiedad_id or '—'}).",
                "fecha": m.fecha_vencimiento.strftime("%Y-%m-%d") if m.fecha_vencimiento else None,
            })
        elif m.fecha_vencimiento and 0 <= (m.fecha_vencimiento - hoy).days <= 7:
            notificaciones.append({
                "tipo": "proximo", "severidad": "media",
                "titulo": "Pago próximo a vencer",
                "mensaje": f"{concepto_nombre} por {monto} vence el {m.fecha_vencimiento.strftime('%d/%m/%Y')}.",
                "fecha": m.fecha_vencimiento.strftime("%Y-%m-%d"),
            })

    # 2) Eventos próximos (7 días)
    eventos = db.query(models.Evento).filter(
        models.Evento.fecha >= hoy, models.Evento.fecha <= hoy + timedelta(days=7)
    ).order_by(models.Evento.fecha).all() if ve("eventos") else []
    for ev in eventos:
        notificaciones.append({
            "tipo": "evento", "severidad": "baja",
            "titulo": "Evento próximo",
            "mensaje": f"{ev.titulo} — {ev.fecha.strftime('%d/%m/%Y')}" + (f" en {ev.lugar}" if ev.lugar else ""),
            "fecha": ev.fecha.strftime("%Y-%m-%d"),
        })

    # 3) Mantenimientos críticos sin resolver
    criticas = db.query(models.TareaMantenimiento).filter(
        models.TareaMantenimiento.prioridad == "critica",
        models.TareaMantenimiento.estado != "completada",
    ).all() if ve("mantenimiento") else []
    for t in criticas:
        notificaciones.append({
            "tipo": "mantenimiento", "severidad": "alta",
            "titulo": "Mantenimiento crítico",
            "mensaje": f"{t.titulo} está sin resolver (prioridad crítica).",
            "fecha": None,
        })

    # Ordenar por severidad y fecha
    orden = {"alta": 0, "media": 1, "baja": 2}
    notificaciones.sort(key=lambda n: (orden.get(n["severidad"], 3), n["fecha"] or ""))
    return notificaciones
