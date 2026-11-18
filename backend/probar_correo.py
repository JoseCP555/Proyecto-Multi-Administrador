#!/usr/bin/env python
"""Diagnóstico y prueba del envío de correos (SMTP).

Uso:

    cd backend
    .venv/bin/python probar_correo.py                      # solo diagnóstico
    .venv/bin/python probar_correo.py tu@correo.com        # diagnóstico + correo de prueba

Revisa la configuración de backend/.env, se conecta al servidor SMTP, hace el
saludo EHLO, el STARTTLS/SSL, la autenticación y (opcionalmente) envía un correo
de prueba real. Traduce los errores habituales (contraseña normal en vez de
contraseña de aplicación, SMTP deshabilitado, etc.) a instrucciones concretas.
"""
from __future__ import annotations

import smtplib
import ssl
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid

from app.email_config import (
    EMAIL_PASSWORD,
    EMAIL_USER,
    MAIL_FROM,
    MAIL_FROM_NAME,
    MAIL_PORT,
    MAIL_SERVER,
    MAIL_SSL_CERTS,
    MAIL_SSL_TLS,
    MAIL_STARTTLS,
    MAIL_AUTH,
    MAIL_TIMEOUT,
    diagnostico,
    mail_configurado,
    resumen_smtp,
)

OK = "\033[92m✔\033[0m"
MAL = "\033[91m✘\033[0m"
AVISO = "\033[93m!\033[0m"


def _explicar(error: Exception) -> str:
    """Traduce los errores SMTP típicos a pasos accionables."""
    texto = f"{type(error).__name__}: {error}"
    bajo = texto.lower()
    if "535" in bajo or "badcredentials" in bajo or "username and password not accepted" in bajo:
        return ("\n".join([
            "El servidor rechazó usuario/contraseña.",
            "  · Gmail/Workspace: NO uses la contraseña normal de la cuenta. Necesitas una",
            "    «Contraseña de aplicación» de 16 caracteres (requiere verificación en 2 pasos):",
            "    https://myaccount.google.com/apppasswords",
            "  · Pega las 16 letras en EMAIL_PASSWORD (se aceptan con o sin espacios).",
            "  · Si la cuenta es institucional, el administrador debe permitir el acceso SMTP.",
            "  · Outlook/Hotmail: usa una contraseña de aplicación y smtp-mail.outlook.com:587.",
        ]))
    if "534" in bajo or "application-specific password" in bajo or "lesssecure" in bajo:
        return ("El proveedor exige una contraseña de aplicación (o «acceso de apps menos seguras»). "
                "Genera una contraseña de aplicación y actualiza EMAIL_PASSWORD.")
    if "timed out" in bajo or "timeout" in bajo or "connection refused" in bajo:
        return ("\n".join([
            "No se pudo conectar al servidor SMTP.",
            "  · Revisa MAIL_SERVER y MAIL_PORT (Gmail: smtp.gmail.com con 587 STARTTLS o 465 SSL).",
            "  · Muchos proveedores de internet bloquean el puerto 25: usa 587 o 465.",
            "  · En Docker/redes corporativas, el firewall puede bloquear la salida SMTP.",
        ]))
    if "name or service not known" in bajo or "nodename" in bajo or "getaddrinfo" in bajo:
        return "El nombre del servidor SMTP no resuelve. Revisa MAIL_SERVER (por ejemplo smtp.gmail.com)."
    if "ssl" in bajo or "certificate" in bajo:
        return ("Problema de cifrado. Usa MAIL_PORT=465 (SSL) o MAIL_PORT=587 con MAIL_STARTTLS=true. "
                "Solo en un servidor local de pruebas pon MAIL_SSL_CERTS=false.")
    return "Revisa el mensaje anterior y la configuración de backend/.env."


