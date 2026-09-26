#!/usr/bin/env bash
# Freeze-verification entry: boot an isolated backend (fresh DATA_DIR, own
# port), run scripts/verify_export_freeze.py against it, then tear it down.
#
# Exit code mirrors the Python verifier:
#   0 ok | 2 export-side failure | 3 main-DB-side failure | 4 setup failure
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${VERIFY_PORT:-9711}"
BASE_URL="http://127.0.0.1:${PORT}"

if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
else
  PY="$(command -v python3)"
fi

WORKDIR="$(mktemp -d -t wallpaper-freeze-XXXXXX)"
export DATA_DIR="${WORKDIR}/data"
SNAPSHOT="${WORKDIR}/history-export.json"
trap '[[ -n "${SERVER_PID:-}" ]] && kill "${SERVER_PID}" 2>/dev/null; rm -rf "${WORKDIR}"' EXIT

echo "[verify] DATA_DIR=${DATA_DIR}  base=${BASE_URL}"
echo "[verify] snapshot side file: ${SNAPSHOT}"

( cd "${ROOT}/backend" && "${PY}" -m uvicorn app.main:app \
    --host 127.0.0.1 --port "${PORT}" --log-level warning ) &
SERVER_PID=$!

HEALTHY=0
for _ in $(seq 1 50); do
  if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
    echo "[FAIL:SETUP] backend exited during startup" >&2
    exit 4
  fi
  if "${PY}" -c "import sys,urllib.request; urllib.request.urlopen(sys.argv[1]+'/api/health',timeout=1)" "${BASE_URL}" 2>/dev/null; then
    HEALTHY=1
    break
  fi
  sleep 0.3
done
if [[ "${HEALTHY}" -ne 1 ]]; then
  echo "[FAIL:SETUP] backend health check timed out" >&2
  exit 4
fi

"${PY}" "${ROOT}/scripts/verify_export_freeze.py" \
  --base-url "${BASE_URL}" --snapshot "${SNAPSHOT}"
