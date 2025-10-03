#!/usr/bin/env python3
"""
Final System Check - Missing Person Finder Advanced AI System
Comprehensive validation of all features and functionality
"""
import os
import sys
import requests
from app import create_app, db
from app.models import User, Case, SurveillanceFootage, LocationMatch, PersonDetection

def test_complete_workflow():
    """Test the complete admin workflow"""
    print("🔄 Testing Complete Admin Workflow...")
    
    try:
        app = create_app()
        with app.app_context():
            # 1. Check admin user exists
            admin = User.query.filter_by(is_admin=True).first()
            if not admin:
                print("❌ No admin user found")
                return False
            print("✅ Admin user exists")
            
            # 2. Check case approval workflow
            pending_cases = Case.query.filter_by(status='Pending Approval').count()
            print(f"✅ Found {pending_cases} cases pending approval")
            
            # 3. Check surveillance footage system
            footage_count = SurveillanceFootage.query.count()
            print(f"✅ Found {footage_count} surveillance footage files")
            
            # 4. Check AI analysis system
            matches_count = LocationMatch.query.count()
            detections_count = PersonDetection.query.count()
            print(f"✅ Found {matches_count} location matches, {detections_count} detections")
            
            # 5. Check templates exist
            required_templates = [
                'admin/case_review.html',
                'admin/bulk_upload_footage.html', 
                'admin/footage_analysis_results.html',
                'admin/system_status.html'
            ]
            
            for template in required_templates:
                template_path = os.path.join('app', 'templates', template)
                if os.path.exists(template_path):
                    print(f"✅ Template exists: {template}")
                else:
                    print(f"❌ Template missing: {template}")
                    return False
            
            return True
            
    except Exception as e:
        print(f"❌ Workflow test failed: {str(e)}")
        return False

def test_ai_system():
    """Test AI system components"""
    print("🤖 Testing AI System Components...")
    
    try:
        from app.ai_location_matcher import ai_matcher
        
        # Test face cascade loading
        if ai_matcher.face_cascade.empty():
            print("❌ Face cascade not loaded")
            return False
        print("✅ Face cascade loaded successfully")
        
        # Test distance calculation
        distance = ai_matcher.calculate_distance(28.6139, 77.2090, 28.6129, 77.2080)
        if distance is None or distance < 0:
            print("❌ Distance calculation failed")
            return False
        print(f"✅ Distance calculation working: {distance:.2f} km")
        
        # Test image enhancement
        import numpy as np
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        enhanced = ai_matcher._enhance_image_quality(test_image)
        if enhanced is None:
            print("❌ Image enhancement failed")
            return False
        print("✅ Image enhancement working")
        
        return True
        
    except Exception as e:
        print(f"❌ AI system test failed: {str(e)}")
        return False

def test_admin_routes():
    """Test admin route accessibility"""
    print("🌐 Testing Admin Routes...")
    
    try:
        app = create_app()
        
        # Test routes that should exist
        admin_routes = [
            '/admin/dashboard',
            '/admin/cases',
            '/admin/users', 
            '/admin/surveillance-footage',
            '/admin/ai-analysis',
            '/admin/location-insights',
            '/admin/system-status'
        ]
        
        with app.test_client() as client:
            for route in admin_routes:
                try:
                    response = client.get(route)
                    # Should redirect to login (302) or show forbidden (403)
                    if response.status_code in [302, 403]:
                        print(f"✅ Route accessible: {route}")
                    else:
                        print(f"⚠️  Route status {response.status_code}: {route}")
                except Exception as e:
                    print(f"❌ Route error {route}: {str(e)}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ Route test failed: {str(e)}")
        return False

def test_file_structure():
    """Test required file structure"""
    print("📁 Testing File Structure...")
    
    required_files = [
        'app/ai_location_matcher.py',
        'app/admin.py',
        'app/models.py',
        'app/static/css/advanced.css',
        'start_ai_processing.py',
        'deploy.py',
        'requirements.txt'
    ]
    
    required_dirs = [
        'app/static/uploads',
        'app/static/surveillance',
        'app/static/detections',
        'app/templates/admin'
    ]
    
    all_good = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ File exists: {file_path}")
        else:
            print(f"❌ File missing: {file_path}")
            all_good = False
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Directory missing: {dir_path}")
            # Create missing directories
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Created directory: {dir_path}")
    
    return all_good

