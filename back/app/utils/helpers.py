import re
from datetime import datetime


def obtener_fecha_actual():
    return datetime.now()


def validar_correo(correo: str):
    patron = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(patron, correo) is not None