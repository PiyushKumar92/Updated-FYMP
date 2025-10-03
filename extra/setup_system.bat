@echo off
echo ========================================
echo   Missing Person AI - System Setup
echo ========================================
echo.

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.11+
    pause
    exit /b 1
)

echo ✅ Python found
echo.

:: Install main requirements
echo 📦 Installing main dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install main requirements
    pause
    exit /b 1
)

echo ✅ Main dependencies installed
echo.

:: Install dlib with fallback
echo 🔧 Setting up dlib (face recognition)...
python install_dlib.py
echo.

:: Check Redis
echo 🔍 Checking Redis...
redis-server --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Redis not found. Installing Redis...
    echo 📥 Downloading Redis for Windows...
    
    :: Create Redis directory
    if not exist "redis" mkdir redis
    cd redis
    
    :: Download and extract Redis (using curl if available)
    curl -L -o redis.zip https://github.com/microsoftarchive/redis/releases/download/win-3.0.504/Redis-x64-3.0.504.zip
    if errorlevel 1 (
        echo ❌ Failed to download Redis. Please install manually.
        echo 💡 Download from: https://github.com/microsoftarchive/redis/releases
        cd ..
    ) else (
        powershell -command "Expand-Archive -Path redis.zip -DestinationPath . -Force"
        echo ✅ Redis downloaded and extracted
        cd ..
    )
) else (
    echo ✅ Redis found
)
echo.

:: Initialize database
echo 🗄️  Setting up database...
if not exist "app.db" (
    python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✅ Database initialized')"
) else (
    echo ✅ Database already exists
)
echo.

:: Create admin user
echo 👤 Creating admin user...
python -c "
from app import create_app, db
from app.models import User
from flask_bcrypt import Bcrypt

app = create_app()
bcrypt = Bcrypt(app)

with app.app_context():
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            is_admin=True,
            is_verified=True
        )
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin user created (admin@example.com / admin123)')
    else:
        print('✅ Admin user already exists')
"
echo.

:: Create startup scripts
echo 📝 Creating startup scripts...

:: Create start_redis.bat
echo @echo off > start_redis.bat
echo echo Starting Redis server... >> start_redis.bat
echo if exist "redis\redis-server.exe" ( >> start_redis.bat
echo     redis\redis-server.exe >> start_redis.bat
echo ) else ( >> start_redis.bat
echo     redis-server >> start_redis.bat
echo ) >> start_redis.bat

:: Create start_celery.bat
echo @echo off > start_celery.bat
echo echo Starting Celery worker... >> start_celery.bat
echo celery -A app.celery worker --loglevel=info --pool=solo >> start_celery.bat

:: Create start_flask.bat
echo @echo off > start_flask.bat
echo echo Starting Flask application... >> start_flask.bat
echo python run.py >> start_flask.bat

:: Create start_all.bat
echo @echo off > start_all.bat
echo echo ======================================== >> start_all.bat
echo echo   Missing Person AI - Starting System >> start_all.bat
echo echo ======================================== >> start_all.bat
echo echo. >> start_all.bat
echo echo Starting Redis... >> start_all.bat
echo start "Redis Server" start_redis.bat >> start_all.bat
echo timeout /t 3 /nobreak ^>nul >> start_all.bat
echo echo. >> start_all.bat
echo echo Starting Celery Worker... >> start_all.bat
echo start "Celery Worker" start_celery.bat >> start_all.bat
echo timeout /t 3 /nobreak ^>nul >> start_all.bat
echo echo. >> start_all.bat
echo echo Starting Flask Application... >> start_all.bat
echo timeout /t 2 /nobreak ^>nul >> start_all.bat
echo start "Flask App" start_flask.bat >> start_all.bat
echo echo. >> start_all.bat
echo echo ✅ All services started! >> start_all.bat
echo echo 🌐 Open http://localhost:5000 in your browser >> start_all.bat
echo echo 👤 Login: admin@example.com / admin123 >> start_all.bat
echo pause >> start_all.bat

echo ✅ Startup scripts created
echo.

echo ========================================
echo   🎉 Setup Complete!
echo ========================================
echo.
echo 🚀 To start the system:
echo    - Run: start_all.bat
echo.
echo 🌐 Access the application:
echo    - URL: http://localhost:5000
echo    - Admin: admin@example.com / admin123
echo.
echo 📁 Individual services:
echo    - Redis: start_redis.bat
echo    - Celery: start_celery.bat  
echo    - Flask: start_flask.bat
echo.
pause