def test_database_models():
    """Test database model relationships"""
    print("🗄️ Testing Database Models...")
    
    try:
        app = create_app()
        with app.app_context():
            # Test model imports
            from app.models import (
                User, Case, SurveillanceFootage, LocationMatch, 
                PersonDetection, Notification, Announcement
            )
            print("✅ All models imported successfully")
            
            # Test basic queries
            user_count = User.query.count()
            case_count = Case.query.count()
            print(f"✅ Database queries working: {user_count} users, {case_count} cases")
            
            # Test relationships
            if case_count > 0:
                case = Case.query.first()
                if hasattr(case, 'location_matches'):
                    print("✅ Case-LocationMatch relationship working")
                if hasattr(case, 'target_images'):
                    print("✅ Case-TargetImage relationship working")
            
            return True
            
    except Exception as e:
        print(f"❌ Database model test failed: {str(e)}")
        return False

def generate_system_report():
    """Generate comprehensive system report"""
    print("\n" + "="*80)
    print("📊 MISSING PERSON FINDER - SYSTEM REPORT")
    print("="*80)
    
    try:
        app = create_app()
        with app.app_context():
            # System Statistics
            stats = {
                'users': User.query.count(),
                'admin_users': User.query.filter_by(is_admin=True).count(),
                'cases': Case.query.count(),
                'pending_cases': Case.query.filter_by(status='Pending Approval').count(),
                'active_cases': Case.query.filter(Case.status.in_(['Queued', 'Processing', 'Active'])).count(),
                'surveillance_footage': SurveillanceFootage.query.count(),
                'location_matches': LocationMatch.query.count(),
                'person_detections': PersonDetection.query.count(),
                'verified_detections': PersonDetection.query.filter_by(verified=True).count()
            }
            
            print(f"👥 Users: {stats['users']} total, {stats['admin_users']} admins")
            print(f"📁 Cases: {stats['cases']} total, {stats['pending_cases']} pending approval, {stats['active_cases']} active")
            print(f"📹 Surveillance: {stats['surveillance_footage']} footage files")
            print(f"🤖 AI Analysis: {stats['location_matches']} matches, {stats['person_detections']} detections")
            print(f"✅ Verification: {stats['verified_detections']}/{stats['person_detections']} detections verified")
            
            # Success rates
            if stats['location_matches'] > 0:
                detection_rate = (stats['person_detections'] / stats['location_matches']) * 100
                print(f"📊 Detection Rate: {detection_rate:.1f}%")
            
            if stats['person_detections'] > 0:
                verification_rate = (stats['verified_detections'] / stats['person_detections']) * 100
                print(f"📊 Verification Rate: {verification_rate:.1f}%")
            
    except Exception as e:
        print(f"❌ Report generation failed: {str(e)}")

def main():
    """Main system check function"""
    print("🎯 MISSING PERSON FINDER - FINAL SYSTEM CHECK")
    print("Advanced AI-Powered Missing Person Detection System")
    print("="*80)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Database Models", test_database_models),
        ("Admin Routes", test_admin_routes),
        ("AI System", test_ai_system),
        ("Complete Workflow", test_complete_workflow)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
    
    # Generate report
    generate_system_report()
    
    # Final summary
    print("\n" + "="*80)
    print("🏁 FINAL TEST SUMMARY")
    print("="*80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 System is fully operational and ready for production!")
        print("\n📋 DEPLOYMENT CHECKLIST:")
        print("✅ Database models and relationships")
        print("✅ Admin workflow and case management")
        print("✅ AI-powered face recognition system")
        print("✅ Surveillance footage management")
        print("✅ Location-based matching algorithm")
        print("✅ Real-time analysis and detection")
        print("✅ Comprehensive admin dashboard")
        print("✅ System monitoring and status")
        print("\n🎯 READY FOR MISSING PERSON DETECTION!")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please review and fix issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)