#!/usr/bin/env bash

set -e

cd "$(dirname "$0")"

echo "========================================"
echo " CMPE 272 GitHub Issues Service"
echo " Non-Docker Setup"
echo "========================================"
echo

# Check for .env
if [ ! -f ".env" ]; then
    echo "ERROR: .env file was not found."
    echo
    echo "Create a .env file before running the service."
    exit 1
fi

# Check Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "ERROR: Python is not installed."
    exit 1
fi

# Create virtual environment if needed
if [ ! -f ".venv/bin/python" ]; then
    echo "Creating virtual environment..."
    "$PYTHON" -m venv .venv
fi

echo
echo "Installing dependencies..."
echo

".venv/bin/python" -m pip install --upgrade pip
".venv/bin/python" -m pip install -r requirements.txt

echo
echo "========================================"
echo " Starting FastAPI"
echo "========================================"
echo
echo "API:     http://localhost:8000"
echo "Swagger: http://localhost:8000/docs"
echo "Health:  http://localhost:8000/healthz"
echo
echo "Press CTRL+C to stop the server."
echo

# Open Swagger shortly after startup
if [[ "$OSTYPE" == "darwin"* ]]; then
    (sleep 2 && open "http://localhost:8000/docs") &
elif command -v xdg-open >/dev/null 2>&1; then
    (sleep 2 && xdg-open "http://localhost:8000/docs" >/dev/null 2>&1) &
fi

exec ".venv/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port 8000