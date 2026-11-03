"""Poblado inicial de datos reales para la demo (roles, admin, propiedades, finanzas, etc.)."""
from datetime import datetime, date, timedelta
import random

from sqlalchemy.orm import Session

from app.models import (
    Rol, Usuario, Residente, Propiedad, ConceptoFinanciero,
    MovimientoFinanciero, TareaMantenimiento, Documento, Evento,
    Configuracion,
)
from app.security import hashear_password


def _del_days(d: int) -> date:
    return date.today() - timedelta(days=d)


def ejecutar_seed(db: Session) -> None:
    """Solo inserta los datos de demo si aún no existe el usuario administrador
    (idempotente). Reutiliza los roles ya creados por db/init.sql."""
    if db.query(Usuario).filter(Usuario.correo == "admin@multiadmin.com").first():
        return

    # ---- Roles: usar los ya existentes o crearlos si faltan ---------------
    nombres_roles = ["super_admin", "admin", "residente", "tesoreria", "seguridad"]
    roles = {}
    for nombre in nombres_roles:
        rol = db.query(Rol).filter(Rol.nombre == nombre).first()
        if not rol:
            rol = Rol(nombre=nombre)
            db.add(rol)
            db.flush()
        roles[nombre] = rol

    # ---- Usuario administrador por defecto --------------------------------
    admin_rol = roles["super_admin"]  # la cuenta sembrada es el super administrador del sistema
    super_admin = Usuario(
        nombre="Super Administrador",
        telefono="3001234567",
        correo="admin@multiadmin.com",
        contrasena_hash=hashear_password("Admin2026!"),
        rol_id=admin_rol.id,
        activo=True,
        correo_verificado=True,
        fecha_creacion=datetime.utcnow(),
    )
    db.add(super_admin)
    db.flush()

    # ---- Datos de ejemplo (residentes + propiedades) -----------------------
    nombres = [
        ("Isabella Olivares", "propietario"), ("Sayeth Medina", "inquilino"),
        ("Kristian Luna", "propietario"), ("Jose Caicedo", "inquilino"),
        ("Laura Rodríguez", "propietario"), ("Carlos Pérez", "propietario"),
    ]
    residentes = []
    for i, (nombre, tipo) in enumerate(nombres, start=1):
        res = Residente(
            tipo=tipo,
            identificacion=f"CC-{1000000000 + i * 34567}",
            telefono_adicional=f"3{i}0{i}8{i}7{i}6",
            contacto_emergencia=f"Familiar de {nombre}",
            telefono_emergencia="3105550101",
            activo=True,
            fecha_creacion=datetime.utcnow(),
        )
        db.add(res)
        residentes.append(res)
    db.flush()

    bloques = ["A", "B", "C"]
    torres = ["T1", "T2"]
    propiedades = []
    idx = 0
    estados = ["ocupado", "ocupado", "ocupado", "ocupado", "vacio", "mantenimiento"]
    for bloque in bloques:
        for torre in torres:
            apto = f"{bloque}-{torre}-{101 + idx}"
            prop = Propiedad(
                bloque=bloque, torre=torre, apartamento=apto,
                piso=1 + (idx % 5), area=random.choice([55, 68, 82, 96, 120]),
                habitaciones=random.choice([2, 3, 4]),
                banos=random.choice([1, 2]),
                parqueaderos=random.choice([0, 1]),
                estado=estados[idx % len(estados)],
                estrato=random.choice([2, 3, 4]),
                residente_id=residentes[idx % len(residentes)].id,
                fecha_creacion=datetime.utcnow(),
            )
            db.add(prop)
            propiedades.append(prop)
            idx += 1
    db.flush()

    # ---- Conceptos financieros --------------------------------------------
    conceptos = [
        ConceptoFinanciero(codigo="ADM_FEE", nombre="Cuota de Administración", tipo="ingreso", monto_default=150000, recurrente=True, descripcion="Cuota mensual de administración"),
        ConceptoFinanciero(codigo="EXTRA", nombre="Gastos Extraordinarios", tipo="ingreso", monto_default=0, recurrente=False, descripcion="Aportes para imprevistos"),
        ConceptoFinanciero(codigo="PARKING", nombre="Parqueadero", tipo="ingreso", monto_default=50000, recurrente=True, descripcion="Alquiler de parqueadero"),
        ConceptoFinanciero(codigo="MAINT", nombre="Mantenimiento General", tipo="gasto", monto_default=0, recurrente=False, descripcion="Gastos en reparaciones"),
        ConceptoFinanciero(codigo="SERV", nombre="Servicios Comunes", tipo="gasto", monto_default=0, recurrente=False, descripcion="Energía, aseo, vigilancia"),
    ]
    db.add_all(conceptos)
    db.flush()

    # ---- Movimientos financieros (historial de 6 meses) --------------------
    concepto_adm = conceptos[0]
    concepto_parking = conceptos[2]
    concepto_maint = conceptos[3]
    concepto_serv = conceptos[4]

    estados_pago = ["pagado", "pagado", "pagado", "pendiente", "vencido"]
    for prop in propiedades:
        for mes in range(6, 0, -1):
            venc = date.today().replace(day=1) - timedelta(days=30 * mes)
            # Cuota de administración
            # Meses más antiguos suelen estar pagados; los recientes varían.
            estado = random.choice(estados_pago if mes < 2 else ["pagado", "pagado", "pagado", "vencido"])
            pago = venc + timedelta(days=random.randint(0, 8)) if estado in ("pagado",) else None
            db.add(MovimientoFinanciero(
                propiedad_id=prop.id, concepto_id=concepto_adm.id,
                monto=150000, fecha_vencimiento=venc, fecha_pago=pago,
                estado=estado, numero_recibo=f"REC-{prop.id}-{mes}",
                metodo_pago="transferencia" if estado == "pagado" else None,
                fecha_creacion=datetime.utcnow(),
            ))
            # Parqueadero (a veces)
            if prop.parqueaderos and mes % 2 == 0:
                db.add(MovimientoFinanciero(
                    propiedad_id=prop.id, concepto_id=concepto_parking.id,
                    monto=50000, fecha_vencimiento=venc,
                    fecha_pago=pago, estado=estado,
                    numero_recibo=f"RECP-{prop.id}-{mes}",
                    metodo_pago="transferencia" if estado == "pagado" else None,
                    fecha_creacion=datetime.utcnow(),
                ))
    # Gastos del conjunto (mensuales)
    for mes in range(6, 0, -1):
        venc = date.today().replace(day=1) - timedelta(days=30 * mes)
        db.add(MovimientoFinanciero(
            concepto_id=concepto_maint.id, monto=random.choice([420000, 510000, 380000]),
            fecha_vencimiento=venc, fecha_pago=venc + timedelta(days=3),
            estado="pagado", numero_recibo=f"G-MAINT-{mes}",
            metodo_pago="transferencia", fecha_creacion=datetime.utcnow(),
        ))
        db.add(MovimientoFinanciero(
            concepto_id=concepto_serv.id, monto=random.choice([280000, 310000, 260000]),
            fecha_vencimiento=venc, fecha_pago=venc + timedelta(days=5),
            estado="pagado", numero_recibo=f"G-SERV-{mes}",
            metodo_pago="transferencia", fecha_creacion=datetime.utcnow(),
        ))
    db.flush()

    # ---- Mantenimiento -----------------------------------------------------
    tareas = [
        ("Reparación de portería", "El sensor de la portería principal falla.", "alta"),
        ("Fumigación zonas comunes", "Programar fumigación trimestral.", "media"),
        ("Cambio de luminarias", "Reemplazar luminarias del pasillo B.", "media"),
        ("Ascensor T2 fuera de servicio", "El ascensor de la torre 2 necesita revisión.", "critica"),
        ("Pintura de fachada", "Retoque de pintura en la entrada.", "baja"),
        ("Revisión de bombas", "Mantenimiento preventivo del sistema de bombas.", "alta"),
    ]
    for i, (titulo, desc, prio) in enumerate(tareas):
        prop = propiedades[i % len(propiedades)]
        db.add(TareaMantenimiento(
            propiedad_id=prop.id, residente_id=residentes[i % len(residentes)].id,
            titulo=titulo, descripcion=desc, prioridad=prio,
            estado="pendiente" if i < 4 else "completada",
            asignado_a=super_admin.id if i % 2 else None,
            costo_estimado=random.choice([80000, 150000, 300000]),
            fecha_programada=date.today() + timedelta(days=i + 1),
            fecha_completada=datetime.utcnow() if i >= 4 else None,
            fecha_creacion=_del_days(i + 2),
        ))
    db.flush()

    # ---- Documentos --------------------------------------------------------
    docs = [
        ("Reglamento Interno", "Reglamento de convivencia del conjunto.", "reglamento", True),
        ("Acta de Asamblea 2026", "Acta de la asamblea general de propietarios.", "acta", True),
        ("Manual de Convivencia", "Normas de convivencia y uso de zonas comunes.", "manual", True),
        ("Presupuesto Anual", "Presupuesto de ingresos y gastos del año.", "financiero", False),
        ("Contrato de Seguridad", "Contrato vigente con la empresa de vigilancia.", "contrato", False),
    ]
    for i, (tit, desc, tipo, publico) in enumerate(docs):
        db.add(Documento(
            titulo=tit, descripcion=desc, ruta_archivo=f"/archivos/{i + 1}.pdf",
            tipo_documento=tipo, mime="application/pdf", tamano=random.randint(120000, 900000),
            subido_por=super_admin.id, publico=publico, version=1,
            fecha_creacion=_del_days(i + 1),
        ))
    db.flush()

    # ---- Eventos -----------------------------------------------------------
    eventos = [
        ("Reunión de copropiedad", "Asamblea ordinaria de propietarios.", date.today() + timedelta(days=7), "Salón comunal"),
        ("Feria de servicios", "Jornada de servicios para residentes.", date.today() + timedelta(days=14), "Parqueadero"),
        ("Mantenimiento de piscina", "Cierre temporal por mantenimiento.", date.today() + timedelta(days=3), "Piscina"),
    ]
    for tit, desc, fecha, lugar in eventos:
        db.add(Evento(titulo=tit, descripcion=desc, fecha=fecha, lugar=lugar, creado_por=super_admin.id))
    db.flush()

    # ---- Configuración -----------------------------------------------------
    configs = [
        ("company_name", "Multi-Administrador S.A.S.", "Nombre de la empresa admin"),
        ("currency", "COP", "Moneda (pesos colombianos)"),
        ("interest_rate_late", "0.02", "Interés mensual por mora"),
        ("chatbot_engine", "local", "Motor del chatbot (local o llm)"),
    ]
    for clave, valor, desc in configs:
        db.add(Configuracion(clave=clave, valor=valor, descripcion=desc))

    db.commit()


