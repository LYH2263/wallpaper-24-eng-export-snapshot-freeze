from fastapi import APIRouter

from app.repositories import history as repo
from app.services.history_export import build_snapshot

router = APIRouter()


@router.get("/runs")
def list_runs(limit: int = 50):
    return {"items": repo.list_runs(limit)}


@router.get("/export")
def export_runs():
    # Snapshot of every calc_run as JSON; field assembly lives in history_export.
    return build_snapshot(repo.all_runs())
