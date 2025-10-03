#!/usr/bin/env python3
"""
System Validation Script
Tests all components and dependencies
"""

import sys
import importlib
import subprocess

def test_import(module_name, description=""):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"[OK] {module_name} - {description}")
        return True
    except ImportError as e:
        print(f"[FAIL] {module_name} - {description} - Error: {e}")
        return False

def test_command(command, description=""):
    """Test if a command works"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] {description}")
            return True
        else:
            print(f"[FAIL] {description} - Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"[FAIL] {description} - Error: {e}")
        return False

def main():
    """Main validation function"""
    print("Missing Person AI - System Validation")
    print("=" * 50)
    
    # Test core dependencies
    print("\nCore Dependencies:")
    core_tests = [
        ("flask", "Flask web framework"),
        ("flask_sqlalchemy", "Database ORM"),
        ("flask_migrate", "Database migrations"),
        ("flask_wtf", "Form handling"),
        ("flask_login", "User authentication"),
        ("flask_bcrypt", "Password hashing"),
        ("celery", "Background tasks"),
        ("redis", "Cache and message broker"),
    ]
    
    core_passed = sum(test_import(module, desc) for module, desc in core_tests)
    
    # Test AI dependencies
    print("\nAI Dependencies:")
    ai_tests = [
        ("cv2", "OpenCV computer vision"),
        ("face_recognition", "Face recognition library"),
        ("dlib", "Machine learning library"),
        ("numpy", "Numerical computing"),
        ("sklearn", "Machine learning"),
        ("PIL", "Image processing"),
        ("scipy", "Scientific computing"),
        ("matplotlib", "Plotting library"),
    ]
    
    ai_passed = sum(test_import(module, desc) for module, desc in ai_tests)
    
    # Test location dependencies
    print("\nLocation Dependencies:")
    location_tests = [
        ("geopy", "Geocoding library"),
        ("folium", "Interactive maps"),
        ("geojson", "GeoJSON support"),
    ]
    
    location_passed = sum(test_import(module, desc) for module, desc in location_tests)
    
    # Test database
    print("\nDatabase:")
    db_tests = [
        ("psycopg2", "PostgreSQL adapter"),
        ("alembic", "Database migrations"),
        ("sqlalchemy", "SQL toolkit"),
    ]
    
    db_passed = sum(test_import(module, desc) for module, desc in db_tests)
    
    # Test utilities
    print("\nUtilities:")
    util_tests = [
        ("wtforms", "Form validation"),
        ("email_validator", "Email validation"),
        ("validators", "Data validators"),
        ("bleach", "HTML sanitization"),
        ("cryptography", "Cryptographic functions"),
        ("requests", "HTTP library"),
        ("jinja2", "Template engine"),
    ]
    
    util_passed = sum(test_import(module, desc) for module, desc in util_tests)
    
    # Test face recognition functionality
    print("\nFace Recognition Test:")
    try:
        import face_recognition
        import numpy as np
        from PIL import Image
        
        # Create a test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        face_locations = face_recognition.face_locations(test_image)
        print("[OK] Face recognition functionality working")
        face_test_passed = 1
    except Exception as e:
        print(f"[FAIL] Face recognition test failed: {e}")
        face_test_passed = 0
    
    # Summary
    total_tests = len(core_tests) + len(ai_tests) + len(location_tests) + len(db_tests) + len(util_tests) + 1
    total_passed = core_passed + ai_passed + location_passed + db_passed + util_passed + face_test_passed
    
    print("\n" + "=" * 50)
    print(f"VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Passed: {total_passed}/{total_tests}")
    print(f"Failed: {total_tests - total_passed}/{total_tests}")
    print(f"Success Rate: {(total_passed/total_tests)*100:.1f}%")
    
    if total_passed == total_tests:
        print("\nALL TESTS PASSED! System is ready to use.")
        print("Run 'setup_system.bat' to initialize the system.")
    else:
        print(f"\nWARNING: {total_tests - total_passed} tests failed. Check the errors above.")
        if total_passed >= total_tests * 0.8:
            print("Most components are working. System should still function.")
        else:
            print("Please fix the failed dependencies before proceeding.")
    
    return total_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)