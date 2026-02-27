from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

url = "https://www.saashub.com/best-finance-software"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_load_state("networkidle")

    while True:        
        # Scroll to bottom to trigger lazy-load
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(.5)

        # Scroll to bottom to trigger lazy-load
        try:
            show_more = page.locator("#load_more_services_btn")
            show_more.scroll_into_view_if_needed(timeout=2000)  # ensure it's clickable

            show_more.click()
        except:
            break

    # Now all products should be loaded
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

    input(f"All {len(products)} products loaded. Press Enter to close browser...")
    browser.close()
    p.stop()

    for p in products:
        print(p)

    print("Total products:", len(products))