#!/usr/bin/env python3
"""
Check duplicate cases in database
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_duplicate_cases():
    """Check for duplicate cases"""
    
    try:
        from app import create_app, db
        from app.models import Case
        
        app = create_app()
        
        with app.app_context():
            cases = Case.query.all()
            print(f"Total cases: {len(cases)}")
            
            for case in cases:
                print(f"Case {case.id}: {case.person_name} - {case.created_at}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_duplicate_cases()