from fastapi import FastAPI

from app.infrastructure.api.routers import clasificar, health

app = FastAPI(title="LLM-JALA", version="0.1.0")
app.include_router(health.router)
app.include_router(clasificar.router)
