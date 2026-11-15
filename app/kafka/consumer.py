import json
import logging
from datetime import datetime, timezone
from typing import Optional

from aiokafka import AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from app.database import SessionLocal
from app.kafka.config import (
    kafka_enabled,
    kafka_settings,
    kafka_topics,
    leads_publica_resumen,
    _seguridad,
)
from app.kafka.producer import publish_resumen_solicitado
from app.model import Lead
from app.model.nivel_calificacion import NivelCalificacion
from app.model.nombre_estados import NombreEstados

logger = logging.getLogger(__name__)

_consumer_task: Optional[object] = None
_consumer: Optional[AIOKafkaConsumer] = None


async def handle_lead_calificado(message_value: dict) -> None:
    payload = message_value.get("payload", message_value)
    lead_id = payload.get("leadId")
    nivel = payload.get("nivel")
    # calificacion publica "puntos"; se tolera también "puntaje" por compatibilidad.
    puntaje = payload.get("puntos", payload.get("puntaje"))
    origen = payload.get("origen")
    motivos = payload.get("motivos", [])

    logger.info(
        "Lead calificado recibido: leadId=%s nivel=%s puntaje=%s origen=%s",
        lead_id,
        nivel,
        puntaje,
        origen,
    )

    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.nivel = nivel
            lead.puntaje = puntaje
            lead.estado = NombreEstados.CALIFICADO.value
            db.commit()
            logger.info(
                "Lead actualizado: leadId=%s nivel=%s puntaje=%s",
                lead_id,
                nivel,
                puntaje,
            )
            # Con el lead calificado, pedir el resumen comercial a la IA, salvo que
            # lo haga el orquestador (LEADS_PUBLICA_RESUMEN=false).
            if leads_publica_resumen:
                await publish_resumen_solicitado(
                    lead,
                    correlation_id=message_value.get("correlationId"),
                )
            else:
                logger.info(
                    "Resumen de leadId=%s: lo pide el orquestador (LEADS_PUBLICA_RESUMEN=false).",
                    lead_id,
                )
        else:
            logger.warning("Lead no encontrado para actualizar: leadId=%s", lead_id)
    except Exception as exc:
        db.rollback()
        logger.exception("Error actualizando lead %s: %s", lead_id, exc)
        raise
    finally:
        db.close()


async def handle_resumen_generado(message_value: dict) -> None:
    payload = message_value.get("payload", message_value)
    lead_id = payload.get("leadId")
    resumen = payload.get("resumen")

    logger.info("Resumen generado recibido: leadId=%s", lead_id)

    if not resumen:
        logger.warning("Resumen vacío para leadId=%s; se ignora.", lead_id)
        return

    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.resumen = resumen
            lead.resumen_generado_en = datetime.now(timezone.utc)
            db.commit()
            logger.info("Resumen persistido para leadId=%s", lead_id)
        else:
            logger.warning("Lead no encontrado para guardar resumen: leadId=%s", lead_id)
    except Exception as exc:
        db.rollback()
        logger.exception("Error guardando resumen del lead %s: %s", lead_id, exc)
        raise
    finally:
        db.close()


async def _despachar(message_value: dict, topic: str) -> None:
    """Despacha el mensaje según el tópico de origen."""
    if topic == kafka_settings.topic_lead_calificado:
        await handle_lead_calificado(message_value)
    elif topic == kafka_settings.topic_resumen_generado:
        await handle_resumen_generado(message_value)
    else:
        logger.warning("Mensaje de tópico no manejado: %s", topic)


async def consume_messages(consumer: AIOKafkaConsumer) -> None:
    try:
        async for message in consumer:
            try:
                value = json.loads(message.value.decode("utf-8"))
                await _despachar(value, message.topic)
            except json.JSONDecodeError as exc:
                logger.error("Mensaje con JSON invalido: %s", exc)
            except Exception as exc:
                logger.exception("Error procesando mensaje de %s: %s", message.topic, exc)
    finally:
        await consumer.stop()


async def _asegurar_topicos() -> None:
    """Crea los tópicos que no existen (Aiven no auto-crea tópicos).

    Si no se pueden crear (falta de permisos o broker caído), se registra el
    error y se continúa: el arranque no debe depender de la creación.
    """
    try:
        admin = AIOKafkaAdminClient(
            bootstrap_servers=kafka_settings.bootstrap_servers,
            client_id=f"{kafka_settings.client_id}-admin",
            **_seguridad(),
        )
        await admin.start()
        try:
            existentes = set(await admin.list_topics())
            nuevos = [
                NewTopic(name=nombre, num_partitions=3, replication_factor=1)
                for nombre in kafka_topics
                if nombre not in existentes
            ]
            if nuevos:
                await admin.create_topics(new_topics=nuevos)
                logger.info("Tópicos creados: %s", [n.name for n in nuevos])
            else:
                logger.info("Tópicos ya existentes: %s", kafka_topics)
        finally:
            await admin.close()
    except Exception as exc:
        logger.warning("No se pudieron asegurar los tópicos de Kafka: %s", exc)


async def start_consumer() -> None:
    global _consumer, _consumer_task
    if not kafka_enabled:
        logger.info("Kafka deshabilitado: consumer no iniciado.")
        return
    if _consumer is not None:
        return

    await _asegurar_topicos()

    _consumer = AIOKafkaConsumer(
        kafka_settings.topic_lead_calificado,
        kafka_settings.topic_resumen_generado,
        bootstrap_servers=kafka_settings.bootstrap_servers,
        group_id=kafka_settings.consumer_group_id,
        client_id=kafka_settings.client_id,
        auto_offset_reset="earliest",
        value_deserializer=lambda value: value,
        **_seguridad(),
    )
    await _consumer.start()
    logger.info(
        "Consumer Kafka iniciado: topics=%s group_id=%s",
        [kafka_settings.topic_lead_calificado, kafka_settings.topic_resumen_generado],
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
