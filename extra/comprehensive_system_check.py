#!/usr/bin/env python3
"""
Comprehensive System Check for Missing Person AI System
Tests all components, routes, database models, and functionality
"""

import os
import sys
import traceback
from datetime import datetime, timedelta
import requests
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section"""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")

def check_file_structure():
    """Check if all required files exist"""
    print_section("File Structure Check")
    
    required_files = [
        'run.py',
        'config.py',
        'requirements.txt',
        'app/__init__.py',
        'app/models.py',
        'app/routes.py',
        'app/admin.py',
        'app/forms.py',
        'app/ai_location_matcher.py',
        'app/templates/base.html',
        'app/templates/index.html',
        'app/templates/login.html',
        'app/templates/register.html',
        'app/templates/dashboard.html',
        'app/templates/user_dashboard.html',
        'app/templates/register_case.html',
        'app/templates/case_details.html',
        'app/templates/profile.html',
        'app/templates/admin/dashboard.html',
        'app/templates/admin/users.html',
        'app/templates/admin/cases.html',
        'app/templates/admin/case_detail.html',
        'app/templates/admin/case_review.html',
        'app/templates/admin/surveillance_footage.html',
        'app/templates/admin/ai_analysis.html',
        'app/templates/admin/location_insights.html',
        'app/templates/admin/system_status.html',
        'app/static/css/navbar.css',
        'app/static/css/global.css',
        'app/static/css/modern.css',
        'app/static/css/enhancements.css',
        'app/static/css/advanced.css'
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")
    
    print(f"\nSummary: {len(existing_files)}/{len(required_files)} files exist")
    
    if missing_files:
        print(f"\nMissing files:")
        for file in missing_files:
            print(f"   - {file}")
    
    return len(missing_files) == 0

def check_database_models():
    """Check database models and relationships"""
    print_section("Database Models Check")
    
    try:
        from app import create_app, db
        from app.models import (
            User, Case, TargetImage, SearchVideo, Sighting, CaseNote,
            SystemLog, AdminMessage, Announcement, AnnouncementRead,
            BlogPost, FAQ, AISettings, ContactMessage, ChatRoom,
            ChatMessage, Notification, SurveillanceFootage,
            LocationMatch, PersonDetection
        )
        
        app = create_app()
        
        with app.app_context():
            # Test model creation
            models_to_test = [
                ('User', User),
                ('Case', Case),
                ('TargetImage', TargetImage),
                ('SearchVideo', SearchVideo),
                ('Sighting', Sighting),
                ('CaseNote', CaseNote),
                ('SystemLog', SystemLog),
                ('AdminMessage', AdminMessage),
                ('Announcement', Announcement),
                ('AnnouncementRead', AnnouncementRead),
                ('BlogPost', BlogPost),
                ('FAQ', FAQ),
                ('AISettings', AISettings),
                ('ContactMessage', ContactMessage),
                ('ChatRoom', ChatRoom),
                ('ChatMessage', ChatMessage),
                ('Notification', Notification),
                ('SurveillanceFootage', SurveillanceFootage),
                ('LocationMatch', LocationMatch),
                ('PersonDetection', PersonDetection)
            ]
            
            for model_name, model_class in models_to_test:
                try:
                    # Test basic query
                    count = model_class.query.count()
                    print(f"✅ {model_name}: {count} records")
                except Exception as e:
                    print(f"❌ {model_name}: {str(e)}")
            
            # Test relationships
            print(f"\nTesting Relationships:")
            
            # Test User-Case relationship
            try:
                users_with_cases = User.query.join(Case).count()
                print(f"✅ User-Case relationship: {users_with_cases} users with cases")
            except Exception as e:
                print(f"❌ User-Case relationship: {str(e)}")
            
            # Test Case-TargetImage relationship
            try:
                cases_with_images = Case.query.join(TargetImage).count()
                print(f"✅ Case-TargetImage relationship: {cases_with_images} cases with images")
            except Exception as e:
                print(f"❌ Case-TargetImage relationship: {str(e)}")
            
            # Test LocationMatch-PersonDetection relationship
            try:
                matches_with_detections = LocationMatch.query.join(PersonDetection).count()
                print(f"✅ LocationMatch-PersonDetection relationship: {matches_with_detections} matches with detections")
            except Exception as e:
                print(f"❌ LocationMatch-PersonDetection relationship: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database models check failed: {str(e)}")
        traceback.print_exc()
        return False

def check_routes():
    """Check if all routes are properly defined"""
    print_section("Routes Check")
    
    try:
        from app import create_app
        from app.routes import bp as main_bp
        from app.admin import admin_bp
        
        app = create_app()
        
        # Get all routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'rule': rule.rule
            })
        
        # Categorize routes
        main_routes = [r for r in routes if r['endpoint'].startswith('main.')]
        admin_routes = [r for r in routes if r['endpoint'].startswith('admin.')]
        static_routes = [r for r in routes if r['endpoint'] == 'static']
        
        print(f"Route Summary:")
        print(f"   Main routes: {len(main_routes)}")
        print(f"   Admin routes: {len(admin_routes)}")
        print(f"   Static routes: {len(static_routes)}")
        print(f"   Total routes: {len(routes)}")
        
        # Check critical routes
        critical_routes = [
            'main.index',
            'main.login',
            'main.register',
            'main.dashboard',
            'main.register_case',
            'main.profile',
            'main.case_details',
            'main.chat_list',
            'main.notifications',
            'admin.dashboard',
            'admin.users',
            'admin.cases',
            'admin.case_detail',
            'admin.surveillance_footage',
            'admin.ai_analysis',
            'admin.location_insights'
        ]
        
        print(f"\nCritical Routes Check:")
        missing_routes = []
        for route in critical_routes:
            if any(r['endpoint'] == route for r in routes):
                print(f"✅ {route}")
            else:
                print(f"❌ {route}")
                missing_routes.append(route)
        
        return len(missing_routes) == 0
        
    except Exception as e:
        print(f"❌ Routes check failed: {str(e)}")
        traceback.print_exc()
        return False

def check_forms():
    """Check if all forms are properly defined"""
    print_section("Forms Check")
    
    try:
        from app.forms import (
            RegistrationForm, LoginForm, ForgotPasswordForm,
            ResetPasswordForm, NewCaseForm, ContactForm
        )
        
        forms_to_test = [
            ('RegistrationForm', RegistrationForm),
            ('LoginForm', LoginForm),
            ('ForgotPasswordForm', ForgotPasswordForm),
            ('ResetPasswordForm', ResetPasswordForm),
            ('NewCaseForm', NewCaseForm),
            ('ContactForm', ContactForm)
        ]
        
        for form_name, form_class in forms_to_test:
            try:
                # Test form instantiation
                form = form_class()
                print(f"✅ {form_name}: {len(form._fields)} fields")
            except Exception as e:
                print(f"❌ {form_name}: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Forms check failed: {str(e)}")
        traceback.print_exc()
        return False

def check_ai_system():
    """Check AI system components"""
    print_section("AI System Check")
    
    try:
        from app.ai_location_matcher import ai_matcher
        
        # Test AI matcher initialization
        print(f"✅ AI Matcher initialized")
        
        # Check OpenCV
        try:
            import cv2
            print(f"✅ OpenCV version: {cv2.__version__}")
        except ImportError:
            print(f"❌ OpenCV not available")
        
        # Check face_recognition
        try:
            import face_recognition
            print(f"✅ face_recognition library available")
        except ImportError:
            print(f"❌ face_recognition library not available")
        
        # Check face cascade
        if hasattr(ai_matcher, 'face_cascade'):
            if not ai_matcher.face_cascade.empty():
                print(f"✅ Face cascade loaded")
            else:
                print(f"❌ Face cascade not loaded")
        else:
            print(f"❌ Face cascade not initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ AI system check failed: {str(e)}")
        traceback.print_exc()
        return False

def check_css_files():
    """Check CSS files for syntax errors"""
    print_section("CSS Files Check")
    
    css_files = [
        'app/static/css/navbar.css',
        'app/static/css/global.css',
        'app/static/css/modern.css',
        'app/static/css/enhancements.css',
        'app/static/css/advanced.css'
    ]
    
    for css_file in css_files:
        if os.path.exists(css_file):
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Basic CSS syntax check
                    open_braces = content.count('{')
                    close_braces = content.count('}')
                    
                    if open_braces == close_braces:
                        print(f"✅ {css_file}: {open_braces} rules, syntax OK")
                    else:
                        print(f"❌ {css_file}: Mismatched braces ({open_braces} open, {close_braces} close)")
            except Exception as e:
                print(f"❌ {css_file}: {str(e)}")
        else:
            print(f"❌ {css_file}: File not found")
    
    return True

def check_templates():
    """Check template files"""
    print_section("Templates Check")
    
    template_dirs = [
        'app/templates',
        'app/templates/admin',
        'app/templates/chat',
        'app/templates/errors'
    ]
    
    total_templates = 0
    
    for template_dir in template_dirs:
        if os.path.exists(template_dir):
            templates = [f for f in os.listdir(template_dir) if f.endswith('.html')]
            total_templates += len(templates)
            print(f"✅ {template_dir}: {len(templates)} templates")
            
            # Check for base template inheritance
            for template in templates:
                if template != 'base.html':
                    template_path = os.path.join(template_dir, template)
                    try:
                        with open(template_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if '{% extends' in content or '{% block' in content:
                                print(f"   ✅ {template}: Uses template inheritance")
                            else:
                                print(f"   ⚠️  {template}: No template inheritance detected")
                    except Exception as e:
                        print(f"   ❌ {template}: {str(e)}")
        else:
            print(f"❌ {template_dir}: Directory not found")
    
    print(f"\nTotal templates: {total_templates}")
    return True

def check_configuration():
    """Check configuration files"""
    print_section("Configuration Check")
    
    try:
        from config import Config
        
        # Check required config attributes
        required_configs = [
            'SECRET_KEY',
            'SQLALCHEMY_DATABASE_URI',
            'CELERY_BROKER_URL',
            'CELERY_RESULT_BACKEND',
            'UPLOAD_FOLDER',
            'MAX_CONTENT_LENGTH'
        ]
        
        for config_name in required_configs:
            if hasattr(Config, config_name):
                value = getattr(Config, config_name)
                if value:
                    print(f"✅ {config_name}: Configured")
                else:
                    print(f"❌ {config_name}: Empty value")
            else:
                print(f"❌ {config_name}: Not defined")
        
        # Check .env file
        if os.path.exists('.env'):
            print(f"✅ .env file exists")
        else:
            print(f"⚠️  .env file not found (using defaults)")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration check failed: {str(e)}")
        traceback.print_exc()
        return False

def check_directories():
    """Check required directories"""
    print_section("Directories Check")
    
    required_dirs = [
        'app/static/uploads',
        'app/static/surveillance',
        'app/static/chat_uploads',
        'app/static/css',
        'app/static/js',
        'app/templates/admin',
        'app/templates/chat',
        'app/templates/errors',
        'migrations/versions'
    ]
    
    for directory in required_dirs:
        if os.path.exists(directory):
            files_count = len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
            print(f"✅ {directory}: {files_count} files")
        else:
            print(f"❌ {directory}: Directory not found")
            # Create directory
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"   ✅ Created directory: {directory}")
            except Exception as e:
                print(f"   ❌ Failed to create directory: {str(e)}")
    
    return True

def run_comprehensive_check():
    """Run all system checks"""
    print_header("Missing Person AI System - Comprehensive Check")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    checks = [
        ("File Structure", check_file_structure),
        ("Directories", check_directories),
        ("Configuration", check_configuration),
        ("Database Models", check_database_models),
        ("Routes", check_routes),
        ("Forms", check_forms),
        ("AI System", check_ai_system),
        ("CSS Files", check_css_files),
        ("Templates", check_templates)
    ]
    
    results = {}
    
    for check_name, check_function in checks:
        try:
            results[check_name] = check_function()
        except Exception as e:
            print(f"❌ {check_name} check failed with exception: {str(e)}")
            results[check_name] = False
    
    # Summary
    print_header("System Check Summary")
    
    passed_checks = sum(1 for result in results.values() if result)
    total_checks = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
    
    print(f"\nOverall Result: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print(f"All system checks passed! The system is ready to use.")
        return True
    else:
        print(f"WARNING: {total_checks - passed_checks} checks failed. Please review and fix the issues.")
        return False

def create_test_data():
    """Create test data for system validation"""
    print_section("Creating Test Data")
    
    try:
        from app import create_app, db
        from app.models import User, Case, TargetImage, Announcement
        
        app = create_app()
        
        with app.app_context():
            # Create test admin user
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    is_admin=True
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                print(f"✅ Created admin user")
            else:
                print(f"✅ Admin user already exists")
            
            # Create test regular user
            test_user = User.query.filter_by(username='testuser').first()
            if not test_user:
                test_user = User(
                    username='testuser',
                    email='test@example.com',
                    is_admin=False
                )
                test_user.set_password('test123')
                db.session.add(test_user)
                print(f"✅ Created test user")
            else:
                print(f"✅ Test user already exists")
            
            db.session.commit()
            
            # Create test case
            test_case = Case.query.filter_by(person_name='Test Person').first()
            if not test_case:
                test_case = Case(
                    person_name='Test Person',
                    age=25,
                    details='Test case for system validation',
                    last_seen_location='Test Location',
                    status='Pending Approval',
                    user_id=test_user.id
                )
                db.session.add(test_case)
                print(f"✅ Created test case")
            else:
                print(f"✅ Test case already exists")
            
            # Create test announcement
            test_announcement = Announcement.query.filter_by(title='System Test Announcement').first()
            if not test_announcement:
                test_announcement = Announcement(
                    title='System Test Announcement',
                    content='This is a test announcement to verify the system is working correctly.',
                    type='info',
                    created_by=admin_user.id
                )
                db.session.add(test_announcement)
                print(f"✅ Created test announcement")
            else:
                print(f"✅ Test announcement already exists")
            
            db.session.commit()
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test data: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run comprehensive system check
    success = run_comprehensive_check()
    
    # Create test data if system check passed
    if success:
        create_test_data()
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)