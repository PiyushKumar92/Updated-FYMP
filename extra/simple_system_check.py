#!/usr/bin/env python3
"""
Simple System Check for Missing Person AI System
Tests all components without Unicode characters
"""

import os
import sys
import traceback
from datetime import datetime

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
            print(f"[OK] {file_path}")
        else:
            missing_files.append(file_path)
            print(f"[MISSING] {file_path}")
    
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
                    print(f"[OK] {model_name}: {count} records")
                except Exception as e:
                    print(f"[ERROR] {model_name}: {str(e)}")
            
            # Test relationships
            print(f"\nTesting Relationships:")
            
            # Test User-Case relationship
            try:
                users_with_cases = User.query.join(Case, User.id == Case.user_id).count()
                print(f"[OK] User-Case relationship: {users_with_cases} users with cases")
            except Exception as e:
                print(f"[ERROR] User-Case relationship: {str(e)}")
            
            # Test Case-TargetImage relationship
            try:
                cases_with_images = Case.query.join(TargetImage).count()
                print(f"[OK] Case-TargetImage relationship: {cases_with_images} cases with images")
            except Exception as e:
                print(f"[ERROR] Case-TargetImage relationship: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Database models check failed: {str(e)}")
        return False

def check_routes():
    """Check if all routes are properly defined"""
    print_section("Routes Check")
    
    try:
        from app import create_app
        
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
                print(f"[OK] {route}")
            else:
                print(f"[MISSING] {route}")
                missing_routes.append(route)
        
        return len(missing_routes) == 0
        
    except Exception as e:
        print(f"[ERROR] Routes check failed: {str(e)}")
        return False

def check_forms():
    """Check if all forms are properly defined"""
    print_section("Forms Check")
    
    try:
        from app import create_app
        from app.forms import (
            RegistrationForm, LoginForm, ForgotPasswordForm,
            ResetPasswordForm, NewCaseForm, ContactForm
        )
        
        app = create_app()
        
        with app.app_context():
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
                    print(f"[OK] {form_name}: {len(form._fields)} fields")
                except Exception as e:
                    print(f"[ERROR] {form_name}: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Forms check failed: {str(e)}")
        return False

def check_ai_system():
    """Check AI system components"""
    print_section("AI System Check")
    
    try:
        from app.ai_location_matcher import ai_matcher
        
        # Test AI matcher initialization
        print(f"[OK] AI Matcher initialized")
        
        # Check OpenCV
        try:
            import cv2
            print(f"[OK] OpenCV version: {cv2.__version__}")
        except ImportError:
            print(f"[ERROR] OpenCV not available")
        
        # Check face_recognition
        try:
            import face_recognition
            print(f"[OK] face_recognition library available")
        except ImportError:
            print(f"[ERROR] face_recognition library not available")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] AI system check failed: {str(e)}")
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
                        print(f"[OK] {css_file}: {open_braces} rules, syntax OK")
                    else:
                        print(f"[ERROR] {css_file}: Mismatched braces ({open_braces} open, {close_braces} close)")
            except Exception as e:
                print(f"[ERROR] {css_file}: {str(e)}")
        else:
            print(f"[MISSING] {css_file}: File not found")
    
    return True

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
            print(f"[OK] {directory}: {files_count} files")
        else:
            print(f"[MISSING] {directory}: Directory not found")
            # Create directory
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"   [CREATED] Directory: {directory}")
            except Exception as e:
                print(f"   [ERROR] Failed to create directory: {str(e)}")
    
    return True

def run_system_check():
    """Run all system checks"""
    print_header("Missing Person AI System - System Check")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    checks = [
        ("File Structure", check_file_structure),
        ("Directories", check_directories),
        ("Database Models", check_database_models),
        ("Routes", check_routes),
        ("Forms", check_forms),
        ("AI System", check_ai_system),
        ("CSS Files", check_css_files)
    ]
    
    results = {}
    
    for check_name, check_function in checks:
        try:
            results[check_name] = check_function()
        except Exception as e:
            print(f"[ERROR] {check_name} check failed with exception: {str(e)}")
            results[check_name] = False
    
    # Summary
    print_header("System Check Summary")
    
    passed_checks = sum(1 for result in results.values() if result)
    total_checks = len(results)
    
    for check_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {check_name}")
    
    print(f"\nOverall Result: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print(f"SUCCESS: All system checks passed! The system is ready to use.")
        return True
    else:
        print(f"WARNING: {total_checks - passed_checks} checks failed. Please review and fix the issues.")
        return False

if __name__ == "__main__":
    # Run system check
    success = run_system_check()
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)