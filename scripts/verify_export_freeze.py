#!/usr/bin/env python3
"""Verify that the calc_runs export is a frozen point-in-time snapshot.

Flow:
  1. save calc run A via POST /api/estimate, record its rolls
  2. call GET /api/export/runs, land the payload in a sidecar file,
     assert run A's rolls are readable from the file
  3. save calc run B (different wall/roll pair) WITHOUT calling export
  4. re-read the sidecar file: row count and run A's rolls must still
     be exactly what they were at export time

Exit codes:
  0  pass
  1  precondition/infra (API unreachable, malformed payloads)
  2  export side   (snapshot file missing/stale/mutated/wrong content)
  3  main DB side  (estimate not persisted, /api/runs disagrees)

Env:
  API_BASE        default http://localhost:9700
  EXPORT_SIDECAR  default <repo>/scripts/out/calc_runs_snapshot.json
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

EXIT_OK = 0
EXIT_INFRA = 1
EXIT_EXPORT_SIDE = 2
EXIT_MAINDB_SIDE = 3

API_BASE = os.environ.get("API_BASE", "http://localhost:9700").rstrip("/")
SIDECAR = Path(
    os.environ.get(
        "EXPORT_SIDECAR",
        Path(__file__).resolve().parent / "out" / "calc_runs_snapshot.json",
    )
)


def fail(code: int, side: str, msg: str) -> "NoReturn":  # noqa: F821
    print(f"FAIL[{side}] {msg}", file=sys.stderr)
    sys.exit(code)


class ApiError(Exception):
    """The API answered with a non-2xx status (distinct from unreachable)."""

    def __init__(self, status: int, detail: str):
        super().__init__(f"HTTP {status}: {detail}")
        self.status = status


def http(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ApiError(exc.code, exc.read().decode("utf-8", "replace")) from exc
    except urllib.error.URLError as exc:
        fail(EXIT_INFRA, "infra", f"{method} {url} unreachable: {exc}")
    except json.JSONDecodeError as exc:
        fail(EXIT_INFRA, "infra", f"{method} {url} returned non-JSON: {exc}")


def pick_clean(items: list, what: str) -> list:
    clean = [x for x in items if x.get("data_quality") != "dirty"]
    if not clean:
        fail(EXIT_INFRA, "infra", f"no clean {what} seeded")
    return clean


def save_estimate(wall_id: int, roll_id: int, note: str) -> dict:
    try:
        payload = http(
            "POST",
            "/api/estimate",
            {"wall_id": wall_id, "roll_id": roll_id, "save": True, "note": note},
        )
    except ApiError as exc:
        fail(EXIT_MAINDB_SIDE, "main-db", f"estimate(wall={wall_id}, roll={roll_id}) rejected: {exc}")
    if not payload.get("run_id") or "rolls" not in payload:
        fail(
            EXIT_MAINDB_SIDE,
            "main-db",
            f"estimate(wall={wall_id}, roll={roll_id}) not persisted: {payload}",
        )
    return payload


def find_run(run_id: int) -> dict | None:
    for item in http("GET", "/api/runs?limit=500").get("items", []):
        if item.get("id") == run_id:
            return item
    return None


def read_sidecar() -> dict:
    try:
        return json.loads(SIDECAR.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(EXIT_EXPORT_SIDE, "export", f"sidecar file missing: {SIDECAR}")
    except json.JSONDecodeError as exc:
        fail(EXIT_EXPORT_SIDE, "export", f"sidecar file not parseable JSON: {exc}")


def snapshot_row(snapshot: dict, run_id: int) -> dict | None:
    for item in snapshot.get("items", []):
        if item.get("run_id") == run_id:
            return item
    return None


def main() -> int:
    walls = pick_clean(http("GET", "/api/walls").get("items", []), "walls")
    rolls = pick_clean(http("GET", "/api/rolls").get("items", []), "rolls")
    wall_a, roll_a = walls[0], rolls[0]
    # run B must differ from run A: prefer a different wall, else a different roll
    wall_b = walls[1] if len(walls) > 1 else walls[0]
    roll_b = rolls[0] if len(walls) > 1 else rolls[min(1, len(rolls) - 1)]
    if (wall_b["id"], roll_b["id"]) == (wall_a["id"], roll_a["id"]):
        fail(EXIT_INFRA, "infra", "cannot build a distinct second wall/roll pair")

    # 1) first calc run, record its rolls
    run_a = save_estimate(wall_a["id"], roll_a["id"], "freeze-verify A")
    run_a_id, run_a_rolls = run_a["run_id"], run_a["rolls"]
    print(f"run A saved: id={run_a_id} rolls={run_a_rolls}")

    # 2) export -> sidecar file, assert run A's rolls are readable from it
    try:
        export_payload = http("GET", "/api/export/runs")
    except ApiError as exc:
        fail(EXIT_EXPORT_SIDE, "export", f"export endpoint failed: {exc}")
    if export_payload.get("kind") != "calc_runs_snapshot":
        fail(EXIT_EXPORT_SIDE, "export", f"unexpected export kind: {export_payload.get('kind')!r}")
    try:
        SIDECAR.parent.mkdir(parents=True, exist_ok=True)
        SIDECAR.write_text(json.dumps(export_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        fail(EXIT_EXPORT_SIDE, "export", f"cannot land sidecar file {SIDECAR}: {exc}")

    snap = read_sidecar()
    exported_count = snap.get("count")
    if exported_count != len(snap.get("items", [])):
        fail(EXIT_EXPORT_SIDE, "export", f"count={exported_count} but items={len(snap.get('items', []))}")
    row_a = snapshot_row(snap, run_a_id)
    if row_a is None:
        fail(EXIT_EXPORT_SIDE, "export", f"run {run_a_id} missing from export file")
    if row_a.get("rolls") != run_a_rolls:
        fail(EXIT_EXPORT_SIDE, "export", f"run {run_a_id} rolls in file={row_a.get('rolls')} != {run_a_rolls}")
    print(f"export frozen at count={exported_count}, run A rolls readable from {SIDECAR}")

    # main DB must agree with what the estimate returned
    db_a = find_run(run_a_id)
    if db_a is None or (db_a.get("result") or {}).get("rolls") != run_a_rolls:
        fail(EXIT_MAINDB_SIDE, "main-db", f"run {run_a_id} rolls in DB mismatch: {db_a}")

    # 3) second calc run, different wall/roll pair, NO export call afterwards
    run_b = save_estimate(wall_b["id"], roll_b["id"], "freeze-verify B")
    run_b_id = run_b["run_id"]
    print(f"run B saved: id={run_b_id} rolls={run_b['rolls']} (no export called)")

    if find_run(run_b_id) is None:
        fail(EXIT_MAINDB_SIDE, "main-db", f"run {run_b_id} not visible in /api/runs after save")

    # 4) re-read the sidecar directly: must still be frozen at export time
    snap2 = read_sidecar()
    if snap2.get("count") != exported_count or len(snap2.get("items", [])) != exported_count:
        fail(
            EXIT_EXPORT_SIDE,
            "export",
            f"snapshot no longer frozen: count {exported_count} -> {snap2.get('count')}",
        )
    row_a2 = snapshot_row(snap2, run_a_id)
    if row_a2 is None or row_a2.get("rolls") != run_a_rolls:
        fail(EXIT_EXPORT_SIDE, "export", f"run {run_a_id} rolls drifted in snapshot file")
    if snapshot_row(snap2, run_b_id) is not None:
        fail(EXIT_EXPORT_SIDE, "export", f"run {run_b_id} leaked into snapshot without a new export")

    print(f"snapshot still frozen: count={exported_count}, run A rolls={run_a_rolls}")
    print("PASS: export snapshot is frozen at export time")
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ApiError as exc:
        fail(EXIT_INFRA, "infra", f"unexpected API error: {exc}")
