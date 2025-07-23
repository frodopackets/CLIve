#!/bin/bash

# AI Assistant CLI Development Setup Script
# This script sets up the development environment for the AI Assistant CLI project

set -e

echo "🚀 Setting up AI Assistant CLI development environment..."

# Check if we're in WSL
if grep -q Microsoft /proc/version; then
    echo "✅ Running in WSL environment"
else
    echo "⚠️  This script is designed for WSL Ubuntu environment"
fi

# Check Python version
echo "🐍 Checking Python version..."
python3 --version

# Create and activate virtual environment
echo "📦 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
echo "✅ Virtual environment activated"

# Install backend dependencies
echo "📚 Installing backend dependencies..."
pip install -r backend/requirements.txt
echo "✅ Backend dependencies installed"

# Install agent dependencies
echo "🤖 Installing agent dependencies..."
pip install -r agent/requirements.txt
echo "✅ Agent dependencies installed"

# Check if Node.js is available
echo "📦 Checking Node.js availability..."
if command -v node &> /dev/null; then
    echo "✅ Node.js is available: $(node --version)"
    
    # Install frontend dependencies
    echo "🎨 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    echo "✅ Frontend dependencies installed"
else
    echo "⚠️  Node.js not found. Please install Node.js to set up frontend dependencies."
    echo "   You can install it using: sudo apt install nodejs npm"
fi

# Create .env file from example
echo "⚙️  Setting up environment configuration..."
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env from example"
    echo "⚠️  Please update backend/.env with your actual AWS credentials"
else
    echo "✅ backend/.env already exists"
fi

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Update backend/.env with your AWS credentials"
echo "2. Start the backend: source venv/bin/activate && python backend/main.py"
echo "3. Start the frontend: cd frontend && npm run dev"
echo "4. Start the agent: source venv/bin/activate && python agent/birmingham_agent.py"
echo ""
echo "Happy coding! 🚀"