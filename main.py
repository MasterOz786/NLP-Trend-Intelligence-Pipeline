
import json, os

# v1 480 entries
print("v1 (480 entries) -> data/raw/products_raw.json")
data = [{}]
with open("data/raw/products_raw.json", "r") as f:
    data = json.load(f)


# v2 180 entries
print("v2 (180 entries) -> data/raw/products_raw.json")
data = data[:180]
with open("data/raw/products_raw.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

