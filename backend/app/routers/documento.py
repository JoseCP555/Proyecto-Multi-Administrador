"""Gestión documental: CRUD + subida y descarga real de archivos."""
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape
import os
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app import schemas
from app import notificaciones_servicio as notif
from app.models import Conjunto, Documento
from app.database import get_db
from app.deps import require_permiso, get_current_user
from app.conjunto_ctx import conjunto_activo, filtrar, ids_conjuntos_usuario, ve_todos_los_conjuntos

router = APIRouter(prefix="/documentos", tags=["Documentos"], dependencies=[Depends(require_permiso("documentos.ver"))])

# Carpeta donde se guardan los archivos subidos.
ARCHIVOS_DIR = os.getenv("ARCHIVOS_DIR", "./archivos_documentos")
os.makedirs(ARCHIVOS_DIR, exist_ok=True)

# UH-03: se permiten archivos PDF y Word de hasta 20 MB.
MAX_BYTES = 20 * 1024 * 1024
EXTENSIONES_PERMITIDAS = {
    ".pdf", ".doc", ".docx",           # PDF y Word (criterio de la HU-03)
    ".xls", ".xlsx", ".ppt", ".pptx",  # otras actas/anexos ofimáticos
    ".png", ".jpg", ".jpeg",           # fotos de actas escaneadas
    ".txt", ".csv",
}

TIPO_POR_EXT = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
    ".csv": "text/csv",
}

EXT_POR_MIME = {v: k for k, v in TIPO_POR_EXT.items()}


def _dinero(v) -> str:
    return f"${float(v or 0):,.0f}".replace(",", ".")


def _resolver_ruta_fisica(d: Documento) -> str | None:
    """Busca el archivo físico del documento en disco (en ARCHIVOS_DIR o ruta absoluta)."""
    cruda = (d.ruta_archivo or "").strip()
    if not cruda:
        return None
    candidatos = [os.path.join(ARCHIVOS_DIR, os.path.basename(cruda))]
    if os.path.isabs(cruda):
        candidatos.append(cruda)
    for ruta in candidatos:
        if os.path.isfile(ruta):
            return ruta
    return None


def _nombre_descarga(d: Documento, ruta: str) -> str:
    """Genera un nombre de archivo seguro con la extensión real del documento."""
    base = re.sub(r'[\\/:*?"<>|\r\n]+', " ", (d.titulo or f"documento-{d.id}")).strip() or f"documento-{d.id}"
    ext_ruta = os.path.splitext(ruta)[1].lower()
    ext_mime = EXT_POR_MIME.get((d.mime or "").lower(), "")
    ext = ext_ruta or ext_mime or ".pdf"
    if not base.lower().endswith(ext):
        base = f"{base}{ext}"
    return base


