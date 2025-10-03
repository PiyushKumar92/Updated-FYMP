#!/usr/bin/env python3
"""
Clean up test/dummy data from the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import SurveillanceFootage, LocationMatch, PersonDetection

def cleanup_test_data():
    """Remove all test/dummy data from database"""
    
    app = create_app()
    
    with app.app_context():
        print("🧹 Cleaning up test/dummy data...")
        print("=" * 40)
        
        # Remove test surveillance footage
        test_footage = SurveillanceFootage.query.filter(
            SurveillanceFootage.video_path.like('%test%')
        ).all()
        
        if test_footage:
            print(f"Removing {len(test_footage)} test footage entries...")
            for footage in test_footage:
                print(f"  - {footage.title}")
                db.session.delete(footage)
        else:
            print("No test footage found")
        
        # Remove any location matches with test data
        test_matches = LocationMatch.query.join(SurveillanceFootage).filter(
            SurveillanceFootage.video_path.like('%test%')
        ).all()
        
        if test_matches:
            print(f"Removing {len(test_matches)} test location matches...")
            for match in test_matches:
                db.session.delete(match)
        
        # Remove any person detections with test data
        test_detections = PersonDetection.query.join(LocationMatch).join(SurveillanceFootage).filter(
            SurveillanceFootage.video_path.like('%test%')
        ).all()
        
        if test_detections:
            print(f"Removing {len(test_detections)} test detections...")
            for detection in test_detections:
                db.session.delete(detection)
        
        # Commit changes
        try:
            db.session.commit()
            print("✅ Test data cleanup completed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during cleanup: {str(e)}")
            return False
        
        # Show current counts
        print("\n📊 Current database counts:")
        print(f"  - Surveillance Footage: {SurveillanceFootage.query.count()}")
        print(f"  - Location Matches: {LocationMatch.query.count()}")
        print(f"  - Person Detections: {PersonDetection.query.count()}")
        
        return True

if __name__ == "__main__":
    success = cleanup_test_data()
    if success:
        print("\n🎯 Database is now clean and ready for real data!")
    else:
        print("\n❌ Cleanup failed. Please check the errors above.")