#!/usr/bin/env python3
"""
Check current system state - show real data counts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import SurveillanceFootage, LocationMatch, PersonDetection, Case, User

def check_system_state():
    """Check current system state and show real data counts"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Current System State")
        print("=" * 40)
        
        # Check surveillance footage
        total_footage = SurveillanceFootage.query.count()
        real_footage = SurveillanceFootage.query.filter(
            ~SurveillanceFootage.video_path.like('%test%')
        ).count()
        test_footage = total_footage - real_footage
        
        print(f"\n📹 Surveillance Footage:")
        print(f"   Total: {total_footage}")
        print(f"   Real: {real_footage}")
        print(f"   Test: {test_footage}")
        
        if test_footage > 0:
            print("   ⚠️  Test footage found - run cleanup script!")
        else:
            print("   ✅ No test footage found")
        
        # Check cases
        total_cases = Case.query.count()
        pending_cases = Case.query.filter_by(status='Pending Approval').count()
        approved_cases = Case.query.filter_by(status='Approved').count()
        processing_cases = Case.query.filter_by(status='Processing').count()
        
        print(f"\n📁 Cases:")
        print(f"   Total: {total_cases}")
        print(f"   Pending Approval: {pending_cases}")
        print(f"   Approved: {approved_cases}")
        print(f"   Processing: {processing_cases}")
        
        # Check location matches
        total_matches = LocationMatch.query.count()
        real_matches = LocationMatch.query.join(SurveillanceFootage).filter(
            ~SurveillanceFootage.video_path.like('%test%')
        ).count()
        
        print(f"\n🔗 Location Matches:")
        print(f"   Total: {total_matches}")
        print(f"   Real: {real_matches}")
        
        # Check users
        total_users = User.query.count()
        admin_users = User.query.filter_by(is_admin=True).count()
        regular_users = total_users - admin_users
        
        print(f"\n👥 Users:")
        print(f"   Total: {total_users}")
        print(f"   Admins: {admin_users}")
        print(f"   Regular: {regular_users}")
        
        # System status
        print(f"\n🎯 System Status:")
        if test_footage > 0:
            print("   ❌ System has test data - needs cleanup")
            print("   Run: python init_clean_system.py")
        elif real_footage == 0:
            print("   ⚠️  No CCTV footage uploaded yet")
            print("   Admin should upload surveillance footage")
        elif pending_cases > 0 and real_footage > 0:
            print("   ✅ Ready for case approval workflow")
            print("   Admin can review and approve pending cases")
        else:
            print("   ✅ System is clean and operational")
        
        return True

if __name__ == "__main__":
    check_system_state()