from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import CrearLeadDTO, LeadDetalleDTO
from app.model import Lead
from app.database import get_db

router = APIRouter(
    prefix="/leads"
)

@router.post("")
async def crear_preformulario(datos: CrearLeadDTO):
    pass

@router.get("")
async def obtener_cola_telemarketing(estado: str, nivel: str):
    pass

@router.get("/{id_lead}", response_model=LeadDetalleDTO)
async def obtener_detalle_lead(id_lead: UUID, db = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == id_lead).first()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead no encontrado",
        )

    return lead

@router.patch("/{id_lead}/state")
async def cambiar_estado_lead(id_lead):
    pass