# ey-ay/models/intent_classifier.py

"""
Intent Classifier Neural Network

This is a simple feedforward neural network (also called Multi-Layer Perceptron)

Architecture:
Input Layer -> Hidden Layer 1 -> Hidden Layer 2 -> Output Layer

Key Concepts:
1. Linear layers: perform matrix multiplication (y = Wx + b)
2. ReLU activation: adds non-linearity (helps learn complex patterns)
3. Forward pass: data flows through the network
"""

import torch
import torch.nn as nn


class IntentClassifier(nn.Module):
    """
    Simple Neural Network for Intent Classification

    Args:
        input_size: size of input (vocabulary size)
        hidden_size: number of neurons in hidden layers
        num_classes: number of intents to classify
    """

    def __init__(self, input_size, hidden_size, num_classes):
        super(IntentClassifier, self).__init__()

        self.l1 = nn.Linear(input_size, hidden_size)
        self.l2 = nn.Linear(hidden_size, hidden_size)
        self.l3 = nn.Linear(hidden_size, num_classes)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        out = self.l1(x)
        out = self.relu(out)
        out = self.dropout(out)  # Apply dropout

        out = self.l2(out)
        out = self.relu(out)
        out = self.dropout(out)

        out = self.l3(out)
        return out


if __name__ == "__main__":
    # Test the model
    print("=== Testing Neural Network ===\n")

    # Example dimensions
    vocab_size = 50  # 50 unique words
    hidden_size = 8  # 8 neurons in hidden layers
    num_intents = 5  # 5 different intents

    # Create model
    model = IntentClassifier(vocab_size, hidden_size, num_intents)
    print(f"Model architecture:\n{model}\n")

    # Create dummy input (bag of words for one sentence)
    dummy_input = torch.randn(1, vocab_size)  # batch_size=1

    # Forward pass
    output = model(dummy_input)
    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Output (raw scores): {output}")

    # Get predicted class
    _, predicted = torch.max(output, dim=1)
    print(f"Predicted intent: {predicted.item()}")

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"\nTotal parameters: {total_params}")
