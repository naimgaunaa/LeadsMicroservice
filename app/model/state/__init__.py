from app.model.nombre_estados import NombreEstados
from app.model.state.calificado import Calificado
from app.model.state.derivado import Derivado
from app.model.state.descartado import Descartado
from app.model.state.enGestion import EnGestion
from app.model.state.estadoLead import EstadoLead
from app.model.state.pendiente import Pendiente

__all__ = [
    "EstadoLead",
    "NombreEstados",
    "Pendiente",
    "Calificado",
    "EnGestion",
    "Derivado",
    "Descartado",
]
