from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json
import os
from datetime import datetime

urls = [
    "https://www.saashub.com/best-finance-software",
    "https://www.saashub.com/best-investing-software"
]

RATE_LIMIT_SECONDS = 1  # Wait between scrolls/clicks
MAX_RETRIES = 3  # Retry attempts for "Load more"

all_results = []

# Ensure directory exists
os.makedirs("data/raw", exist_ok=True)

def scrape_page(page, base_url):
    """Scrape products from a single page, including features"""
    products = []

    soup = BeautifulSoup(page.content(), "html.parser")

    for item in soup.select("li[itemtype='http://schema.org/ListItem']"):
        name_tag = item.select_one("span[itemprop='name']")
        link_tag = item.select_one("a[href*='-alternatives']")
        desc_tag = item.select_one("p[itemprop='description']")
        tags = [t.get_text(strip=True) for t in item.select(".categories a")]  # categories/tags
        popularity_tag = item.select_one(".rating")  # likes/upvotes/comments
        features_tag = item.select("p.features-list span")  # feature list
        features = [f.get_text(strip=True) for f in features_tag] if features_tag else []

        timestamp_utc = datetime.utcnow().isoformat()

        if not name_tag or not link_tag:
            continue  # skip incomplete entries

        product = {
            "name": name_tag.get_text(strip=True) if name_tag else None,
            "tagline": desc_tag.get_text(strip=True) if desc_tag else None,
            "tags": tags if tags else [],
            "features": features,  # new field for features
            "popularity": popularity_tag.get_text(strip=True) if popularity_tag else None,
            "url": urljoin(base_url, link_tag["href"]) if link_tag else None,
            "scrape_timestamp_utc": timestamp_utc
        }
        products.append(product)

    return products

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    for url in urls:
        print(f"\nScraping: {url}")
        page.goto(url)
        page.wait_for_load_state("networkidle")

        # Scroll and load all products
        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(RATE_LIMIT_SECONDS)

            retries = 0
            while retries < MAX_RETRIES:
                try:
                    show_more = page.locator("#load_more_services_btn")
                    show_more.scroll_into_view_if_needed(timeout=2000)
                    show_more.click()
                    time.sleep(RATE_LIMIT_SECONDS)
                    break  # success
                except PlaywrightTimeoutError:
                    retries += 1
                    print(f"Retry {retries}/{MAX_RETRIES} for Load More button...")
                    time.sleep(RATE_LIMIT_SECONDS)
                except Exception:
                    # Likely no more button
                    retries = MAX_RETRIES
                    break
            else:
                # No more retries, exit scroll loop
                break

        # Scrape products from fully loaded page
        products = scrape_page(page, url)
        print(f"Loaded {len(products)} products from {url}")
        all_results.extend(products)

    input("\nAll URLs scraped. Press Enter to close browser...")
    browser.close()

# Save raw data to JSON
with open("data/raw/products_raw.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=4)

print("\nRaw dataset saved to data/raw/products_raw.json")