from fastapi import FastAPI
from app.routers import leads

app = FastAPI(
    title = "LeadsMicroservice"
)

app.include_router(leads.router)