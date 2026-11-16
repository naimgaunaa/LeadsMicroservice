"""Normalización de patente argentina (formato AAA123 o AB123CD).

Coincide con `Patente.normalizar` del servicio vehiculos: sin espacios ni
guiones, en mayúsculas. A diferencia de vehiculos, es un campo opcional del
preformulario: una patente vacía se devuelve como None en lugar de fallar.
"""

import re
from typing import Optional

_PATENTE = re.compile(r"^([A-Z]{3}[0-9]{3}|[A-Z]{2}[0-9]{3}[A-Z]{2})$")


def normalizar_patente(valor: Optional[str]) -> Optional[str]:
    """Devuelve la patente normalizada, o None si no se informó.

    Lanza ValueError si viene un valor inválido no vacío.
    """
    if not valor:
        return None
    normalizada = valor.strip().upper().replace(" ", "").replace("-", "")
    if not normalizada:
        return None
    if not _PATENTE.match(normalizada):
        raise ValueError("La patente debe tener el formato AAA123 o AB123CD")
    return normalizada
