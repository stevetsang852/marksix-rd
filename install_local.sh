#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "[marksix-rd] install local Python venv"
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1; then
    if "$c" -c 'import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)'; then
      PY="$c"
      break
    fi
  fi
done
if [[ -z "$PY" ]]; then
  echo "Need Python 3.10+. macOS: brew install python; Linux: apt install python3 python3-venv"
  exit 1
fi
if [[ ! -d .venv ]]; then
  "$PY" -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo "[marksix-rd] install done"
