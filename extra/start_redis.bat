@echo off
title Redis Server - Missing Person AI

echo ========================================
echo   Starting Redis Server
echo ========================================
echo.

REM Check if Redis is installed
where redis-server >nul 2>&1
if errorlevel 1 (
    echo Redis server not found in PATH
    echo.
    echo Please install Redis:
    echo 1. Download from: https://github.com/microsoftarchive/redis/releases
    echo 2. Extract and add to PATH
    echo 3. Or use WSL: sudo apt install redis-server
    echo.
    pause
    exit /b 1
)

echo Starting Redis server...
echo Press Ctrl+C to stop Redis
echo.

redis-server