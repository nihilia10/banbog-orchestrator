#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo -e "${BLUE}Stopping servers...${NC}"
    # Kill all background jobs started by this script
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}--- Starting BanBog Orchestrator ---${NC}"

# 1. Start Backend API
echo -e "${BLUE}Starting Backend API (FastAPI)...${NC}"
# Use python3 -m uvicorn for better compatibility
# PYTHONPATH is set to include the current directory for imports in api/index.py
export PYTHONPATH=$PYTHONPATH:$(pwd)
./env/bin/python -m uvicorn api.index:app --reload --port 8000 &

# 2. Wait a moment for backend to initialize
sleep 2

# 3. Start Frontend
echo -e "${BLUE}Starting Frontend (Next.js)...${NC}"
if [ -d "frontend" ]; then
    cd frontend
    npm run dev &
    cd ..
else
    echo -e "\033[0;31mError: frontend directory not found!\033[0m"
    cleanup
fi

echo -e "${GREEN}------------------------------------${NC}"
echo -e "Backend: ${BLUE}http://localhost:8000${NC}"
echo -e "Frontend: ${BLUE}http://localhost:3000${NC}"
echo -e "Press ${GREEN}Ctrl+C${NC} to stop both servers."
echo -e "${GREEN}------------------------------------${NC}"

# Wait for background processes to keep the script running
wait
