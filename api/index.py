import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Add the parent directory to sys.path so we can import orchestrator_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestrator_agent import create_orchestrator

app = FastAPI()

# Add CORS middleware to allow the frontend to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the orchestrator once
orchestrator = create_orchestrator()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        # The orchestrator.invoke expects the query string
        answer = orchestrator.invoke(request.message)
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
