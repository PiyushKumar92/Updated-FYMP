#!/usr/bin/env python3
"""
Fix SearchVideo table by adding missing columns
"""

import os
import sys
from sqlalchemy import create_engine, text

def fix_search_video_table():
    """Add missing columns to search_video table"""
    
    database_url = "sqlite:///app.db"
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            print("Connected to database successfully!")
            
            # Add missing columns to search_video table
            columns_to_add = [
                ('admin_verified', 'BOOLEAN DEFAULT 0'),
                ('verification_status', 'VARCHAR(20) DEFAULT "pending"'),
                ('verified_by', 'INTEGER'),
                ('verified_at', 'DATETIME'),
                ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
            ]
            
            for column_name, column_def in columns_to_add:
                try:
                    # Check if column exists
                    result = connection.execute(text('PRAGMA table_info(search_video)'))
                    existing_columns = [row[1] for row in result.fetchall()]
                    
                    if column_name not in existing_columns:
                        # Add the column
                        alter_sql = f'ALTER TABLE search_video ADD COLUMN {column_name} {column_def}'
                        connection.execute(text(alter_sql))
                        print(f"Added column: {column_name}")
                    else:
                        print(f"Column {column_name} already exists")
                        
                except Exception as e:
                    print(f"Error adding column {column_name}: {e}")
            
            # Commit changes
            connection.commit()
            print("All columns added successfully!")
            
    except Exception as e:
        print(f"Database fix failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Fixing search_video table...")
    success = fix_search_video_table()
    
    if success:
        print("Table fix completed successfully!")
    else:
        print("Table fix failed!")
        sys.exit(1)