def _secciones_por_tipo(d: Documento, conjunto: Conjunto | None) -> list[tuple[str, list[str]]]:
    """Contenido estructurado en español para generar el PDF oficial del documento."""
    nombre_c = conjunto.nombre if conjunto else "Multi-Administrador"
    cuota = _dinero(conjunto.cuota) if conjunto and conjunto.cuota else "$180.000"
    dia_cobro = f"día {conjunto.dia_cobro}" if conjunto and conjunto.dia_cobro else "primeros 5 días"
    silencio = (conjunto.silencio if conjunto and conjunto.silencio else "22:00 - 06:00")
    reunion = (conjunto.reunion if conjunto and conjunto.reunion else "todos los residentes")
    admin_nom = (conjunto.administrador if conjunto and conjunto.administrador else "Administración General")
    habitantes = (conjunto.habitantes if conjunto and conjunto.habitantes else 200)

    tipo = (d.tipo_documento or "").strip().lower()
    if tipo == "reglamento":
        return [
            ("1. Objeto y alcance", [
                f"El presente Reglamento Interno rige la convivencia, uso de bienes comunes y obligaciones de propietarios, arrendatarios y visitantes de {nombre_c}.",
                f"Toda reforma a este reglamento debe ser aprobada en Asamblea General de Copropietarios ({reunion}).",
            ]),
            ("2. Horarios de silencio y convivencia", [
                f"Horario oficial de silencio y descanso: {silencio}. Durante esta franja se prohíben ruidos, música a alto volumen o remodelaciones.",
                "Las mascotas deben transitar con correa en pasillos, ascensores y zonas comunes, recogiendo siempre sus desechos.",
                "Los residuos deben depositarse debidamente separados en el cuarto de basuras en los horarios establecidos.",
            ]),
            ("3. Cuotas de administración y uso de áreas comunes", [
                f"La cuota ordinaria base vigente es de {cuota}, con fecha de corte el {dia_cobro} de cada mes.",
                "El uso de salón comunal, BBQ y zonas recreativas requiere reserva previa a través de la plataforma Multi-Administrador.",
            ]),
        ]
    if tipo == "acta":
        return [
            ("1. Instalación y verificación de quórum", [
                f"En la sede de {nombre_c}, se reunió la Asamblea General ({reunion}) con representación válida conforme a la Ley 675 de 2001.",
                f"Presidió la sesión la administración a cargo de {admin_nom}, con un censo registrado de {habitantes} habitantes.",
            ]),
            ("2. Orden del día y decisiones aprobadas", [
                "Aprobación del informe de gestión administrativa y estados financieros del periodo.",
                f"Ratificación de la cuota ordinaria de administración ({cuota}, cobro el {dia_cobro} de cada mes) y plan de mantenimiento preventivo.",
                "Autorización de mejoras prioritarias en zonas comunes, ascensores, luminarias y sistema de bombeo.",
            ]),
            ("3. Cierre y constancia", [
                "Sin más asuntos por tratar, se levanta la sesión y se publica esta acta oficial en la biblioteca digital de Multi-Administrador para consulta de la copropiedad.",
            ]),
        ]
    if tipo == "manual":
        return [
            ("1. Principios de sana convivencia", [
                f"Este Manual de Convivencia promueve el respeto mutuo, la seguridad y el cuidado de las instalaciones de {nombre_c}.",
                f"Horario de silencio vigente: {silencio}. Los trabajos locativos solo se autorizan en jornada diurna hábil.",
            ]),
            ("2. Uso de zonas comunes y parqueaderos", [
                "Las reservas de salón comunal, BBQ, piscina y canchas deben gestionarse desde el módulo Reservas de la plataforma.",
                "Los parqueaderos de visitantes son de uso temporal y requieren registro obligatorio en portería.",
            ]),
            ("3. Canales de atención y PQRS", [
                "Cualquier petición, queja, reclamo o sugerencia puede radicarse en el módulo PQRS o mediante el Chat directo con Administración.",
            ]),
        ]
    if tipo == "financiero":
        return [
            ("1. Resumen presupuestal", [
                f"Presupuesto anual de ingresos y egresos proyectado para {nombre_c}.",
                f"Cuota ordinaria base de administración: {cuota} mensuales (fecha de cobro: {dia_cobro} de cada mes).",
            ]),
            ("2. Rubros principales de ejecución", [
                "Servicios de vigilancia 24/7, aseo y mantenimiento de zonas comunes.",
                "Mantenimiento preventivo y correctivo de ascensores, motobombas, luminarias y áreas recreativas.",
                "Fondo de imprevistos conforme a la normativa de propiedad horizontal vigente.",
            ]),
            ("3. Seguimiento y transparencia", [
                "Los estados financieros detallados y reportes mensuales están disponibles para revisión del Consejo de Administración y copropietarios autorizados.",
            ]),
        ]
    if tipo == "contrato":
        return [
            ("1. Objeto contractual", [
                f"Contrato de prestación de servicios suscrito por {nombre_c} para garantizar la operación continua y segura de la copropiedad.",
                f"Supervisión administrativa a cargo de {admin_nom}.",
            ]),
            ("2. Obligaciones y niveles de servicio", [
                "Cumplimiento permanente de protocolos de control de acceso, rondas preventivas y reporte inmediato de novedades en plataforma.",
                "Personal debidamente acreditado, afiliado a seguridad social y con dotación vigente.",
            ]),
            ("3. Vigencia y archivo", [
                "Este documento reposa en el archivo digital oficial de la administración para control del Consejo y auditoría.",
            ]),
        ]
    return [
        ("Contenido del documento", [
            d.descripcion or f"Documento oficial registrado en la biblioteca digital de {nombre_c}.",
            "Disponible para descarga y consulta desde la plataforma Multi-Administrador.",
        ]),
    ]


