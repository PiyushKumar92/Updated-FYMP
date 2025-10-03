#!/usr/bin/env python3
"""
Update existing users with login data for testing
"""

import os
import sys
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def update_user_login_data():
    """Update existing users with realistic login data"""
    
    try:
        from app import create_app, db
        from app.models import User
        
        app = create_app()
        
        with app.app_context():
            users = User.query.all()
            
            for user in users:
                # Generate realistic login data
                if user.username == 'admin':
                    # Admin user - recent activity
                    user.last_login = datetime.utcnow() - timedelta(hours=2)
                    user.login_count = random.randint(15, 30)
                else:
                    # Regular users - varied activity
                    days_ago = random.randint(1, 7)
                    hours_ago = random.randint(1, 24)
                    user.last_login = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)
                    user.login_count = random.randint(3, 15)
                
                user.is_active = True
                
            db.session.commit()
            print(f"Updated login data for {len(users)} users")
            
            # Display updated data
            for user in users:
                print(f"User: {user.username}")
                print(f"  Last Login: {user.last_login}")
                print(f"  Login Count: {user.login_count}")
                print(f"  Active: {user.is_active}")
                print()
                
    except Exception as e:
        print(f"Error updating login data: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Updating user login data...")
    success = update_user_login_data()
    
    if success:
        print("Login data updated successfully!")
    else:
        print("Failed to update login data!")
        sys.exit(1)