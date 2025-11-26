# ey-ay/services/llm_fallback.py

import os
import json
import aiohttp
from typing import Optional, List, Dict
from datetime import datetime
from config.logging_config import get_logger

logger = get_logger(__name__)


class LLMFallbackService:
    """
    Fallback service using free LLM APIs

    Priority: Groq > OpenRouter
    """

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        # Stats tracking
        self.stats = {
            "total_requests": 0,
            "groq_requests": 0,
            "openrouter_requests": 0,
            "errors": 0,
            "avg_response_time_ms": 0,
        }

        # Load SFA knowledge base from intents
        self.knowledge_base = self._load_knowledge_base()

        logger.info("LLM Fallback Service initialized")
        if self.groq_api_key:
            logger.info("Groq API configured")
        if self.openrouter_api_key:
            logger.info("OpenRouter API configured")

    def _load_knowledge_base(self) -> str:
        """Load SFA domain knowledge from intents.json"""
        try:
            intents_path = "data/intents.json"
            if os.path.exists(intents_path):
                with open(intents_path, "r") as f:
                    intents_data = json.load(f)

                # Extract key information
                kb_parts = ["SFA Support Assistant Knowledge Base:\n"]

                for intent in intents_data.get("intents", []):
                    tag = intent.get("tag", "")
                    patterns = intent.get("patterns", [])
                    responses = intent.get("responses", [])

                    if responses:
                        kb_parts.append(f"\n{tag.upper()}:")
                        kb_parts.append(f"  Example: {patterns[0] if patterns else ''}")
                        kb_parts.append(f"  Solution: {responses[0]}")

                # Add metadata
                metadata = intents_data.get("metadata", {})
                if metadata.get("escalation_contacts"):
                    kb_parts.append("\n\nEscalation Contacts:")
                    for role, contact in metadata["escalation_contacts"].items():
                        kb_parts.append(f"  {role}: {contact}")

                return "\n".join(kb_parts)
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")

        return "SFA Support Assistant - helping with Sales Force Automation issues."

    def _build_system_prompt(self) -> str:
        """Build system prompt with SFA domain knowledge"""
        return f"""You are an expert SFA (Sales Force Automation) Support Assistant chatbot.

Your role is to help Field Sales Personnel and Sales Development Officers troubleshoot and resolve SFA mobile app issues.

{self.knowledge_base}

IMPORTANT GUIDELINES:
1. Be concise and helpful - users need quick solutions
2. For technical issues, provide step-by-step troubleshooting
3. When unsure, suggest checking with the appropriate team (SAP, DW, etc.)
4. Always maintain a professional but friendly tone
5. If the issue requires escalation, clearly state who to contact
6. Reference specific database tables or technical details when relevant

Remember: You're assisting busy sales personnel who need fast, accurate solutions."""

    async def get_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        original_intent: Optional[str] = None,
        original_confidence: Optional[float] = None,
    ) -> Optional[str]:
        """
        Get response from LLM fallback service

        Args:
            user_message: User's question
            conversation_history: Recent conversation context
            original_intent: Intent predicted by PyTorch model
            original_confidence: Confidence score from PyTorch model

        Returns:
            LLM-generated response or None if all providers fail
        """
        start_time = datetime.now()
        self.stats["total_requests"] += 1

        # Try Groq first (fastest, free)
        if self.groq_api_key:
            response = await self._query_groq(
                user_message, conversation_history, original_intent
            )
            if response:
                self._update_stats("groq", start_time)
                return response

        # Fallback to OpenRouter
        if self.openrouter_api_key:
            response = await self._query_openrouter(
                user_message, conversation_history, original_intent
            )
            if response:
                self._update_stats("openrouter", start_time)
                return response

        # All providers failed
        self.stats["errors"] += 1
        logger.error("All LLM providers failed")
        return None

    async def _query_groq(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]],
        original_intent: Optional[str],
    ) -> Optional[str]:
        """Query Groq API (Free, Fast)"""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"

            messages = [{"role": "system", "content": self._build_system_prompt()}]

            # Add conversation history
            if conversation_history:
                for conv in conversation_history[-3:]:  # Last 3 exchanges
                    messages.append(
                        {"role": "user", "content": conv.get("user_message", "")}
                    )
                    messages.append(
                        {"role": "assistant", "content": conv.get("bot_response", "")}
                    )

            # Add current message with context
            current_msg = user_message
            if original_intent and original_intent != "unknown":
                current_msg += f"\n[Context: Possible intent - {original_intent}]"

            messages.append({"role": "user", "content": current_msg})

            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "llama-3.3-70b-versatile",  # Fast, capable model
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500,
                "top_p": 0.9,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=headers, timeout=30
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response = data["choices"][0]["message"]["content"]
                        logger.info(f"Groq response received ({len(response)} chars)")
                        return response
                    else:
                        error_text = await resp.text()
                        logger.error(f"Groq API error {resp.status}: {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Groq query failed: {e}")
            return None

    async def _query_openrouter(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]],
        original_intent: Optional[str],
    ) -> Optional[str]:
        """Query OpenRouter API (Free tier available)"""
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"

            messages = [{"role": "system", "content": self._build_system_prompt()}]

            # Add conversation history
            if conversation_history:
                for conv in conversation_history[-3:]:
                    messages.append(
                        {"role": "user", "content": conv.get("user_message", "")}
                    )
                    messages.append(
                        {"role": "assistant", "content": conv.get("bot_response", "")}
                    )

            # Add current message
            current_msg = user_message
            if original_intent and original_intent != "unknown":
                current_msg += f"\n[Context: Possible intent - {original_intent}]"

            messages.append({"role": "user", "content": current_msg})

            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/jrsnasis/ey-ay",
                "X-Title": "EY-AY Chatbot",
            }

            payload = {
                "model": "google/gemma-3-27b-it:free",  # Free model
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=headers, timeout=30
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response = data["choices"][0]["message"]["content"]
                        logger.info(
                            f"OpenRouter response received ({len(response)} chars)"
                        )
                        return response
                    else:
                        error_text = await resp.text()
                        logger.error(
                            f"OpenRouter API error {resp.status}: {error_text}"
                        )
                        return None

        except Exception as e:
            logger.error(f"OpenRouter query failed: {e}")
            return None

    def _update_stats(self, provider: str, start_time: datetime):
        """Update request statistics"""
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

        if provider == "groq":
            self.stats["groq_requests"] += 1
        elif provider == "openrouter":
            self.stats["openrouter_requests"] += 1

        # Update average response time
        total = self.stats["total_requests"]
        current_avg = self.stats["avg_response_time_ms"]
        self.stats["avg_response_time_ms"] = (
            current_avg * (total - 1) + elapsed_ms
        ) / total

    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return self.stats.copy()


# Standalone test
async def test_llm_fallback():
    """Test the LLM fallback service"""
    import asyncio

    print("=== Testing LLM Fallback Service ===\n")

    service = LLMFallbackService()

    test_messages = [
        "My customer is missing in the app",
        "How do I check old past due?",
        "DR cleared but still showing in list",
    ]

    for msg in test_messages:
        print(f"User: {msg}")
        response = await service.get_response(msg)
        print(f"LLM: {response}\n")
        print("-" * 60 + "\n")

    print(f"Stats: {service.get_stats()}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_llm_fallback())
