"""Serialize calc_runs rows into exportable history snapshots.

Field assembly lives here (not in the router body) so the JSON shape is
reusable by the HTTP export route, file dumps and tests.
"""

from datetime import datetime, timezone

# Result keys lifted onto each item's top level so script consumers can read
# them directly (item["rolls"]) instead of digging into item["result"].
LIFTED_RESULT_KEYS = ("rolls", "drops", "strips_per_roll", "drop_len_m", "pattern_m")


def serialize_run(row: dict) -> dict:
    result = dict(row.get("result") or {})
    item = {
        "id": row["id"],
        "wall_id": row["wall_id"],
        "roll_id": row["roll_id"],
        "wall_name": row.get("wall_name"),
        "roll_name": row.get("roll_name"),
        "note": row.get("note", ""),
        "created_at": row.get("created_at"),
        "result": result,
    }
    for key in LIFTED_RESULT_KEYS:
        if key in result:
            item[key] = result[key]
    return item


def serialize_runs(runs) -> list:
    return [serialize_run(dict(r)) for r in runs]


def build_snapshot(runs) -> dict:
    items = serialize_runs(runs)
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "items": items,
    }
