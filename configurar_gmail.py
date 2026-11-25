"""Asistente de Docker: verifica SMTP antes de editar exclusivamente sus claves en .env."""
import getpass
import os
from pathlib import Path
import re
import smtplib
import ssl
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
HOST = 'smtp.gmail.com'


def comprobar(cuenta, clave):
    ctx = ssl.create_default_context()
    for port in (587, 465):
        try:
            cliente = (smtplib.SMTP_SSL(HOST, port, timeout=12, context=ctx) if port == 465
                       else smtplib.SMTP(HOST, port, timeout=12))
            with cliente as smtp:
                if port == 587:
                    smtp.starttls(context=ctx)
                smtp.login(cuenta, clave)
            return port
        except (TimeoutError, ConnectionError, smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected):
            if port == 465:
                raise
            print('El puerto 587 no responde. Probando 465 con TLS...')


def guardar(ruta, valores):
    base = ruta if ruta.exists() else ruta.with_name('.env.example')
    contenido = base.read_text(encoding='utf-8-sig').splitlines()
    resto = [linea for linea in contenido if not any(re.match(r'^\s*(?:export\s+)?'+k+r'\s*=', linea) for k in valores)]
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=ruta.parent, delete=False) as tmp:
        nombre = tmp.name
        try:
            tmp.write('\n'.join(resto + [f'{k}={v}' for k,v in valores.items()])+'\n')
            tmp.close()
            os.replace(nombre, ruta)
        finally:
            Path(nombre).unlink(missing_ok=True)


def main():
    if not sys.stdin.isatty():
        sys.exit('Abre una terminal interactiva para introducir la clave de forma privada.')
    cuenta = input('Gmail remitente [multiadmin0@gmail.com]: ').strip() or 'multiadmin0@gmail.com'
    if not re.fullmatch(r'[A-Za-z0-9._+-]+@gmail\.com', cuenta, re.I):
        sys.exit('Escribe una dirección personal de Gmail válida.')
    clave = getpass.getpass('Nueva contraseña de aplicación de Google (entrada oculta): ').replace(' ', '')
    if not re.fullmatch(r'[a-zA-Z0-9]{16}', clave):
        sys.exit('Usa los 16 caracteres de la contraseña de aplicación, no tu contraseña habitual.')
    try:
        port = comprobar(cuenta, clave)
    except smtplib.SMTPAuthenticationError:
        sys.exit('Gmail rechazó la clave. Genera una contraseña de aplicación en esa cuenta. No se modificó el .env.')
    except (OSError, smtplib.SMTPException) as e:
        sys.exit(f'No se pudo conectar con Gmail de forma segura ({type(e).__name__}). No se modificó el .env.')
    guardar(ROOT / '.env', dict(EMAIL_USER=cuenta, MAIL_FROM=cuenta, EMAIL_PASSWORD=clave, MAIL_SERVER=HOST,
            MAIL_PORT=port, MAIL_AUTH='true', MAIL_SSL_CERTS='true', MAIL_STARTTLS=str(port==587).lower(),
            MAIL_SSL_TLS=str(port==465).lower()))
    print('Gmail aceptó las credenciales. Configuración SMTP guardada en el .env local.')


if __name__ == '__main__':
    main()
