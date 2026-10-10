from fastapi import APIRouter
from app.schemas import CrearLeadDTO

router = APIRouter(
    prefix="/leads"
)

@router.post("")
async def crear_preformulario(datos: CrearLeadDTO):
    pass

@router.get("")
async def obtener_cola_telemarketing(estado: str, nivel: str):
    pass

@router.get("/{id_lead}")
async def obtener_detalle_lead(id_lead):
    pass

@router.patch("/{id_lead}/state")
async def cambiar_estado_lead(id_lead):
    pass