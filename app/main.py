from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import configure_logging
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router


configure_logging()

app = FastAPI(title=settings.app_name)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    return {"service": settings.app_name}
