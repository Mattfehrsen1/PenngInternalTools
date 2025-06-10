#!/bin/bash

echo "Clone Advisor MVP Setup"
echo "======================"
echo ""

# Check for Python 3.12
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
if [[ ! "$python_version" =~ ^3\.(12|13) ]]; then
    echo "❌ Python 3.12+ is required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version"

# Check for Node.js
echo "Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi
node_version=$(node --version)
echo "✅ Node.js $node_version"

# Setup backend
echo ""
echo "Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "✅ Backend dependencies installed"

# Setup frontend
echo ""
echo "Setting up frontend..."
cd ../frontend
npm install
echo "✅ Frontend dependencies installed"

# Instructions
echo ""
echo "Setup complete! Next steps:"
echo ""
echo "1. Configure your API keys in backend/.env:"
echo "   - OPENAI_API_KEY"
echo "   - ANTHROPIC_API_KEY"
echo "   - PINECONE_API_KEY"
echo "   - PINECONE_ENV"
echo "   - PINECONE_PROJECT_ID"
echo ""
echo "2. Set up PostgreSQL:"
echo "   - Install PostgreSQL if not already installed"
echo "   - Create database: createdb cloneadvisor"
echo "   - Update DATABASE_URL in backend/.env"
echo ""
echo "3. Run the application:"
echo "   ./run-local.sh"
echo ""
