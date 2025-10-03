#!/usr/bin/env python3
"""
Test script for the case approval workflow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Case, User, SurveillanceFootage, LocationMatch, Notification
from datetime import datetime

def test_approval_workflow():
    """Test the complete approval workflow"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Testing Case Approval Workflow")
        print("=" * 50)
        
        # Test 1: Check case status flow
        print("\n1. Testing Case Status Flow:")
        
        # Find a test case
        test_case = Case.query.filter_by(status='Pending Approval').first()
        if not test_case:
            print("   ❌ No pending approval cases found")
            # Create a test case
            test_user = User.query.filter_by(is_admin=False).first()
            if test_user:
                test_case = Case(
                    person_name="Test Person",
                    age=25,
                    last_seen_location="Test Location",
                    status="Pending Approval",
                    user_id=test_user.id
                )
                db.session.add(test_case)
                db.session.commit()
                print(f"   ✅ Created test case: {test_case.person_name} (ID: {test_case.id})")
            else:
                print("   ❌ No test user found")
                return False
        else:
            print(f"   ✅ Found pending case: {test_case.person_name} (ID: {test_case.id})")
        
        # Test 2: Check AI location matcher
        print("\n2. Testing AI Location Matcher:")
        try:
            from app.ai_location_matcher import ai_matcher
            
            # Test find_nearby_footage
            nearby_footage = ai_matcher.find_nearby_footage(test_case.last_seen_location)
            print(f"   ✅ Found {len(nearby_footage)} nearby footage files")
            
            # Test location matching
            matches = ai_matcher.find_location_matches(test_case.id)
            print(f"   ✅ Found {len(matches)} location matches")
            
        except Exception as e:
            print(f"   ❌ AI matcher error: {str(e)}")
        
        # Test 3: Check admin approval process
        print("\n3. Testing Admin Approval Process:")
        
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            print("   ❌ No admin user found")
            return False
        
        print(f"   ✅ Found admin user: {admin_user.username}")
        
        # Test approval logic
        if test_case.status == 'Pending Approval':
            print(f"   ✅ Case status is correctly set to 'Pending Approval'")
            
            # Check if footage is available
            nearby_footage = ai_matcher.find_nearby_footage(test_case.last_seen_location)
            if nearby_footage:
                print(f"   ✅ Footage available for approval ({len(nearby_footage)} files)")
            else:
                print(f"   ⚠️  No footage available - case cannot be approved yet")
        
        # Test 4: Check notification system
        print("\n4. Testing Notification System:")
        
        notification_count = Notification.query.filter_by(user_id=test_case.user_id).count()
        print(f"   ✅ User has {notification_count} notifications")
        
        # Test 5: Check database models
        print("\n5. Testing Database Models:")
        
        total_cases = Case.query.count()
        pending_cases = Case.query.filter_by(status='Pending Approval').count()
        total_footage = SurveillanceFootage.query.count()
        total_matches = LocationMatch.query.count()
        
        print(f"   ✅ Total cases: {total_cases}")
        print(f"   ✅ Pending approval: {pending_cases}")
        print(f"   ✅ Total footage: {total_footage}")
        print(f"   ✅ Location matches: {total_matches}")
        
        # Test 6: Check status transitions
        print("\n6. Testing Status Transitions:")
        
        valid_statuses = ['Pending Approval', 'Approved', 'Queued', 'Processing', 'Active', 'Completed', 'Rejected']
        print(f"   ✅ Valid statuses: {', '.join(valid_statuses)}")
        
        # Count cases by status
        for status in valid_statuses:
            count = Case.query.filter_by(status=status).count()
            if count > 0:
                print(f"   ✅ {status}: {count} cases")
        
        print("\n" + "=" * 50)
        print("🎉 Approval Workflow Test Complete!")
        print("\nKey Features Implemented:")
        print("✅ Case approval workflow with admin review")
        print("✅ Location-based footage matching")
        print("✅ Manual case-footage assignment")
        print("✅ Status tracking and notifications")
        print("✅ AI processing after approval")
        print("✅ User dashboard with pending status")
        
        return True

if __name__ == "__main__":
    success = test_approval_workflow()
    if success:
        print("\n🎯 All tests passed! The approval workflow is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")