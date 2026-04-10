# shared/database.py - Async MySQL using aiomysql

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

import aiomysql
import logging
from typing import Optional, List, Dict
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class Database:
    _pool: Optional[aiomysql.Pool] = None

    @classmethod
    async def init(cls):
        """Initialize connection pool"""
        if cls._pool is None:
            loop = asyncio.get_event_loop()
            cls._pool = await aiomysql.create_pool(
                loop=loop,
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 3306)),
                user=os.getenv("DB_USER", "chatbot_user"),
                password=os.getenv("DB_PASSWORD", ""),
                db=os.getenv("DB_NAME", "chatbot_db"),
                charset="utf8mb4",
                autocommit=True,
                minsize=1,
                maxsize=5,
            )
            logger.info("Database pool initialized")

    @classmethod
    async def close(cls):
        """Close connection pool"""
        if cls._pool:
            cls._pool.close()
            await cls._pool.wait_closed()
            cls._pool = None
            logger.info("Database pool closed")

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        """Get connection from pool"""
        if cls._pool is None:
            await cls.init()
        async with cls._pool.acquire() as conn:
            yield conn

    @classmethod
    async def fetch_one(cls, query: str, args: tuple = None) -> Optional[Dict]:
        """Fetch one row"""
        async with cls.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, args or ())
                return await cursor.fetchone()

    @classmethod
    async def fetch_all(cls, query: str, args: tuple = None) -> List[Dict]:
        """Fetch all rows"""
        async with cls.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, args or ())
                return await cursor.fetchall()

    @classmethod
    async def execute(cls, query: str, args: tuple = None):
        """Execute a query"""
        async with cls.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, args or ())
                return cursor


async def log_conversation(
    session_id: str,
    user_message: str,
    predicted_intent: str,
    confidence: float,
    bot_response: str,
    response_time_ms: int = 0,
) -> int:
    """Log a conversation to the database"""
    query = """
        INSERT INTO conversations 
        (session_id, user_message, predicted_intent, confidence, bot_response, response_time_ms)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor = await Database.execute(query, (
        session_id, user_message, predicted_intent, confidence, bot_response, response_time_ms
    ))
    await cursor.close()
    return cursor.lastrowid


async def get_random_response(intent_tag: str) -> Optional[str]:
    """Get a random response for an intent"""
    query = """
        SELECT r.text 
        FROM responses r
        JOIN intents i ON r.intent_id = i.id
        WHERE i.tag = %s
        ORDER BY RAND()
        LIMIT 1
    """
    result = await Database.fetch_one(query, (intent_tag,))
    return result["text"] if result else None


async def get_conversation_history(session_id: str, limit: int = 10) -> List[Dict]:
    """Get conversation history for a session"""
    query = """
        SELECT * FROM conversations
        WHERE session_id = %s
        ORDER BY created_at DESC
        LIMIT %s
    """
    return await Database.fetch_all(query, (session_id, limit))
