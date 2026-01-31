from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import configure_logging
from app.api.health import router as health_router
from app.api.ask import router as chat_router

configure_logging()

app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(chat_router)

@app.get("/")
async def root():
    return {"service": settings.app_name}
