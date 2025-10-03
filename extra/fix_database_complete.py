#!/usr/bin/env python3
"""
Complete database initialization and fix script
"""

import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_database():
    """Complete database initialization"""
    
    try:
        from app import create_app, db
        from app.models import (User, Case, TargetImage, SearchVideo, Sighting, 
                               CaseNote, SystemLog, AdminMessage, Announcement, 
                               AnnouncementRead, BlogPost, FAQ, AISettings, 
                               ContactMessage, ChatRoom, ChatMessage, Notification, 
                               SurveillanceFootage, LocationMatch, PersonDetection)
        
        app = create_app()
        
        with app.app_context():
            print("Dropping existing tables...")
            db.drop_all()
            
            print("Creating all database tables...")
            db.create_all()
            
            print("Database tables created successfully!")
            
            # Create admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True,
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create a test user
            user = User(
                username='testuser',
                email='test@example.com',
                is_admin=False,
                is_active=True
            )
            user.set_password('test123')
            db.session.add(user)
            
            db.session.commit()
            print("Admin user created: username=admin, password=admin123")
            print("Test user created: username=testuser, password=test123")
            
            # Verify tables
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"\nCreated {len(tables)} tables:")
            for table in sorted(tables):
                print(f"  - {table}")
                
    except Exception as e:
        print(f"Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("Fixing database completely...")
    success = fix_database()
    
    if success:
        print("\nDatabase initialization completed successfully!")
    else:
        print("\nDatabase initialization failed!")
        sys.exit(1)