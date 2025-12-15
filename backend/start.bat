@echo off
echo Starting Azure Chatbot Backend API...
echo =========================================
echo.

if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure it.
    pause
    exit /b 1
)

echo Checking Python dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting server on http://localhost:8000
echo API Documentation: http://localhost:8000/api/docs
echo Health Check: http://localhost:8000/api/health
echo.
echo Press Ctrl+C to stop
echo =========================================
echo.

python main.py
pause
