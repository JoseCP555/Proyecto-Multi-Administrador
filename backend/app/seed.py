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
