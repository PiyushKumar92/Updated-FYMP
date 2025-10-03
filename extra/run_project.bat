@echo off
echo ========================================
echo   Missing Person AI - Quick Start
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [1/6] Checking Python version...
python --version

echo.
echo [2/6] Installing dependencies...
pip install -r requirements.txt

echo.
echo [3/6] Setting up environment...
if not exist .env (
    echo Creating .env file...
    (
        echo SECRET_KEY=dev-secret-key-change-in-production
        echo FLASK_ENV=development
        echo FLASK_DEBUG=True
        echo DATABASE_URL=sqlite:///app.db
        echo CELERY_BROKER_URL=redis://localhost:6379/0
        echo CELERY_RESULT_BACKEND=redis://localhost:6379/0
    ) > .env
)

echo.
echo [4/6] Creating directories...
if not exist "app\static\uploads" mkdir "app\static\uploads"
if not exist "app\static\detections" mkdir "app\static\detections"
if not exist "app\static\surveillance" mkdir "app\static\surveillance"
if not exist "logs" mkdir "logs"

echo.
echo [5/6] Setting up database...
if not exist app.db (
    echo Initializing database...
    flask db init
    flask db migrate -m "Initial migration"
    flask db upgrade
) else (
    echo Database already exists, running migrations...
    flask db upgrade
)

echo.
echo [6/6] Creating admin user...
python -c "
from app import create_app, db
from app.models import User
import sys

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('✓ Admin user created (username: admin, password: admin123)')
    else:
        print('✓ Admin user already exists')
"

echo.
echo ========================================
echo   Setup Complete! 
echo ========================================
echo.
echo IMPORTANT: You need Redis server running!
echo.
echo Windows: Download from https://github.com/microsoftarchive/redis/releases
echo Or use WSL: sudo apt install redis-server
echo.
echo To start the application:
echo 1. Start Redis server in separate terminal
echo 2. Run: python run.py
echo 3. Open: http://localhost:5000
echo.
echo Admin Login:
echo Username: admin
echo Password: admin123
echo.
pause