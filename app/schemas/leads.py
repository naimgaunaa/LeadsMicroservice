from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class ClientDTO(BaseModel):
    name: str
    last_name : str
    email: EmailStr
    phone: str
    cuil: str
    consent: bool

class PermutaDTO(BaseModel):
    have_permuta: bool
    description: Optional[str] = None
    declareted_value: Optional[str] = None

class LocationDTO(BaseModel):
    province: str
    place: str

class CreateLeadDTO(BaseModel):
    client: ClientDTO
    vehicle_id: UUID
    advance: float
    permuta: PermutaDTO
    Location: LocationDTO
    apply_for_funding: bool