# ===========================================================================
# MULTI-CONJUNTO (HU-07): conjuntos de demostración + datos por conjunto
# ===========================================================================
# Conjuntos que se muestran en el "Panel Multi-Administrador". Coinciden con
# la maqueta funcional: nombre, dirección, teléfono, habitantes, correo,
# administrador, cuota, día de cobro y reglas propias de cada uno.
CONJUNTOS_DEMO = [
    dict(
        nombre="Conjunto Residencial Los Pinos",
        nit="900.123.456-1",
        direccion="Cra 15 #45-67",
        ciudad="Bogotá",
        telefono="(+57) 601 555 0101",
        correo="admin@lospinos.com",
        administrador="Carlos Ramírez",
        habitantes=248,
        cuota=180000,
        dia_cobro=5,
        reunion="solo propietarios",
        silencio="22:00 - 06:00",
    ),
    dict(
        nombre="Edificio Altos del Parque",
        nit="900.234.567-2",
        direccion="Calle 82 #12-34",
        ciudad="Chapinero",
        telefono="(+57) 601 555 0202",
        correo="administracion@altosdelparque.com",
        administrador="María Fernanda López",
        habitantes=186,
        cuota=240000,
        dia_cobro=10,
        reunion="todos los residentes",
        silencio="23:00 - 05:00",
    ),
    dict(
        nombre="Reservas de la Colina",
        nit="900.345.678-3",
        direccion="Av. Circunvalar #99-88",
        ciudad="Norte",
        telefono="(+57) 601 555 0303",
        correo="admin@reservasdelacolina.com",
        administrador="Andrés Felipe Murcia",
        habitantes=312,
        cuota=210000,
        dia_cobro=15,
        reunion="solo propietarios",
        silencio="22:30 - 06:30",
    ),
    dict(
        nombre="Torres de San Martín",
        nit="900.456.789-4",
        direccion="Cra 50 #23-11",
        ciudad="Teusaquillo",
        telefono="(+57) 601 555 0404",
        correo="gerencia@torressanmartin.com",
        administrador="Luz Dary Castañeda",
        habitantes=164,
        cuota=195000,
        dia_cobro=8,
        reunion="todos los residentes",
        silencio="23:00 - 06:00",
    ),
]

