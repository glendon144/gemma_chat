#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/forward_m3_llm.sh
#   ./scripts/forward_m3_llm.sh user@M3
#
# Override either port when needed:
#   LOCAL_LLM_PORT=8081 REMOTE_LLM_PORT=8080 ./scripts/forward_m3_llm.sh user@M3

SSH_TARGET="${1:-M3}"
LOCAL_LLM_PORT="${LOCAL_LLM_PORT:-8081}"
REMOTE_LLM_PORT="${REMOTE_LLM_PORT:-8080}"

if ! command -v ssh >/dev/null 2>&1; then
  echo "Error: ssh is not installed or is not on PATH." >&2
  exit 1
fi

if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"${LOCAL_LLM_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Error: local port ${LOCAL_LLM_PORT} is already in use." >&2
  echo "Stop the existing listener or choose another LOCAL_LLM_PORT." >&2
  exit 1
fi

echo "Forwarding 127.0.0.1:${LOCAL_LLM_PORT} -> ${SSH_TARGET}:127.0.0.1:${REMOTE_LLM_PORT}"
echo "Keep this terminal open. Press Ctrl+C to stop the tunnel."

exec ssh \
  -N \
  -T \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -L "127.0.0.1:${LOCAL_LLM_PORT}:127.0.0.1:${REMOTE_LLM_PORT}" \
  "${SSH_TARGET}"
