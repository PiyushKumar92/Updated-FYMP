@echo off
echo ========================================
echo  Missing Person AI System - Quick Start
echo ========================================

echo.
echo [1/5] Installing Dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/5] Initializing Database...
if not exist "migrations" (
    flask db init
    flask db migrate -m "Initial migration"
    flask db upgrade
) else (
    echo Database already initialized
)

echo.
echo [3/5] Creating Admin User...
if not exist "admin_created.txt" (
    python create_my_admin.py
    echo admin_created > admin_created.txt
) else (
    echo Admin user already exists
)

echo.
echo [4/5] Starting Redis Server...
start "Redis Server" cmd /k "redis-server"
timeout /t 3 /nobreak > nul

echo.
echo [5/5] Starting Celery Worker...
start "Celery Worker" cmd /k "python celery_worker.py"
timeout /t 3 /nobreak > nul

echo.
echo ========================================
echo  System Ready! Starting Flask App...
echo ========================================
echo.
echo Access the system at: http://localhost:8080
echo.
python run.py

pause