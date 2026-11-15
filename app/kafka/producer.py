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
    ahora = datetime.now(timezone.utc).isoformat()
    return {
        "eventId": str(uuid.uuid4()),
        "eventType": event_type,
        "version": 1,
        "occurredAt": ahora,
        "timestamp": ahora,
        "correlationId": correlation_id or str(uuid.uuid4()),
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
    patente: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> None:
    """Publica PreformularioCompletado con todos los datos que calificacion necesita.

    Viaja envuelto en el sobre común de integración (eventId, eventType,
    correlationId, timestamp, payload). El payload incluye: leadId, clienteId,
    vehiculoId, montoAnticipo, montoPermuta, permutaNoComputable,
    solicitaFinanciacion, ubicacion y patente (opcional).
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
    if patente:
        payload["patente"] = patente
    await publish_event(
        topic=kafka_settings.topic_eventos,
        key=str(lead_id),
        event_type="PreformularioCompletado",
        payload=payload,
        correlation_id=correlation_id,
    )


async def publish_dlt(mensaje_original: bytes, clave: Optional[bytes] = None) -> None:
    """Manda a `crm.dlt` el mensaje que agotó sus reintentos, tal como se recibió (con su sobre)."""
    producer = await get_producer()
    if producer is None:
        logger.info("Kafka deshabilitado: mensaje no enviado a la DLT.")
        return
    await producer.send_and_wait(kafka_settings.topic_dlt, key=clave, value=json.loads(mensaje_original))


async def stop_producer() -> None:
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
