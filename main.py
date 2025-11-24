# ey-ay/main.py

import sys
import os

from src.train import train_chatbot
from src.chatbot_v2 import ChatbotV2

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def print_banner():
    """Print welcome banner"""
    print("\n" + "=" * 60)
    print(" " * 15 + "PyTorch Chatbot Project")
    print(" " * 10 + "A Simple AI Assistant for Learning")
    print("=" * 60 + "\n")


def main():
    print_banner()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python main.py train    # Train the model")
        print("  python main.py chat     # Chat with the bot")
        print("  python main.py test     # Test with sample message")
        return

    command = sys.argv[1].lower()

    if command == "train":
        print("Starting training process...\n")
        train_chatbot(
            data_path="data/intents.json",
            hidden_size=8,
            num_epochs=1000,
            batch_size=8,
            learning_rate=0.001,
        )
        print("\nTraining complete!")
        print("Now you can chat: python main.py chat")

    elif command == "chat":
        if not os.path.exists("data/processed/chatbot_model.pth"):
            print("Error: Model not trained yet!")
            print("Please run: python main.py train")
            return

        bot = ChatbotV2()
        bot.chat()

    elif command == "test":
        if not os.path.exists("data/processed/chatbot_model.pth"):
            print("Error: Model not trained yet!")
            print("Please run: python main.py train")
            return

        # Test with sample messages
        test_messages = [
            "Hello!",
            "What can you do?",
            "Thanks for your help",
            "See you later",
            "I need some help",
        ]

        print("Testing chatbot with sample messages...\n")
        bot = ChatbotV2()

        for msg in test_messages:
            response, intent, confidence = bot.get_response(msg)
            print(f"User: {msg}")
            print(f"Bot:  {response}")
            print(f"      [Intent: {intent}, Confidence: {confidence:.2%}]\n")

    else:
        print(f"Unknown command: {command}")
        print("Use 'train', 'chat', or 'test'")


if __name__ == "__main__":
    main()
