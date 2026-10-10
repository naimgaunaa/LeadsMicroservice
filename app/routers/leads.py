import os
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_db
from app.kafka import publish_preformulario_completado
from app.model import Lead
from app.model.nombre_estados import NombreEstados
from app.model.nivel_calificacion import NivelCalificacion
from app.schemas import (
    CrearLeadDTO,
    LeadCreadoResponse,
    LeadDetalleDTO,
    MensajeResponse,
)
from app.services.estado_lead import cambiar_estado_lead as cambiar_estado_lead_service

router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
)

CLIENTES_URL = os.getenv("CLIENTES_URL", "http://localhost:8001")


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=LeadCreadoResponse,
    summary="Crear preformulario de lead",
    description="""
Recibe los datos del preformulario, crea el cliente en el microservicio de
**Clientes**, persiste el lead en estado `PENDIENTE` con nivel
`SIN_CALIFICACION` y publica el evento `PreformularioCompletado` en Kafka
para que el servicio de scoring continúe el proceso de forma asíncrona.

**Flujo de negocio:**
1. POST al microservicio de Clientes → obtiene `cliente_id`.
2. Crea el lead en la base de datos (`PENDIENTE` / `SIN_CALIFICACION`).
3. Publica en Kafka el evento `PreformularioCompletado`.
4. Responde `202 Accepted` con el `leadId` generado.

El análisis crediticio (BCRA) se procesa de forma asíncrona y el lead se
actualiza cuando llega el resultado vía Kafka.
""",
    responses={
        status.HTTP_202_ACCEPTED: {
            "description": "Preformulario aceptado y en procesamiento.",
            "model": LeadCreadoResponse,
        },
        status.HTTP_502_BAD_GATEWAY: {
            "description": "El microservicio de Clientes rechazó la creación del cliente.",
        },
    },
)
async def crear_preformulario(
    datos: CrearLeadDTO,
    db=Depends(get_db),
):
    """Crea un nuevo preformulario de lead de forma asíncrona."""
    # 1. Crear el cliente en el microservicio de clientes
    async with httpx.AsyncClient() as client:
        cliente_payload = datos.cliente.model_dump()
        response = await client.post(
            f"{CLIENTES_URL}/clientes",
            json=cliente_payload,
        )

        if response.status_code != status.HTTP_201_CREATED:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al crear el cliente: {response.text}",
            )

        cliente_id = response.json().get("id")

    # 2. Crear el lead en la base de datos
    nuevo_lead = Lead(
        cliente_id=cliente_id,
        vehiculo_id=datos.vehiculo_id,
        anticipo=datos.anticipo,
        solicita_financiacion=datos.solicita_financiacion,
        ficha_completa=True,
        estado=NombreEstados.PENDIENTE.value,
        nivel=NivelCalificacion.SIN_CALIFICACION.value,
        provincia=datos.ubicacion.provincia,
        localidad=datos.ubicacion.localidad,
        permuta_tiene=datos.permuta.tiene_permuta,
        permuta_descripcion=datos.permuta.descripcion,
        permuta_valor_declarado=datos.permuta.valor_declarado,
        permuta_computable=None,
        puntaje=None,
    )
    db.add(nuevo_lead)
    db.commit()
    db.refresh(nuevo_lead)

    # 3. Enviar evento PreformularioCompletado via Kafka
    await publish_preformulario_completado(
        lead_id=str(nuevo_lead.id),
        cliente_id=str(cliente_id),
        vehiculo_id=str(datos.vehiculo_id),
    )

    # 4. Responder 202 Accepted con el leadId
    return LeadCreadoResponse(lead_id=str(nuevo_lead.id))


@router.get(
    "",
    response_model=list[LeadDetalleDTO],
    summary="Obtener cola de telemarketing",
    description="""
Devuelve la lista de leads filtrada por **estado** y **nivel de
calificación**. Este endpoint alimenta la cola de trabajo de telemarketing.
""",
    response_description="Lista de leads que coinciden con los filtros.",
)
async def obtener_cola_telemarketing(
    estado: NombreEstados = Query(
        ...,
        description="Estado actual del lead.",
        examples=["PENDIENTE"],
    ),
    nivel: NivelCalificacion = Query(
        ...,
        description="Nivel de calificación crediticia del lead.",
        examples=["SIN_CALIFICACION"],
    ),
    db=Depends(get_db),
):
    leads = (
        db.query(Lead)
        .filter(Lead.estado == estado.value, Lead.nivel == nivel.value)
        .all()
    )
    return leads


@router.get(
    "/{id_lead}",
    response_model=LeadDetalleDTO,
    summary="Obtener detalle de un lead",
    description="Devuelve toda la información persistida del lead identificado por `id_lead`.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No existe un lead con ese ID."},
    },
)
async def obtener_detalle_lead(
    id_lead: UUID,
    db=Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == id_lead).first()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead no encontrado",
        )

    return lead


@router.patch(
    "/{id_lead}/state",
    response_model=MensajeResponse,
    summary="Actualizar estado de un lead",
    description="""
Cambia el estado del lead respetando la máquina de estados definida en el
servicio. Si la transición no es válida se devuelve `400 Bad Request`.
""",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "La transición de estado solicitada no es válida.",
        },
        status.HTTP_404_NOT_FOUND: {"description": "No existe un lead con ese ID."},
    },
)
async def actualizar_estado_lead(
    id_lead: UUID,
    nuevo_estado: NombreEstados = Query(
        ...,
        description="Nuevo estado al que se quiere transicionar el lead.",
        examples=["EN_GESTION"],
    ),
    db=Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == id_lead).first()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead no encontrado",
        )

    try:
        cambiar_estado_lead_service(lead, nuevo_estado)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    db.commit()
    db.refresh(lead)

    return {"message": "Estado del lead actualizado correctamente."}