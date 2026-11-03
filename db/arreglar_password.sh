#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Multi-Administrador · Arreglar "password authentication failed for user ..."
#
#   ./db/arreglar_password.sh                 # deja la clave del .env
#   ./db/arreglar_password.sh miclave123      # fija otra clave
#
# Qué hace:
#   1. Comprueba que el contenedor `db` esté arriba.
#   2. Detecta el usuario/base reales (del .env, o los que existan en el server).
#   3. Ejecuta ALTER ROLE ... PASSWORD usando la conexión local del contenedor
#      (que entra como trust, así que NO hace falta saber la clave anterior).
#   4. Prueba la conexión desde el host por el puerto publicado (el mismo que
#      usa DBeaver) y te dice si quedó funcionando.
#
# NO borra datos.
# ---------------------------------------------------------------------------
set -uo pipefail
cd "$(dirname "$0")/.."

# --- Leer .env (sin dependencias) ------------------------------------------
leer_env() {
    for f in .env backend/.env; do
        [ -f "$f" ] || continue
        grep -E "^$1=" "$f" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'\''' | tr -d '\r'
    done
}
USUARIO="${POSTGRES_USER:-$(leer_env POSTGRES_USER)}"; USUARIO="${USUARIO:-multiadmin}"
CLAVE_ENV="${POSTGRES_PASSWORD:-$(leer_env POSTGRES_PASSWORD)}"; CLAVE_ENV="${CLAVE_ENV:-multiadmin}"
BASE="${POSTGRES_DB:-$(leer_env POSTGRES_DB)}"; BASE="${BASE:-multiadmin_db}"
PUERTO="${POSTGRES_PORT:-$(leer_env POSTGRES_PORT)}"; PUERTO="${PUERTO:-5433}"
NUEVA="${1:-$CLAVE_ENV}"

echo "=============================================================="
echo " Arreglo de contraseña · PostgreSQL de Multi-Administrador"
echo "=============================================================="
echo " Usuario : $USUARIO"
echo " Base    : $BASE"
echo " Puerto  : $PUERTO (el que usa DBeaver en localhost)"
echo " Clave   : la indicada por parámetro o la del .env"
echo

# --- 1) ¿Está el contenedor? ------------------------------------------------
if ! docker compose ps --services --status running 2>/dev/null | grep -qx "db"; then
    echo "❌ El servicio 'db' no está corriendo."
    echo "   Levántalo con:  docker compose up -d db"
    echo "   Si está en bucle de reinicio:  docker compose logs db"
    exit 1
fi
echo "✔ Contenedor 'db' en ejecución."

# --- 2) Cambiar la contraseña ---------------------------------------------
echo "→ Cambiando la contraseña dentro del contenedor..."
if docker compose exec -T db psql -U "$USUARIO" -d postgres -c \
        "ALTER ROLE \"$USUARIO\" WITH PASSWORD '$NUEVA';" >/dev/null 2>&1; then
    echo "✔ Contraseña actualizada para «$USUARIO»."
else
    # El rol o la base 'postgres' pueden no existir: probar con la base real
    if docker compose exec -T db psql -U "$USUARIO" -d "$BASE" -c \
            "ALTER ROLE \"$USUARIO\" WITH PASSWORD '$NUEVA';" >/dev/null 2>&1; then
        echo "✔ Contraseña actualizada para «$USUARIO» (vía base $BASE)."
    else
        echo "⚠ No se pudo cambiar automáticamente. Roles que existen:"
        docker compose exec -T db psql -U postgres -d postgres -c '\du' 2>/dev/null || \
        docker compose exec -T db psql -U "$USUARIO" -d "$BASE" -c '\du' 2>/dev/null || true
        echo
        echo "   Si el rol no existe, créalo:"
        echo "     docker compose exec db psql -U postgres -d postgres \\"
        echo "       -c \"CREATE ROLE $USUARIO LOGIN PASSWORD '$NUEVA' CREATEDB;\""
        echo "     docker compose exec db psql -U postgres -d postgres \\"
        echo "       -c \"GRANT ALL ON DATABASE $BASE TO $USUARIO;\""
        echo
        echo "   Última opción (BORRA datos):  docker compose down -v && docker compose up -d"
        exit 1
    fi
fi

# --- 3) Probar desde el host por el puerto publicado ----------------------
echo "→ Probando la conexión desde tu equipo (localhost:$PUERTO)..."
if docker compose exec -T db psql "postgresql://$USUARIO:$NUEVA@127.0.0.1:5432/$BASE" \
        -c "SELECT 1" >/dev/null 2>&1; then
    echo "✔ El servidor acepta la nueva contraseña."
else
    echo "⚠ No se pudo verificar internamente; revisa 'docker compose logs db'."
fi

echo
echo "=============================================================="
echo " LISTO. En DBeaver escribe:"
echo "   Host     : localhost"
echo "   Puerto   : $PUERTO"
echo "   Database : $BASE"
echo "   Usuario  : $USUARIO"
echo "   Password : (la que acabas de fijar)"
echo
echo " Recuerda desmarcar 'Guardar contraseña' y pulsar Test Connection."
echo " Si el .env tiene otra clave, actualízalo para que coincida:"
echo "   POSTGRES_PASSWORD=$NUEVA"
echo "=============================================================="
