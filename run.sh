#!/usr/bin/env bash

# Make executable once: chmod +x run.sh

# Stop on unhandled errors
set -e

# Always run from the directory containing this script
cd "$(dirname "$0")"

echo "========================================"
echo " CMPE 272 GitHub Issues Service"
echo "========================================"
echo


# ------------------------------------------------------------
# Check .env
# ------------------------------------------------------------

if [ ! -f ".env" ]; then
    echo "ERROR: .env file was not found."
    echo
    echo "Create a .env file containing:"
    echo
    echo "APP_GITHUB_TOKEN=your_token"
    echo "APP_GITHUB_OWNER=your_owner"
    echo "APP_GITHUB_REPO=your_repo"
    echo "WEBHOOK_SECRET=your_webhook_secret"
    echo "PORT=8000"
    echo
    echo "Optional:"
    echo "NGROK_AUTH_TOKEN="
    echo "NGROK_DOMAIN="
    echo
    exit 1
fi


# ------------------------------------------------------------
# Check Docker installation
# ------------------------------------------------------------

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker is not installed."
    echo

    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Install Docker Desktop for macOS:"
        echo "https://www.docker.com/products/docker-desktop/"
    else
        echo "Install Docker for Linux:"
        echo "https://docs.docker.com/engine/install/"
    fi

    echo
    exit 1
fi


# ------------------------------------------------------------
# Check Docker Compose
# ------------------------------------------------------------

if ! docker compose version >/dev/null 2>&1; then
    echo "ERROR: Docker Compose is not available."
    echo "Install Docker Compose and try again."
    exit 1
fi


# ------------------------------------------------------------
# Check whether Docker is running
# ------------------------------------------------------------

if ! docker info >/dev/null 2>&1; then
    echo "Docker is installed but is not running."
    echo

    if [[ "$OSTYPE" == "darwin"* ]]; then

        echo "Starting Docker Desktop..."

        open -a Docker

        DOCKER_ATTEMPTS=0

        while ! docker info >/dev/null 2>&1; do
            DOCKER_ATTEMPTS=$((DOCKER_ATTEMPTS + 1))

            if [ "$DOCKER_ATTEMPTS" -ge 24 ]; then
                echo
                echo "ERROR: Docker did not start within 2 minutes."
                echo "Open Docker Desktop manually and try again."
                exit 1
            fi

            echo "Waiting for Docker..."
            sleep 5
        done

    else

        echo "Attempting to start Docker..."

        if command -v systemctl >/dev/null 2>&1; then
            sudo systemctl start docker || true
        fi

        DOCKER_ATTEMPTS=0

        while ! docker info >/dev/null 2>&1; do
            DOCKER_ATTEMPTS=$((DOCKER_ATTEMPTS + 1))

            if [ "$DOCKER_ATTEMPTS" -ge 24 ]; then
                echo
                echo "ERROR: Docker did not start within 2 minutes."
                echo "Start Docker manually and run this script again."
                exit 1
            fi

            echo "Waiting for Docker..."
            sleep 5
        done
    fi
fi


echo "Docker is ready."
echo


# ------------------------------------------------------------
# Build and start application
# ------------------------------------------------------------

echo "Building and starting Docker containers..."
echo

if ! docker compose up --build -d; then
    echo
    echo "ERROR: Docker Compose failed to start the service."
    echo
    echo "Recent Docker logs:"
    docker compose logs --tail=50
    echo
    exit 1
fi


# ------------------------------------------------------------
# Check curl
# ------------------------------------------------------------

if ! command -v curl >/dev/null 2>&1; then
    echo
    echo "ERROR: curl is required for the health check."
    echo "Install curl and run this script again."
    exit 1
fi


# ------------------------------------------------------------
# Wait for FastAPI
# ------------------------------------------------------------

echo
echo "Waiting for the API to become ready..."

API_ATTEMPTS=0

while ! curl -f -s http://localhost:8000/healthz >/dev/null 2>&1; do

    API_ATTEMPTS=$((API_ATTEMPTS + 1))

    if [ "$API_ATTEMPTS" -ge 30 ]; then
        echo
        echo "ERROR: The container started, but the API did not become healthy."
        echo

        echo "Container status:"
        docker compose ps

        echo
        echo "Recent Docker logs:"
        docker compose logs --tail=100

        echo
        exit 1
    fi

    echo "Waiting for API..."
    sleep 2
done


# ------------------------------------------------------------
# Success
# ------------------------------------------------------------

echo
echo "========================================"
echo " Service started successfully!"
echo "========================================"
echo
echo "API:"
echo "http://localhost:8000"
echo
echo "Swagger:"
echo "http://localhost:8000/docs"
echo
echo "Health:"
echo "http://localhost:8000/healthz"
echo
echo "To stop the service:"
echo "docker compose down"
echo


# ------------------------------------------------------------
# Open Swagger automatically
# ------------------------------------------------------------

if [[ "$OSTYPE" == "darwin"* ]]; then
    open "http://localhost:8000/docs" >/dev/null 2>&1 &
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:8000/docs" >/dev/null 2>&1 &
fi