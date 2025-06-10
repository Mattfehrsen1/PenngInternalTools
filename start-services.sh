#!/bin/bash

echo "🚀 Starting Clone Advisor Services..."
echo "===================================="

# Function to cleanup background processes
cleanup() {
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped."
    exit 0
}

# Trap exit signals
trap cleanup EXIT INT TERM

# Start backend
echo "🔧 Starting backend server..."
cd backend
source venv310/bin/activate
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend  
echo "🌐 Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for both to start
sleep 5

# Test if services are running
echo "🧪 Testing services..."
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✅ Backend running at http://localhost:8000"
else
    echo "❌ Backend failed to start"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend running at http://localhost:3000"
else
    echo "❌ Frontend failed to start"
fi

echo ""
echo "🎉 Clone Advisor is ready!"
echo ""
echo "📋 Demo credentials:"
echo "   Username: demo"
echo "   Password: demo123"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services..."

# Keep script running
wait
