"""Normalización de provincia al enum compartido con clientes/calificacion.

El frontend envía la provincia como texto libre ("Buenos Aires", "CABA",
"Córdoba", ...). Los servicios Spring esperan el enum `Provincia`
(BUENOS_AIRES, CORDOBA, ...). Este módulo mapea ambas formas.
"""

from typing import Optional

# Mapa de formas posibles (sin acentos, mayúsculas) -> valor del enum Provincia.
_PROVINCIAS = {
    "BUENOS_AIRES": "BUENOS_AIRES",
    "BUENOS AIRES": "BUENOS_AIRES",
    "BSAS": "BUENOS_AIRES",
    "BS_AS": "BUENOS_AIRES",
    "GBA": "BUENOS_AIRES",
    "PROVINCIA_DE_BUENOS_AIRES": "BUENOS_AIRES",
    "CABA": "CABA",
    "CIUDAD_AUTONOMA_DE_BUENOS_AIRES": "CABA",
    "CATAMARCA": "CATAMARCA",
    "CHACO": "CHACO",
    "CHUBUT": "CHUBUT",
    "CORDOBA": "CORDOBA",
    "CORRIENTES": "CORRIENTES",
    "ENTRE_RIOS": "ENTRE_RIOS",
    "FORMOSA": "FORMOSA",
    "JUJUY": "JUJUY",
    "LA_PAMPA": "LA_PAMPA",
    "LA_RIOJA": "LA_RIOJA",
    "MENDOZA": "MENDOZA",
    "MISIONES": "MISIONES",
    "NEUQUEN": "NEUQUEN",
    "RIO_NEGRO": "RIO_NEGRO",
    "SALTA": "SALTA",
    "SAN_JUAN": "SAN_JUAN",
    "SAN_LUIS": "SAN_LUIS",
    "SANTA_CRUZ": "SANTA_CRUZ",
    "SANTA_FE": "SANTA_FE",
    "SANTIAGO_DEL_ESTERO": "SANTIAGO_DEL_ESTERO",
    "TIERRA_DEL_FUEGO": "TIERRA_DEL_FUEGO",
    "TUCUMAN": "TUCUMAN",
}


def normalizar_provincia(valor: Optional[str]) -> Optional[str]:
    """Devuelve el valor del enum Provincia o None si no se reconoce."""
    if not valor:
        return None
    clave = valor.strip().upper()
    return _PROVINCIAS.get(clave)
