from fastapi import APIRouter
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.ask import router as chat_router

api_router = APIRouter()


api_router.include_router(router=health_router)
api_router.include_router(router=chat_router, tags=["/chat"])
