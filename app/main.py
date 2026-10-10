from fastapi import FastAPI
from app.routers import leads
from app.database import engine, Base
from app.model.lead import Lead

app = FastAPI(
    title="LeadsMicroservice"
)

# Crear las tablas definidas por los modelos SQLAlchemy.
Base.metadata.create_all(bind=engine)

app.include_router(leads.router)