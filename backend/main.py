# ey-ay/backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os
from datetime import datetime
from src.chatbot_v2 import ChatbotV2
from services.llm_fallback import LLMFallbackService
from config.logging_config import get_logger

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

logger = get_logger(__name__)

app = FastAPI(
    title="EY-AY Chatbot API",
    description="PyTorch-powered chatbot with LLM fallback",
    version="2.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
try:
    chatbot = ChatbotV2()
    llm_fallback = LLMFallbackService()
    logger.info("Services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {e}")
    chatbot = None
    llm_fallback = None


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_fallback: Optional[bool] = True  # Allow disabling fallback


class ChatResponse(BaseModel):
    message: str
    intent: str
    confidence: float
    timestamp: str
    session_id: str
    used_fallback: bool = False
    fallback_reason: Optional[str] = None


@app.get("/")
async def root():
    return {
        "message": "EY-AY Chatbot API",
        "status": "online",
        "version": "2.0.0",
        "features": ["PyTorch Intent Classification", "LLM Fallback Support"],
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "chatbot_ready": chatbot is not None,
        "llm_fallback_ready": llm_fallback is not None,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint with intelligent fallback

    Flow:
    1. Try PyTorch model first
    2. If confidence < threshold, use LLM fallback
    3. Log which approach was used
    """
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        # Primary: Get response from PyTorch model
        response, intent, confidence = chatbot.get_response(request.message)

        used_fallback = False
        fallback_reason = None

        # Fallback logic
        CONFIDENCE_THRESHOLD = 0.75

        if request.use_fallback and confidence < CONFIDENCE_THRESHOLD:
            logger.info(f"Low confidence ({confidence:.2%}), using LLM fallback")

            try:
                # Get conversation history for context
                from database.operations import get_conversation_history

                history = get_conversation_history(chatbot.session_id, limit=5)

                # Use LLM fallback
                fallback_response = await llm_fallback.get_response(
                    user_message=request.message,
                    conversation_history=history,
                    original_intent=intent,
                    original_confidence=confidence,
                )

                if fallback_response:
                    response = fallback_response
                    intent = "llm_fallback"
                    used_fallback = True
                    fallback_reason = f"Low confidence: {confidence:.2%}"

                    logger.info("Successfully used LLM fallback")

            except Exception as e:
                logger.error(f"LLM fallback failed: {e}")
                # Keep original response if fallback fails
                fallback_reason = f"Fallback error: {str(e)}"

        return ChatResponse(
            message=response,
            intent=intent,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            session_id=chatbot.session_id,
            used_fallback=used_fallback,
            fallback_reason=fallback_reason,
        )

    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 10):
    """Get conversation history"""
    try:
        from database.operations import get_conversation_history

        history = get_conversation_history(session_id, limit)
        return {"history": history}
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get conversation statistics including fallback usage"""
    try:
        from database.operations import get_conversation_stats

        stats = get_conversation_stats()

        # Add fallback stats if available
        if llm_fallback:
            stats["fallback_stats"] = llm_fallback.get_stats()

        return stats
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
