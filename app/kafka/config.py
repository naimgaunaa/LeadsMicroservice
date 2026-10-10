import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class KafkaSettings:
    bootstrap_servers: str
    topic_preformulario_completado: str
    topic_lead_calificado: str
    consumer_group_id: str
    client_id: Optional[str] = None


kafka_settings = KafkaSettings(
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    topic_preformulario_completado=os.getenv(
        "KAFKA_TOPIC_PREFORMULARIO_COMPLETADO", "preformulario-completado"
    ),
    topic_lead_calificado=os.getenv(
        "KAFKA_TOPIC_LEAD_CALIFICADO", "lead-calificado"
    ),
    consumer_group_id=os.getenv("KAFKA_CONSUMER_GROUP", "leads-service"),
    client_id=os.getenv("KAFKA_CLIENT_ID", "leads-microservice"),
)
