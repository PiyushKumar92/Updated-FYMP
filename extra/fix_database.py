#!/usr/bin/env python3
"""
Database Fix Script - Missing Person AI
Fixes relationship errors and resets database
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_database():
    """Fix database relationship issues"""
    
    print("Fixing Missing Person AI Database...")
    
    # Remove existing database
    db_path = "app.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Removed old database")
    
    # Remove migrations folder
    migrations_path = "migrations"
    if os.path.exists(migrations_path):
        import shutil
        shutil.rmtree(migrations_path)
        print("Removed old migrations")
    
    # Initialize fresh database
    try:
        from app import create_app, db
        from app.models import User, Case, TargetImage, SearchVideo, Sighting
        from app.models import CaseNote, SystemLog, AdminMessage, Announcement
        from app.models import BlogPost, FAQ, AISettings, ContactMessage
        from app.models import ChatRoom, ChatMessage, Notification
        from app.models import SurveillanceFootage, LocationMatch, PersonDetection
        
        app = create_app()
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("Created fresh database tables")
            
            # Create admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create sample announcement
            announcement = Announcement(
                title='Welcome to Missing Person AI',
                content='System is ready for use. Report missing persons and upload surveillance footage.',
                type='success',
                created_by=1
            )
            db.session.add(announcement)
            
            # Create sample FAQ
            faq = FAQ(
                question='How does the AI system work?',
                answer='Our AI uses advanced face recognition and clothing analysis to match missing persons with surveillance footage.',
                category='General',
                created_by=1
            )
            db.session.add(faq)
            
            db.session.commit()
            print("Created admin user and sample data")
            
        print("\nDatabase fixed successfully!")
        print("\nLogin Credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("\nStart the app with: python run.py")
        
    except Exception as e:
        print(f"Error fixing database: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    fix_database()