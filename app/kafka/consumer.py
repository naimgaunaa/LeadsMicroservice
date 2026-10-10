import json
import logging
from datetime import datetime, timezone
from typing import Optional

from aiokafka import AIOKafkaConsumer
from app.kafka.config import kafka_settings

logger = logging.getLogger(__name__)

_consumer_task: Optional[object] = None
_consumer: Optional[AIOKafkaConsumer] = None


async def handle_lead_calificado(message_value: dict) -> None:
    payload = message_value.get("payload", message_value)
    lead_id = payload.get("leadId")
    nivel = payload.get("nivel")
    puntaje = payload.get("puntaje")
    origen = payload.get("origen")
    motivos = payload.get("motivos", [])

    logger.info(
        "Lead calificado recibido: leadId=%s nivel=%s puntaje=%s origen=%s",
        lead_id,
        nivel,
        puntaje,
        origen,
    )

    # TODO: actualizar el lead en la base de datos.
    # Ejemplo conceptual:
    # lead_repository.update_calificacion(
    #     lead_id=lead_id,
    #     nivel=nivel,
    #     puntaje=puntaje,
    #     origen=origen,
    #     motivos=motivos,
    #     estado="CALIFICADO",
    #     calculada_en=datetime.now(timezone.utc),
    # )


async def consume_messages(consumer: AIOKafkaConsumer) -> None:
    try:
        async for message in consumer:
            try:
                value = json.loads(message.value.decode("utf-8"))
                await handle_lead_calificado(value)
            except json.JSONDecodeError as exc:
                logger.error("Mensaje con JSON invalido: %s", exc)
            except Exception as exc:
                logger.exception("Error procesando mensaje lead-calificado: %s", exc)
    finally:
        await consumer.stop()


async def start_consumer() -> None:
    global _consumer, _consumer_task
    if _consumer is not None:
        return

    _consumer = AIOKafkaConsumer(
        kafka_settings.topic_lead_calificado,
        bootstrap_servers=kafka_settings.bootstrap_servers,
        group_id=kafka_settings.consumer_group_id,
        client_id=kafka_settings.client_id,
        auto_offset_reset="earliest",
        value_deserializer=lambda value: value,
    )
    await _consumer.start()
    logger.info(
        "Consumer Kafka iniciado: topic=%s group_id=%s",
        kafka_settings.topic_lead_calificado,
        kafka_settings.consumer_group_id,
    )

    # Se ejecuta como tarea de fondo para no bloquear el lifespan.
    import asyncio

    _consumer_task = asyncio.create_task(consume_messages(_consumer))


async def stop_consumer() -> None:
    global _consumer, _consumer_task
    if _consumer is not None:
        await _consumer.stop()
        _consumer = None
    if _consumer_task is not None:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except Exception:
            pass
        _consumer_task = None
