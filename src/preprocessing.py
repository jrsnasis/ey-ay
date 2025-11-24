# ey-ay/src/preprocessing.py

"""
Text Preprocessing Module

This module handles:
1. Tokenization - breaking sentences into words
2. Stemming - reducing words to root form (e.g., "running" -> "run")
3. Vocabulary building - creating a word-to-index mapping
"""

import nltk
from nltk.stem.porter import PorterStemmer
import numpy as np

# Download required NLTK data (run once)
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

stemmer = PorterStemmer()


def tokenize(sentence):
    """
    Split sentence into array of words/tokens
    Example: "Hello, how are you?" -> ["Hello", "how", "are", "you", "?"]
    """
    return nltk.word_tokenize(sentence)


def stem(word):
    """
    Reduce word to its root form
    Examples:
    - "organizing" -> "organ"
    - "organized" -> "organ"
    - "organizes" -> "organ"
    """
    return stemmer.stem(word.lower())


def bag_of_words(tokenized_sentence, vocabulary):
    """
    Convert sentence to a "bag of words" array

    This is a KEY concept in NLP:
    - Create an array of 0s and 1s
    - 1 if word exists in vocabulary, 0 otherwise

    Example:
    sentence = "Hello, how are you"
    vocabulary = ["hi", "hello", "I", "you", "bye", "thank", "cool"]
    bag = [0, 1, 0, 1, 0, 0, 0]
           (hello=1, you=1, others=0)

    Args:
        tokenized_sentence: list of words
        vocabulary: list of known words

    Returns:
        numpy array of 0s and 1s
    """
    # Stem each word in the sentence
    sentence_words = [stem(word) for word in tokenized_sentence]

    # Initialize bag with 0s
    bag = np.zeros(len(vocabulary), dtype=np.float32)

    # Set 1 for each word that exists in vocabulary
    for idx, word in enumerate(vocabulary):
        if word in sentence_words:
            bag[idx] = 1

    return bag


def build_vocabulary(patterns):
    """
    Create vocabulary from all training patterns

    Args:
        patterns: list of sentences

    Returns:
        sorted list of unique stemmed words
    """
    all_words = []

    for pattern in patterns:
        # Tokenize each sentence
        words = tokenize(pattern)
        # Stem and add to list
        all_words.extend([stem(w) for w in words])

    # Remove duplicates and ignore punctuation
    ignore_chars = ["?", "!", ".", ","]
    all_words = [w for w in all_words if w not in ignore_chars]

    # Sort and remove duplicates
    vocabulary = sorted(set(all_words))

    return vocabulary


if __name__ == "__main__":
    # Test the preprocessing functions
    print("=== Testing Preprocessing ===\n")

    sentence = "Hello! How are you doing?"
    print(f"Original: {sentence}")

    tokens = tokenize(sentence)
    print(f"Tokenized: {tokens}")

    stemmed = [stem(w) for w in tokens]
    print(f"Stemmed: {stemmed}")

    # Test bag of words
    vocab = ["hi", "hello", "are", "you", "bye"]
    bag = bag_of_words(tokens, vocab)
    print(f"\nVocabulary: {vocab}")
    print(f"Bag of words: {bag}")
