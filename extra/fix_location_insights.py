#!/usr/bin/env python3
"""
Fix location insights dashboard - remove test data and ensure correct counts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import SurveillanceFootage, LocationMatch, PersonDetection

def fix_location_insights():
    """Fix location insights by removing test data"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Fixing Location Insights Dashboard")
        print("=" * 50)
        
        # Remove test surveillance footage
        test_footage = SurveillanceFootage.query.filter(
            SurveillanceFootage.video_path.like('%test%')
        ).all()
        
        if test_footage:
            print(f"Removing {len(test_footage)} test footage entries...")
            for footage in test_footage:
                print(f"  - {footage.title} ({footage.video_path})")
                db.session.delete(footage)
        else:
            print("✅ No test footage found")
        
        # Remove orphaned location matches
        orphaned_matches = LocationMatch.query.filter(
            ~LocationMatch.footage_id.in_(
                db.session.query(SurveillanceFootage.id).filter(
                    ~SurveillanceFootage.video_path.like('%test%')
                )
            )
        ).all()
        
        if orphaned_matches:
            print(f"Removing {len(orphaned_matches)} orphaned location matches...")
            for match in orphaned_matches:
                db.session.delete(match)
        
        # Remove orphaned detections
        orphaned_detections = PersonDetection.query.filter(
            ~PersonDetection.location_match_id.in_(
                db.session.query(LocationMatch.id)
            )
        ).all()
        
        if orphaned_detections:
            print(f"Removing {len(orphaned_detections)} orphaned detections...")
            for detection in orphaned_detections:
                db.session.delete(detection)
        
        # Commit changes
        try:
            db.session.commit()
            print("✅ Database cleanup completed!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {str(e)}")
            return False
        
        # Verify counts
        print("\n📊 Current Real Data Counts:")
        real_footage = SurveillanceFootage.query.filter(
            ~SurveillanceFootage.video_path.like('%test%')
        ).count()
        real_matches = LocationMatch.query.join(SurveillanceFootage).filter(
            ~SurveillanceFootage.video_path.like('%test%')
        ).count()
        real_detections = PersonDetection.query.join(LocationMatch).join(SurveillanceFootage).filter(
            ~SurveillanceFootage.video_path.like('%test%')
        ).count()
        
        print(f"  📹 Real CCTV Footage: {real_footage}")
        print(f"  🔗 Real Location Matches: {real_matches}")
        print(f"  🔍 Real Person Detections: {real_detections}")
        
        if real_footage == 0:
            print("\n✅ Location Insights will now show 0 for CCTV footage")
            print("   Upload real footage to see proper counts")
        
        return True

if __name__ == "__main__":
    success = fix_location_insights()
    if success:
        print("\n🎯 Location Insights Dashboard fixed!")
        print("   All test data removed, counts will be accurate")
    else:
        print("\n❌ Fix failed. Please check the errors above.")