# chatbot/chatbot.py - Chatbot core module

import os
import sys
import uuid
import time
import logging
import torch
import nltk
from nltk.stem.porter import PorterStemmer
from .intent_classifier import IntentClassifier

# Get project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Ensure logs directory exists
os.makedirs(os.path.join(PROJECT_ROOT, "logs"), exist_ok=True)

# Configure logging
log_path = os.path.join(PROJECT_ROOT, "logs", "chatbot.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Download NLTK data
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

stemmer = PorterStemmer()


def tokenize(sentence):
    return nltk.word_tokenize(sentence)


def stem_word(word):
    return stemmer.stem(word.lower())


def bag_of_words(tokenized_sentence, vocabulary):
    sentence_words = [stem_word(w) for w in tokenized_sentence]
    bag = [0] * len(vocabulary)
    for idx, word in enumerate(vocabulary):
        if word in sentence_words:
            bag[idx] = 1
    return bag


class Chatbot:
    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = os.path.join(PROJECT_ROOT, "chatbot", "data", "processed", "chatbot_model.pth")

        self.session_id = str(uuid.uuid4())[:8]
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Initializing chatbot. Session: {self.session_id}")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")

        data = torch.load(model_path, map_location=self.device)
        self.all_words = data["all_words"]
        self.tags = data["tags"]

        self.model = IntentClassifier(
            len(self.all_words),
            data["hidden_size"],
            len(self.tags)
        ).to(self.device)
        self.model.load_state_dict(data["model_state"])
        self.model.eval()

        logger.info(f"Model loaded: {len(self.all_words)} words, {len(self.tags)} intents")

    def predict(self, user_input: str):
        sentence = tokenize(user_input)
        X = bag_of_words(sentence, self.all_words)
        X = torch.tensor([X], dtype=torch.float32).to(self.device)

        output = self.model(X)
        probs = torch.softmax(output, dim=1)
        confidence, predicted = torch.max(probs, dim=1)

        tag = self.tags[predicted.item()]
        return tag, confidence.item()

    async def get_response(self, user_message: str, confidence_threshold: float = 0.75):
        from shared.database import get_random_response, log_conversation

        intent, confidence = self.predict(user_message)

        response = None
        used_fallback = False
        fallback_reason = None

        if confidence >= confidence_threshold:
            response = await get_random_response(intent)
            if not response:
                fallback_reason = f"No response for intent: {intent}"
                logger.warning(fallback_reason)
        else:
            fallback_reason = f"Low confidence: {confidence:.2%} < {confidence_threshold:.2%}"
            logger.warning(fallback_reason)

        if not response:
            response = "I understand, but I don't have a response for that yet."

        # Log conversation
        try:
            await log_conversation(
                session_id=self.session_id,
                user_message=user_message,
                predicted_intent=intent,
                confidence=confidence,
                bot_response=response,
                response_time_ms=0,
            )
        except Exception as e:
            logger.error(f"Failed to log conversation: {e}")

        return {
            "message": response,
            "intent": intent,
            "confidence": confidence,
            "session_id": self.session_id,
            "used_fallback": used_fallback,
            "fallback_reason": fallback_reason,
        }


# Standalone CLI for testing
if __name__ == "__main__":
    import asyncio
    from shared.database import Database

    async def test():
        await Database.init()
        bot = Chatbot()
        
        queries = [
            "What type is Pikachu?",
            "How does Charmander evolve?",
            "Who is Mewtwo?",
        ]
        
        for q in queries:
            result = await bot.get_response(q)
            print(f"Q: {q}")
            print(f"  Intent: {result['intent']} ({result['confidence']:.2%})")
            print(f"  Response: {result['message']}")
            print()

    asyncio.run(test())
