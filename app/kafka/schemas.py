from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OrigenCalificacion(str, Enum):
    AUTOMATICA = "AUTOMATICA"
    MANUAL = "MANUAL"


class MotivoCalificacionDTO(BaseModel):
    regla: str
    puntos: int
    descripcion: str


class LeadCalificadoDTO(BaseModel):
    lead_id: UUID = Field(..., alias="leadId")
    cliente_id: UUID = Field(..., alias="clienteId")
    nivel: str
    puntaje: int
    origen: OrigenCalificacion
    motivos: list[MotivoCalificacionDTO]
    calculada_en: Optional[str] = Field(None, alias="calculadaEn")


class EventEnvelope(BaseModel):
    event_id: str = Field(..., alias="eventId")
    event_type: str = Field(..., alias="eventType")
    correlation_id: str = Field(..., alias="correlationId")
    timestamp: str
    payload: dict[str, Any]
