#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-0.0.0.0}"

GATEWAY_PORT="${GATEWAY_PORT:-8000}"
TRIAGE_PORT="${TRIAGE_PORT:-8001}"
KNOWLEDGE_PORT="${KNOWLEDGE_PORT:-8002}"
FACILITY_PORT="${FACILITY_PORT:-8003}"
TRANSPORT_PORT="${TRANSPORT_PORT:-8004}"
CHAT_PORT="${CHAT_PORT:-8005}"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON="python"
else
  echo "Python was not found."
  exit 1
fi

cleanup() {
  if [[ -n "${PIDS:-}" ]]; then
    kill ${PIDS} >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

"$PYTHON" -m uvicorn backend.services.knowledge.main:app --host "$HOST" --port "$KNOWLEDGE_PORT" --reload &
P1=$!
"$PYTHON" -m uvicorn backend.services.facility.main:app --host "$HOST" --port "$FACILITY_PORT" --reload &
P2=$!
"$PYTHON" -m uvicorn backend.services.transport.main:app --host "$HOST" --port "$TRANSPORT_PORT" --reload &
P3=$!
"$PYTHON" -m uvicorn backend.services.triage.main:app --host "$HOST" --port "$TRIAGE_PORT" --reload &
P4=$!
"$PYTHON" -m uvicorn backend.services.chat.main:app --host "$HOST" --port "$CHAT_PORT" --reload &
P5=$!
"$PYTHON" -m uvicorn backend.services.gateway.main:app --host "$HOST" --port "$GATEWAY_PORT" --reload &
P6=$!

PIDS="$P1 $P2 $P3 $P4 $P5 $P6"

echo "GenAI Practitioner v2 services:"
echo "  gateway   -> http://$HOST:$GATEWAY_PORT"
echo "  triage    -> http://$HOST:$TRIAGE_PORT"
echo "  knowledge -> http://$HOST:$KNOWLEDGE_PORT"
echo "  facility  -> http://$HOST:$FACILITY_PORT"
echo "  transport -> http://$HOST:$TRANSPORT_PORT"
echo "  chat      -> http://$HOST:$CHAT_PORT"

wait
