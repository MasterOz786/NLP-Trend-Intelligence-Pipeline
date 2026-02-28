import json
import ast
import numpy as np
import pandas as pd
from collections import Counter
from itertools import tee

INPUT_PATH = "data/processed/products_clean.csv"
VOCAB_PATH = "data/features/vocab.json"
BOW_PATH = "data/features/bow_matrix.npy"


def generate_bigrams(tokens):
    a, b = tee(tokens)
    next(b, None)
    return list(zip(a, b))


def main():
    df = pd.read_csv(INPUT_PATH)

    # Convert token string → list
    documents = [
        ast.literal_eval(row)
        for row in df["tokens"].fillna("[]")
    ]

    # Vocabulary Extraction
    vocab = sorted(set(token for doc in documents for token in doc))
    print(vocab)
    vocab_index = {word: idx for idx, word in enumerate(vocab)}

    # Save vocab
    with open(VOCAB_PATH, "w") as f:
        json.dump(vocab_index, f, indent=4)

    # One-Hot Encoding
    print("\nOne-Hot Encoding")
    # print(documents)
    for doc in documents:
        vector = [0] * len(vocab)
        for token in doc:
            vector[vocab_index[token]] = 1
        # print(vector)

    # Bag-of-Words Matrix
    bow_matrix = np.zeros((len(documents), len(vocab)), dtype=int)

    for doc_idx, doc in enumerate(documents):
        for token in doc:
            bow_matrix[doc_idx][vocab_index[token]] += 1

    np.save(BOW_PATH, bow_matrix)

    # Unigram Frequency
    unigram_freq = Counter(token for doc in documents for token in doc)
    print("\nTop 50 Unigrams:")
    print(unigram_freq.most_common(50))

    # Bigram Frequency
    bigram_freq = Counter(
        bigram
        for doc in documents
        for bigram in generate_bigrams(doc)
    )

    print("\nTop 50 Bigrams:")
    print(bigram_freq.most_common(50))

if __name__ == "__main__":
    main()
    