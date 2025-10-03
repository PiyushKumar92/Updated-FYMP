#!/usr/bin/env python3
"""
Check existing database tables
"""

import os
import sys
from sqlalchemy import create_engine, text

def check_tables():
    """Check existing tables in database"""
    
    database_url = "sqlite:///app.db"
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            print("Connected to database successfully!")
            
            # Get all tables
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table}")
            
            # Check SearchVideo table specifically
            if 'search_video' in tables:
                print("\nSearchVideo table columns:")
                result = connection.execute(text('PRAGMA table_info("search_video")'))
                for row in result.fetchall():
                    print(f"  - {row[1]} ({row[2]})")
            else:
                print("\nSearchVideo table not found!")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_tables()