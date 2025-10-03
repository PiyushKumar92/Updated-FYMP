#!/usr/bin/env python3
"""
Check actual usernames in database
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_users():
    """Check all users in database"""
    
    try:
        from app import create_app, db
        from app.models import User
        
        app = create_app()
        
        with app.app_context():
            users = User.query.all()
            print(f"Total users in database: {len(users)}")
            print()
            
            for user in users:
                print(f"ID: {user.id}")
                print(f"Username: '{user.username}'")
                print(f"Email: '{user.email}'")
                print(f"Is Admin: {user.is_admin}")
                print(f"Is Active: {user.is_active}")
                print(f"Last Login: {user.last_login}")
                print("-" * 40)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_users()