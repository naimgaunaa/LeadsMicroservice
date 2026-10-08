from fastapi import APIRouter
from app.schemas import ClientDTO, CreateLeadDTO

router = APIRouter(
    prefix="/leads"
)

@router.post("")
async def send_preform(body: CreateLeadDTO):
    pass

@router.get("")
async def queque_telemarketer(estado: str, nivel: str):
    pass

@router.get("/{lead_id}")
async def panel_detail(lead_id):
    pass

@router.patch("/{lead_id}/state")
async def change_state_lead(lead_id):
    pass