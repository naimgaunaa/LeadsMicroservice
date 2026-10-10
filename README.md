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
| `VEHICLE_MICROSERVICE` | URL del microservicio de vehículos | `http://localhost:1001` |
| `BCRA_API` | Host de la API BCRA | `api.bcra.gob.ar` |
| `KAFKA_BOOTSTRAP_SERVERS` | Servidores Kafka | `localhost:9092` |
| `KAFKA_TOPIC_PREFORMULARIO_COMPLETADO` | Topic de salida | `preformulario-completado` |
| `KAFKA_TOPIC_LEAD_CALIFICADO` | Topic de entrada | `lead-calificado` |
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

### Ejecutar con docker-compose (ejemplo)

```yaml
version: "3.8"
services:
  leads:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - kafka
```

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/leads` | Crear un nuevo preformulario (aceptado para procesamiento asíncrono) |
| `GET` | `/leads` | Listar leads filtrados por estado y nivel |
| `GET` | `/leads/{id_lead}` | Obtener detalle de un lead |
| `PATCH` | `/leads/{id_lead}/state` | Actualizar el estado de un lead |

Para más detalles, accede a la documentación interactiva en `/docs` o `/redoc`.