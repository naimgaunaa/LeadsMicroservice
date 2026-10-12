import logging
import os
from typing import Optional
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

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
from app.services.provincia import normalizar_provincia

logger = logging.getLogger(__name__)

# Orden de la cola de telemarketing: de mayor a menor potabilidad. Los niveles
# desconocidos van al final.
_ORDEN_NIVEL_COLA = {
    NivelCalificacion.MUY_POTABLE.value: 0,
    NivelCalificacion.POTABLE.value: 1,
    NivelCalificacion.NO_POTABLE.value: 2,
    NivelCalificacion.SIN_CALIFICACION.value: 3,
}


def _clave_orden_cola(lead: Lead) -> tuple:
    """Clave de orden: nivel (potabilidad), puntaje descendente y antigüedad."""
    puntaje = lead.puntaje if lead.puntaje is not None else -10**9
    return (
        _ORDEN_NIVEL_COLA.get(lead.nivel, 4),
        -puntaje,
        lead.creado_en,
    )


router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
)

# Por defecto se asume ejecución dentro de Docker (compose separados).
# Fuera de Docker, definir CLIENTES_URL=http://localhost:8082
CLIENTES_URL = os.getenv("CLIENTES_URL", "http://host.docker.internal:8082")
CLIENTES_CLAVE_LEADS = os.getenv("CLIENTES_CLAVE_LEADS")

CLIENTES_TIMEOUT = 5.0
CLIENTES_MAX_INTENTOS = 2


def _error_configuracion() -> HTTPException:
    """Error de configuración del servicio (clave faltante o rechazada)."""
    logger.error("CLIENTES_CLAVE_LEADS faltante o inválida (401 de clientes)")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error de configuración del servicio.",
    )


def _armar_body_cliente(datos: CrearLeadDTO) -> dict:
    """Arma el body para POST /clientes a partir del preformulario.

    - cuil y consentimiento solo se incluyen si solicita_financiacion es True.
    - Nunca se envía cuil como string vacío.
    """
    provincia_normalizada = normalizar_provincia(datos.ubicacion.provincia)
    body = {
        "nombre": datos.cliente.nombre,
        "apellido": datos.cliente.apellido,
        "email": datos.cliente.email,
        "provincia": provincia_normalizada or datos.ubicacion.provincia,
    }
    if datos.cliente.telefono:
        body["telefono"] = datos.cliente.telefono
    if datos.ubicacion.localidad:
        body["localidad"] = datos.ubicacion.localidad
    if datos.cliente.canal_origen:
        body["canalOrigen"] = datos.cliente.canal_origen
    if datos.solicita_financiacion:
        body["cuil"] = datos.cliente.cuil
        body["consentimiento"] = datos.cliente.consentimiento
    return body


