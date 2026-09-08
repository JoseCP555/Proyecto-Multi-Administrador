"""Motor del chatbot: responde con datos reales de la base de datos (intents en español).

Si se configura un motor LLM (OPENAI_API_KEY), el chatbot usa un modelo externo;
por defecto usa un motor local basado en reglas + datos del sistema, de modo que
es 100 % funcional sin depender de servicios de pago.
"""
import os
import difflib
from datetime import date

from sqlalchemy.orm import Session

from app import models

# Catálogo de intents (palabras clave). Se normaliza a minúsculas y sin tildes.
def _norm(t: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return t.lower()


INTENTS = {
    "saludo": ["hola", "buenos dias", "buenas tardes", "buenas noches", "hey", "saludos", "que tal"],
    "balance": ["balance", "saldo", "cuanto tengo", "cuanto debo", "deuda", "estado cuenta", "estado de cuenta"],
    "ingresos": ["ingresos", "ingreso", "cuanto entra", "recaudado", "recaudacion"],
    "gastos": ["gastos", "gasto", "egresos", "cuanto sale", "erogacion"],
    "pagos_pendientes": ["pago pendiente", "pagos", "pendiente", "sin pagar", "mora", "morosos"],
    "mantenimiento": ["mantenimiento", "tarea", "reparacion", "averia", "arreglo", "falla"],
    "propiedades": ["propiedades", "inmuebles", "apartamento", "unidades", "bloque", "torre"],
    "residentes": ["residente", "residentes", "propietario", "inquilino"],
    "documentos": ["documento", "documentos", "reglamento", "acta", "manual", "archivo"],
    "eventos": ["evento", "reunion", "asamblea", "agenda", "actividad"],
    "ayuda": ["ayuda", "que puedes hacer", "funciones", "como usar", "help"],
    "gracias": ["gracias", "genial", "perfecto", "excelente", "ok"],
}


def detectar_intent(mensaje: str) -> str:
    n = _norm(mensaje)
    for intent, palabras in INTENTS.items():
        if any(palabra in n for palabra in palabras):
            return intent
    return "general"


def _format_money(v) -> str:
    number = float(v or 0)
    return f"${number:,.0f}".replace(",", ".")


# Módulo (permiso `<modulo>.ver`) que requiere cada intent con datos reales.
INTENT_MODULO = {
    "balance": "finanzas", "ingresos": "finanzas", "gastos": "finanzas",
    "pagos_pendientes": "finanzas", "mantenimiento": "mantenimiento",
    "propiedades": "propiedades", "residentes": "residentes",
    "documentos": "documentos", "eventos": "eventos",
}

SIN_PERMISO = (
    "Esa información pertenece al módulo de {modulo}, al que tu rol no tiene acceso. "
    "Si la necesitas, comunícate con la administración del conjunto. 🔒"
)


def responder(db: Session, mensaje: str, permisos: list[str] | None = None) -> str:
    """Genera la respuesta. Si se pasan `permisos` (códigos RBAC del rol),
    los intents con datos de un módulo se responden solo si el rol puede verlo."""
    intent = detectar_intent(mensaje)

    modulo = INTENT_MODULO.get(intent)
    if permisos is not None and modulo and f"{modulo}.ver" not in permisos:
        return SIN_PERMISO.format(modulo=modulo)

    respuestas = {
        "saludo": (
            "¡Hola! 👋 Soy el asistente virtual de Multi-Administrador. "
            "Puedo ayudarte con información sobre finanzas, pagos, mantenimiento, "
            "propiedades, residentes, documentos y eventos del conjunto. "
            "¿Qué deseas saber?"
        ),
        "ayuda": (
            "Puedo responderte sobre: \n"
            "• Finanzas: balance, ingresos, gastos\n"
            "• Pagos: pendientes / en mora\n"
            "• Mantenimiento: tareas y su estado\n"
            "• Propiedades y residentes\n"
            "• Documentos y eventos del conjunto\n"
            "Prueba con: \"¿Cuál es el saldo?\" o \"¿Hay pagos pendientes?\""
        ),
        "gracias": "¡Con gusto! Estoy aquí para lo que necesites. 😊",
    }

    if intent in respuestas:
        return respuestas[intent]

    # ---- Intents basados en datos reales ------------------------------------
    if intent in ("balance", "ingresos", "gastos", "pagos_pendientes"):
        return _responder_finanzas(db, intent)

    if intent == "mantenimiento":
        return _responder_mantenimiento(db)

    if intent == "propiedades":
        return _responder_propiedades(db)

    if intent == "residentes":
        return _responder_residentes(db)

    if intent == "documentos":
        return _responder_documentos(db)

    if intent == "eventos":
        return _responder_eventos(db)

    # Fallback: sugerir el intent más parecido.
    sugerido = _sugerir_intent(mensaje)
    if sugerido:
        return (
            f"Creo que quieres saber sobre {sugerido}. Vuelve a preguntarme con "
            f"más detalle, por ejemplo: ¿Cuál es el saldo? o ¿Hay pagos pendientes?"
        )

    return (
        "No estoy seguro de haber entendido. Puedo ayudarte con finanzas, pagos, "
        "mantenimiento, propiedades, documentos y eventos. Escribe \"ayuda\" para ver opciones."
    )


# ---- Intents específicos ---------------------------------------------------
def _responder_finanzas(db: Session, intent: str) -> str:
    ingresos = (
        db.query(models.MovimientoFinanciero)
        .join(models.ConceptoFinanciero)
        .filter(models.ConceptoFinanciero.tipo == "ingreso", models.MovimientoFinanciero.estado == "pagado")
        .all()
    )
    gastos = (
        db.query(models.MovimientoFinanciero)
        .join(models.ConceptoFinanciero)
        .filter(models.ConceptoFinanciero.tipo == "gasto", models.MovimientoFinanciero.estado == "pagado")
        .all()
    )
    total_ing = sum(float(m.monto) for m in ingresos)
    total_gas = sum(float(m.monto) for m in gastos)
    saldo = total_ing - total_gas

    pendientes = (
        db.query(models.MovimientoFinanciero)
        .filter(models.MovimientoFinanciero.estado.in_(["pendiente", "vencido"]))
        .all()
    )
    total_pend = sum(float(m.monto) for m in pendientes)

    if intent == "ingresos":
        return (
            f"Los ingresos recaudados del periodo suman {_format_money(total_ing)} "
            f"en {len(ingresos)} movimientos registrados. 💰"
        )
    if intent == "gastos":
        return (
            f"Los gastos del periodo suman {_format_money(total_gas)} "
            f"en {len(gastos)} movimientos. 📉"
        )
    if intent == "pagos_pendientes":
        if not pendientes:
            return "¡Buenas noticias! No hay pagos pendientes ni en mora. ✅"
        return (
            f"Hay {len(pendientes)} pagos pendientes o en mora por un total de "
            f"{_format_money(total_pend)}. Revisa el módulo de Finanzas para gestionarlos."
        )

    # balance
    return (
        f"📊 Resumen financiero:\n"
        f"• Ingresos: {_format_money(total_ing)}\n"
        f"• Gastos: {_format_money(total_gas)}\n"
        f"• Saldo: {_format_money(saldo)}\n"
        f"• Pendientes/En mora: {_format_money(total_pend)}\n\n"
        "¿Quieres detalle de ingresos, gastos o pagos pendientes?"
    )


def _responder_mantenimiento(db: Session) -> str:
    pendientes = db.query(models.TareaMantenimiento).filter(
        models.TareaMantenimiento.estado.in_(["pendiente", "en_proceso"])
    ).count()
    completadas = db.query(models.TareaMantenimiento).filter(
        models.TareaMantenimiento.estado == "completada"
    ).count()
    criticas = db.query(models.TareaMantenimiento).filter(
        models.TareaMantenimiento.prioridad == "critica",
        models.TareaMantenimiento.estado != "completada",
    ).count()
    return (
        f"🛠️ Mantenimiento:\n"
        f"• Tareas pendientes/en proceso: {pendientes}\n"
        f"• Completadas: {completadas}\n"
        f"• Críticas sin resolver: {criticas}\n\n"
        "Consulta el módulo de Mantenimiento para ver el detalle."
    )


def _responder_propiedades(db: Session) -> str:
    total = db.query(models.Propiedad).count()
    ocupadas = db.query(models.Propiedad).filter(models.Propiedad.estado == "ocupado").count()
    vacias = db.query(models.Propiedad).filter(models.Propiedad.estado == "vacio").count()
    return (
        f"🏢 El conjunto cuenta con {total} propiedades: "
        f"{ocupadas} ocupadas y {vacias} vacías. "
        "¿Quieres conocer el estado de alguna torre o bloque en particular?"
    )


def _responder_residentes(db: Session) -> str:
    total = db.query(models.Residente).count()
    activos = db.query(models.Residente).filter(models.Residente.activo == True).count()
    propietarios = db.query(models.Residente).filter(models.Residente.tipo == "propietario").count()
    inquilinos = db.query(models.Residente).filter(models.Residente.tipo == "inquilino").count()
    return (
        f"👥 Hay {total} residentes registrados ({activos} activos).\n"
        f"• Propietarios: {propietarios}\n"
        f"• Inquilinos: {inquilinos}\n\n"
        "Consulta el módulo de Residentes para el detalle completo."
    )


def _responder_documentos(db: Session) -> str:
    total = db.query(models.Documento).count()
    publicos = db.query(models.Documento).filter(models.Documento.publico == True).count()
    return (
        f"📄 Hay {total} documentos cargados, de los cuales {publicos} son de acceso público "
        "(reglamentos, actas, manuales). Consulta el módulo de Documentos."
    )


def _responder_eventos(db: Session) -> str:
    hoy = date.today()
    eventos = db.query(models.Evento).filter(models.Evento.fecha >= hoy).order_by(models.Evento.fecha).all()
    if not eventos:
        return "No hay eventos próximos programados. 📅"
    lineas = "\n".join(f"• {e.titulo} — {e.fecha.strftime('%d/%m/%Y')} ({e.lugar})" for e in eventos[:5])
    return f"📅 Próximos eventos del conjunto:\n{lineas}"


def _sugerir_intent(mensaje: str) -> str:
    """Recomienda una categoría por similitud de palabras."""
    n = _norm(mensaje)
    palabras = n.split()
    mejor = None
    mejor_score = 0.6
    for intent, claves in INTENTS.items():
        for clave in claves:
            score = difflib.SequenceMatcher(None, n, clave).ratio()
            if score > mejor_score:
                mejor_score = score
                mejor = intent
    return mejor


def crear_sesion(db: Session, usuario_id=None) -> models.SesionChat:
    s = models.SesionChat(usuario_id=usuario_id, titulo="Chat asistente")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def guardar_mensaje(db: Session, sesion_id: int, rol: str, contenido: str) -> models.MensajeChat:
    m = models.MensajeChat(sesion_id=sesion_id, rol=rol, contenido=contenido)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def cambiar_titulo_si_necesario(db: Session, sesion_id: int, contenido: str) -> None:
    s = db.query(models.SesionChat).get(sesion_id)
    if s and s.titulo == "Chat asistente":
        s.titulo = contenido[:45]
        db.commit()
