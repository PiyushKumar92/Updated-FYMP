@echo off
title Missing Person AI - Application Server

echo ========================================
echo   Missing Person AI - Starting Server
echo ========================================
echo.

REM Check if Redis is running
echo Checking Redis connection...
python -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('✓ Redis is running')
except:
    print('✗ Redis is not running!')
    print('Please start Redis server first')
    input('Press Enter to continue anyway...')
" 2>nul

echo.
echo Starting Flask application...
echo.
echo ========================================
echo   Server Information
echo ========================================
echo Local URL:    http://localhost:5000
echo Network URL:  http://%COMPUTERNAME%:5000
echo Admin Login:  admin / admin123
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

python run.py