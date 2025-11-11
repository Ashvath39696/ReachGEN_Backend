"""
Lead Finder Agent
-----------------
Loads leads_full.json from scraper, sends all data to LLM,
asks for prioritization (HIGH / MEDIUM / LOW) and one-line reasoning.
"""

import os
import json
from typing import TypedDict, List, Dict, Optional
from config.llm_client import LLMClient

import pathlib
ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT_DIR / "prompts" / "lead_finder.txt"

llm = LLMClient().get_client()


class LeadFinderState(TypedDict):
    value_prop: str
    customer_profile: str
    search_queries: List[str]
    business_domains: List[str]
    results: Optional[Dict]


async def research_companies(state: LeadFinderState):
    """
    Reads scraped data directly from state["scraped_leads"] and sends all context to the LLM.
    """
    companies = state.get("scraped_leads", {})
    if not companies:
        print("⚠️ No scraped companies found in state.")
        return {}

    # Prepare company text for LLM prompt
    companies_text = json.dumps(companies, indent=2, ensure_ascii=False)

    # Load template prompt
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    prompt = template.format(
        product_name=state.get("product_name", ""),
        description=state.get("description", ""),
        features=", ".join(state.get("features", [])),
        competitors=", ".join(state.get("competitors", [])),
        value_prop=state.get("value_prop", ""),
        customer_profile=state.get("customer_profile", ""),
        business_domains=", ".join(state.get("business_domains", [])),
        companies=companies_text
    )

    print("🧠 Sending companies to LLM for prioritization...")
    try:
        response = llm.invoke(prompt)
        ranked = json.loads(response.content)
    except Exception as e:
        print("❌ LLM or JSON parse error:", e)
        print("Raw output:\n", response if "response" in locals() else "(none)")
        return {}

    # Save output
    os.makedirs("data", exist_ok=True)
    with open("data/leads_ranked.json", "w", encoding="utf-8") as f:
        json.dump(ranked, f, indent=2, ensure_ascii=False)

    print("💾 Saved ranked leads → data/leads_ranked.json")
    return ranked
