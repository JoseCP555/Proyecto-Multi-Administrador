"""Diagnóstico de la base de datos de Multi-Administrador.

Comprueba, sobre la base que use el backend en este momento, que todo exista:

    cd backend
    python verificar_bd.py

Revisa:
  • Motor y destino (PostgreSQL o SQLite), y si hubo algún aviso.
  • Que estén las 18 tablas del modelo.
  • Que no falte ninguna columna respecto a app/models.py (lo que provoca
    errores tipo "column ... does not exist").
  • Conteo de filas por tabla.
  • Que exista el usuario administrador y que el RBAC esté sembrado.

Devuelve código 0 si todo está bien y 1 si encontró problemas.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import inspect  # noqa: E402

from app.database import (  # noqa: E402
    Base, engine, SessionLocal, MOTOR, AVISO_BD, DATABASE_URL_ENMASCARADA,
)
from app import models  # noqa: F401,E402  (registra los modelos)

LINEA = "=" * 68
problemas: list[str] = []
avisos: list[str] = []


def titulo(texto: str) -> None:
    print(f"\n{LINEA}\n{texto}\n{LINEA}")


def main() -> int:
    titulo("MULTI-ADMINISTRADOR · VERIFICACIÓN DE LA BASE DE DATOS")
    print(f"Motor   : {MOTOR}")
    print(f"Destino : {DATABASE_URL_ENMASCARADA}")
    if AVISO_BD:
        print(f"AVISO   : {AVISO_BD}")
        avisos.append(AVISO_BD)

    try:
        with engine.connect() as conn:
            inspector = inspect(conn)
            existentes = set(inspector.get_table_names())
    except Exception as exc:  # noqa: BLE001
        print(f"\n❌ No hay conexión con la base de datos: {exc}")
        return 1

    # Autorreparación idempotente: crea lo que falte (tablas rol/permisos/datos
    # base) exactamente igual que hace la API al arrancar. Así este script no
    # solo diagnostica: deja la base utilizable.
    try:
        Base.metadata.create_all(bind=engine)
        from app.permisos import sincronizar_permisos
        from app.seed import ejecutar_seed, sembrar_conjuntos

        db0 = SessionLocal()
        try:
            sincronizar_permisos(db0)
            ejecutar_seed(db0)
            sembrar_conjuntos(db0)
            db0.commit()
        finally:
            db0.close()
        print("Esquema y datos base asegurados (create_all + seed idempotente).")
        with engine.connect() as conn:
            existentes = set(inspect(conn).get_table_names())
    except Exception as exc:  # noqa: BLE001
        print(f"AVISO: no se pudo asegurar el esquema automáticamente: {exc}")

    titulo("1) TABLAS")
    esperadas = [t.name for t in Base.metadata.sorted_tables]
    faltantes = [t for t in esperadas if t not in existentes]
    for t in esperadas:
        print(f"  {'✔' if t in existentes else '✘'} {t}")
    if faltantes:
        problemas.append(f"Faltan tablas: {', '.join(faltantes)}")

    titulo("2) COLUMNAS")
    for tabla in Base.metadata.sorted_tables:
        if tabla.name not in existentes:
            continue
        reales = {c["name"] for c in inspect(engine).get_columns(tabla.name)}
        faltan = [c.name for c in tabla.columns if c.name not in reales]
        if faltan:
            problemas.append(f"{tabla.name}: faltan columnas {', '.join(faltan)}")
            print(f"  ✘ {tabla.name}: faltan {', '.join(faltan)}")
    if not any("faltan columnas" in p for p in problemas):
        print("  ✔ Todas las columnas del modelo existen")

    titulo("3) DATOS")
    db = SessionLocal()
    try:
        conteos = {
            "roles": db.query(models.Rol).count(),
            "permisos": db.query(models.Permiso).count(),
            "rol_permisos": db.query(models.RolPermiso).count(),
            "usuarios": db.query(models.Usuario).count(),
            "conjuntos": db.query(models.Conjunto).count(),
            "residentes": db.query(models.Residente).count(),
            "propiedades": db.query(models.Propiedad).count(),
            "movimientos_financieros": db.query(models.MovimientoFinanciero).count(),
            "tareas_mantenimiento": db.query(models.TareaMantenimiento).count(),
            "documentos": db.query(models.Documento).count(),
            "eventos": db.query(models.Evento).count(),
        }
        for tabla, n in conteos.items():
            print(f"  {tabla:<28} {n:>6}")
        if conteos["roles"] < 5:
            problemas.append("Faltan roles base (deben ser 5)")
        if conteos["permisos"] == 0:
            problemas.append("No hay permisos sembrados (RBAC vacío)")
        admin = db.query(models.Usuario).filter(
            models.Usuario.correo == "admin@multiadmin.com").first()
        if admin is None:
            problemas.append(
                "No existe el usuario admin@multiadmin.com "
                "(arranca el backend una vez para sembrarlo)")
            print("  ✘ usuario admin: no existe")
        else:
            print(f"  ✔ usuario admin id={admin.id} activo={admin.activo}")
    finally:
        db.close()

    titulo("RESULTADO")
    if avisos:
        print("⚠ Avisos (no bloquean el funcionamiento):")
        for a in avisos:
            print(f"   • {a}")
        print()
    if problemas:
        print("❌ Se encontraron problemas:")
        for p in problemas:
            print(f"   • {p}")
        print("\nSugerencias:")
        print("   docker compose down -v && docker compose up -d   (recrea la BD en Docker)")
        print("   python db/crear_bd.py --recrear                  (sin Docker)")
        return 1
    print("✅ La base de datos está completa y funcionando.")
    if avisos:
        print("   (revisa los avisos de arriba si esperabas PostgreSQL)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
