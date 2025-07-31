$ErrorActionPreference = "Stop"

if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PYTHON = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PYTHON = "python"
} else {
    Write-Error "Python is not installed."
    exit 1
}

Write-Host "Using Python: $PYTHON"

if (-Not (Test-Path -Path ".venv")) {
    Write-Host "Initializing venv..."
    & $PYTHON -m venv .venv
}

Write-Host "Activating venv..."
& .\.venv\Scripts\Activate.ps1

Write-Host "Updating pip..."
& python.exe -m pip install --upgrade pip
Write-Host "Updating dependencies..."
& pip install --upgrade -r requirements.txt

Write-Host "Launching main.py..."
& python src/ReqDeployer/main.py