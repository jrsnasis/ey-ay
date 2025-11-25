# ey-ay/src/chatbot_v2.py

import torch
import sys
import os
import uuid
import time
import logging
import nltk
from nltk.stem.porter import PorterStemmer
from database.operations import (
    get_random_response,
    log_conversation,
    get_conversation_history,
)
from models.intent_classifier import IntentClassifier

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

stemmer = PorterStemmer()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/chat.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def tokenize(sentence):
    return nltk.word_tokenize(sentence)


def stem(word):
    return stemmer.stem(word.lower())


def bag_of_words(tokenized_sentence, vocabulary):
    sentence_words = [stem(word) for word in tokenized_sentence]
    bag = [0] * len(vocabulary)
    for idx, word in enumerate(vocabulary):
        if word in sentence_words:
            bag[idx] = 1
    return bag


class ChatbotV2:

    def __init__(self, model_path="data/processed/chatbot_model.pth"):
        """Initialize chatbot"""
        logger.info("=" * 60)
        logger.info("Initializing Chatbot V2")
        logger.info("=" * 60)

        # Generate unique session ID
        self.session_id = str(uuid.uuid4())[:8]
        logger.info(f"Session ID: {self.session_id}")

        # Load model
        logger.info("Loading trained model...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")

        if not os.path.exists(model_path):
            logger.error(f"Model not found at: {model_path}")
            raise FileNotFoundError(
                "Model not trained yet! Run: python train_standalone.py"
            )

        data = torch.load(model_path, map_location=self.device)

        input_size = data["input_size"]
        hidden_size = data["hidden_size"]
        output_size = data["output_size"]
        self.all_words = data["all_words"]
        self.tags = data["tags"]

        logger.info(
            f"Model loaded - Vocabulary: {len(self.all_words)}, Intents: {len(self.tags)}"
        )

        self.model = IntentClassifier(input_size, hidden_size, output_size).to(
            self.device
        )
        self.model.load_state_dict(data["model_state"])
        self.model.eval()

        logger.info("Chatbot initialization complete!")

    def predict_intent(self, user_input):
        start_time = time.time()

        # Preprocess
        logger.debug(f"User input: {user_input}")
        sentence = tokenize(user_input)
        X = bag_of_words(sentence, self.all_words)
        X = torch.tensor([X], dtype=torch.float32).to(self.device)

        # Predict
        output = self.model(X)
        _, predicted = torch.max(output, dim=1)
        tag = self.tags[predicted.item()]

        # Get confidence
        probs = torch.softmax(output, dim=1)
        confidence = probs[0][predicted.item()].item()

        prediction_time = (time.time() - start_time) * 1000  # ms

        logger.debug(
            f"Predicted: {tag} (confidence: {confidence:.2%}, time: {prediction_time:.1f}ms)"
        )

        return tag, confidence, prediction_time

    def get_response(self, user_input, confidence_threshold=0.75):
        start_time = time.time()

        logger.info(f"[{self.session_id}] Processing message...")

        # Predict intent
        intent, confidence, pred_time = self.predict_intent(user_input)

        # Get response from database
        if confidence > confidence_threshold:
            logger.info(f"Intent: {intent} (confidence: {confidence:.2%})")
            response = get_random_response(intent)

            if not response:
                logger.warning(f"No responses found in database for: {intent}")
                response = "I understand, but I don't have a response for that yet."
        else:
            logger.warning(
                f"Low confidence: {confidence:.2%} (threshold: {confidence_threshold:.2%})"
            )
            intent = "unknown"
            response = "I'm not sure I understand. Can you rephrase that?"

        # Calculate total response time
        total_time = int((time.time() - start_time) * 1000)  # ms

        # Log conversation to database
        try:
            log_conversation(
                session_id=self.session_id,
                user_message=user_input,
                predicted_intent=intent,
                confidence=confidence,
                bot_response=response,
                response_time_ms=total_time,
            )
            logger.debug(f"Conversation logged to database")
        except Exception as e:
            logger.error(f"Failed to log conversation: {e}")

        logger.info(f"Response time: {total_time}ms")

        return response, intent, confidence

    def chat(self):
        """Start interactive chat session"""
        print("\n" + "=" * 60)
        print(" " * 10 + "Chatbot V2")
        print("=" * 60)
        print(f"\nSession ID: {self.session_id}")
        print("Type 'quit' to exit, 'history' to see conversation history")
        print("=" * 60 + "\n")

        logger.info(f"[{self.session_id}] Chat session started")

        message_count = 0

        while True:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "quit":
                print("\nBot: Goodbye! Have a great day!")
                logger.info(
                    f"[{self.session_id}] Session ended - {message_count} messages"
                )
                break

            if user_input.lower() == "history":
                self.show_history()
                continue

            # Get response
            response, intent, confidence = self.get_response(user_input)

            # Display response
            print(f"Bot: {response}")
            print(f"     [Intent: {intent} | Confidence: {confidence:.2%}]\n")

            message_count += 1

        # Show session summary
        print("\n" + "=" * 60)
        print("Session Summary:")
        print(f"  Messages: {message_count}")
        print(f"  Session ID: {self.session_id}")
        print(f"  Logs saved to: logs/chat.log")
        print("=" * 60 + "\n")

    def show_history(self):
        """Show conversation history"""
        try:
            history = get_conversation_history(self.session_id, limit=10)

            if not history:
                print("\n[No conversation history yet]\n")
                return

            print("\n" + "=" * 60)
            print("Conversation History (last 10 messages):")
            print("=" * 60)

            for i, conv in enumerate(reversed(history), 1):
                timestamp = conv["timestamp"]
                print(f"\n{i}. [{timestamp}]")
                print(f"   You: {conv['user_message']}")
                print(f"   Bot: {conv['bot_response']}")
                print(
                    f"   Intent: {conv['predicted_intent']} ({conv['confidence']:.2%})"
                )

            print("=" * 60 + "\n")

        except Exception as e:
            logger.error(f"Failed to fetch history: {e}")
            print("\n[Error fetching history]\n")


def main():
    """Main entry point"""

    # Check if model exists
    if not os.path.exists("data/processed/chatbot_model.pth"):
        print("\nError: Model not trained yet!")
        print("Please run: python train_standalone.py\n")
        logger.error("Model not found")
        return

    try:
        # Create and run chatbot
        bot = ChatbotV2()
        bot.chat()

    except KeyboardInterrupt:
        print("\n\nChat interrupted by user")
        logger.info("Chat interrupted by user")

    except Exception as e:
        print(f"\nError: {e}")
        logger.error(f"Chat error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
