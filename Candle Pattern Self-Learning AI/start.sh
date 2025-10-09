#!/bin/bash

# Candle Pattern Self-Learning AI - Startup Script

echo "🚀 Starting Candle Pattern Self-Learning AI"
echo "============================================"
echo ""

# Check if backend dependencies are installed
if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ Error: Backend directory not found"
    exit 1
fi

# Start backend server
echo "📡 Starting Backend Server..."
cd backend
python3 api/server.py &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID)"
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 3

# Start frontend server
echo "🎨 Starting Frontend Server..."
cd frontend
npm start &
FRONTEND_PID=$!
echo "✓ Frontend started (PID: $FRONTEND_PID)"
cd ..

echo ""
echo "✅ System Started Successfully!"
echo "================================"
echo "📡 Backend API: http://localhost:8000"
echo "🎨 Frontend:    http://localhost:3000"
echo "📚 API Docs:    http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
