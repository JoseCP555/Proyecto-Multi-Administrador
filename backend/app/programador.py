"""Tareas periódicas del sistema (segundo plano).

* **UH-01** — Avisa a todos los residentes activos las asambleas/reuniones que
  se celebran en **menos de 48 horas** (notificación push + correo). El aviso
  se envía una sola vez por evento (`eventos.notificado_48h`).
* **UH-25** — Cierra automáticamente las votaciones cuyo plazo venció y
  publica los resultados al consejo.

El bucle corre cada 30 minutos en un hilo *daemon* y nunca debe tumbar la API:
cualquier error se registra en el log y se continúa. Para desactivarlo (por
ejemplo en pruebas) basta con `DESACTIVAR_PROGRAMADOR=1`.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app import models
from app import notificaciones_servicio as notif

logger = logging.getLogger("app.programador")

INTERVALO_SEGUNDOS = int(os.getenv("PROGRAMADOR_INTERVALO", "1800"))
_detenido = threading.Event()


def _desactivado() -> bool:
    return (os.getenv("DESACTIVAR_PROGRAMADOR", "") or "").strip().lower() in ("1", "true", "yes", "si", "sí")


# ---------------------------------------------------------------------------
# UH-01: aviso de asambleas con menos de 48 horas
# ---------------------------------------------------------------------------
def _inicio_evento(evento: models.Evento) -> datetime:
    hora = evento.hora or "00:00"
    try:
        h, m = (int(x) for x in hora.split(":")[:2])
    except (ValueError, AttributeError):
        h, m = 0, 0
    return datetime.combine(evento.fecha, datetime.min.time()).replace(hour=h, minute=m)


def avisar_asambleas(db: Session, ahora: datetime | None = None) -> int:
    """Notifica los eventos que ocurren dentro de las próximas 48 horas."""
    ahora = ahora or datetime.utcnow()
    limite = ahora + timedelta(hours=48)
    enviados = 0

    eventos = (
        db.query(models.Evento)
        .filter(models.Evento.notificado_48h.is_(False))
        .all()
    )
    for evento in eventos:
        inicio = _inicio_evento(evento)
        if inicio < ahora:
            # Ya pasó: se marca para no volver a evaluarlo.
            evento.notificado_48h = True
            continue
        if inicio > limite:
            continue

        horas = max(1, int((inicio - ahora).total_seconds() // 3600))
        tipo_txt = (evento.tipo or "actividad").replace("_", " ")
        notif.notificar_seguro(
            db=db, id_conjunto=evento.id_conjunto, tipo="asamblea",
            titulo=f"{tipo_txt.capitalize()} en {horas} hora(s): {evento.titulo}",
            mensaje=(
                f"Recuerda: «{evento.titulo}» el {evento.fecha:%d/%m/%Y}"
                + (f" a las {evento.hora}" if evento.hora else "")
                + (f" en {evento.lugar}" if evento.lugar else "")
                + ". Faltan menos de 48 horas."
            ),
            clave=f"48h:{evento.id}", severidad="alta",
            url="/dashboard/eventos", fecha=evento.fecha,
        )
        evento.notificado_48h = True
        enviados += 1

    if enviados or eventos:
        db.commit()
    return enviados


# ---------------------------------------------------------------------------
# UH-25: cierre automático de votaciones
# ---------------------------------------------------------------------------
def cerrar_votaciones(db: Session, hoy: date | None = None) -> int:
    hoy = hoy or date.today()
    cerradas = 0
    abiertas = db.query(models.Votacion).filter(models.Votacion.estado == "abierta").all()
    for v in abiertas:
        if v.fecha_cierre < hoy:
            v.estado = "cerrada"
            db.commit()
            votos = db.query(models.Voto).filter(models.Voto.votacion_id == v.id).all()
            opciones = {
                o.id: o.texto
                for o in db.query(models.VotacionOpcion)
                .filter(models.VotacionOpcion.votacion_id == v.id)
                .all()
            }
            conteo: dict[int, int] = {}
            for voto in votos:
                conteo[voto.opcion_id] = conteo.get(voto.opcion_id, 0) + 1
            ganadora_id = max(conteo, key=conteo.get) if conteo else None
            detalle = (
                f"Más votada: «{opciones.get(ganadora_id, '—')}» con {conteo.get(ganadora_id, 0)} voto(s)."
                if ganadora_id else "Sin votos registrados."
            )
            notif.notificar_seguro(
                db=db, id_conjunto=v.id_conjunto, tipo="votacion",
                titulo=f"Resultados de la votación «{v.titulo}»",
                mensaje=f"La votación se cerró automáticamente. {detalle}",
                clave=f"resultados:{v.id}", severidad="media",
                url="/dashboard/votaciones",
            )
            cerradas += 1
    return cerradas


# ---------------------------------------------------------------------------
# Bucle
# ---------------------------------------------------------------------------
def ejecutar_ciclo(db: Session) -> dict:
    """Una pasada completa de todas las tareas programadas."""
    resultado = {"asambleas": 0, "votaciones": 0}
    try:
        resultado["asambleas"] = avisar_asambleas(db)
    except Exception:  # noqa: BLE001
        logger.exception("[programador] falló el aviso de asambleas")
        db.rollback()
    try:
        resultado["votaciones"] = cerrar_votaciones(db)
    except Exception:  # noqa: BLE001
        logger.exception("[programador] falló el cierre de votaciones")
        db.rollback()
    return resultado


def _bucle() -> None:
    from app.database import SessionLocal

    # Pequeña espera para que la API termine de arrancar.
    if _detenido.wait(10):
        return
    while not _detenido.is_set():
        db = SessionLocal()
        try:
            ejecutar_ciclo(db)
        except Exception:  # noqa: BLE001
            logger.exception("[programador] ciclo fallido")
        finally:
            db.close()
        if _detenido.wait(INTERVALO_SEGUNDOS):
            break


def iniciar() -> None:
    """Arranca el hilo del programador (idempotente)."""
    if _desactivado():
        logger.info("[programador] desactivado por DESACTIVAR_PROGRAMADOR")
        return
    hilo = threading.Thread(target=_bucle, name="programador", daemon=True)
    hilo.start()
    logger.info("[programador] iniciado (intervalo %ss)", INTERVALO_SEGUNDOS)


def detener() -> None:
    _detenido.set()
