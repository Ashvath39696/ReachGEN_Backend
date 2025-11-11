"""
Google Custom Search Engine (CSE) Scraper
------------------------------------------
Reads API key from .env file
Input  : List of search queries
Output : JSON with title, link, snippet for top results

Dependencies:
    pip install google-api-python-client python-dotenv
Run:
    python utils/google_search_api_scraper.py
"""

import json
import os
from pathlib import Path
from googleapiclient.discovery import build
from dotenv import load_dotenv

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()

API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")  # from your .env file
SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")  # optional if you add it to .env too

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "google_webscrap_results.json"
OUTPUT_PATH.parent.mkdir(exist_ok=True)

if not API_KEY:
    raise ValueError("❌ Missing 'GOOGLE_SEARCH_API_KEY' in your .env file!")

if not SEARCH_ENGINE_ID:
    raise ValueError("❌ Missing 'GOOGLE_SEARCH_ENGINE_ID' in your .env file!")

# ------------------------------
# Google Search Function
# ------------------------------
def google_search(query, api_key, cse_id, num_results=5):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=query, cx=cse_id, num=num_results).execute()
    results = []
    for item in res.get("items", []):
        results.append({
            "title": item.get("title"),
            "snippet": item.get("snippet"),
            "link": item.get("link")
        })
    return results


# ------------------------------
# Main Scraper Function
# ------------------------------
def run_cse_scraper(queries, results_per_query=5):
    all_results = {}
    for q in queries:
        print(f"🔍 Searching: {q}")
        try:
            all_results[q] = google_search(q, API_KEY, SEARCH_ENGINE_ID, results_per_query)
            print(f"✅ {len(all_results[q])} results found.")
        except Exception as e:
            print(f"⚠️ Error fetching '{q}': {e}")
            all_results[q] = []
    
    # Save results to JSON
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Results saved to: {OUTPUT_PATH.resolve()}")
    return all_results


# ------------------------------
# Example Run
# ------------------------------
if __name__ == "__main__":
    queries = [
        "Business prospecting tools for sales teams",
        "AI platforms for lead generation and automation",
        "Companies using multi-agent systems for market research"
    ]
    run_cse_scraper(queries, results_per_query=5)
