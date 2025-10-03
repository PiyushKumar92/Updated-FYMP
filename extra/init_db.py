#!/usr/bin/env python3
"""
Initialize database with all tables
"""

import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """Initialize database with all tables"""
    
    try:
        from app import create_app, db
        
        app = create_app()
        
        with app.app_context():
            print("Creating database tables...")
            
            # Create all tables
            db.create_all()
            
            print("Database tables created successfully!")
            
            # Create admin user if not exists
            from app.models import User
            admin = User.query.filter_by(username='admin').first()
            
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("Admin user created: username=admin, password=admin123")
            else:
                print("Admin user already exists")
                
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Initializing database...")
    success = init_database()
    
    if success:
        print("Database initialization completed successfully!")
    else:
        print("Database initialization failed!")
        sys.exit(1)