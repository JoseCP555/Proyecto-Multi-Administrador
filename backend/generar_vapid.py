"""Genera un par de claves VAPID para las notificaciones push.

Uso:

    python backend/generar_vapid.py            # imprime las variables
    python backend/generar_vapid.py --guardar  # además las añade al .env raíz

Después reinicia el backend (`docker compose up --build -d`) para que tome
los valores nuevos. La clave PRIVADA nunca debe subirse a GitHub.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> None:
    from app.push import generar_claves_vapid

    publica, privada = generar_claves_vapid()
    print("Añade estas líneas a tu .env (la privada NO va a GitHub):\n")
    print(f"VAPID_PUBLIC_KEY={publica}")
    print(f"VAPID_PRIVATE_KEY={privada}")
    print("VAPID_SUBJECT=mailto:tu-correo@gmail.com\n")

    if "--guardar" in sys.argv:
        ruta = ROOT / ".env"
        existente = ruta.read_text(encoding="utf-8") if ruta.exists() else ""
        lineas = [l for l in existente.splitlines()
                  if not l.startswith(("VAPID_PUBLIC_KEY=", "VAPID_PRIVATE_KEY=", "VAPID_SUBJECT="))]
        lineas += [
            "",
            "# --- Web Push (notificaciones del navegador) ---",
            f"VAPID_PUBLIC_KEY={publica}",
            f"VAPID_PRIVATE_KEY={privada}",
            "VAPID_SUBJECT=mailto:" + os.getenv("EMAIL_USER", "tu-correo@gmail.com"),
        ]
        ruta.write_text("\n".join(lineas).strip() + "\n", encoding="utf-8")
        print(f"Guardado en {ruta}")


if __name__ == "__main__":
    main()
