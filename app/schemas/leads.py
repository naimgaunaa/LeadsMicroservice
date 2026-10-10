from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr

class ClienteDTO(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    telefono: str
    cuil: str
    consentimiento: bool

class PermutaDTO(BaseModel):
    tiene_permuta: bool
    descripcion: Optional[str] = None
    valor_declarado: Optional[float] = None

class UbicacionDTO(BaseModel):
    provincia: str
    localidad: str

class CrearLeadDTO(BaseModel):
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