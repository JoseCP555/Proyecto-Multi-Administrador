"""Paleta de colores de los conjuntos.

Un conjunto guarda en `conjuntos.color` either:

* el **id** de un color de la paleta (`azul`, `verde`, `ambar`, `rosa`,
  `violeta`, `cian`), que en el frontend se traduce a un tema completo; o
* un **hexadecimal** `#RRGGBB` elegido libremente por el usuario.

`NULL` significa "color automático": el frontend usa el color que le toca
por su posición en la lista, que es el comportamiento histórico.
"""
import re

PALETA = ("azul", "verde", "ambar", "rosa", "violeta", "cian")
_HEX6 = re.compile(r"^#[0-9a-f]{6}$")
_HEX3 = re.compile(r"^#[0-9a-f]{3}$")

__all__ = ["PALETA", "normalizar_color", "sugerir_color"]


def normalizar_color(valor, *, estricto: bool = False) -> str | None:
    """Devuelve el color normalizado (id de paleta o `#rrggbb`), o `None`.

    Con `estricto=True` lanza `ValueError` si el valor no es reconocible;
    se usa desde los validadores de Pydantic para responder 422.
    """
    if valor is None:
        return None
    v = str(valor).strip().lower()
    if not v:
        return None
    if v in PALETA:
        return v
    if not v.startswith("#"):
        v = "#" + v
    if _HEX3.match(v):
        v = "#" + "".join(ch * 2 for ch in v[1:])
    if _HEX6.match(v):
        return v
    if estricto:
        raise ValueError(
            "Color inválido. Usa un nombre de la paleta "
            f"({', '.join(PALETA)}) o un hexadecimal #RRGGBB."
        )
    return None


def sugerir_color(indice: int) -> str:
    """Color de la paleta que le toca al conjunto número `indice`."""
    return PALETA[max(0, int(indice)) % len(PALETA)]
