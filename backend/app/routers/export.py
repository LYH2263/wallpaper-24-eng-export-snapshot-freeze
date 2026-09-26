from fastapi import APIRouter
from app.services import export_service

router = APIRouter()


@router.get("/export/runs")
def export_runs():
    path, payload = export_service.write_snapshot()
    return {"path": str(path), **payload}
