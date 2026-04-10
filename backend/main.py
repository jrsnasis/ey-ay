# backend/main.py - FastAPI backend

import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from shared.database import Database
from chatbot import Chatbot

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# Database lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.init()
    yield
    await Database.close()


app = FastAPI(
    title="EY-AY Chatbot API",
    description="PyTorch-powered chatbot with LLM fallback",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize chatbot
try:
    chatbot = Chatbot()
except Exception as e:
    print(f"Failed to initialize chatbot: {e}")
    chatbot = None


# Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_fallback: Optional[bool] = True


class ChatResponse(BaseModel):
    message: str
    intent: str
    confidence: float
    timestamp: str
    session_id: str
    used_fallback: bool = False
    fallback_reason: Optional[str] = None


# Routes
@app.get("/")
async def root():
    return {
        "message": "EY-AY Chatbot API",
        "status": "online",
        "version": "2.0.0",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "chatbot_ready": chatbot is not None,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        result = await chatbot.get_response(request.message)
        return ChatResponse(
            message=result["message"],
            intent=result["intent"],
            confidence=result["confidence"],
            timestamp=datetime.now().isoformat(),
            session_id=result["session_id"],
            used_fallback=result.get("used_fallback", False),
            fallback_reason=result.get("fallback_reason"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 10):
    from shared.database import get_conversation_history

    history = await get_conversation_history(session_id, limit)
    return {"history": history}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
