#!/usr/bin/env python3
"""
Deployment script for Missing Person Finder - Advanced AI System
"""
import os
import sys
import subprocess
import time

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print("✅ Python version check passed")
    
    # Check if Redis is available
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
    except:
        print("⚠️  Redis not available - background processing will be limited")
    
    return True

def setup_environment():
    """Set up the environment"""
    print("🌍 Setting up environment...")
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        env_content = """# Flask Configuration
SECRET_KEY=your-secret-key-change-this-in-production
FLASK_ENV=production
FLASK_DEBUG=False

# Database
DATABASE_URL=sqlite:///missing_person.db

# Redis Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AI Configuration
AI_CONFIDENCE_THRESHOLD=0.6
MAX_VIDEO_DURATION=300
FACE_DETECTION_MODEL=hog

# File Upload
MAX_CONTENT_LENGTH=500MB
UPLOAD_FOLDER=app/static/uploads

# Security
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
    else:
        print("✅ .env file already exists")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    return run_command("pip install -r requirements.txt", "Installing Python packages")

def setup_database():
    """Set up the database"""
    print("🗄️ Setting up database...")
    
    # Initialize database if needed
    if not os.path.exists('migrations'):
        run_command("flask db init", "Initializing database")
    
    # Create migration
    run_command("flask db migrate -m 'Deployment migration'", "Creating database migration")
    
    # Apply migration
    return run_command("flask db upgrade", "Applying database migration")

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        'app/static/uploads',
        'app/static/surveillance',
        'app/static/detections',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_admin_user():
    """Create admin user"""
    print("👤 Creating admin user...")
    
    admin_script = """
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123').decode('utf-8'),
            is_admin=True,
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created (username: admin, password: admin123)")
    else:
        print("✅ Admin user already exists")
"""
    
    with open('create_admin.py', 'w') as f:
        f.write(admin_script)
    
    result = run_command("python create_admin.py", "Creating admin user")
    os.remove('create_admin.py')
    return result

def start_services():
    """Start all services"""
    print("🚀 Starting services...")
    
    print("📋 To start the application, run these commands in separate terminals:")
    print("1. Main application: python run.py")
    print("2. Background worker: python celery_worker.py")
    print("3. AI processing: python start_ai_processing.py")
    print()
    print("🌐 Application will be available at: http://localhost:5000")
    print("👤 Admin login: username=admin, password=admin123")

def main():
    """Main deployment function"""
    print("🎯 Missing Person Finder - Advanced AI System Deployment")
    print("=" * 60)
    
    # Check requirements
    if not check_requirements():
        print("❌ Requirements check failed")
        sys.exit(1)
    
    # Setup steps
    setup_environment()
    
    if not install_dependencies():
        print("❌ Dependency installation failed")
        sys.exit(1)
    
    create_directories()
    
    if not setup_database():
        print("❌ Database setup failed")
        sys.exit(1)
    
    if not create_admin_user():
        print("❌ Admin user creation failed")
        sys.exit(1)
    
    start_services()
    
    print()
    print("🎉 Deployment completed successfully!")
    print("🔧 System is ready for advanced missing person detection")
    print("📊 Access admin dashboard for full system management")

if __name__ == "__main__":
    main()