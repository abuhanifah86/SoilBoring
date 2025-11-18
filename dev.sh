#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"

if [[ -z "${UVICORN_CMD:-}" ]]; then
  if [[ -x "$ROOT_DIR/.venv/bin/uvicorn" ]]; then
    UVICORN_CMD="$ROOT_DIR/.venv/bin/uvicorn"
  else
    UVICORN_CMD="uvicorn"
  fi
fi

log() {
  printf '[dev] %s\n' "$*"
}

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM
  set +e
  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    log "Stopping backend (pid: $BACKEND_PID)…"
    kill "$BACKEND_PID"
    wait "$BACKEND_PID" 2>/dev/null
  fi
  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    log "Stopping frontend (pid: $FRONTEND_PID)…"
    kill "$FRONTEND_PID"
    wait "$FRONTEND_PID" 2>/dev/null
  fi
  set -e
  exit "$exit_code"
}

trap cleanup EXIT
trap cleanup INT TERM

if ! command -v "$UVICORN_CMD" >/dev/null 2>&1; then
  log "Could not find uvicorn command: $UVICORN_CMD"
  log "If you use a venv, set UVICORN_CMD=/path/to/uvicorn before running."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  log "npm is required to run the frontend."
  exit 1
fi

log "Starting backend on http://$BACKEND_HOST:$BACKEND_PORT"
"$UVICORN_CMD" backend.app.main:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT" &
BACKEND_PID=$!

log "Starting frontend on http://$FRONTEND_HOST:$FRONTEND_PORT"
(cd frontend && npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT") &
FRONTEND_PID=$!

log "Backend PID: $BACKEND_PID"
log "Frontend PID: $FRONTEND_PID"
log "Press Ctrl+C to stop both services."

wait -n "$BACKEND_PID" "$FRONTEND_PID"
