#!/bin/bash

echo "Starting Azure Chatbot Backend API..."
echo "========================================="
echo ""

if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi

echo "Checking Python dependencies..."
if ! pip show fastapi > /dev/null 2>&1; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "Starting server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/api/docs"
echo "Health Check: http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================="
echo ""

python main.py
