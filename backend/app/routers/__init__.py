from fastapi import APIRouter
from app.routers import estimates, history_router, rolls, settings, walls

api_router = APIRouter(prefix="/api")
api_router.include_router(walls.router)
api_router.include_router(rolls.router)
api_router.include_router(estimates.router)
api_router.include_router(history_router.router)
api_router.include_router(settings.router)
