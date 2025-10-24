#!/bin/bash

# Universal Scraper Startup Script for macOS/Linux
# This script starts both the backend and frontend servers

set -e

echo "=================================="
echo "  Universal Scraper Startup"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found!${NC}"
    echo -e "Please create a .env file with your API keys."
    echo -e "See README.md for configuration details."
    echo ""
    
    # Offer to create from template
    if [ -f .env.template ]; then
        echo -e "Would you like to copy .env.template to .env? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            cp .env.template .env
            echo -e "${GREEN}✓ Created .env file from template${NC}"
            echo -e "${YELLOW}⚠️  Please edit .env and add your API keys before continuing${NC}"
            exit 1
        fi
    fi
    
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
    echo ""
    
    echo -e "${BLUE}Installing Python dependencies...${NC}"
    source venv/bin/activate
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
    echo ""
else
    source venv/bin/activate
fi

# Check if node_modules exists in frontend
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Frontend dependencies not found. Installing...${NC}"
    cd frontend
    npm install
    cd ..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
    echo ""
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}✓ Servers stopped${NC}"
    exit 0
}

trap cleanup EXIT INT TERM

# Start Backend
echo -e "${BLUE}Starting Backend Server...${NC}"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Check if backend started successfully
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Backend server started (PID: $BACKEND_PID)${NC}"
    echo -e "  API: ${BLUE}http://localhost:8000${NC}"
    echo -e "  Docs: ${BLUE}http://localhost:8000/docs${NC}"
else
    echo -e "${RED}✗ Backend server failed to start${NC}"
    echo -e "Check backend.log for errors"
    exit 1
fi

echo ""

# Start Frontend
echo -e "${BLUE}Starting Frontend Server...${NC}"
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait a bit for frontend to start
sleep 3

# Check if frontend started successfully
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Frontend server started (PID: $FRONTEND_PID)${NC}"
    echo -e "  App: ${BLUE}http://localhost:5173${NC}"
else
    echo -e "${RED}✗ Frontend server failed to start${NC}"
    echo -e "Check frontend.log for errors"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "=================================="
echo -e "${GREEN}✓ Universal Scraper is running!${NC}"
echo "=================================="
echo ""
echo -e "Frontend: ${BLUE}http://localhost:5173${NC}"
echo -e "Backend:  ${BLUE}http://localhost:8000${NC}"
echo -e "API Docs: ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo ""

# Wait for user to press Ctrl+C
wait


