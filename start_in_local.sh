#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
"$(dirname "$0")/install_local.sh"
echo "[marksix-rd] local dashboard http://localhost:8501"
echo "[marksix-rd] local api       http://localhost:8000/docs"
source .venv/bin/activate
export PYTHONPATH=src
uvicorn app.api:app --host 0.0.0.0 --port 8000 --app-dir . &
api_pid=$!
trap 'kill "$api_pid" 2>/dev/null || true' EXIT
streamlit run app/dashboard.py --server.port 8501