# Nombres distintos por conjunto para que los datos no se vean repetidos.
_RESIDENTES_DEMO = [
    [("Sofía Ramírez", "propietario"), ("Julián Cortés", "inquilino"),
     ("Mariana Vélez", "propietario"), ("Esteban Rincón", "propietario"),
     ("Valeria Nieto", "inquilino"), ("Tomás Herrera", "propietario"),
     ("Daniela Suárez", "propietario"), ("Emilio Pardo", "inquilino")],
    [("Camila Ortiz", "propietario"), ("Ricardo Salas", "propietario"),
     ("Paula Benítez", "inquilino"), ("Nicolás Ariza", "propietario"),
     ("Fernanda Rojas", "inquilino"), ("Mateo Beltrán", "propietario"),
     ("Isabella Cárdenas", "propietario")],
    [("Santiago Molina", "propietario"), ("Laura Espinosa", "propietario"),
     ("Diego Barrera", "inquilino"), ("Manuela Cardozo", "propietario"),
     ("Sebastián Lozano", "inquilino"), ("Gabriela Pinto", "propietario"),
     ("Andrea Quintero", "propietario"), ("Juan Pablo Cely", "inquilino")],
    [("Valentina Duarte", "propietario"), ("Cristian Acosta", "inquilino"),
     ("Natalia Franco", "propietario"), ("Óscar Beltrán", "propietario"),
     ("Laura Camacho", "inquilino"), ("Felipe Torres", "propietario")],
]