async def _crear_cliente(
    datos: CrearLeadDTO, correlation_id: str
) -> UUID | JSONResponse:
    """Llama al microservicio de clientes y devuelve el cliente_id.

    Ante 422 devuelve un JSONResponse con el ProblemDetail recibido para
    propagarlo al front. Ante otros errores lanza HTTPException.
    """
    if not CLIENTES_CLAVE_LEADS:
        raise _error_configuracion()

    body = _armar_body_cliente(datos)
    headers = {
        "X-Api-Key": CLIENTES_CLAVE_LEADS,
        "X-Correlation-Id": correlation_id,
    }

    async with httpx.AsyncClient(timeout=CLIENTES_TIMEOUT) as client:
        response: httpx.Response | None = None
        for intento in range(1, CLIENTES_MAX_INTENTOS + 1):
            try:
                response = await client.post(
                    f"{CLIENTES_URL}/clientes",
                    json=body,
                    headers=headers,
                )
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                logger.warning(
                    "clientes no disponible (intento %d/%d): %s",
                    intento,
                    CLIENTES_MAX_INTENTOS,
                    type(exc).__name__,
                )
                response = None
            else:
                if response.status_code < 500:
                    break  # respuesta definitiva, no reintentar
                logger.warning(
                    "clientes respondió %d (intento %d/%d)",
                    response.status_code,
                    intento,
                    CLIENTES_MAX_INTENTOS,
                )

    if response is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de clientes no está disponible.",
        )

    if response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED):
        return UUID(response.json()["clienteId"])

    if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.json(),
        )

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        raise _error_configuracion()

    logger.error(
        "clientes respondió %d: %s", response.status_code, response.text[:500]
    )
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="El servicio de clientes rechazó la solicitud.",
    )


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
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Datos inválidos (validación propia o del servicio de Clientes).",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Error de configuración (clave de Clientes faltante o inválida).",
        },
        status.HTTP_502_BAD_GATEWAY: {
            "description": "El microservicio de Clientes rechazó la creación del cliente.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "El microservicio de Clientes no está disponible.",
        },
    },
)
async def crear_preformulario(
    datos: CrearLeadDTO,
    request: Request,
    db=Depends(get_db),
):
    """Crea un nuevo preformulario de lead de forma asíncrona."""
    # Validación propia: con financiación, cuil y consentimiento son obligatorios.
    if datos.solicita_financiacion:
        errores = []
        if not datos.cliente.cuil:
            errores.append(
                {"campo": "cuil", "mensaje": "El CUIL es obligatorio cuando se solicita financiación."}
            )
        if datos.cliente.consentimiento is None:
            errores.append(
                {
                    "campo": "consentimiento",
                    "mensaje": "El consentimiento es obligatorio cuando se solicita financiación.",
                }
            )
        if errores:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "status": 422,
                    "codigo": "VALIDACION",
                    "detail": "Datos inválidos para la solicitud de financiación.",
                    "errores": errores,
                },
            )

    # 1. Crear el cliente en el microservicio de clientes
    correlation_id = request.headers.get("X-Correlation-Id") or str(uuid4())
    resultado = await _crear_cliente(datos, correlation_id)
    if isinstance(resultado, JSONResponse):
        return resultado  # 422: se propaga el ProblemDetail al front
    cliente_id = resultado

    # 2. Crear el lead en la base de datos
    provincia_normalizada = normalizar_provincia(datos.ubicacion.provincia) or datos.ubicacion.provincia
    nuevo_lead = Lead(
        cliente_id=cliente_id,
        vehiculo_id=datos.vehiculo_id,
        anticipo=datos.anticipo,
        solicita_financiacion=datos.solicita_financiacion,
        ficha_completa=True,
        estado=NombreEstados.PENDIENTE.value,
        nivel=NivelCalificacion.SIN_CALIFICACION.value,
        provincia=provincia_normalizada,
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
        anticipo=float(datos.anticipo),
        solicita_financiacion=datos.solicita_financiacion,
        provincia=provincia_normalizada,
        monto_permuta=float(datos.permuta.valor_declarado)
        if datos.permuta.valor_declarado is not None
        else None,
        permuta_no_computable=False,
        correlation_id=correlation_id,
    )

    # 4. Responder 202 Accepted con el leadId
    return LeadCreadoResponse(lead_id=str(nuevo_lead.id))


@router.get(
    "",
    response_model=list[LeadDetalleDTO],
    summary="Obtener cola de telemarketing",
    description="""\
Devuelve la lista de leads que alimenta la cola de trabajo de telemarketing,
ordenada por nivel de potabilidad (descendente), puntaje (descendente) y
antigüedad. Los filtros `estado` y `nivel` son **opcionales**: si se omiten se
devuelven todos los leads. Esto evita que el front deba iterar sobre todas las
combinaciones estado × nivel.
""",
    response_description="Lista de leads que coinciden con los filtros, ya ordenada.",
)
async def obtener_cola_telemarketing(
    estado: Optional[NombreEstados] = Query(
        None,
        description="Estado actual del lead (opcional).",
        examples=["CALIFICADO"],
    ),
    nivel: Optional[NivelCalificacion] = Query(
        None,
        description="Nivel de calificación crediticia del lead (opcional).",
        examples=["MUY_POTABLE"],
    ),
    db=Depends(get_db),
):
    query = db.query(Lead)
    if estado is not None:
        query = query.filter(Lead.estado == estado.value)
    if nivel is not None:
        query = query.filter(Lead.nivel == nivel.value)
    leads = query.all()
    leads.sort(key=_clave_orden_cola)
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