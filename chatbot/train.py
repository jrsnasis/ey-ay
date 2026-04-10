# ey-ay/src/train.py

"""
Training Script

This script:
1. Loads the training data (intents.json)
2. Preprocesses the text
3. Creates the neural network
4. Trains the model
5. Saves the trained model

Key Training Concepts:
- Loss function: measures how wrong the model is
- Optimizer: adjusts weights to minimize loss
- Epochs: number of times to go through all training data
- Backpropagation: how the network learns from mistakes
"""

import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import sys
import os

from models.intent_classifier import IntentClassifier
from src.preprocessing import tokenize, stem, bag_of_words

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)


class ChatDataset(Dataset):
    """
    Custom PyTorch Dataset for chat data

    PyTorch Dataset is like a smart container for your data:
    - Knows how many samples you have (__len__)
    - Can fetch any sample by index (__getitem__)
    """

    def __init__(self, X_train, y_train):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train

    def __len__(self):
        return self.n_samples

    def __getitem__(self, idx):
        return self.x_data[idx], self.y_data[idx]


def train_chatbot(
    data_path="data/intents.json",
    hidden_size=8,
    num_epochs=1000,
    batch_size=8,
    learning_rate=0.001,
):
    """
    Main training function

    Args:
        data_path: path to intents.json
        hidden_size: number of neurons in hidden layers
        num_epochs: number of training iterations
        batch_size: number of samples per batch
        learning_rate: how fast the model learns
    """

    print("=" * 50)
    print("Starting Training Process")
    print("=" * 50)

    # 1. Load intents data
    print("\n[1/6] Loading training data...")
    with open(data_path, "r") as f:
        intents = json.load(f)

    # 2. Prepare data
    print("[2/6] Preprocessing data...")
    all_words = []
    tags = []
    xy = []  # Will hold (pattern, tag) pairs

    for intent in intents["intents"]:
        tag = intent["tag"]
        tags.append(tag)

        for pattern in intent["patterns"]:
            # Tokenize each pattern
            words = tokenize(pattern)
            all_words.extend(words)
            xy.append((words, tag))

    # Stem and clean words
    ignore_chars = ["?", "!", ".", ","]
    all_words = [stem(w) for w in all_words if w not in ignore_chars]
    all_words = sorted(set(all_words))
    tags = sorted(set(tags))

    print(f"   Found {len(all_words)} unique words")
    print(f"   Found {len(tags)} intents: {tags}")

    # 3. Create training data
    print("[3/6] Creating training dataset...")
    X_train = []
    y_train = []

    for pattern_words, tag in xy:
        # Convert sentence to bag of words
        bag = bag_of_words(pattern_words, all_words)
        X_train.append(bag)

        # Convert tag to label (number)
        label = tags.index(tag)
        y_train.append(label)

    X_train = np.array(X_train)
    y_train = np.array(y_train)

    print(f"   Training samples: {len(X_train)}")

    # 4. Create PyTorch dataset and dataloader
    dataset = ChatDataset(X_train, y_train)
    train_loader = DataLoader(
        dataset=dataset,
        batch_size=batch_size,
        shuffle=True,  # Shuffle for better training
        num_workers=0,
    )

    # 5. Set up model, loss, and optimizer
    print("[4/6] Initializing model...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"   Using device: {device}")

    input_size = len(all_words)
    output_size = len(tags)

    model = IntentClassifier(input_size, hidden_size, output_size).to(device)

    # Loss function - CrossEntropyLoss for classification
    criterion = nn.CrossEntropyLoss()

    # Optimizer - Adam (adaptive learning rate)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    print(f"   Model: {input_size} -> {hidden_size} -> {output_size}")

    # 6. Training loop
    print(f"[5/6] Training for {num_epochs} epochs...")
    for epoch in range(num_epochs):
        for words, labels in train_loader:
            words = words.to(device)
            labels = labels.to(dtype=torch.long).to(device)

            # Forward pass
            outputs = model(words)
            loss = criterion(outputs, labels)

            # Backward pass and optimization
            optimizer.zero_grad()  # Clear old gradients
            loss.backward()  # Calculate new gradients
            optimizer.step()  # Update weights

        # Print progress
        if (epoch + 1) % 100 == 0:
            print(f"   Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}")

    print(f"\n   Final loss: {loss.item():.4f}")

    # 7. Save the model
    print("[6/6] Saving model...")

    data = {
        "model_state": model.state_dict(),
        "input_size": input_size,
        "hidden_size": hidden_size,
        "output_size": output_size,
        "all_words": all_words,
        "tags": tags,
    }

    os.makedirs("data/processed", exist_ok=True)
    save_path = "data/processed/chatbot_model.pth"

    torch.save(data, save_path)
    print(f"   Model saved to {save_path}")

    print("\n" + "=" * 50)
    print("Training Complete!")
    print("=" * 50)


if __name__ == "__main__":
    # Train the chatbot
    train_chatbot(
        data_path="data/intents.json",
        hidden_size=8,
        num_epochs=1000,
        batch_size=8,
        learning_rate=0.001,
    )
