#!/bin/bash
# Clone Advisor Development Startup Script
# Manages frontend, backend, and worker in one place

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Clone Advisor Development Environment${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${RED}🛑 Shutting down services...${NC}"
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "worker.py" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    wait
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Setup signal handling
trap cleanup SIGINT SIGTERM

# Check if backend virtual environment exists
if [ ! -d "backend/venv310" ]; then
    echo -e "${RED}❌ Backend virtual environment not found!${NC}"
    echo "Run: cd backend && python3 -m venv venv310 && source venv310/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
    cd frontend && npm install && cd ..
fi

# Create log directory
mkdir -p logs

echo -e "${GREEN}🔧 Starting Backend Services...${NC}"

# Start Backend API
cd backend
source venv310/bin/activate
python -c "from dotenv import load_dotenv; load_dotenv()"

# Start backend in background with logging
nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

# Start RQ Worker in background with logging  
nohup python worker.py > ../logs/worker.log 2>&1 &
WORKER_PID=$!

cd ..

echo -e "${GREEN}🎨 Starting Frontend...${NC}"

# Start Frontend in background with logging
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for services to start
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 5

# Check if services are running
echo -e "${GREEN}📊 Service Status:${NC}"

# Check backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "   ✅ Backend API: http://localhost:8000"
else
    echo -e "   ❌ Backend API: Failed to start"
fi

# Check frontend  
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "   ✅ Frontend: http://localhost:3000"
else
    echo -e "   ❌ Frontend: Failed to start"
fi

echo -e "   📋 Worker: Running (PID: $WORKER_PID)"

echo -e "\n${GREEN}🎉 All services started!${NC}"
echo -e "${BLUE}📖 Access your app at: http://localhost:3000${NC}"
echo -e "${BLUE}📊 API docs at: http://localhost:8000/docs${NC}"
echo -e "${BLUE}📝 Logs available in: ./logs/${NC}"
echo -e "\n${GREEN}Press Ctrl+C to stop all services${NC}"

# Monitor logs in real-time (optional)
echo -e "\n${BLUE}📋 Recent logs (press Ctrl+C to stop):${NC}"

# Keep script running and show logs
tail -f logs/backend.log logs/frontend.log logs/worker.log 