from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.kafka import start_consumer, stop_consumer, stop_producer
from app.model.lead import Lead  # noqa: F401
from app.routers import leads


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear las tablas definidas por los modelos SQLAlchemy.
    Base.metadata.create_all(bind=engine)
    await start_consumer()
    yield
    await stop_consumer()
    await stop_producer()


app = FastAPI(
    title="LeadsMicroservice",
    lifespan=lifespan,
)

app.include_router(leads.router)