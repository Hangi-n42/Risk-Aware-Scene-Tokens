#!/usr/bin/env bash
set -euo pipefail

HOST_ADDRESS="${RAST_API_HOST:-127.0.0.1}"
PORT="${RAST_API_PORT:-8000}"

echo "Starting RAST API on http://${HOST_ADDRESS}:${PORT}"
python -m uvicorn apps.api.main:app --host "${HOST_ADDRESS}" --port "${PORT}"
