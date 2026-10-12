from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr
from pydantic.alias_generators import to_camel

# El contrato con el front usa camelCase (vehiculoId, solicitaFinanciacion,
# tienePermuta, valorDeclarado). Con populate_by_name aceptamos tanto camelCase
# como snake_case; la salida se serializa en snake_case por defecto.
_camel_config = ConfigDict(
    alias_generator=to_camel,
    populate_by_name=True,
)


class ClienteDTO(BaseModel):
    model_config = _camel_config

    nombre: str
    apellido: str
    email: EmailStr
    telefono: Optional[str] = None
    canal_origen: Optional[str] = None
    cuil: Optional[str] = None
    consentimiento: Optional[bool] = None


class PermutaDTO(BaseModel):
    model_config = _camel_config

    tiene_permuta: bool
    descripcion: Optional[str] = None
    valor_declarado: Optional[float] = None


class UbicacionDTO(BaseModel):
    model_config = _camel_config

    provincia: str
    localidad: Optional[str] = None


class CrearLeadDTO(BaseModel):
    model_config = _camel_config

    cliente: ClienteDTO
    vehiculo_id: UUID
    anticipo: float
    permuta: PermutaDTO
    ubicacion: UbicacionDTO
    solicita_financiacion: bool


class LeadDetalleDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cliente_id: UUID
    vehiculo_id: UUID
    anticipo: float
    solicita_financiacion: bool
    ficha_completa: bool
    puntaje: Optional[int] = None
    nivel: Optional[str] = None
    estado: str
    provincia: Optional[str] = None
    localidad: Optional[str] = None
    permuta_tiene: bool
    permuta_descripcion: Optional[str] = None
    permuta_valor_declarado: Optional[float] = None
    permuta_computable: Optional[bool] = None
    creado_en: datetime


class LeadCreadoResponse(BaseModel):
    """Respuesta al crear un preformulario."""

    lead_id: str

    model_config = {
        "json_schema_extra": {
            "example": {"lead_id": "e6e4be8d-cc1c-4f6c-bcd0-b2c8be5af5e0"}
        }
    }


class MensajeResponse(BaseModel):
    """Respuesta genérica con mensaje."""

    message: str

    model_config = {
        "json_schema_extra": {
            "example": {"message": "Estado del lead actualizado correctamente."}
        }
    }