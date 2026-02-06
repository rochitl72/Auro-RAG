#!/bin/bash

# Start script for AuroRag - Agentic RAG Text-to-SQL System
# Runs both backend (Streamlit) and frontend (React/Vite)

echo "🚀 Starting AuroRag System..."
echo "================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Ollama is running
echo -e "${BLUE}Checking Ollama service...${NC}"
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Warning: Ollama service not detected at http://localhost:11434${NC}"
    echo -e "${YELLOW}   Make sure Ollama is running: ollama serve${NC}"
else
    echo -e "${GREEN}✅ Ollama service is running${NC}"
fi

# Check if llama3.1:8b model is available
if curl -s http://localhost:11434/api/tags | grep -q "llama3.1:8b"; then
    echo -e "${GREEN}✅ llama3.1:8b model is available${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: llama3.1:8b model not found${NC}"
    echo -e "${YELLOW}   Download it with: ollama pull llama3.1:8b${NC}"
fi

echo ""
echo -e "${BLUE}Starting services...${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    kill $API_PID $VITE_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Start FastAPI backend
echo -e "${GREEN}🚀 Starting FastAPI backend (port 8000)...${NC}"
cd backend
python3 -m uvicorn api_server:app --host 0.0.0.0 --port 8000 > /tmp/api_server.log 2>&1 &
API_PID=$!
cd ..

# Wait a bit for API to start
sleep 3

# Start Vite frontend
echo -e "${GREEN}⚛️  Starting React frontend (port 5173)...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi
npm run dev > /tmp/vite.log 2>&1 &
VITE_PID=$!
cd ..

# Wait a bit for Vite to start
sleep 3

echo ""
echo -e "${GREEN}✅ Services started!${NC}"
echo "================================"
echo ""
echo -e "${BLUE}Backend (FastAPI):${NC}   http://localhost:8000"
echo -e "${BLUE}Frontend (React):${NC}    http://localhost:5173"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for processes
wait
