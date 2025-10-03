#!/usr/bin/env python3
"""
Database migration script to add video verification fields to SearchVideo model
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def add_video_verification_fields():
    """Add video verification fields to SearchVideo table"""
    
    # Database configuration
    database_url = "sqlite:///app.db"
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Connect to database
        with engine.connect() as connection:
            print("Connected to database successfully!")
            
            # Add verification fields to SearchVideo table
            fields_to_add = [
                ('admin_verified', 'BOOLEAN DEFAULT FALSE'),
                ('verification_status', 'VARCHAR(20) DEFAULT "pending"'),
                ('verified_by', 'INTEGER'),
                ('verified_at', 'DATETIME'),
                ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
            ]
            
            for field_name, field_definition in fields_to_add:
                try:
                    # Check if column already exists
                    result = connection.execute(text(f'PRAGMA table_info("search_video")'))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if field_name not in columns:
                        # Add the column
                        alter_sql = f'ALTER TABLE "search_video" ADD COLUMN {field_name} {field_definition}'
                        connection.execute(text(alter_sql))
                        print(f"Added column: {field_name}")
                    else:
                        print(f"Column {field_name} already exists, skipping...")
                        
                except OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"Column {field_name} already exists, skipping...")
                    else:
                        print(f"Error adding column {field_name}: {e}")
            
            # Add foreign key constraint for verified_by (SQLite doesn't support adding FK constraints after table creation)
            print("Note: Foreign key constraint for verified_by should be handled in model definition")
            
            # Commit changes
            connection.commit()
            print("All video verification fields added successfully!")
            
    except Exception as e:
        print(f"Database migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Starting video verification fields migration...")
    success = add_video_verification_fields()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1)