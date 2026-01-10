#!/bin/bash
# Test runner script for Kalami backend
# This script installs dependencies and runs the test suite

set -e  # Exit on error

echo "========================================="
echo "Kalami Backend Test Suite"
echo "========================================="
echo ""

# Navigate to backend directory
cd "$(dirname "$0")"

# Step 1: Install pip if not available
echo "[1/5] Checking Python and pip..."
if ! python3 -m pip --version > /dev/null 2>&1; then
    echo "Installing pip..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3
fi
python3 --version
python3 -m pip --version
echo ""

# Step 2: Create virtual environment (recommended)
echo "[2/5] Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
source venv/bin/activate
echo "Virtual environment activated."
echo ""

# Step 3: Install dependencies
echo "[3/5] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "Dependencies installed."
echo ""

# Step 4: Check imports
echo "[4/5] Verifying imports..."
python3 -c "
import fastapi
import uvicorn
import sqlalchemy
import pytest
print('✓ FastAPI:', fastapi.__version__)
print('✓ Uvicorn:', uvicorn.__version__)
print('✓ SQLAlchemy:', sqlalchemy.__version__)
print('✓ Pytest:', pytest.__version__)
"
echo ""

# Step 5: Run tests
echo "[5/5] Running test suite..."
echo ""
echo "========================================="
pytest tests/ -v --tb=short

# Test result
TEST_EXIT_CODE=$?
echo ""
echo "========================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed!"
else
    echo "✗ Some tests failed. See output above."
fi
echo "========================================="

exit $TEST_EXIT_CODE