def generar_pdf_documento(db: Session, d: Documento) -> str:
    """Genera un PDF real en ARCHIVOS_DIR para documentos sin archivo físico en disco."""
    os.makedirs(ARCHIVOS_DIR, exist_ok=True)
    nombre_archivo = f"doc_{d.id}.pdf"
    destino = os.path.join(ARCHIVOS_DIR, nombre_archivo)

    conjunto = db.query(Conjunto).get(d.id_conjunto) if d.id_conjunto else None
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "DocTitulo", parent=estilos["Heading1"], fontSize=18, leading=22,
        textColor=colors.HexColor("#0F172A"), spaceAfter=4,
    )
    estilo_sub = ParagraphStyle(
        "DocSub", parent=estilos["Normal"], fontSize=10, leading=14,
        textColor=colors.HexColor("#475569"), spaceAfter=10,
    )
    estilo_h2 = ParagraphStyle(
        "DocH2", parent=estilos["Heading2"], fontSize=12, leading=16,
        textColor=colors.HexColor("#1D4ED8"), spaceBefore=10, spaceAfter=4,
    )
    estilo_body = ParagraphStyle(
        "DocBody", parent=estilos["Normal"], fontSize=10, leading=15,
        textColor=colors.HexColor("#1E293B"), spaceAfter=6,
    )
    estilo_pie = ParagraphStyle(
        "DocPie", parent=estilos["Normal"], fontSize=8.5, leading=12,
        textColor=colors.HexColor("#64748B"), spaceBefore=16,
    )

    pdf = SimpleDocTemplate(
        destino, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
        title=d.titulo or "Documento",
        author="Multi-Administrador",
    )

    elementos = []
    # Encabezado institucional
    nombre_c = conjunto.nombre if conjunto else "Multi-Administrador"
    encabezado = Table(
        [[
            Paragraph(
                f"<b><font color='#FFFFFF' size='13'>Multi-Administrador</font></b><br/>"
                f"<font color='#DBEAFE' size='9'>{xml_escape(nombre_c)}</font>",
                estilos["Normal"],
            ),
            Paragraph(
                f"<font color='#FFFFFF' size='9'><b>{(d.tipo_documento or 'Documento').upper()}</b><br/>"
                f"Versión {d.version or 1}</font>",
                ParagraphStyle("EncDer", parent=estilos["Normal"], alignment=2),
            ),
        ]],
        colWidths=[125 * mm, 45 * mm],
    )
    encabezado.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1D4ED8")),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elementos.append(encabezado)
    elementos.append(Spacer(1, 10))

    # Título y descripción
    elementos.append(Paragraph(xml_escape(d.titulo or "Documento"), estilo_titulo))
    if d.descripcion:
        elementos.append(Paragraph(xml_escape(d.descripcion), estilo_sub))

    # Ficha técnica
    fecha_txt = d.fecha_creacion.strftime("%d/%m/%Y") if d.fecha_creacion else datetime.utcnow().strftime("%d/%m/%Y")
    filas_meta = [
        ["Conjunto", nombre_c, "Fecha", fecha_txt],
        [
            "Categoría", (d.tipo_documento or "General").capitalize(),
            "Visibilidad", "Público" if d.publico else "Privado",
        ],
    ]
    if conjunto:
        filas_meta.append([
            "Dirección", f"{conjunto.direccion or '—'}" + (f", {conjunto.ciudad}" if conjunto.ciudad else ""),
            "Administrador", conjunto.administrador or "—",
        ])
        if conjunto.nit or conjunto.correo:
            filas_meta.append([
                "NIT", conjunto.nit or "—",
                "Contacto", conjunto.correo or conjunto.telefono or "—",
            ])

    tabla_meta = Table(filas_meta, colWidths=[28 * mm, 67 * mm, 28 * mm, 47 * mm])
    tabla_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#475569")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabla_meta)
    elementos.append(Spacer(1, 8))

    # Secciones de contenido
    for titulo_sec, parrafos in _secciones_por_tipo(d, conjunto):
        elementos.append(Paragraph(xml_escape(titulo_sec), estilo_h2))
        for p in parrafos:
            elementos.append(Paragraph(f"• {xml_escape(p)}", estilo_body))

    elementos.append(
        Paragraph(
            f"Documento oficial generado y almacenado por Multi-Administrador · ID #{d.id}.",
            estilo_pie,
        )
    )

    pdf.build(elementos)

    d.ruta_archivo = nombre_archivo
    d.mime = "application/pdf"
    d.tamano = os.path.getsize(destino)
    db.commit()
    return destino


