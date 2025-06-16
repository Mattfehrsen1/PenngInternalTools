#!/bin/bash
# Stop all Clone Advisor development services

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}🛑 Stopping Clone Advisor Development Services...${NC}"

# Kill all related processes
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "worker.py" 2>/dev/null || true  
pkill -f "next dev" 2>/dev/null || true

# Wait a moment for graceful shutdown
sleep 2

echo -e "${GREEN}✅ All services stopped${NC}" 