@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo  CMPE 272 GitHub Issues Service
echo  Non-Docker Setup
echo ========================================
echo.

REM Check for .env
if not exist ".env" (
    echo ERROR: .env file was not found.
    echo.
    echo Create a .env file before running the service.
    echo.
    pause
    exit /b 1
)

REM Check Python
python --version >nul 2>&1

if errorlevel 1 (
    echo ERROR: Python is not installed or is not in PATH.
    echo.
    echo Install Python and try again.
    pause
    exit /b 1
)

REM Create virtual environment if needed
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv

    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo.
echo Installing dependencies...
echo.

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Starting FastAPI
echo ========================================
echo.
echo API:     http://localhost:8000
echo Swagger: http://localhost:8000/docs
echo Health:  http://localhost:8000/healthz
echo.
echo Press CTRL+C to stop the server.
echo.

REM Open Swagger shortly after server starts
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000/docs"

".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000

endlocal