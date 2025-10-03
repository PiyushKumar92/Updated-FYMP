#!/usr/bin/env python3
"""
Initialize clean system - remove test data and prepare for real usage
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import SurveillanceFootage, LocationMatch, PersonDetection, Case, User

def init_clean_system():
    """Initialize a clean system ready for real usage"""
    
    app = create_app()
    
    with app.app_context():
        print("🚀 Initializing Clean System")
        print("=" * 50)
        
        # 1. Remove all test/dummy surveillance footage
        print("\n1. Cleaning surveillance footage...")
        test_footage = SurveillanceFootage.query.filter(
            SurveillanceFootage.video_path.like('%test%')
        ).all()
        
        for footage in test_footage:
            print(f"   Removing: {footage.title}")
            db.session.delete(footage)
        
        # 2. Remove orphaned location matches
        print("\n2. Cleaning location matches...")
        orphaned_matches = LocationMatch.query.filter(
            ~LocationMatch.footage_id.in_(
                db.session.query(SurveillanceFootage.id).filter(
                    ~SurveillanceFootage.video_path.like('%test%')
                )
            )
        ).all()
        
        for match in orphaned_matches:
            print(f"   Removing orphaned match: {match.id}")
            db.session.delete(match)
        
        # 3. Remove orphaned person detections
        print("\n3. Cleaning person detections...")
        orphaned_detections = PersonDetection.query.filter(
            ~PersonDetection.location_match_id.in_(
                db.session.query(LocationMatch.id)
            )
        ).all()
        
        for detection in orphaned_detections:
            print(f"   Removing orphaned detection: {detection.id}")
            db.session.delete(detection)
        
        # 4. Reset case statuses if needed
        print("\n4. Checking case statuses...")
        processing_cases = Case.query.filter_by(status='Processing').all()
        for case in processing_cases:
            # Check if case has any real footage matches
            real_matches = LocationMatch.query.join(SurveillanceFootage).filter(
                LocationMatch.case_id == case.id,
                ~SurveillanceFootage.video_path.like('%test%')
            ).count()
            
            if real_matches == 0:
                case.status = 'Pending Approval'
                print(f"   Reset case {case.id} to Pending Approval (no real footage)")
        
        # 5. Commit all changes
        try:
            db.session.commit()
            print("\n✅ System cleanup completed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during cleanup: {str(e)}")
            return False
        
        # 6. Show final statistics
        print("\n📊 Clean System Statistics:")
        print(f"   👥 Total Users: {User.query.count()}")
        print(f"   📁 Total Cases: {Case.query.count()}")
        print(f"   ⏳ Pending Approval: {Case.query.filter_by(status='Pending Approval').count()}")
        print(f"   ✅ Approved Cases: {Case.query.filter_by(status='Approved').count()}")
        print(f"   🎥 Real Footage: {SurveillanceFootage.query.filter(~SurveillanceFootage.video_path.like('%test%')).count()}")
        print(f"   🔗 Location Matches: {LocationMatch.query.count()}")
        print(f"   🔍 Person Detections: {PersonDetection.query.count()}")
        
        print("\n🎯 System is now clean and ready for real usage!")
        print("\nNext steps:")
        print("1. Admin can review pending cases")
        print("2. Upload real CCTV footage for locations")
        print("3. Approve cases when footage is available")
        print("4. AI will automatically start analysis")
        
        return True

if __name__ == "__main__":
    success = init_clean_system()
    if success:
        print("\n🚀 System initialization complete!")
    else:
        print("\n❌ System initialization failed.")