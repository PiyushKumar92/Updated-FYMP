# 🚀 Missing Person AI - Complete Setup Guide

## 📋 Prerequisites

### 1. Install Python 3.8+

```bash
# Check Python version
python --version
```

### 2. Install Redis (Required for AI processing)

**Windows:**

- Download Redis from: https://github.com/microsoftarchive/redis/releases
- Or use WSL: `sudo apt install redis-server`

**Linux:**

```bash
sudo apt update
sudo apt install redis-server
```

**macOS:**

```bash
brew install redis
```

## 🔧 Quick Setup (Automated)

### Step 1: Run Setup Script

```bash
cd "Missing_Person_AI-main"
python setup.py
```

## 🛠️ Manual Setup (If needed)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Create Environment File

Create `.env` file:

```env
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=sqlite:///app.db
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Step 3: Initialize Database

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## 🚀 Start the Application

### Terminal 1: Start Redis Server

```bash
redis-server
```

### Terminal 2: Start Flask App

```bash
python run.py
```

### Terminal 3: Start AI Worker (Optional)

```bash
python celery_worker.py
```

## 🌐 Access the Application

- **Main App**: http://localhost:5000
- **Mobile Access**: http://YOUR_IP:5000 (for mobile testing)

## 👤 Create Admin User

### Method 1: Using Python Shell

```bash
python
```

```python
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    admin = User(username='admin', email='admin@example.com', is_admin=True)
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print("Admin user created!")
```

### Method 2: Register normally then make admin

1. Go to http://localhost:5000/register
2. Create account
3. Run in Python shell:

```python
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='YOUR_USERNAME').first()
    user.is_admin = True
    db.session.commit()
    print("User made admin!")
```

## 📱 Testing the System

### 1. Register a Test Case

- Login as regular user
- Go to "New Case"
- Fill form with test data
- Upload sample photos

### 2. Upload CCTV Footage (Admin)

- Login as admin
- Go to "Surveillance" → "Upload Footage"
- Add location matching the test case
- Upload sample video

### 3. Check AI Results

- Admin: Go to "AI Analysis" to see results
- User: Check case details for detections

## 🔧 Troubleshooting

### Redis Connection Error

```bash
# Start Redis manually
redis-server

# Check if Redis is running
redis-cli ping
# Should return: PONG
```

### Database Issues

```bash
# Reset database
rm app.db
flask db init
flask db migrate -m "Fresh start"
flask db upgrade
```

### Port Already in Use

```bash
# Kill process on port 5000
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F
```

### Missing Dependencies

```bash
# Install specific packages
pip install flask flask-sqlalchemy flask-login
pip install opencv-python face-recognition
pip install celery redis
```

## 📂 Project Structure

```
Missing_Person_AI-main/
├── app/
│   ├── templates/          # HTML templates
│   ├── static/            # CSS, JS, uploads
│   ├── models.py          # Database models
│   ├── routes.py          # User routes
│   ├── admin.py           # Admin routes
│   └── ai_location_matcher.py  # AI engine
├── run.py                 # Main app runner
├── celery_worker.py       # Background worker
├── requirements.txt       # Dependencies
└── config.py             # Configuration
```

## 🎯 Key Features to Test

1. **User Registration & Login**
2. **Case Registration with Photos**
3. **Admin CCTV Upload**
4. **AI Location Matching**
5. **Person Detection Results**
6. **Real-time Notifications**
7. **Chat System**
8. **Mobile Responsiveness**

## 🔐 Default Login Credentials

**Admin:**

- Username: `admin`
- Password: `admin123`

**Test User:**

- Create via registration form

## 📞 Support

If you encounter issues:

1. Check Redis is running
2. Verify Python version (3.8+)
3. Ensure all dependencies installed
4. Check database migrations completed

## 🚀 Production Deployment

For production:

1. Change `SECRET_KEY` in `.env`
2. Set `FLASK_ENV=production`
3. Use PostgreSQL instead of SQLite
4. Configure proper Redis server
5. Use Gunicorn/uWSGI for serving
6. Set up reverse proxy (Nginx)

---

**Ready to start! 🎉**
