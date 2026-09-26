"""Snapshot export of calc_runs: field assembly and file writing.

The route layer stays thin; every key that ends up in the exported JSON
is assembled here so the wire format has exactly one owner.
"""

import json
from pathlib import Path

from app.config import DATA_DIR
from app.repositories import history

SNAPSHOT_KIND = "calc_runs_snapshot"
SNAPSHOT_VERSION = 1

DEFAULT_EXPORT_PATH = DATA_DIR / "exports" / "calc_runs.json"


def build_run_row(run: dict) -> dict:
    """Assemble one export row from a history list row (result already decoded)."""
    result = run.get("result") or {}
    return {
        "run_id": run["id"],
        "wall_id": run.get("wall_id"),
        "roll_id": run.get("roll_id"),
        "wall_name": run.get("wall_name"),
        "roll_name": run.get("roll_name"),
        "rolls": result.get("rolls"),
        "drops": result.get("drops"),
        "drop_len_m": result.get("drop_len_m"),
        "pattern_m": result.get("pattern_m"),
        "strips_per_roll": result.get("strips_per_roll"),
        "note": run.get("note") or "",
        "created_at": run.get("created_at"),
    }


def build_snapshot() -> dict:
    """Serialize every calc_run into the snapshot payload."""
    rows = [build_run_row(run) for run in history.list_all_runs()]
    return {
        "kind": SNAPSHOT_KIND,
        "version": SNAPSHOT_VERSION,
        "count": len(rows),
        "items": rows,
    }


def write_snapshot(path: Path | None = None) -> tuple[Path, dict]:
    """Build the snapshot and persist it as JSON; returns (path, payload)."""
    target = Path(path) if path else DEFAULT_EXPORT_PATH
    payload = build_snapshot()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target, payload
