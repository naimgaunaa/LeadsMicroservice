import ast
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.kafka import start_consumer, stop_consumer, stop_producer
from app.model.lead import Lead  # noqa: F401
from app.routers import leads

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear las tablas definidas por los modelos SQLAlchemy.
    Base.metadata.create_all(bind=engine)
    await start_consumer()
    yield
    await stop_consumer()
    await stop_producer()


def _parse_origins(value: str | None) -> list[str]:
    if not value:
        return ["*"]
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except (ValueError, SyntaxError):
        pass
    return [origin.strip() for origin in value.split(",") if origin.strip()]


app = FastAPI(
    title="LeadsMicroservice",
    lifespan=lifespan,
)

origins = _parse_origins(os.getenv("FRONTEND_LIST"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads.router)