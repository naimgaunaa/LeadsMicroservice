from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4


class OrigenCalificacion(str, Enum):
    AUTOMATICA = "AUTOMATICA"
    MANUAL = "MANUAL"


@dataclass
class MotivoCalificacion:
    regla: str
    puntos: int
    descripcion: str


@dataclass
class LeadCalificadoPayload:
    lead_id: UUID
    cliente_id: UUID
    nivel: str
    puntaje: int
    origen: OrigenCalificacion
    motivos: list[MotivoCalificacion] = field(default_factory=list)
    calculada_en: Optional[datetime] = None


@dataclass
class EventEnvelope:
    event_id: str
    event_type: str
    correlation_id: str
    timestamp: str
    payload: dict[str, Any]

    @classmethod
    def build(
        cls,
        event_type: str,
        payload: dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> "EventEnvelope":
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            correlation_id=correlation_id or str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload=payload,
        )