def asegurar_archivos_documentos(db: Session) -> int:
    """Garantiza que todos los documentos registrados tengan un archivo real descargable."""
    generados = 0
    for d in db.query(Documento).all():
        if _resolver_ruta_fisica(d) is None:
            generar_pdf_documento(db, d)
            generados += 1
    return generados


@router.get("", response_model=list[schemas.DocumentoResponse])
def listar(
    categoria: str | None = None,
    orden: str | None = None,
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
):
    """Lista los documentos del conjunto, filtrables por categoría y ordenables por fecha (UH-19)."""
    from sqlalchemy import func

    q = filtrar(db.query(Documento), Documento, cid)
    if categoria and categoria.strip().lower() not in ("", "todas", "todos", "all"):
        q = q.filter(func.lower(Documento.tipo_documento) == categoria.strip().lower())
    if orden == "fecha_asc":
        q = q.order_by(Documento.fecha_creacion.asc())
    elif orden == "categoria":
        q = q.order_by(Documento.tipo_documento.asc(), Documento.fecha_creacion.desc())
    else:
        q = q.order_by(Documento.fecha_creacion.desc())
    return q.all()


@router.get("/{documento_id}/descargar", dependencies=[Depends(require_permiso("documentos.descargar"))])
def descargar(
    documento_id: int,
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
    usuario=Depends(get_current_user),
):
    """Descarga el archivo físico asociado al documento.

    Si el documento existe en BD pero corresponde a un registro semilla o sin
    archivo físico en disco, genera automáticamente su PDF oficial para que
    todos los documentos sean siempre descargables.
    """
    d = db.query(Documento).get(documento_id)
    if not d:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    # Verificar acceso al conjunto del documento
    if d.id_conjunto is not None:
        permitidos = ids_conjuntos_usuario(db, usuario)
        if not ve_todos_los_conjuntos(db, usuario) and d.id_conjunto not in permitidos:
            raise HTTPException(status_code=404, detail="Documento no encontrado.")
        if cid is not None and d.id_conjunto != cid and d.id_conjunto not in permitidos:
            raise HTTPException(status_code=404, detail="Documento no encontrado.")

    ruta = _resolver_ruta_fisica(d)
    if ruta is None:
        ruta = generar_pdf_documento(db, d)

    return FileResponse(
        ruta,
        media_type=d.mime or "application/pdf",
        filename=_nombre_descarga(d, ruta),
    )


