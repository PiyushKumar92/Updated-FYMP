# 🚀 Missing Person AI System - Installation Guide

## ✅ Quick Installation

### Step 1: Install All Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# (Optional - system works with defaults)
```

### Step 3: Initialize Database
```bash
# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Step 4: Create Admin User
```bash
# Create admin account
python create_my_admin.py
```

### Step 5: Start the System
```bash
# Start Redis (in separate terminal)
redis-server

# Start Celery worker (in separate terminal)
python celery_worker.py

# Start Flask application
python run.py
```

### Step 6: Access the System
- **Web Interface**: http://localhost:8080
- **Admin Login**: Use credentials created in Step 4
- **User Registration**: Available at /register

---

## 📋 System Requirements

### Python Version
- **Required**: Python 3.8 or higher
- **Recommended**: Python 3.11

### Operating System
- **Windows**: ✅ Fully supported
- **macOS**: ✅ Fully supported  
- **Linux**: ✅ Fully supported

### Hardware Requirements
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 2GB free space
- **CPU**: Any modern processor (AI processing benefits from faster CPUs)

---

## 🔧 Detailed Installation Steps

### 1. Python Environment Setup

#### Option A: Using Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv missing_person_env

# Activate virtual environment
# Windows:
missing_person_env\Scripts\activate
# macOS/Linux:
source missing_person_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Option B: Using Conda
```bash
# Create conda environment
conda create -n missing_person python=3.11
conda activate missing_person

# Install dependencies
pip install -r requirements.txt
```

### 2. System Dependencies

#### Windows
```bash
# No additional system dependencies required
# All packages install via pip
```

#### macOS
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Redis
brew install redis

# Install CMake (for dlib)
brew install cmake
```

#### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y python3-dev python3-pip
sudo apt install -y cmake build-essential
sudo apt install -y libopenblas-dev liblapack-dev
sudo apt install -y libx11-dev libgtk-3-dev

# Install Redis
sudo apt install -y redis-server
```

### 3. Database Setup

#### SQLite (Default - No setup required)
```bash
# SQLite database is created automatically
# No additional configuration needed
```

#### PostgreSQL (Production)
```bash
# Install PostgreSQL
# Windows: Download from postgresql.org
# macOS: brew install postgresql
# Linux: sudo apt install postgresql postgresql-contrib

# Create database
createdb missing_person_db

# Update .env file
DATABASE_URL=postgresql://username:password@localhost/missing_person_db
```

### 4. Redis Setup

#### Windows
```bash
# Download Redis for Windows from:
# https://github.com/microsoftarchive/redis/releases

# Or use Docker:
docker run -d -p 6379:6379 redis:alpine
```

#### macOS
```bash
# Install via Homebrew
brew install redis

# Start Redis
brew services start redis
```

#### Linux
```bash
# Install Redis
sudo apt install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

---

## 🔍 Troubleshooting

### Common Installation Issues

#### 1. dlib Installation Fails
```bash
# Windows: Install Visual Studio Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# macOS: Install Xcode Command Line Tools
xcode-select --install

# Linux: Install build essentials
sudo apt install build-essential cmake
```

#### 2. OpenCV Installation Issues
```bash
# If opencv-python fails, try:
pip install opencv-python-headless==4.8.1.78

# Or install system OpenCV:
# Ubuntu: sudo apt install python3-opencv
# macOS: brew install opencv
```

#### 3. face_recognition Installation Fails
```bash
# Install dependencies first:
pip install cmake dlib
pip install face_recognition

# If still fails, try pre-compiled wheel:
pip install --upgrade pip
pip install face_recognition --no-cache-dir
```

#### 4. Redis Connection Issues
```bash
# Check if Redis is running:
redis-cli ping

# Should return: PONG

# If not running:
# Windows: Start redis-server.exe
# macOS/Linux: redis-server
```

#### 5. Database Migration Issues
```bash
# Reset database (WARNING: Deletes all data)
rm -rf migrations/
rm app.db
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Verification Commands

#### Test All Dependencies
```bash
python validate_requirements.py
```

#### Test System Components
```bash
python simple_system_check.py
```

#### Test Full System
```bash
python final_validation.py
```

---

## 🌐 Environment Configuration

### .env File Settings
```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Database (SQLite default)
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
```

---

## 🚀 Production Deployment

### 1. Environment Setup
```bash
# Set production environment
export FLASK_ENV=production
export FLASK_DEBUG=False

# Use PostgreSQL database
export DATABASE_URL=postgresql://user:pass@localhost/missing_person_db
```

### 2. Web Server Setup
```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 run:app

# Using uWSGI
uwsgi --http :8080 --module run:app --processes 4
```

### 3. Process Management
```bash
# Using systemd (Linux)
sudo systemctl enable missing-person-app
sudo systemctl start missing-person-app

# Using supervisor
supervisorctl start missing-person-app
```

---

## ✅ Installation Verification

After installation, verify everything works:

1. **Start all services**:
   - Redis server
   - Celery worker  
   - Flask application

2. **Access web interface**: http://localhost:8080

3. **Test user registration**: Create a test account

4. **Test admin functions**: Login as admin

5. **Test case submission**: Submit a test missing person case

6. **Test AI system**: Upload surveillance footage (admin)

7. **Test chat system**: Send messages between user and admin

---

## 📞 Support

If you encounter issues:

1. **Check logs**: Look at console output for error messages
2. **Run validation**: Use provided validation scripts
3. **Check dependencies**: Ensure all packages are installed correctly
4. **Verify services**: Confirm Redis and database are running
5. **Review documentation**: Check this guide and README.md

---

## 🎉 Success!

Once installation is complete, you'll have a fully functional Missing Person AI System ready to help families reunite with their loved ones through advanced AI technology.

**System Features Available**:
- ✅ User registration and authentication
- ✅ Missing person case management  
- ✅ AI-powered facial recognition
- ✅ Surveillance footage analysis
- ✅ Real-time chat system
- ✅ Admin dashboard and controls
- ✅ Notification system
- ✅ Location-based matching