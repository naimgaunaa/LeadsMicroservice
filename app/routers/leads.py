import os
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.kafka import publish_preformulario_completado
from app.model import Lead
from app.model.nombre_estados import NombreEstados
from app.model.nivel_calificacion import NivelCalificacion
from app.schemas import CrearLeadDTO, LeadDetalleDTO
from app.services.estado_lead import cambiar_estado_lead as cambiar_estado_lead_service

router = APIRouter(prefix="/leads")

CLIENTES_URL = os.getenv("CLIENTES_URL", "http://localhost:8001")


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def crear_preformulario(
    datos: CrearLeadDTO,
    db=Depends(get_db),
):
    """
    La logica de negocio de este enpoint es la siguiente:
    1. hago post al microservicio de clientes como indica documentacion -> recibo 201 con id_cliente
    2. creo el lead en la base de datos con estado PENDIENTE y nivel de calificacion SIN_CALIFICACION
    3. envio a api BCRA /CentralDeDeudores/v1.0/Deudas/cuil (solo numeros del cuil, viene en string con guiones) -> me quedo del resultado 200 results.periodos.entidades[0].situacion
    3. envio con kafka el preformulario completado
    4. envio 202 (accepted) al cliente
    5. recibo de kafka el resultado del analisis de BCRA y actualizo el lead con el nivel de calificacion correspondiente
    6. actualizo lead
    """
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
    return {"leadId": str(nuevo_lead.id)}


@router.get("", response_model=list[LeadDetalleDTO])
async def obtener_cola_telemarketing(
    estado: NombreEstados,
    nivel: NivelCalificacion,
    db=Depends(get_db),
):
    leads = (
        db.query(Lead)
        .filter(Lead.estado == estado.value, Lead.nivel == nivel.value)
        .all()
    )
    return leads


@router.get("/{id_lead}", response_model=LeadDetalleDTO)
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


@router.patch("/{id_lead}/state")
async def actualizar_estado_lead(
    id_lead: UUID,
    nuevo_estado: NombreEstados,
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