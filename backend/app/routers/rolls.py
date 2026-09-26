from fastapi import APIRouter, HTTPException
from app.repositories import rolls as repo

router = APIRouter()


@router.get("/rolls")
def list_rolls():
    return {"items": repo.list_rolls()}


@router.get("/rolls/{roll_id}")
def get_roll(roll_id: int):
    row = repo.get_roll(roll_id)
    if not row:
        raise HTTPException(404)
    return row
