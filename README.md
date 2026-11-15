# LeadsMicroservice

Microservicio de gestión de leads construido con FastAPI. Expone endpoints para crear preformularios, consultar el detalle de un lead, listar leads por estado/nivel y actualizar el estado de un lead.

## Requisitos

- Python 3.12+
- Docker (opcional)
- PostgreSQL (o cualquier base soportada por SQLAlchemy)
- Kafka

## Variables de entorno

Copia el archivo de ejemplo y ajusta los valores:

```bash
cp .env.example .env
```

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | URL de conexión a la base de datos | `postgresql://user:pass@localhost:5432/leads` |
| `FRONTEND_LIST` | Orígenes permitidos para CORS | `["http://localhost:5173"]` |
| `CLIENTES_URL` / `CLIENT_MICROSERVICE` | URL del microservicio de clientes | `http://localhost:8001` |
| `ORQUESTADOR_CLAVE_SERVICIO` | Credencial de leads ante el orquestador (API Gateway). Obligatoria si `CLIENTES_URL` apunta al orquestador (`<orquestador>/api`): se manda en `X-Clave-Servicio`, junto con `X-Origen-Servicio: leads`. Vacía si se llama a clientes directo | `(32+ caracteres)` |
| `VEHICLE_MICROSERVICE` | URL del microservicio de vehículos | `http://localhost:1001` |
| `BCRA_API` | Host de la API BCRA | `api.bcra.gob.ar` |
| `KAFKA_BOOTSTRAP_SERVERS` | Servidores Kafka | `localhost:9092` |
| `KAFKA_TOPIC_PREFORMULARIO_COMPLETADO` | Topic de salida | `preformulario-completado` |
| `KAFKA_TOPIC_LEAD_CALIFICADO` | Topic de entrada | `lead-calificado` |
| `KAFKA_TOPIC_RESUMEN_SOLICITADO` | Topic de salida (solicitud de resumen a IA) | `resumen-solicitado` |
| `KAFKA_TOPIC_RESUMEN_GENERADO` | Topic de entrada (resumen generado por IA) | `resumen-generado` |
| `LEADS_PUBLICA_RESUMEN` | Quién pide el resumen a la IA al calificarse el lead. `true` (por defecto): lo publica leads. `false`: lo publica el orquestador (`ORQUESTADOR_PUBLICA_RESUMEN=true` allá). Nunca los dos a la vez | `true` |
| `KAFKA_CONSUMER_GROUP` | Grupo consumidor | `leads-service` |
| `KAFKA_CLIENT_ID` | ID del cliente Kafka | `leads-microservice` |

## Ejecución local

1. Crear y activar un entorno virtual:

```bash
python -m venv .venv
. .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno en `.env`.

4. Iniciar el servidor:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en `http://localhost:8000`.

## Ejecución con Docker

### Construir la imagen

```bash
docker build -t leads-microservice:latest .
```

### Ejecutar el contenedor

```bash
docker run -p 8000:8000 --env-file .env leads-microservice:latest
```

### Ejecutar con docker-compose

El repositorio incluye un `docker-compose.yml` con PostgreSQL, Kafka (más Zookeeper) y el propio microservicio.

```bash
cp .env.example .env
docker compose up --build
```

La API estará en `http://localhost:8000`.

> Nota: en `.env.example` la variable `KAFKA_ENABLED` está en `true`, ya que Docker Compose levanta un broker Kafka. Para correr solo el servicio local sin Kafka, usá `KAFKA_ENABLED=false`.

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/leads` | Crear un nuevo preformulario (aceptado para procesamiento asíncrono) |
| `GET` | `/leads` | Listar leads filtrados por estado y nivel |
| `GET` | `/leads/{id_lead}` | Obtener detalle de un lead |
| `PATCH` | `/leads/{id_lead}/state` | Actualizar el estado de un lead |

Para más detalles, accede a la documentación interactiva en `/docs` o `/redoc`.