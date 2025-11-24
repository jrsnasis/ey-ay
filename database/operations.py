# ey-ay/database/operations.py

import sys
from pathlib import Path
from database.connection import get_db
from config.logging_config import get_logger
import random
from typing import List, Dict, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = get_logger(__name__)


def create_intent(tag: str, description: str = None) -> int:
    logger.info(f"Creating intent: {tag}")

    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO intents (tag, description) VALUES (%s, %s)", (tag, description)
        )

        intent_id = cursor.lastrowid
        cursor.close()
        logger.info(f"Created intent '{tag}' with ID: {intent_id}")
        return intent_id


def get_intent_by_tag(tag: str) -> Optional[Dict]:
    logger.debug(f"Fetching intent: {tag}")

    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM intents WHERE tag = %s", (tag,))

        row = cursor.fetchone()
        cursor.close()
        return row


def get_all_intents() -> List[Dict]:
    logger.debug("Fetching all intents")

    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM intents ORDER BY tag")
        results = cursor.fetchall()
        cursor.close()
        return results


def add_pattern(intent_tag: str, text: str) -> int:
    logger.info(f"Adding pattern to '{intent_tag}': {text}")

    intent = get_intent_by_tag(intent_tag)
    if not intent:
        logger.error(f"Intent not found: {intent_tag}")
        raise ValueError(f"Intent '{intent_tag}' does not exist")

    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO patterns (intent_id, text) VALUES (%s, %s)",
            (intent["id"], text),
        )

        pattern_id = cursor.lastrowid
        cursor.close()
        logger.info(f"Added pattern with ID: {pattern_id}")
        return pattern_id


def get_patterns_by_intent(intent_tag: str) -> List[str]:
    logger.debug(f"Fetching patterns for intent: {intent_tag}")

    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT p.text
            FROM patterns p
            JOIN intents i ON p.intent_id = i.id
            WHERE i.tag = %s
            ORDER BY p.id
            """,
            (intent_tag,),
        )

        patterns = [row["text"] for row in cursor.fetchall()]
        cursor.close()
        logger.debug(f"Found {len(patterns)} patterns for '{intent_tag}'")
        return patterns


def get_all_patterns() -> List[Dict]:
    logger.debug("Fetching all patterns")

    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT p.id, p.text, i.tag as intent_tag
            FROM patterns p
            JOIN intents i ON p.intent_id = i.id
            WHERE p.is_active = TRUE
            ORDER BY i.tag, p.id
            """
        )

        results = cursor.fetchall()
        cursor.close()
        return results


def add_response(intent_tag: str, text: str, priority: int = 1) -> int:
    logger.info(f"Adding response to '{intent_tag}': {text}")

    intent = get_intent_by_tag(intent_tag)
    if not intent:
        logger.error(f"Intent not found: {intent_tag}")
        raise ValueError(f"Intent '{intent_tag}' does not exist")

    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO responses (intent_id, text, priority) VALUES (%s, %s, %s)",
            (intent["id"], text, priority),
        )

        response_id = cursor.lastrowid
        cursor.close()
        logger.info(f"Added response with ID: {response_id}")
        return response_id


def get_responses_by_intent(intent_tag: str) -> List[str]:
    logger.debug(f"Fetching responses for intent: {intent_tag}")

    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT r.text, r.priority
            FROM responses r
            JOIN intents i ON r.intent_id = i.id
            WHERE i.tag = %s
            ORDER BY r.priority DESC, r.id
            """,
            (intent_tag,),
        )

        responses = [row["text"] for row in cursor.fetchall()]
        cursor.close()
        logger.debug(f"Found {len(responses)} responses for '{intent_tag}'")
        return responses


def get_random_response(intent_tag: str) -> Optional[str]:
    logger.debug(f"Getting random response for: {intent_tag}")

    responses = get_responses_by_intent(intent_tag)

    if not responses:
        logger.warning(f"No responses found for intent: {intent_tag}")
        return None

    response = random.choice(responses)
    logger.debug(f"Selected response: {response}")
    return response


def log_conversation(
    session_id: str,
    user_message: str,
    predicted_intent: str,
    confidence: float,
    bot_response: str,
    response_time_ms: int = 0,
) -> int:
    logger.info(f"[{session_id}] Logging conversation")
    logger.debug(f"  User: {user_message}")
    logger.debug(f"  Intent: {predicted_intent} (confidence: {confidence:.2f})")
    logger.debug(f"  Bot: {bot_response}")
    logger.debug(f"  Response time: {response_time_ms}ms")

    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO conversations (
                session_id, user_message, predicted_intent,
                confidence, bot_response, response_time_ms
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                session_id,
                user_message,
                predicted_intent,
                confidence,
                bot_response,
                response_time_ms,
            ),
        )

        conversation_id = cursor.lastrowid
        cursor.close()
        logger.info(f"Logged conversation with ID: {conversation_id}")
        return conversation_id


def get_conversation_history(session_id: str, limit: int = 10) -> List[Dict]:
    logger.debug(f"Fetching conversation history for: {session_id}")

    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM conversations
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (session_id, limit),
        )

        history = cursor.fetchall()
        cursor.close()
        logger.debug(f"Found {len(history)} messages")
        return history


def get_conversation_stats() -> Dict:
    logger.debug("Calculating conversation statistics")

    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        # Total conversations
        cursor.execute("SELECT COUNT(*) as count FROM conversations")
        total = cursor.fetchone()["count"]

        # Average confidence
        cursor.execute("SELECT AVG(confidence) as avg FROM conversations")
        avg_confidence = cursor.fetchone()["avg"] or 0

        # Most common intents
        cursor.execute(
            """
            SELECT predicted_intent, COUNT(*) as count
            FROM conversations
            GROUP BY predicted_intent
            ORDER BY count DESC
            LIMIT 5
            """
        )
        top_intents = [
            (row["predicted_intent"], row["count"]) for row in cursor.fetchall()
        ]

        cursor.close()

        stats = {
            "total_conversations": total,
            "average_confidence": avg_confidence,
            "top_intents": top_intents,
        }

        logger.info(f"Conversation stats: {stats}")
        return stats


if __name__ == "__main__":
    # Test database operations
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=" * 50)
    print("Testing Database Operations")
    print("=" * 50)

    # Test intent operations
    print("\n1. Testing Intent Operations...")
    intents = get_all_intents()
    print(f"   Found {len(intents)} intents")
    for intent in intents[:3]:
        print(f"   - {intent['tag']}")

    # Test response retrieval
    print("\n2. Testing Response Retrieval...")
    if intents:
        tag = intents[0]["tag"]
        responses = get_responses_by_intent(tag)
        print(f"   Intent '{tag}' has {len(responses)} responses")
        if responses:
            print(f"   Random response: {get_random_response(tag)}")

    # Test conversation stats
    print("\n3. Testing Conversation Stats...")
    stats = get_conversation_stats()
    print(f"   Total conversations: {stats['total_conversations']}")
    print(f"   Average confidence: {stats['average_confidence']:.2f}")

    print("\n" + "=" * 50)
