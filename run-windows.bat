@echo off
REM TaskFlow — one-click launcher for Windows
REM Starts PostgreSQL, backend, frontend, and opens the app in your browser.

setlocal enabledelayedexpansion

set ROOT=%~dp0
set BACKEND=%ROOT%backend
set FRONTEND=%ROOT%frontend

echo ================================================
echo   TaskFlow — starting PostgreSQL, backend, frontend
echo ================================================

REM ----- 0. Start PostgreSQL -----
echo [postgres] ensuring PostgreSQL is running...
net start postgresql >nul 2>&1 || sc start postgresql >nul 2>&1 || echo [postgres] please start PostgreSQL manually.
timeout /t 3 >nul

REM ----- Backend -----
if not exist "%BACKEND%\.venv" (
  echo [backend] creating virtual environment...
  python -m venv "%BACKEND%\.venv"
)

call "%BACKEND%\.venv\Scripts\activate.bat"

echo [backend] installing dependencies...
pip install -q -r "%BACKEND%\requirements.txt"

if not exist "%BACKEND%\.env" (
  echo [backend] copying .env.example to .env (edit it with your AI keys!)...)
  copy "%BACKEND%\.env.example" "%BACKEND%\.env"
)

echo [backend] applying migrations...
cd /d "%BACKEND%"
alembic upgrade head

echo [backend] seeding demo data...
python seed.py

echo [backend] starting uvicorn on http://localhost:8000 ...
start "TaskFlow Backend" cmd /k "cd /d ""%BACKEND%"" && call .venv\Scripts\activate.bat && uvicorn app.main:app --reload"

REM ----- Frontend -----
echo [frontend] installing npm dependencies...
cd /d "%FRONTEND%"
npm install --silent

echo [frontend] starting Vite on http://localhost:5173 ...
start "TaskFlow Frontend" cmd /k "cd /d ""%FRONTEND%"" && npm run dev"

REM ----- Wait, then open browser -----
echo Waiting for servers to start...
timeout /t 8 >nul

echo Opening http://localhost:5173 in your browser...
start http://localhost:5173

echo.
echo TaskFlow is running:
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   Docs:     http://localhost:8000/docs
echo.
echo Close the two console windows to stop the servers.
pause
