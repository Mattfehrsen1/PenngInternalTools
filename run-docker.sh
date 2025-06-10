#!/bin/bash

echo "Starting Clone Advisor with Docker..."
echo "===================================="
echo ""
echo "This will start:"
echo "1. PostgreSQL database in Docker"
echo "2. Backend API in Docker"
echo "3. Frontend locally with Next.js"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Export environment variables from .env file
echo "Exporting environment variables..."
export $(grep -v '^#' backend/.env | xargs)

# Start backend and database with Docker Compose
echo "Starting backend and database with Docker Compose..."
docker-compose up -d postgres
docker-compose up --build -d backend

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 10

# Check if backend is running
if curl -s http://localhost:8000/docs > /dev/null; then
  echo "✅ Backend started successfully!"
else
  echo "⚠️ Backend may not have started properly. Check docker logs with: docker-compose logs backend"
fi

# Start frontend
echo "Starting frontend..."
cd frontend
npm run dev

# Cleanup function
cleanup() {
  echo "Stopping services..."
  cd ..
  docker-compose down
  echo "All services stopped."
  exit 0
}

# Register cleanup function on script exit
trap cleanup EXIT

# Wait for Ctrl+C
wait
