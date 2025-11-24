from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os
from datetime import datetime
from src.chatbot_v2 import ChatbotV2
from config.logging_config import get_logger

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

logger = get_logger(__name__)

app = FastAPI(
    title="EY-AY Chatbot API",
    description="PyTorch-powered chatbot with FastAPI backend",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chatbot
try:
    chatbot = ChatbotV2()
    logger.info("Chatbot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize chatbot: {e}")
    chatbot = None


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    intent: str
    confidence: float
    timestamp: str
    session_id: str


@app.get("/")
async def root():
    return {"message": "EY-AY Chatbot API", "status": "online", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "chatbot_ready": chatbot is not None,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint
    """
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        # Get response from chatbot
        response, intent, confidence = chatbot.get_response(request.message)

        return ChatResponse(
            message=response,
            intent=intent,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            session_id=chatbot.session_id,
        )

    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 10):
    """
    Get conversation history
    """
    try:
        from database.operations import get_conversation_history

        history = get_conversation_history(session_id, limit)
        return {"history": history}
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """
    Get conversation statistics
    """
    try:
        from database.operations import get_conversation_stats

        stats = get_conversation_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