def diagnosticar() -> bool:
    datos = diagnostico()
    print("\n=== Configuración SMTP detectada ===")
    for clave, valor in datos.items():
        print(f"  {clave:18}: {valor}")
    print(f"\n  {resumen_smtp()}\n")

    if not mail_configurado():
        print(f"{MAL} Falta configuración. En backend/.env define:")
        print("     EMAIL_USER=tu_correo@gmail.com")
        print("     EMAIL_PASSWORD=abcdefghijklmnop     # contraseña de aplicación (16 letras)")
        print("     MAIL_SERVER=smtp.gmail.com")
        print("     MAIL_PORT=587")
        return False

    if EMAIL_PASSWORD and len(EMAIL_PASSWORD) < 12:
        print(f"{AVISO} La contraseña tiene {len(EMAIL_PASSWORD)} caracteres. Las de aplicación "
              "de Gmail tienen 16; si es tu contraseña normal, será rechazada (error 535).")

    print("=== Conexión con el servidor SMTP ===")
    try:
        contexto = ssl.create_default_context()
        if not MAIL_SSL_CERTS:
            contexto.check_hostname = False
            contexto.verify_mode = ssl.CERT_NONE
        if MAIL_SSL_TLS:
            print(f"  {OK} Conectando con SSL/TLS a {MAIL_SERVER}:{MAIL_PORT} …")
            servidor = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT, timeout=MAIL_TIMEOUT, context=contexto)
        else:
            print(f"  {OK} Conectando a {MAIL_SERVER}:{MAIL_PORT} …")
            servidor = smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=MAIL_TIMEOUT)
        servidor.ehlo()
        if MAIL_STARTTLS and not MAIL_SSL_TLS:
            servidor.starttls(context=contexto)
            servidor.ehlo()
            print(f"  {OK} STARTTLS negociado")
        print(f"  {OK} Servidor responde: {servidor.noop()[0]} (250 = correcto)")
        if MAIL_AUTH:
            print(f"  {OK} Autenticando como {EMAIL_USER} …")
            servidor.login(EMAIL_USER, EMAIL_PASSWORD)
            print(f"  {OK} Autenticación correcta")
        else:
            print(f"  {OK} Servidor local sin autenticación (MAIL_AUTH=false)")
        servidor.quit()
        return True
    except Exception as error:  # noqa: BLE001
        print(f"  {MAL} {_explicar(error)}")
        return False


def enviar_prueba(destino: str) -> bool:
    print(f"\n=== Enviando correo de prueba a {destino} ===")
    html = """\
<html><body style="font-family:Arial,sans-serif;background:#EEF0F7;padding:24px">
  <div style="max-width:520px;margin:auto;background:#fff;border-radius:18px;padding:28px">
    <h2 style="color:#111827;margin:0 0 8px">Correo de prueba</h2>
    <p style="color:#374151">Si estás leyendo esto, el envío de correos del
    <b>Multi-Administrador</b> está funcionando correctamente.</p>
    <p style="color:#6B7280;font-size:13px">Puedes cerrar este mensaje.</p>
    <p style="color:#9CA3AF;font-size:12px">Recibes este correo porque se pidió una prueba
    desde la configuración del sistema Multi-Administrador.</p>
  </div>
</body></html>"""
    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = "Prueba de correo · Multi-Administrador"
    mensaje["From"] = formataddr((MAIL_FROM_NAME, MAIL_FROM))
    mensaje["To"] = destino
    mensaje["Date"] = formatdate(localtime=True)
    mensaje["Message-ID"] = make_msgid(domain=MAIL_FROM.split("@")[-1])
    mensaje["Reply-To"] = MAIL_FROM
    mensaje["Auto-Submitted"] = "auto-generated"
    mensaje.attach(MIMEText("El envío de correos del Multi-Administrador funciona.", "plain"))
    mensaje.attach(MIMEText(html, "html"))

    try:
        contexto = ssl.create_default_context()
        if not MAIL_SSL_CERTS:
            contexto.check_hostname = False
            contexto.verify_mode = ssl.CERT_NONE
        if MAIL_SSL_TLS:
            servidor = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT, timeout=MAIL_TIMEOUT, context=contexto)
        else:
            servidor = smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=MAIL_TIMEOUT)
        servidor.ehlo()
        if MAIL_STARTTLS and not MAIL_SSL_TLS:
            servidor.starttls(context=contexto)
            servidor.ehlo()
        if MAIL_AUTH:
            servidor.login(EMAIL_USER, EMAIL_PASSWORD)
        servidor.sendmail(MAIL_FROM, [destino], mensaje.as_string())
        servidor.quit()
        print(f"  {OK} Correo aceptado por el servidor. Revisa la bandeja de {destino} "
              "(y la carpeta de spam).")
        return True
    except Exception as error:  # noqa: BLE001
        print(f"  {MAL} No se pudo enviar: {_explicar(error)}")
        return False


def main() -> int:
    destino = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    if not diagnosticar():
        return 1
    if destino:
        return 0 if enviar_prueba(destino) else 2
    print(f"{AVISO} No se envió ningún correo. Para enviar uno de prueba:")
    print("     .venv/bin/python probar_correo.py tu_correo@dominio.com")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
