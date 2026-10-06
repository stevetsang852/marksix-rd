@echo off
setlocal
cd /d "%~dp0"
echo [marksix-rd] install local Python venv
where py >nul 2>&1 && (set PY=py -3) || (set PY=python)
%PY% -c "import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)"
if errorlevel 1 (
  echo Need Python 3.10+. Install from https://www.python.org/downloads/ and tick Add to PATH.
  exit /b 1
)
if not exist .venv (
  %PY% -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo [marksix-rd] install done
endlocal
