#!/usr/bin/env python3
"""
Database Update Script - Add new fields to Case model
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def update_database():
    """Add new fields to existing database"""
    
    print("Updating Missing Person AI Database...")
    
    try:
        from app import create_app, db
        
        app = create_app()
        
        with app.app_context():
            # Add new columns to existing table
            try:
                # Check if columns already exist
                with db.engine.connect() as conn:
                    result = conn.execute(db.text('PRAGMA table_info("case")'))
                    columns = [row[1] for row in result]
                    
                    if 'last_seen_time' not in columns:
                        conn.execute(db.text('ALTER TABLE "case" ADD COLUMN last_seen_time TIME'))
                        conn.commit()
                        print("Added last_seen_time column")
                    else:
                        print("last_seen_time column already exists")
                    
                    if 'contact_address' not in columns:
                        conn.execute(db.text('ALTER TABLE "case" ADD COLUMN contact_address TEXT'))
                        conn.commit()
                        print("Added contact_address column")
                    else:
                        print("contact_address column already exists")
                
                print("Database updated successfully!")
                
            except Exception as e:
                print(f"Error updating database: {str(e)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    update_database()