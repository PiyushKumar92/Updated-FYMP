#!/usr/bin/env python3
"""
Start AI background processing for Missing Person Finder
"""
import os
import sys
from app import create_app
from app.ai_location_matcher import ai_matcher

def start_ai_processing():
    """Initialize and start AI background processing"""
    app = create_app()
    
    with app.app_context():
        print("🤖 Starting AI Location Matcher...")
        print("🔍 Initializing face recognition models...")
        print("📹 Setting up video processing pipeline...")
        print("🎯 Starting background processing thread...")
        
        # Start background processing
        ai_matcher.start_background_processing()
        
        print("✅ AI Processing started successfully!")
        print("🚀 System is now ready for advanced missing person detection")
        print("📊 Monitor progress in Admin > AI Analysis dashboard")
        
        # Keep the script running
        try:
            import time
            while True:
                time.sleep(60)
                print("💡 AI System running... (Press Ctrl+C to stop)")
        except KeyboardInterrupt:
            print("\n🛑 Stopping AI processing...")
            ai_matcher.is_processing = False
            print("✅ AI processing stopped successfully")

if __name__ == "__main__":
    start_ai_processing()