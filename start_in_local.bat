@echo off
setlocal
cd /d "%~dp0"
call "%~dp0install_local.bat"
if errorlevel 1 exit /b 1
echo [marksix-rd] local dashboard http://localhost:8501
echo [marksix-rd] local api       http://localhost:8000/docs
start "marksix-api" cmd /k "cd /d %~dp0 && call .venv\Scripts\activate.bat && set PYTHONPATH=src && uvicorn app.api:app --host 0.0.0.0 --port 8000 --app-dir ."
call .venv\Scripts\activate.bat
set PYTHONPATH=src
streamlit run app/dashboard.py --server.port 8501
endlocal
