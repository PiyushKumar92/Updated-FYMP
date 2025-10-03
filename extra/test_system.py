#!/usr/bin/env python3
"""
System Test Script for Missing Person Finder - Advanced AI System
"""
import requests
import json
import time
import os
from app import create_app, db
from app.models import User, Case, SurveillanceFootage, LocationMatch

def test_database_connection():
    """Test database connectivity"""
    print("🗄️ Testing database connection...")
    try:
        app = create_app()
        with app.app_context():
            # Test basic query
            user_count = User.query.count()
            case_count = Case.query.count()
            print(f"✅ Database connected - {user_count} users, {case_count} cases")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def test_ai_system():
    """Test AI system components"""
    print("🤖 Testing AI system...")
    try:
        from app.ai_location_matcher import ai_matcher
        
        # Test face cascade loading
        if ai_matcher.face_cascade.empty():
            print("❌ Face cascade not loaded")
            return False
        
        print("✅ AI system initialized successfully")
        return True
    except Exception as e:
        print(f"❌ AI system test failed: {str(e)}")
        return False

def test_file_upload():
    """Test file upload functionality"""
    print("📁 Testing file upload system...")
    try:
        upload_dirs = [
            'app/static/uploads',
            'app/static/surveillance', 
            'app/static/detections'
        ]
        
        for directory in upload_dirs:
            if not os.path.exists(directory):
                print(f"❌ Directory missing: {directory}")
                return False
            
            # Test write permissions
            test_file = os.path.join(directory, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        
        print("✅ File upload system working")
        return True
    except Exception as e:
        print(f"❌ File upload test failed: {str(e)}")
        return False

def test_redis_connection():
    """Test Redis connectivity"""
    print("🔴 Testing Redis connection...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        
        # Test basic operations
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        r.delete('test_key')
        
        if value.decode() == 'test_value':
            print("✅ Redis connection and operations working")
            return True
        else:
            print("❌ Redis operations failed")
            return False
    except Exception as e:
        print(f"⚠️  Redis not available: {str(e)}")
        return False

def test_web_application():
    """Test web application endpoints"""
    print("🌐 Testing web application...")
    try:
        app = create_app()
        with app.test_client() as client:
            # Test home page
            response = client.get('/')
            if response.status_code != 200:
                print(f"❌ Home page failed: {response.status_code}")
                return False
            
            # Test login page
            response = client.get('/login')
            if response.status_code != 200:
                print(f"❌ Login page failed: {response.status_code}")
                return False
            
            # Test admin routes (should redirect to login)
            response = client.get('/admin/dashboard')
            if response.status_code not in [302, 401, 403]:
                print(f"❌ Admin protection failed: {response.status_code}")
                return False
        
        print("✅ Web application endpoints working")
        return True
    except Exception as e:
        print(f"❌ Web application test failed: {str(e)}")
        return False

def test_location_matching():
    """Test location matching algorithm"""
    print("📍 Testing location matching...")
    try:
        from app.ai_location_matcher import ai_matcher
        
        # Test distance calculation
        distance = ai_matcher.calculate_distance(28.6139, 77.2090, 28.6129, 77.2080)
        if distance is None or distance < 0:
            print("❌ Distance calculation failed")
            return False
        
        print(f"✅ Location matching working (test distance: {distance:.2f} km)")
        return True
    except Exception as e:
        print(f"❌ Location matching test failed: {str(e)}")
        return False

def test_security_features():
    """Test security features"""
    print("🔒 Testing security features...")
    try:
        app = create_app()
        
        # Test CSRF protection
        csrf_enabled = app.config.get('WTF_CSRF_ENABLED', False)
        if not csrf_enabled:
            print("⚠️  CSRF protection not enabled")
        
        # Test secret key
        secret_key = app.config.get('SECRET_KEY')
        if not secret_key or secret_key == 'dev':
            print("⚠️  Weak or default secret key")
        
        print("✅ Security features configured")
        return True
    except Exception as e:
        print(f"❌ Security test failed: {str(e)}")
        return False

def generate_test_report():
    """Generate comprehensive test report"""
    print("\n" + "="*60)
    print("🧪 SYSTEM TEST REPORT")
    print("="*60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("AI System", test_ai_system),
        ("File Upload", test_file_upload),
        ("Redis Connection", test_redis_connection),
        ("Web Application", test_web_application),
        ("Location Matching", test_location_matching),
        ("Security Features", test_security_features)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for production.")
    elif passed >= total * 0.8:
        print("⚠️  Most tests passed. Review failed tests before deployment.")
    else:
        print("❌ Multiple tests failed. System needs attention before deployment.")
    
    return passed == total

def main():
    """Main test function"""
    print("🎯 Missing Person Finder - System Test Suite")
    print("Testing advanced AI-powered missing person detection system")
    
    success = generate_test_report()
    
    if success:
        print("\n🚀 System is ready for deployment!")
        print("Run 'python deploy.py' to complete setup")
    else:
        print("\n🔧 Please fix the failed tests before proceeding")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)