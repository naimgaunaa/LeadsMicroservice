from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

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