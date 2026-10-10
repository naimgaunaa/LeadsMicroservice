import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from aiokafka import AIOKafkaProducer
from app.kafka.config import kafka_settings

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


async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=kafka_settings.bootstrap_servers,
            client_id=kafka_settings.client_id,
            value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
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
    message = build_event_envelope(event_type, payload, correlation_id)
    await producer.send_and_wait(topic, key=key.encode("utf-8"), value=message)


async def publish_preformulario_completado(
    lead_id: str,
    cliente_id: str,
    vehiculo_id: str,
    correlation_id: Optional[str] = None,
) -> None:
    payload = {
        "leadId": str(lead_id),
        "clienteId": str(cliente_id),
        "vehiculoId": str(vehiculo_id),
    }
    await publish_event(
        topic=kafka_settings.topic_preformulario_completado,
        key=str(lead_id),
        event_type="PreformularioCompletado",
        payload=payload,
        correlation_id=correlation_id,
    )


async def stop_producer() -> None:
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
