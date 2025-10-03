#!/usr/bin/env python3
"""
Quick Installation Test Script
Tests if the system can be installed and run successfully
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n[TEST] {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"[OK] {description} - SUCCESS")
            return True
        else:
            print(f"[ERROR] {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"[ERROR] {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"[ERROR] {description} - EXCEPTION: {str(e)}")
        return False

def main():
    print("="*60)
    print(" Missing Person AI System - Installation Test")
    print("="*60)
    
    # Test commands
    tests = [
        ("python --version", "Python Version Check"),
        ("pip --version", "Pip Version Check"),
        ("python validate_requirements.py", "Requirements Validation"),
        ("python simple_system_check.py", "System Components Check"),
        ("python -c \"from app import create_app; print('Flask app creation: OK')\"", "Flask App Test"),
        ("python -c \"import cv2; print(f'OpenCV version: {cv2.__version__}')\"", "OpenCV Test"),
        ("python -c \"import face_recognition; print('Face recognition: OK')\"", "Face Recognition Test"),
        ("python -c \"from app.ai_location_matcher import ai_matcher; print('AI Matcher: OK')\"", "AI System Test")
    ]
    
    passed = 0
    failed = 0
    
    for command, description in tests:
        if run_command(command, description):
            passed += 1
        else:
            failed += 1
    
    print(f"\n" + "="*60)
    print(f" Installation Test Results")
    print(f"="*60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {len(tests)}")
    
    if failed == 0:
        print(f"\n[SUCCESS] All installation tests passed!")
        print(f"The system is ready to run. Execute: python run.py")
        return True
    else:
        print(f"\n[ERROR] {failed} tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)