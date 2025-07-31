#!/bin/sh
set -e

if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "Error: Python is not installed."
    exit 1
fi

echo "Using Python: $PYTHON"

echo "Checking for venv..."
if [ ! -d ".venv" ]; then
    echo "Initializing venv..."
    $PYTHON -m venv .venv
fi

echo "Activating venv..."
. .venv/bin/activate

echo "Updating pip..."
python -m pip install --upgrade pip

echo "Updating dependencies..."
pip install --upgrade -r requirements.txt

echo "Launching main.py..."
python src/ReqDeployer/main.py