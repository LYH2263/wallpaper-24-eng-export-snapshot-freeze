#!/usr/bin/env python3
"""Freeze verification for the history snapshot export.

Steps:
  1. Save estimate #1 (wall 1 / roll 1), remember its rolls.
  2. GET the export once (/api/export), dump the raw body to a side file, and assert the
     file contains run #1 with the rolls just observed.
  3. Save estimate #2 on a different wall/roll. Do NOT call export again.
  4. Prove the live main store moved on (run #2 present there).
  5. Re-read the side file: row count and run #1's rolls must be frozen at
     the export moment; run #2 must not appear.

Exit codes:
  0  all assertions passed
  2  export-side failure (snapshot wrong at export time, or mutated later)
  3  main-DB-side failure (live store does not reflect estimate #2)
  4  setup/infra failure (server unreachable, HTTP error, identical rolls)
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

EXIT_OK = 0
EXIT_EXPORT = 2
EXIT_DB = 3
EXIT_SETUP = 4


def fail(code, msg):
    side = {2: "EXPORT-SIDE", 3: "MAIN-DB-SIDE", 4: "SETUP"}[code]
    print(f"[FAIL:{side}] {msg}", file=sys.stderr)
    sys.exit(code)


def request(base, method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        base + path, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        fail(EXIT_SETUP, f"{method} {path} failed: {exc}")


def fetch_raw(base, path):
    try:
        return urllib.request.urlopen(base + path, timeout=10).read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        fail(EXIT_SETUP, f"GET {path} failed: {exc}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--snapshot", required=True, help="side file for the exported JSON")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    # 1. estimate #1
    r1 = request(base, "POST", "/api/estimate",
                 {"wall_id": 1, "roll_id": 1, "save": True, "note": "freeze-check-1"})
    run1, rolls1 = r1.get("run_id"), r1.get("rolls")
    if run1 is None or rolls1 is None:
        fail(EXIT_SETUP, f"estimate #1 missing run_id/rolls: {r1}")
    print(f"run #1 saved: id={run1} rolls={rolls1}")

    # 2. export once -> side file, then read it back FROM DISK
    raw = fetch_raw(base, "/api/export")
    with open(args.snapshot, "wb") as fh:
        fh.write(raw)
    print(f"export dumped to {args.snapshot} ({len(raw)} bytes)")

    with open(args.snapshot, encoding="utf-8") as fh:
        snap1 = json.load(fh)
    items1 = snap1.get("items")
    by_id1 = {it.get("id"): it for it in items1} if isinstance(items1, list) else None
    if not isinstance(items1, list) or run1 not in by_id1:
        fail(EXIT_EXPORT, f"snapshot lacks run id={run1}; keys={list(snap1)}")
    if by_id1[run1].get("rolls") != rolls1:
        fail(EXIT_EXPORT,
             f"snapshot rolls for run {run1} = {by_id1[run1].get('rolls')!r}, "
             f"estimate said {rolls1!r}")
    frozen_count = len(items1)
    print(f"snapshot at export: count={frozen_count}, run {run1} rolls={rolls1}")

    # 3. estimate #2 on a different wall/roll (no export call afterwards)
    r2 = request(base, "POST", "/api/estimate",
                 {"wall_id": 2, "roll_id": 2, "save": True, "note": "freeze-check-2"})
    run2, rolls2 = r2.get("run_id"), r2.get("rolls")
    if run2 is None or rolls2 is None:
        fail(EXIT_SETUP, f"estimate #2 missing run_id/rolls: {r2}")
    if rolls2 == rolls1:
        fail(EXIT_SETUP, f"both runs report rolls={rolls1}; freeze check cannot discriminate")
    print(f"run #2 saved (no re-export): id={run2} rolls={rolls2}")

    # 4. live main store must show BOTH runs
    live = request(base, "GET", "/api/runs?limit=50")
    live_items = live.get("items")
    live_ids = {it.get("id") for it in live_items} if isinstance(live_items, list) else set()
    if run1 not in live_ids or run2 not in live_ids:
        fail(EXIT_DB, f"live /runs missing entries: have {sorted(live_ids)}, "
                      f"need {run1},{run2}")
    live2 = next(it for it in live_items if it.get("id") == run2)
    if live2.get("result", {}).get("rolls") != rolls2:
        fail(EXIT_DB, f"live run {run2} result.rolls != {rolls2}")
    print(f"main store moved on: {len(live_items)} run(s), run {run2} rolls={rolls2}")

    # 5. re-read the side file untouched: frozen count + frozen rolls, no run #2
    with open(args.snapshot, encoding="utf-8") as fh:
        snap2 = json.load(fh)
    items2 = snap2.get("items")
    if not isinstance(items2, list):
        fail(EXIT_EXPORT, "snapshot items is not a list on re-read")
    if len(items2) != frozen_count:
        fail(EXIT_EXPORT, f"snapshot row count drifted: {frozen_count} -> {len(items2)}")
    by_id2 = {it.get("id"): it for it in items2}
    if run2 in by_id2:
        fail(EXIT_EXPORT, f"run {run2} leaked into the frozen snapshot without re-export")
    if by_id2.get(run1, {}).get("rolls") != rolls1:
        fail(EXIT_EXPORT,
             f"snapshot rolls for run {run1} drifted: {rolls1} -> "
             f"{by_id2.get(run1, {}).get('rolls')!r}")

    print(f"OK: snapshot frozen at count={frozen_count}, run {run1} rolls={rolls1}; "
          f"main store holds run {run2} rolls={rolls2}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