_TAREAS_DEMO = [
    ("Reparación de portería", "El sensor de la portería principal falla.", "alta"),
    ("Fumigación zonas comunes", "Programar fumigación trimestral.", "media"),
    ("Cambio de luminarias", "Reemplazar luminarias del pasillo B.", "media"),
    ("Ascensor fuera de servicio", "Revisión técnica del ascensor principal.", "critica"),
    ("Pintura de fachada", "Retoque de pintura en la entrada.", "baja"),
    ("Revisión de bombas", "Mantenimiento preventivo del sistema de bombeo.", "alta"),
]


def sembrar_conjuntos(db: Session) -> None:
    """Crea (si faltan) los conjuntos de demostración y puebla sus datos.

    Es idempotente: nunca duplica conjuntos ni datos, así que se puede
    ejecutar en cada arranque sobre bases nuevas o ya existentes.
    """
    from app.models import Conjunto

    creados = []
    for datos in CONJUNTOS_DEMO:
        c = db.query(Conjunto).filter(Conjunto.nombre == datos["nombre"]).first()
        if not c:
            c = Conjunto(**datos, activo=True, fecha_creacion=datetime.utcnow())
            db.add(c)
            db.flush()
            creados.append(c)
    db.commit()

    conjuntos = db.query(Conjunto).order_by(Conjunto.id).all()
    if not conjuntos:
        return

    # 0) Color: los conjuntos creados antes de esta función (o los de demo)
    #    reciben un color estable de la paleta. Los que ya tienen uno elegido
    #    por el usuario no se tocan.
    from app.colores import sugerir_color
    cambio_color = False
    for i, conjunto in enumerate(conjuntos):
        if getattr(conjunto, "color", None) is None:
            conjunto.color = sugerir_color(i)
            cambio_color = True
    if cambio_color:
        db.commit()

    # 1) Backfill: todo lo que aún no tiene conjunto pasa al primero, de modo
    #    que los datos creados antes de esta función sigan siendo visibles.
    from sqlalchemy import text
    primero = conjuntos[0].id
    for tabla in ("residentes", "propiedades", "movimientos_financieros",
                  "tareas_mantenimiento", "documentos", "eventos", "sesiones_chat"):
        try:
            db.execute(text(f"UPDATE {tabla} SET id_conjunto = :c WHERE id_conjunto IS NULL"), {"c": primero})
        except Exception:  # noqa: BLE001 - columna inexistente, BD rara, etc.
            db.rollback()
    try:
        db.execute(text("UPDATE usuarios SET id_conjunto = :c WHERE id_conjunto IS NULL"), {"c": primero})
    except Exception:  # noqa: BLE001
        db.rollback()
    db.commit()

    # 2) Asignación explícita: los usuarios que aún no pertenecen a ningún
    #    conjunto quedan en el primero (el super_admin ve todos por su rol).
    from app.models import UsuarioConjunto
    for u in db.query(Usuario).all():
        if u.rol_id == 1:  # super_admin: acceso total, no necesita filas
            continue
        if not db.query(UsuarioConjunto).filter(UsuarioConjunto.usuario_id == u.id).first():
            db.add(UsuarioConjunto(usuario_id=u.id, conjunto_id=primero))
        if getattr(u, "id_conjunto", None) is None:
            u.id_conjunto = primero
    db.commit()

    # 3) Datos de demo por conjunto (solo si el conjunto está vacío).
    admin = db.query(Usuario).filter(Usuario.correo == "admin@multiadmin.com").first()
    for i, conjunto in enumerate(conjuntos):
        if db.query(Propiedad).filter(Propiedad.id_conjunto == conjunto.id).count():
            continue
        _sembrar_datos_conjunto(db, conjunto, admin, indice=i)


