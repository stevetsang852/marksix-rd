# Start

| File | OS | What it does |
|---|---|---|
| install_local.sh / install_local.bat | Linux/macOS / Windows | Create `.venv` and pip install (Python 3.10+) |
| start_in_local.sh / start_in_local.bat | Linux/macOS / Windows | Install if needed, then dashboard :8501 and API :8000 |
| start_in_docker.sh / start_in_docker.bat | Linux/macOS / Windows | `docker compose up --build dashboard api` |

Linux/macOS: `chmod +x *.sh` once. Docker Desktop or engine must already be installed.
