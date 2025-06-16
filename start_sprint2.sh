#!/bin/bash
# Sprint 2 Development Startup Script
# Starts both the FastAPI server and Redis worker

set -e

echo "🚀 Starting Clone Advisor Sprint 2 Development Environment"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Redis is running
echo -e "${YELLOW}Checking Redis connection...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}❌ Redis is not running. Please start Redis first:${NC}"
    echo "   brew services start redis"
    echo "   # or"
    echo "   redis-server"
    exit 1
fi
echo -e "${GREEN}✅ Redis is running${NC}"

# Check if PostgreSQL is running
echo -e "${YELLOW}Checking PostgreSQL connection...${NC}"
if ! pg_isready > /dev/null 2>&1; then
    echo -e "${RED}❌ PostgreSQL is not running. Please start PostgreSQL first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ PostgreSQL is running${NC}"

# Setup function for cleanup
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
    fi
    if [ ! -z "$WORKER_PID" ]; then
        kill $WORKER_PID 2>/dev/null || true
    fi
    wait
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}
trap cleanup EXIT

# Change to backend directory
cd backend

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv310/bin/activate

# Install new dependencies
echo -e "${YELLOW}Installing new dependencies...${NC}"
pip install -r requirements.txt

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
alembic upgrade head

# Start API server in background
echo -e "${GREEN}🌐 Starting FastAPI server...${NC}"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait a moment for API to start
sleep 3

# Start Redis worker in background
echo -e "${GREEN}⚙️  Starting Redis worker...${NC}"
python worker.py ingestion &
WORKER_PID=$!

# Print status
echo -e "\n${GREEN}✅ Sprint 2 Environment Started!${NC}"
echo -e "${GREEN}📡 API Server: http://localhost:8000${NC}"
echo -e "${GREEN}📋 API Docs: http://localhost:8000/docs${NC}"
echo -e "${GREEN}⚙️  Worker: Processing 'ingestion' queue${NC}"
echo -e "${YELLOW}📊 Monitor Redis: redis-cli monitor${NC}"
echo -e "${YELLOW}🔍 Queue Status: redis-cli llen rq:queue:ingestion${NC}"

# Change to frontend directory and start it
cd ../frontend
echo -e "${GREEN}🎨 Starting Frontend (Next.js)...${NC}"
npm run dev &
FRONTEND_PID=$!

echo -e "\n${GREEN}🎯 Full Stack Ready!${NC}"
echo -e "${GREEN}Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}Backend: http://localhost:8000${NC}"
echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}"

# Wait for all background processes
wait 