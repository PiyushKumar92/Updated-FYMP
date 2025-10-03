#!/usr/bin/env python3
"""
Script to create announcement_read table
"""
import sqlite3
import os

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'app.db')

# Create connection
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create announcement_read table
create_table_sql = """
CREATE TABLE IF NOT EXISTS announcement_read (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    announcement_id INTEGER NOT NULL,
    read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (announcement_id) REFERENCES announcement (id),
    UNIQUE(user_id, announcement_id)
);
"""

try:
    cursor.execute(create_table_sql)
    conn.commit()
    print("SUCCESS: announcement_read table created successfully!")
except Exception as e:
    print(f"ERROR: Error creating table: {e}")
finally:
    conn.close()