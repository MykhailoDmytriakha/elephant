#!/bin/bash

# Script to run backend server
# Usage: ./run_backend.sh

echo "🚀 Starting Elephant Backend Server..."

# Change to backend directory
cd backend

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Start the server
echo "🔄 Starting FastAPI server on http://localhost:8000"
echo "📊 Press Ctrl+C to stop the server"
echo ""

# Set uvicorn log level to show access logs with timestamps
export UVICORN_LOG_LEVEL=info
python src/main.py
