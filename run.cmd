@echo off
setlocal enabledelayedexpansion

where python3 >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    set PYTHON=python3
) ELSE (
    where python >nul 2>&1
    IF %ERRORLEVEL% EQU 0 (
        set PYTHON=python
    ) ELSE (
        echo Error: Python is not installed.
        exit /b 1
    )
)

echo Using Python: %PYTHON%

echo Checking for venv...
IF NOT EXIST ".venv" (
    echo Initializing venv...
    %PYTHON% -m venv .venv
)

echo Activating venv...
call .venv\Scripts\activate.bat

echo Updating pip...
python -m pip install --upgrade pip

echo Updating dependencies...
pip install --upgrade -r requirements.txt

echo Launching main.py...
python src\ReqDeployer\main.py