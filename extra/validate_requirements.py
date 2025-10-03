#!/usr/bin/env python3
"""
Requirements Validation Script
Tests if all required packages can be imported successfully
"""

import sys
import importlib
import subprocess

def test_import(package_name, import_name=None):
    """Test if a package can be imported"""
    if import_name is None:
        import_name = package_name.replace('-', '_')
    
    try:
        importlib.import_module(import_name)
        print(f"[OK] {package_name}")
        return True
    except ImportError as e:
        print(f"[ERROR] {package_name}: {str(e)}")
        return False

def main():
    print("="*60)
    print(" Requirements Validation Test")
    print("="*60)
    
    # Core packages to test
    packages_to_test = [
        ('flask', 'flask'),
        ('flask-sqlalchemy', 'flask_sqlalchemy'),
        ('flask-migrate', 'flask_migrate'),
        ('flask-wtf', 'flask_wtf'),
        ('flask-login', 'flask_login'),
        ('flask-bcrypt', 'flask_bcrypt'),
        ('flask-moment', 'flask_moment'),
        ('python-dotenv', 'dotenv'),
        ('werkzeug', 'werkzeug'),
        ('celery', 'celery'),
        ('redis', 'redis'),
        ('opencv-python', 'cv2'),
        ('face-recognition', 'face_recognition'),
        ('dlib', 'dlib'),
        ('PIL', 'PIL'),
        ('numpy', 'numpy'),
        ('scikit-learn', 'sklearn'),
        ('scipy', 'scipy'),
        ('matplotlib', 'matplotlib'),
        ('geopy', 'geopy'),
        ('folium', 'folium'),
        ('geojson', 'geojson'),
        ('psycopg2-binary', 'psycopg2'),
        ('alembic', 'alembic'),
        ('WTForms', 'wtforms'),
        ('email-validator', 'email_validator'),
        ('validators', 'validators'),
        ('itsdangerous', 'itsdangerous'),
        ('markupsafe', 'markupsafe'),
        ('bleach', 'bleach'),
        ('cryptography', 'cryptography'),
        ('filetype', 'filetype'),
        ('requests', 'requests'),
        ('pytz', 'pytz'),
        ('python-dateutil', 'dateutil'),
        ('gunicorn', 'gunicorn')
    ]
    
    passed = 0
    failed = 0
    
    for package_name, import_name in packages_to_test:
        if test_import(package_name, import_name):
            passed += 1
        else:
            failed += 1
    
    print(f"\n" + "="*60)
    print(f" Results: {passed} passed, {failed} failed")
    print(f"="*60)
    
    if failed == 0:
        print("SUCCESS: All required packages are available!")
        return True
    else:
        print(f"ERROR: {failed} packages are missing or have issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)