def _sembrar_datos_conjunto(db: Session, conjunto, admin, indice: int) -> None:
    """Propiedades, residentes, finanzas, mantenimientos, documentos y eventos
    propios de un conjunto."""
    random.seed(1000 + indice)
    cid = conjunto.id

    residentes = []
    for j, (nombre, tipo) in enumerate(_RESIDENTES_DEMO[indice % len(_RESIDENTES_DEMO)], start=1):
        r = Residente(
            tipo=tipo,
            identificacion=f"CC-{1000000000 + cid * 7919 + j * 104729}",
            telefono_adicional=f"3{cid}0{j}8{j}7{j}6",
            contacto_emergencia=f"Familiar de {nombre}",
            telefono_emergencia="3105550101",
            activo=True,
            id_conjunto=cid,
            fecha_creacion=datetime.utcnow(),
        )
        db.add(r)
        residentes.append(r)
    db.flush()

    bloques = ["A", "B", "C"]
    torres = ["T1", "T2"]
    estados = ["ocupado", "ocupado", "ocupado", "ocupado", "vacio", "mantenimiento"]
    propiedades = []
    idx = 0
    for bloque in bloques:
        for torre in torres:
            prop = Propiedad(
                residencial=conjunto.nombre,
                bloque=bloque, torre=torre,
                apartamento=f"{bloque}-{torre}-{101 + idx}",
                piso=1 + (idx % 5),
                area=random.choice([55, 68, 82, 96, 120]),
                habitaciones=random.choice([2, 3, 4]),
                banos=random.choice([1, 2]),
                parqueaderos=random.choice([0, 1]),
                estado=estados[idx % len(estados)],
                estrato=random.choice([2, 3, 4, 5]),
                residente_id=residentes[idx % len(residentes)].id,
                id_conjunto=cid,
                fecha_creacion=datetime.utcnow(),
            )
            db.add(prop)
            propiedades.append(prop)
            idx += 1
    db.flush()

    # Conceptos financieros (globales; se reutilizan si ya existen).
    def concepto(codigo, nombre, tipo, monto):
        c = db.query(ConceptoFinanciero).filter(ConceptoFinanciero.codigo == codigo).first()
        if not c:
            c = ConceptoFinanciero(codigo=codigo, nombre=nombre, tipo=tipo,
                                   monto_default=monto, recurrente=True,
                                   descripcion=f"{nombre} ({conjunto.nombre})")
            db.add(c)
            db.flush()
        return c

    c_adm = concepto("ADM_FEE", "Cuota de Administración", "ingreso", float(conjunto.cuota or 150000))
    c_extra = concepto("EXTRA", "Gastos Extraordinarios", "ingreso", 0)
    c_parqueo = concepto("PARKING", "Parqueadero", "ingreso", 50000)
    c_mant = concepto("MAINT", "Mantenimiento General", "gasto", 0)
    c_serv = concepto("SERV", "Servicios Comunes", "gasto", 0)

    cuota = float(conjunto.cuota or 150000)
    estados_pago = ["pagado", "pagado", "pagado", "pendiente", "vencido"]
    for prop in propiedades:
        for mes in range(6, 0, -1):
            venc = date.today().replace(day=1) - timedelta(days=30 * mes)
            estado = random.choice(estados_pago if mes < 3 else ["pagado", "pagado", "pagado", "vencido"])
            pago = venc + timedelta(days=random.randint(0, 8)) if estado == "pagado" else None
            db.add(MovimientoFinanciero(
                propiedad_id=prop.id, concepto_id=c_adm.id, monto=cuota,
                fecha_vencimiento=venc, fecha_pago=pago, estado=estado,
                numero_recibo=f"REC-{cid}-{prop.id}-{mes}",
                metodo_pago="transferencia" if estado == "pagado" else None,
                id_conjunto=cid, fecha_creacion=datetime.utcnow(),
            ))
            if prop.parqueaderos and mes % 2 == 0:
                db.add(MovimientoFinanciero(
                    propiedad_id=prop.id, concepto_id=c_parqueo.id, monto=50000,
                    fecha_vencimiento=venc, fecha_pago=pago, estado=estado,
                    numero_recibo=f"RECP-{cid}-{prop.id}-{mes}",
                    metodo_pago="transferencia" if estado == "pagado" else None,
                    id_conjunto=cid, fecha_creacion=datetime.utcnow(),
                ))
    for mes in range(6, 0, -1):
        venc = date.today().replace(day=1) - timedelta(days=30 * mes)
        db.add(MovimientoFinanciero(
            concepto_id=c_mant.id,
            monto=random.choice([320000, 410000, 280000]) + cid * 1000,
            fecha_vencimiento=venc, fecha_pago=venc + timedelta(days=3),
            estado="pagado", numero_recibo=f"G-MAINT-{cid}-{mes}",
            metodo_pago="transferencia", id_conjunto=cid,
            fecha_creacion=datetime.utcnow(),
        ))
        db.add(MovimientoFinanciero(
            concepto_id=c_serv.id,
            monto=random.choice([180000, 210000, 160000]) + cid * 1000,
            fecha_vencimiento=venc, fecha_pago=venc + timedelta(days=5),
            estado="pagado", numero_recibo=f"G-SERV-{cid}-{mes}",
            metodo_pago="transferencia", id_conjunto=cid,
            fecha_creacion=datetime.utcnow(),
        ))
    db.flush()

    for i, (titulo, desc, prio) in enumerate(_TAREAS_DEMO):
        db.add(TareaMantenimiento(
            propiedad_id=propiedades[i % len(propiedades)].id,
            residente_id=residentes[i % len(residentes)].id,
            titulo=titulo, descripcion=desc, prioridad=prio,
            estado="pendiente" if i < 4 else "completada",
            asignado_a=admin.id if (admin and i % 2) else None,
            costo_estimado=random.choice([80000, 150000, 300000]),
            fecha_programada=date.today() + timedelta(days=i + 1),
            fecha_completada=datetime.utcnow() if i >= 4 else None,
            id_conjunto=cid, fecha_creacion=_del_days(i + 2),
        ))
    db.flush()

    docs = [
        ("Reglamento Interno", "Reglamento de convivencia del conjunto.", "reglamento", True),
        (f"Acta de Asamblea 2026", "Acta de la asamblea general de propietarios.", "acta", True),
        ("Manual de Convivencia", "Normas de uso de zonas comunes.", "manual", True),
        ("Presupuesto Anual", "Presupuesto de ingresos y gastos del año.", "financiero", False),
    ]
    for i, (tit, desc, tipo, publico) in enumerate(docs):
        db.add(Documento(
            titulo=tit, descripcion=desc, ruta_archivo=f"/archivos/{cid}-{i + 1}.pdf",
            tipo_documento=tipo, mime="application/pdf",
            tamano=random.randint(120000, 900000),
            subido_por=admin.id if admin else None, publico=publico, version=1,
            id_conjunto=cid, fecha_creacion=_del_days(i + 1),
        ))
    db.flush()

    eventos = [
        ("Reunión de copropiedad", "Asamblea ordinaria de propietarios.", date.today() + timedelta(days=7), "Salón comunal"),
        ("Jornada de mantenimiento", "Mantenimiento preventivo de zonas comunes.", date.today() + timedelta(days=3), "Zonas comunes"),
        ("Feria de servicios", "Jornada de servicios para residentes.", date.today() + timedelta(days=14), "Parqueadero"),
    ]
    for tit, desc, fecha, lugar in eventos:
        db.add(Evento(
            titulo=tit, descripcion=desc, fecha=fecha, lugar=lugar,
            creado_por=admin.id if admin else None, id_conjunto=cid,
        ))
    db.commit()
