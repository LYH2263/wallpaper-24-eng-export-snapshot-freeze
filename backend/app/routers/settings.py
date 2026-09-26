from fastapi import APIRouter
from app.repositories import settings_repo

router = APIRouter()


@router.get("/settings")
def settings():
    return settings_repo.get_all()
