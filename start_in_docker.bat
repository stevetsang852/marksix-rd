@echo off
setlocal
cd /d "%~dp0"
echo [marksix-rd] Docker start (dashboard :8501, api :8000)
where docker >nul 2>&1
if errorlevel 1 (
  echo Docker not found. Install Docker Desktop, then rerun this file.
  exit /b 1
)
docker compose up --build dashboard api
endlocal
