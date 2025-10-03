# Missing Person Finder - Advanced AI System

A comprehensive Flask web application for finding missing persons using cutting-edge AI-powered face recognition, surveillance footage analysis, and location intelligence.

## 🚀 Advanced Features

### 🤖 AI-Powered Analysis
- **Face Recognition**: Advanced facial recognition using OpenCV and face_recognition
- **Multi-Modal Detection**: Face + clothing + body pose analysis
- **Real-time Processing**: Background AI analysis with live progress tracking
- **Confidence Scoring**: Detailed confidence metrics for all detections
- **Batch Processing**: Bulk analysis of surveillance footage

### 📹 Surveillance Management
- **CCTV Upload**: Upload and manage surveillance footage with metadata
- **Location Mapping**: GPS coordinate tracking and distance calculations
- **Video Analysis**: Frame-by-frame analysis with timestamp precision
- **Quality Assessment**: Video quality and resolution optimization
- **Storage Management**: Efficient file storage and retrieval

### 📍 Location Intelligence
- **Hotspot Analysis**: Identify missing person case hotspots
- **Coverage Gap Detection**: Find areas lacking CCTV coverage
- **Strategic Deployment**: Camera placement recommendations
- **Geographic Analytics**: Location-based statistics and insights
- **Distance Calculations**: Precise location matching algorithms

### 👨‍💼 Admin Dashboard
- **Case Approval System**: Admin review before AI processing
- **Real-time Monitoring**: Live AI analysis progress tracking
- **User Management**: Advanced user administration tools
- **Analytics Dashboard**: Comprehensive system analytics
- **Notification System**: Real-time alerts and updates

### 💬 Communication System
- **Real-time Chat**: User-admin communication with file sharing
- **Notification Center**: Centralized notification management
- **Announcement System**: Platform-wide announcements
- **Status Updates**: Real-time case status notifications

## 🛠️ Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up Redis (required for background processing)
```bash
# Install Redis server
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                 # macOS

# Start Redis
redis-server
```

### 3. Initialize Database
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 4. Start the Application
```bash
python run.py
```

### 5. Start Background Services
```bash
# Terminal 1: Start Celery worker
python celery_worker.py

# Terminal 2: Start AI processing
python start_ai_processing.py
```

## 🔧 Environment Variables

Create a `.env` file with the following configuration:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Database
DATABASE_URL=sqlite:///missing_person.db
# For PostgreSQL: postgresql://username:password@localhost/dbname

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

## 📊 System Architecture

### Core Components
1. **Flask Web Application**: Main web interface and API
2. **AI Location Matcher**: Advanced face recognition engine
3. **Background Processing**: Celery-based task queue
4. **Database Layer**: SQLAlchemy with migration support
5. **File Management**: Secure file upload and storage
6. **Real-time Communication**: WebSocket-based updates

### AI Processing Pipeline
1. **Case Registration**: User submits missing person case
2. **Admin Approval**: Quality review and approval process
3. **Location Matching**: Find relevant surveillance footage
4. **Face Analysis**: Extract and compare facial features
5. **Detection Scoring**: Calculate confidence metrics
6. **Result Verification**: Admin verification of detections
7. **Notification**: Real-time alerts to case owners

## 🎯 Usage Guide

### For Users
1. **Register Account**: Create user account with verification
2. **Submit Case**: Upload photos and details of missing person
3. **Wait for Approval**: Admin reviews case for quality
4. **Monitor Progress**: Track AI analysis in real-time
5. **Receive Alerts**: Get notified of potential matches
6. **Verify Results**: Review and confirm detections

### For Administrators
1. **Review Cases**: Approve/reject submitted cases
2. **Upload Footage**: Add surveillance videos with metadata
3. **Monitor AI**: Track analysis progress and results
4. **Manage Users**: User administration and support
5. **Analyze Locations**: Review coverage and hotspots
6. **Generate Reports**: Export data and analytics

## 🔒 Security Features

- **CSRF Protection**: Cross-site request forgery prevention
- **Input Validation**: Comprehensive data sanitization
- **File Security**: Secure file upload with type validation
- **Access Control**: Role-based permissions system
- **Data Encryption**: Sensitive data protection
- **Audit Logging**: Complete activity tracking

## 📈 Performance Optimization

- **Background Processing**: Non-blocking AI analysis
- **Caching**: Redis-based caching for performance
- **Database Optimization**: Indexed queries and pagination
- **File Compression**: Optimized media storage
- **CDN Ready**: Static file delivery optimization
- **Responsive Design**: Mobile-optimized interface

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation wiki

## 🔄 Version History

- **v2.0.0**: Advanced AI analysis and location intelligence
- **v1.5.0**: Real-time chat and notification system
- **v1.0.0**: Basic missing person registration and search

---

**Built with ❤️ for helping families reunite with their loved ones**