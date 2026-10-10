from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db

from uuid import UUID
from app.model import Lead
from app.model.nombre_estados import NombreEstados
from app.model.nivel_calificacion import NivelCalificacion

from app.schemas import CrearLeadDTO, LeadDetalleDTO

router = APIRouter(
    prefix="/leads"
)

@router.post("")
async def crear_preformulario(datos: CrearLeadDTO):
    pass

@router.get("", response_model=list[LeadDetalleDTO])
async def obtener_cola_telemarketing(
    estado: NombreEstados,
    nivel: NivelCalificacion,
    db = Depends(get_db)
):
    leads = db.query(Lead).filter(Lead.estado == estado.value, Lead.nivel == nivel.value).all()
    return leads

@router.get("/{id_lead}", response_model=LeadDetalleDTO)
async def obtener_detalle_lead(
    id_lead: UUID, 
    db = Depends(get_db)
):
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