@router.post("", response_model=schemas.DocumentoResponse, status_code=201, dependencies=[Depends(require_permiso("documentos.crear"))])
def crear(data: schemas.DocumentoCreate, db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    d = Documento(
        titulo=data.titulo, descripcion=data.descripcion, ruta_archivo=data.ruta_archivo,
        tipo_documento=data.tipo_documento, mime=data.mime, tamano=data.tamano,
        propiedad_id=data.propiedad_id, publico=data.publico, id_conjunto=cid,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    notif.notificar_seguro(
        db=db, id_conjunto=cid, tipo="documento",
        titulo="Nuevo documento disponible",
        mensaje=f"Se publicó «{d.titulo}» en la biblioteca de documentos.",
        clave=f"creado:{d.id}",
    )
    return d


@router.post("/upload", response_model=schemas.DocumentoResponse, status_code=201, dependencies=[Depends(require_permiso("documentos.crear"))])
def subir(
    titulo: str = Form(...),
    descripcion: str = Form(None),
    tipo_documento: str = Form(None),
    publico: bool = Form(False),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
):
    """Recibe un archivo real, lo guarda en disco y registra el documento."""
    nombre_original = os.path.basename(archivo.filename or "documento")
    ext = os.path.splitext(nombre_original)[1].lower()

    # UH-03: solo PDF/Word (y anexos ofimáticos habituales) y como máximo 20 MB.
    if ext not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(
            status_code=415,
            detail="Formato no permitido. Sube un archivo PDF o Word (.pdf, .doc, .docx).",
        )

    nombre_guardado = f"{uuid.uuid4().hex}{ext}"
    destino = os.path.join(ARCHIVOS_DIR, nombre_guardado)

    # Escritura en trozos con corte a los 20 MB (no se carga el archivo en memoria).
    escrito = 0
    with open(destino, "wb") as out:
        while True:
            trozo = archivo.file.read(1024 * 1024)
            if not trozo:
                break
            escrito += len(trozo)
            if escrito > MAX_BYTES:
                out.close()
                try:
                    os.remove(destino)
                except OSError:
                    pass
                raise HTTPException(
                    status_code=413,
                    detail="El archivo supera el máximo de 20 MB permitido.",
                )
            out.write(trozo)

    tamano = os.path.getsize(destino)
    # si no se pasó título, usar el nombre original sin extensión
    titulo_final = titulo.strip() or os.path.splitext(nombre_original)[0]

    d = Documento(
        titulo=titulo_final,
        descripcion=descripcion,
        ruta_archivo=nombre_guardado,
        tipo_documento=tipo_documento,
        mime=archivo.content_type or TIPO_POR_EXT.get(ext, "application/octet-stream"),
        tamano=tamano,
        publico=publico,
        version=1,
        id_conjunto=cid,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    notif.notificar_seguro(
        db=db, id_conjunto=cid, tipo="documento",
        titulo="Nuevo documento disponible",
        mensaje=f"Se publicó «{d.titulo}» en la biblioteca de documentos.",
        clave=f"creado:{d.id}",
    )
    return d


@router.put("/{documento_id}", response_model=schemas.DocumentoResponse, dependencies=[Depends(require_permiso("documentos.editar"))])
def actualizar(documento_id: int, data: schemas.DocumentoCreate, db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    d = db.query(Documento).get(documento_id)
    if not d or (cid is not None and d.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    d.titulo = data.titulo
    d.descripcion = data.descripcion
    d.ruta_archivo = data.ruta_archivo
    d.tipo_documento = data.tipo_documento
    d.mime = data.mime
    d.tamano = data.tamano
    d.propiedad_id = data.propiedad_id
    d.publico = data.publico
    db.commit()
    db.refresh(d)
    return d


@router.delete("/{documento_id}", status_code=204, dependencies=[Depends(require_permiso("documentos.eliminar"))])
def eliminar(documento_id: int, db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    d = db.query(Documento).get(documento_id)
    if not d or (cid is not None and d.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    # Borrar el archivo físico si existe.
    ruta = _resolver_ruta_fisica(d)
    if ruta:
        try:
            os.remove(ruta)
        except OSError:
            pass
    db.delete(d)
    db.commit()
    return None
