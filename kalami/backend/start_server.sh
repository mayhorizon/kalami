#!/bin/bash
# Server startup script for Kalami backend

set -e

echo "========================================="
echo "Kalami Backend Server"
echo "========================================="
echo ""

cd "$(dirname "$0")"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "No virtual environment found. Please run ./run_tests.sh first to set up dependencies."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Warning: No .env file found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Please edit .env with your API keys before continuing."
        exit 1
    else
        echo "No .env.example found. Please create .env manually."
        exit 1
    fi
fi

echo "Starting Kalami backend server..."
echo "Server will be available at: http://0.0.0.0:8000"
echo "API docs will be available at: http://0.0.0.0:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

# Start the server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
