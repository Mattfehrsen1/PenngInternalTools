#!/bin/bash

echo "Starting Clone Advisor with Python 3.10..."
echo "=========================================="
echo ""
echo "⚠️  Make sure you have:"
echo "1. PostgreSQL running locally"
echo "2. Updated backend/.env with your API keys"
echo "3. Created the database: createdb cloneadvisor"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Set up pyenv
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

# Start backend
echo "Starting backend with Python 3.10..."
cd backend

# Create virtual environment with Python 3.10
python -m venv venv310
source venv310/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing backend dependencies..."
pip install fastapi==0.110.0 "uvicorn[standard]==0.27.1" python-multipart "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" pydantic==2.5.2 pydantic-settings==2.2.1 sqlalchemy==2.0.28 asyncpg==0.29.0 alembic==1.13.1 pinecone-client==3.1.0 langchain==0.1.12 langchain-openai==0.0.8 langchain-anthropic==0.1.4 "langchain-community>=0.0.28,<0.1" openai==1.14.0 anthropic==0.19.1 tiktoken==0.6.0 pypdf==4.0.2 "pdfminer.six==20221105" httpx==0.27.0 sse-starlette==2.0.0 python-dotenv==1.0.1

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the backend server
echo "Starting backend server..."
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 10

# Check if backend started successfully
if curl -s http://localhost:8000/docs > /dev/null; then
  echo "✅ Backend started successfully!"
else
  echo "⚠️ Backend failed to start. Check the logs above for errors."
  exit 1
fi

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
echo "Demo login credentials:"
echo "Username: demo"
echo "Password: demo123"
echo ""
echo "Press Ctrl+C to stop all services..."

# Cleanup function
cleanup() {
  echo "Stopping services..."
  kill $BACKEND_PID 2>/dev/null
  kill $FRONTEND_PID 2>/dev/null
  echo "All services stopped."
  exit 0
}

# Register cleanup function on script exit
trap cleanup EXIT

# Wait for Ctrl+C
wait
