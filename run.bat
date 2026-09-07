@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo  CMPE 272 GitHub Issues Service
echo ========================================
echo.

REM ------------------------------------------------------------
REM Check .env
REM ------------------------------------------------------------

if exist ".env" goto ENV_OK

echo ERROR: .env file was not found.
echo.
echo Create a .env file containing:
echo.
echo APP_GITHUB_TOKEN=your_token
echo APP_GITHUB_OWNER=your_owner
echo APP_GITHUB_REPO=your_repo
echo WEBHOOK_SECRET=your_webhook_secret
echo PORT=8000
echo.
echo Optional:
echo NGROK_AUTH_TOKEN=
echo NGROK_DOMAIN=
echo.
pause
exit /b 1


:ENV_OK

REM ------------------------------------------------------------
REM Check Docker CLI
REM ------------------------------------------------------------

docker --version >nul 2>&1
if not errorlevel 1 goto CHECK_DOCKER_ENGINE

REM Docker may be installed but missing from PATH
if exist "C:\Program Files\Docker\Docker\resources\bin\docker.exe" goto ADD_DOCKER_PATH

goto INSTALL_DOCKER


:ADD_DOCKER_PATH

echo Docker Desktop was found.
echo Adding Docker to PATH for this session...

set "PATH=%PATH%;C:\Program Files\Docker\Docker\resources\bin"

docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker CLI could not be started.
    pause
    exit /b 1
)

goto CHECK_DOCKER_ENGINE


:INSTALL_DOCKER

echo Docker Desktop is not installed.
echo.

choice /C YN /M "Would you like to install Docker Desktop now"

if errorlevel 2 goto INSTALL_CANCELLED

echo.
echo Installing Docker Desktop...
echo.

winget install --id Docker.DockerDesktop -e

if errorlevel 1 goto INSTALL_FAILED

echo.
echo Docker Desktop was installed successfully.
echo.
echo Start Docker Desktop and run this script again.
echo.
pause
exit /b 0


:INSTALL_CANCELLED

echo.
echo Docker installation cancelled.
pause
exit /b 1


:INSTALL_FAILED

echo.
echo ERROR: Docker Desktop installation failed.
pause
exit /b 1


REM ------------------------------------------------------------
REM Check Docker engine
REM ------------------------------------------------------------

:CHECK_DOCKER_ENGINE

docker info >nul 2>&1

if not errorlevel 1 goto DOCKER_READY

echo Docker Desktop is installed but is not running.
echo Starting Docker Desktop...
echo.

if not exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" goto DOCKER_EXE_MISSING

start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

set DOCKER_ATTEMPTS=0


:WAIT_FOR_DOCKER

docker info >nul 2>&1
if not errorlevel 1 goto DOCKER_READY

set /a DOCKER_ATTEMPTS=%DOCKER_ATTEMPTS%+1

if %DOCKER_ATTEMPTS% GEQ 24 goto DOCKER_TIMEOUT

echo Waiting for Docker...
timeout /t 5 /nobreak >nul

goto WAIT_FOR_DOCKER


:DOCKER_EXE_MISSING

echo ERROR: Docker Desktop executable could not be found.
pause
exit /b 1


:DOCKER_TIMEOUT

echo.
echo ERROR: Docker did not start within 2 minutes.
echo Open Docker Desktop manually and try again.
echo.
pause
exit /b 1


:DOCKER_READY

echo Docker is ready.
echo.


REM ------------------------------------------------------------
REM Build and start application
REM ------------------------------------------------------------

echo Building and starting Docker containers...
echo.

docker compose up --build -d

if errorlevel 1 goto COMPOSE_FAILED


REM ------------------------------------------------------------
REM Wait for FastAPI
REM ------------------------------------------------------------

echo.
echo Waiting for the API to become ready...

set API_ATTEMPTS=0


:WAIT_FOR_API

curl.exe -f -s http://localhost:8000/healthz >nul 2>&1

if not errorlevel 1 goto API_READY

set /a API_ATTEMPTS=%API_ATTEMPTS%+1

if %API_ATTEMPTS% GEQ 30 goto API_FAILED

echo Waiting for API...
timeout /t 2 /nobreak >nul

goto WAIT_FOR_API


:COMPOSE_FAILED

echo.
echo ERROR: Docker Compose failed to start the service.
echo.
echo Recent Docker logs:
docker compose logs --tail=50
echo.
pause
exit /b 1


:API_FAILED

echo.
echo ERROR: The container started, but the API did not become healthy.
echo.

echo Container status:
docker compose ps

echo.
echo Recent Docker logs:
docker compose logs --tail=100

echo.
pause
exit /b 1


REM ------------------------------------------------------------
REM Success
REM ------------------------------------------------------------

:API_READY

echo.
echo ========================================
echo  Service started successfully!
echo ========================================
echo.
echo API:
echo http://localhost:8000
echo.
echo Swagger:
echo http://localhost:8000/docs
echo.
echo Health:
echo http://localhost:8000/healthz
echo.
echo To stop the service:
echo docker compose down
echo.

start "" "http://localhost:8000/docs"

pause

endlocal