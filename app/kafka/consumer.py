import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from aiokafka import AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from app.database import SessionLocal
from app.kafka.config import (
    SERVICIO,
    espera_reintento_segundos,
    kafka_enabled,
    kafka_settings,
    kafka_topics,
    reintentos_comando,
    _seguridad,
)
from app.kafka.producer import publish_dlt
from app.model import Lead
from app.model.nivel_calificacion import NivelCalificacion
from app.model.nombre_estados import NombreEstados

logger = logging.getLogger(__name__)

_consumer_task: Optional[object] = None
_consumer: Optional[AIOKafkaConsumer] = None


async def handle_actualizar_calificacion(message_value: dict) -> None:
    """Comando `ActualizarCalificacion`: guarda nivel, puntaje y estado CALIFICADO del lead."""
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
        else:
            logger.warning("Lead no encontrado para actualizar: leadId=%s", lead_id)
    except Exception as exc:
        db.rollback()
        logger.exception("Error actualizando lead %s: %s", lead_id, exc)
        raise
    finally:
        db.close()


async def handle_guardar_resumen(message_value: dict) -> None:
    """Comando `GuardarResumen`: guarda el resumen que generó la IA."""
    payload = message_value.get("payload", message_value)
    lead_id = payload.get("leadId")
    resumen = payload.get("resumen")

    logger.info("Resumen a guardar recibido: leadId=%s", lead_id)

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


# Comandos que atiende leads (contrato: docs/08 del orquestador).
_COMANDOS = {
    "ActualizarCalificacion": handle_actualizar_calificacion,
    "GuardarResumen": handle_guardar_resumen,
}


async def _despachar(message_value: dict) -> None:
    """Atiende el comando si es para leads; ignora los de otros servicios y los que no conoce."""
    if message_value.get("destino") != SERVICIO:
        return
    manejador = _COMANDOS.get(message_value.get("eventType"))
    if manejador is None:
        logger.warning("Comando desconocido para leads: %s", message_value.get("eventType"))
        return
    await manejador(message_value)


async def _procesar_con_reintentos(message) -> None:
    """Reintenta un comando que falla; si agota los intentos lo manda a `crm.dlt` y sigue con el siguiente."""
    try:
        value = json.loads(message.value.decode("utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("Mensaje con JSON invalido en %s: %s", message.topic, exc)
        return
    if not isinstance(value, dict) or value.get("destino") != SERVICIO:
        return  # no es para leads: sin trabajo ni logs de ruido
    espera = espera_reintento_segundos
    for intento in range(1, reintentos_comando + 1):
        try:
            await _despachar(value)
            return
        except Exception as exc:
            logger.warning(
                "Fallo %s (intento %s/%s): %s", value.get("eventType"), intento, reintentos_comando, exc
            )
            if intento < reintentos_comando:
                await asyncio.sleep(espera)
                espera *= 2
    logger.error("Comando %s agotó sus reintentos: se envía a la DLT.", value.get("eventType"))
    try:
        await publish_dlt(message.value, message.key)
    except Exception as exc:
        logger.exception("No se pudo enviar el comando a la DLT: %s", exc)


async def consume_messages(consumer: AIOKafkaConsumer) -> None:
    try:
        async for message in consumer:
            await _procesar_con_reintentos(message)
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
        kafka_settings.topic_comandos,
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
        [kafka_settings.topic_comandos],
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
