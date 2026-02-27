from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json
import os

urls = [
    "https://www.saashub.com/best-finance-software",
    "https://www.saashub.com/best-investing-software"
]

all_results = {}

# Ensure directory exists
os.makedirs("data/raw", exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    for url in urls:
        print(f"\nScraping: {url}")
        page.goto(url)
        page.wait_for_load_state("networkidle")

        # Load all products
        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(0.5)

            try:
                show_more = page.locator("#load_more_services_btn")
                show_more.scroll_into_view_if_needed(timeout=2000)
                show_more.click()
                time.sleep(0.5)
            except:
                break

        soup = BeautifulSoup(page.content(), "html.parser")
        products = []

        for item in soup.select("li[itemtype='http://schema.org/ListItem']"):
            name_tag = item.select_one("span[itemprop='name']")
            link_tag = item.select_one("a[href*='-alternatives']")
            position_tag = item.select_one("meta[itemprop='position']")
            desc_tag = item.select_one("p[itemprop='description']")
            rating_tag = item.select_one(".rating")

            if name_tag and link_tag:
                products.append({
                    "rank": position_tag["content"] if position_tag else None,
                    "name": name_tag.get_text(strip=True),
                    "url": urljoin(url, link_tag["href"]),
                    "rating_votes": rating_tag.get_text(strip=True) if rating_tag else None,
                    "description": desc_tag.get_text(strip=True) if desc_tag else None
                })

        print(f"Loaded {len(products)} products from {url}")
        all_results[url] = products

    input("\nAll URLs scraped. Press Enter to close browser...")
    browser.close()

# Save raw data to JSON
with open("data/raw/products_raw.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=4)

print("\nRaw dataset saved to data/raw/products_raw.json")