import os
import json
import numpy as np
import pandas as pd
import ast
from collections import Counter
from itertools import tee
from math import log, exp


PROCESSED_PATH = "data/processed/products_clean.csv"
VOCAB_PATH = "data/features/vocab.json"
REPORT_PATH = "reports/trend_summary.txt"


# -----------------------------
# Bigram Generator
# -----------------------------
def generate_bigrams(tokens):
    a, b = tee(tokens)
    next(b, None)
    return list(zip(a, b))


# Optimized Levenshtein / Minimum Edit Distance
def min_edit_distance(s1, s2, threshold=None, token_level=True):
    """
    Compute Levenshtein distance between s1 and s2.

    Parameters
    ----------
    s1, s2 : str
        Strings to compare
    threshold : int, optional
        Stop early if distance exceeds threshold
    token_level : bool
        If True, compute distance at token (word) level
    """
    # Convert to tokens if requested
    if token_level:
        s1 = s1.split()
        s2 = s2.split()

    m, n = len(s1), len(s2)

    # Swap to save space (always make s2 shorter)
    if n > m:
        s1, s2 = s2, s1
        m, n = n, m

    previous = list(range(n + 1))
    current = [0] * (n + 1)

    for i in range(1, m + 1):
        current[0] = i
        min_in_row = current[0]

        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            current[j] = min(
                previous[j] + 1,      # deletion
                current[j - 1] + 1,   # insertion
                previous[j - 1] + cost # substitution
            )
            min_in_row = min(min_in_row, current[j])

        # Early exit if distance exceeds threshold
        if threshold is not None and min_in_row > threshold:
            return threshold + 1

        previous, current = current, previous

    return previous[n]


# -----------------------------
# Main
# -----------------------------
def main():
    os.makedirs("reports", exist_ok=True)

    df = pd.read_csv(PROCESSED_PATH)

    # Convert tokens column properly
    documents = [ast.literal_eval(row) for row in df["tokens"].fillna("[]")]

    # -----------------------------
    # Unigram Frequency
    # -----------------------------
    unigram_freq = Counter(token for doc in documents for token in doc)
    top_30_unigrams = unigram_freq.most_common(30)

    # -----------------------------
    # Bigram Frequency
    # -----------------------------
    bigram_freq = Counter(
        bigram
        for doc in documents
        for bigram in generate_bigrams(doc)
    )
    top_20_bigrams = bigram_freq.most_common(20)

    # -----------------------------
    # Vocabulary Size
    # -----------------------------
    with open(VOCAB_PATH) as f:
        vocab = json.load(f)

    vocab_size = len(vocab)

    # -----------------------------
    # Average Description Length
    # -----------------------------
    lengths = [len(doc) for doc in documents]
    avg_length = sum(lengths) / len(lengths)

    # -----------------------------
    # Duplicate Detection (Title Distance)
    # -----------------------------
    titles = df["text_raw"].fillna("").tolist()
    duplicates = []

    threshold = 5  # small edit distance

    for i in range(len(titles)):
        for j in range(i+1, len(titles)):
            dist = min_edit_distance(titles[i], titles[j])
            if dist <= threshold:
                duplicates.append((titles[i], titles[j], dist))

    # -----------------------------
    # Unigram Probabilities
    # -----------------------------
    total_tokens = sum(unigram_freq.values())
    unigram_probs = {
        word: count / total_tokens
        for word, count in unigram_freq.items()
    }

    # -----------------------------
    # Perplexity (5 held-out docs)
    # -----------------------------
    held_out = documents[-5:]
    train_docs = documents[:-5]

    train_freq = Counter(token for doc in train_docs for token in doc)
    train_total = sum(train_freq.values())

    def perplexity(doc):
        N = len(doc)
        log_prob = 0
        for word in doc:
            prob = train_freq.get(word, 1) / train_total
            log_prob += log(prob)
        return exp(-log_prob / N)

    perplexities = [perplexity(doc) for doc in held_out]

    # -----------------------------
    # Write Report
    # -----------------------------
    with open(REPORT_PATH, "w") as f:
        f.write("===== TrendScope Linguistic Report =====\n\n")

        f.write("Top 30 Unigrams:\n")
        for word, count in top_30_unigrams:
            f.write(f"{word}: {count}\n")

        f.write("\nTop 20 Bigrams:\n")
        for (w1, w2), count in top_20_bigrams:
            f.write(f"{w1} {w2}: {count}\n")

        f.write(f"\nVocabulary Size: {vocab_size}\n")
        f.write(f"Average Description Length: {avg_length:.2f}\n")

        f.write("\nPotential Duplicates (Edit Distance <= 5):\n")
        for t1, t2, dist in duplicates[:20]:
            f.write(f"{dist} | {t1} <-> {t2}\n")

        f.write("\nSample Unigram Probabilities:\n")
        for word, prob in list(unigram_probs.items())[:20]:
            f.write(f"{word}: {prob:.6f}\n")

        f.  write("\nPerplexity (5 Held-Out Docs):\n")
        for p in perplexities:
            f.write(f"{p:.4f}\n")


if __name__ == "__main__":
    main()