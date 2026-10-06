#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "[marksix-rd] Docker start (dashboard :8501, api :8000)"
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found. Install Docker Desktop or docker engine, then rerun."
  exit 1
fi
docker compose up --build dashboard api
