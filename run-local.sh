#!/bin/bash

echo "Starting Clone Advisor Local Development..."
echo "==========================================="
echo ""
echo "⚠️  Make sure you have:"
echo "1. PostgreSQL running locally"
echo "2. Updated backend/.env with your API keys"
echo "3. Created the database: createdb cloneadvisor"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Start backend
echo "Starting backend..."
cd backend

# Install dependencies directly with pip
echo "Installing backend dependencies..."
pip3 install --break-system-packages fastapi uvicorn[standard] python-multipart python-jose[cryptography] passlib[bcrypt] pydantic==2.5.2 pydantic-settings sqlalchemy asyncpg alembic pinecone-client langchain langchain-openai langchain-anthropic langchain-community openai anthropic tiktoken pypdf pdfminer.six httpx sse-starlette python-dotenv

# Start the backend server
echo "Starting backend server..."
python3 -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Check if backend started successfully
sleep 5
if ! curl -s http://localhost:8000/docs > /dev/null; then
  echo "⚠️ Backend failed to start. Check the logs above for errors."
else
  echo "✅ Backend started successfully!"
fi

# Wait for backend to start
sleep 5

# Start frontend
echo "Starting frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Clone Advisor is running!"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
