

import pandas as pd
import json
import re
import os
import string
from bs4 import BeautifulSoup

import nltk
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet')
# nltk.download('punkt_tab')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

import unicodedata

INPUT_FILE = "data/raw/products_raw.json"
OUTPUT_FILE = "data/processed/products_clean.csv"

os.makedirs("data/processed", exist_ok=True)

# Load raw dataset
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)
    products = data

# Initialize NLP tools
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def clean_text(text):
    if not text:
        return "", []

    # Unicode normalization (Normal Form Compatibility Composition)
    text = unicodedata.normalize("NFKC", text)

    # Lowercase
    text = text.lower()

    # Remove HTML
    text = BeautifulSoup(text, "html.parser").get_text(separator=" ")

    # Remove URLs
    text = re.sub(r"http\S+|www\S+", "", text)

    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))

    # Tokenize
    tokens = word_tokenize(text)

    # Remove stopwords, numeric-only, length < 2, and lemmatize
    clean_tokens = [
        lemmatizer.lemmatize(tok)
        for tok in tokens
        if tok not in stop_words and not tok.isnumeric() and len(tok) > 1
    ]

    return text.strip(), clean_tokens

# Process each product
records = []
for product in products:
    # Combine product_name and tagline
    raw_text = (product.get("name") or "") + " " + (product.get("tagline") or "")
    text_raw, tokens = clean_text(raw_text)
    token_count = len(tokens)

    records.append({
        "text_raw": text_raw,
        "text_clean": " ".join(tokens),
        "tokens": tokens,
        "token_count": token_count
    })

# Save to CSV
df = pd.DataFrame(records)
df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

print(f"Processed dataset saved to {OUTPUT_FILE}")
print(f"Total records: {len(df)}")