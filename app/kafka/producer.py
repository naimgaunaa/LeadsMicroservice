import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from aiokafka import AIOKafkaProducer
from app.kafka.config import kafka_enabled, kafka_settings, _seguridad

logger = logging.getLogger(__name__)

_producer: Optional[AIOKafkaProducer] = None


def build_event_envelope(
    event_type: str,
    payload: dict[str, Any],
    correlation_id: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "eventId": str(uuid.uuid4()),
        "eventType": event_type,
        "correlationId": correlation_id or str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }


async def get_producer() -> Optional[AIOKafkaProducer]:
    global _producer
    if not kafka_enabled:
        return None
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=kafka_settings.bootstrap_servers,
            client_id=kafka_settings.client_id,
            value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
            **_seguridad(),
        )
        await _producer.start()
    return _producer


async def publish_event(
    topic: str,
    key: str,
    event_type: str,
    payload: dict[str, Any],
    correlation_id: Optional[str] = None,
) -> None:
    producer = await get_producer()
    if producer is None:
        logger.info(
            "Kafka deshabilitado: evento %s para topic %s no publicado.",
            event_type,
            topic,
        )
        return
    message = build_event_envelope(event_type, payload, correlation_id)
    await producer.send_and_wait(topic, key=key.encode("utf-8"), value=message)


async def publish_preformulario_completado(
    lead_id: str,
    cliente_id: str,
    vehiculo_id: str,
    *,
    anticipo: float,
    solicita_financiacion: bool,
    provincia: str,
    monto_permuta: Optional[float] = None,
    permuta_no_computable: bool = False,
    correlation_id: Optional[str] = None,
) -> None:
    """Publica PreformularioCompletado con todos los datos que calificacion necesita.

    Viaja envuelto en el sobre común de integración (eventId, eventType,
    correlationId, timestamp, payload). El payload incluye: leadId, clienteId,
    vehiculoId, montoAnticipo, montoPermuta, permutaNoComputable,
    solicitaFinanciacion y ubicacion.
    """
    payload = {
        "leadId": str(lead_id),
        "clienteId": str(cliente_id),
        "vehiculoId": str(vehiculo_id),
        "montoAnticipo": anticipo,
        "montoPermuta": monto_permuta if monto_permuta is not None else 0,
        "permutaNoComputable": permuta_no_computable,
        "solicitaFinanciacion": solicita_financiacion,
        "ubicacion": provincia,
    }
    await publish_event(
        topic=kafka_settings.topic_preformulario_completado,
        key=str(lead_id),
        event_type="PreformularioCompletado",
        payload=payload,
        correlation_id=correlation_id,
    )


async def publish_resumen_solicitado(
    lead,
    correlation_id: Optional[str] = None,
) -> None:
    """Publica ResumenSolicitado para que el servicio de IA genere el resumen.

    Se dispara cuando el lead queda CALIFICADO. El payload incluye los datos
    comerciales que la IA necesita para armar el `ClientePotencial`; los datos
    de contacto (nombre/apellido) y del vehículo (marca/modelo/anio) los
    consulta la propia IA a `clientes` y `vehiculos` por REST a partir de los
    IDs. Viaja envuelto en el sobre común de integración.
    """
    payload = {
        "leadId": str(lead.id),
        "clienteId": str(lead.cliente_id),
        "vehiculoId": str(lead.vehiculo_id),
        "anticipo": lead.anticipo,
        "solicitaFinanciacion": lead.solicita_financiacion,
        "permuta": {
            "tienePermuta": lead.permuta_tiene,
            "descripcion": lead.permuta_descripcion,
            "valorDeclarado": lead.permuta_valor_declarado,
        },
        "ubicacion": {
            "provincia": lead.provincia,
            "localidad": lead.localidad,
        },
    }
    await publish_event(
        topic=kafka_settings.topic_resumen_solicitado,
        key=str(lead.id),
        event_type="ResumenSolicitado",
        payload=payload,
        correlation_id=correlation_id,
    )


async def stop_producer() -> None:
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
