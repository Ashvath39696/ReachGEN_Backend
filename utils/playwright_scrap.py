"""
Universal Web Scraper (Resilient Bing + Playwright)
---------------------------------------------------
✓ Works across Bing HTML variants (global regions)
✓ Extracts and cleans actual target URLs
✓ Fully headless
✓ Stores all page text → data/raw_scraped_data.json
"""

import asyncio
import base64
import json
import re
from urllib.parse import parse_qs, urlparse
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
OUT_FILE = DATA_DIR / "raw_scraped_data.json"

# -------------------------------
# Helper: decode Bing redirect URLs
# -------------------------------
def clean_bing_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        encoded = params.get("u", [None])[0]
        if encoded:
            decoded = base64.b64decode(encoded).decode("utf-8", errors="ignore")
            if decoded.startswith("http"):
                return decoded
        return url
    except Exception:
        return url

# -------------------------------
# Bing Search (robust extraction)
# -------------------------------
async def bing_search(playwright, query, max_links=8):
    print(f"🔍 Searching Bing for: {query}")
    urls = []
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()

    try:
        await page.goto(f"https://www.bing.com/search?q={query.replace(' ', '+')}",
                        timeout=60000, wait_until="domcontentloaded")

        # Give Bing time to load dynamic results
        await page.wait_for_timeout(3000)

        # Scroll to load more results
        for _ in range(2):
            await page.mouse.wheel(0, 2500)
            await page.wait_for_timeout(1500)

        # Collect links using multiple selectors
        anchors = await page.query_selector_all("li.b_algo h2 a, a[href^='http']")
        seen = set()
        for a in anchors:
            href = await a.get_attribute("href")
            if href and href.startswith("http"):
                clean = clean_bing_url(href)
                if "bing.com" not in clean and clean not in seen:
                    seen.add(clean)
                    urls.append(clean)
            if len(urls) >= max_links:
                break
    except Exception as e:
        print(f"⚠️ Bing search failed for '{query}': {e}")
    finally:
        await browser.close()

    print(f"✅ Found {len(urls)} clean URLs for query '{query}'")
    return urls

# -------------------------------
# Scraper for each webpage
# -------------------------------
async def scrape_page(page, url):
    await page.goto(url, timeout=60000, wait_until="domcontentloaded")
    html = await page.content()
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.string.strip() if soup.title else ""
    text = soup.get_text(separator="\n", strip=True)
    return {"url": url, "title": title, "raw_text": text[:50000]}

# -------------------------------
# Main Orchestrator
# -------------------------------
async def run_scraper(queries, per_query=8):
    results = []
    async with async_playwright() as p:
        all_urls = []
        for q in queries:
            found = await bing_search(p, q, max_links=per_query)
            all_urls.extend(found)

        unique_urls = list(dict.fromkeys(all_urls))
        print(f"🌐 Total unique URLs to scrape: {len(unique_urls)}")

        if not unique_urls:
            print("⚠️ No URLs found — please try again later or check network.")
            return []

        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for i, url in enumerate(unique_urls, 1):
            try:
                print(f"[{i}/{len(unique_urls)}] 🧭 Scraping: {url}")
                data = await scrape_page(page, url)
                results.append(data)
                print(f"✅ Done: {url}")
            except Exception as e:
                print(f"❌ Failed {url}: {e}")

        await browser.close()

    OUT_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"📦 Saved {len(results)} raw pages → {OUT_FILE.resolve()}")
    return results

# -------------------------------
# CLI Entrypoint
# -------------------------------
def main():
    queries = [
        "Business prospecting tools for sales teams",
        "AI platforms for lead generation and automation",
        "Companies using multi-agent systems for market research",
    ]
    asyncio.run(run_scraper(queries, per_query=8))

if __name__ == "__main__":
    main()
