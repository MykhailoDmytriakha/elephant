#!/bin/bash

# Script to run frontend server
# Usage: ./run_frontend.sh

echo "🌐 Starting Elephant Frontend Server..."

# Change to frontend directory
cd frontend

# Check if node_modules exists, if not - install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the development server
echo "🔄 Starting React development server on http://localhost:3000"
echo "📊 Press Ctrl+C to stop the server"
echo ""

npm start
