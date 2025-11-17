"""
LangGraph Lead Research Pipeline (API-ready, StateGraph-based)
--------------------------------------------------------------
Pipeline:
1️⃣ Input Enhancer → generates optimized search queries & domains
2️⃣ Playwright Scraper → scrapes company data
3️⃣ Lead Finder → ranks companies via LLM
"""

import asyncio
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Import agents and utils
from agents.input_enhancer import generate_queries_and_domains
from agents.lead_finder import research_companies
from utils.google_scraper import run_cse_scraper



# ============================================================
# Shared State
# ============================================================
from typing import TypedDict, List, Dict, Any, Optional

class LeadPipelineState(TypedDict, total=False):
    product_name: str
    description: str
    features: List[str]
    competitors: List[str]
    search_queries: List[str]
    business_domains: List[str]
    messages: List[str]
    scraped_leads: Optional[Dict[str, Any]]
    ranked_leads: Optional[Dict[str, Any]]



# ============================================================
# Node 1: Input Enhancer (make async)
# ============================================================
async def node_input_enhancer(state: LeadPipelineState) -> LeadPipelineState:
    print("\n🔹 Running Input Enhancer...")

    # Run enhancer
    enhanced_output = generate_queries_and_domains(state)

    # Ensure proper state update
    if isinstance(enhanced_output, dict):
        for k, v in enhanced_output.items():
            state[k] = v

    print("✅ Input Enhancer Output:")
    print(state)

    # Explicitly return same state object (not a new dict)
    return state



# ============================================================
# Node 2: Web Scraper
# ============================================================
async def node_google_scraper(state: LeadPipelineState) -> LeadPipelineState:
    print("\n🔹 Running Google Web Scraper...")
    print("🧠 State before scraper:", state.keys())

    queries = state.get("search_queries", [])
    print("🧩 Queries received from Input Enhancer:", queries)

    if not queries:
        print("⚠️ No search queries found. Skipping Google Scraper.")
        return state

    #from utils.google_scraper import run_cse_scraper
    results = run_cse_scraper(queries, results_per_query=5)
    state["scraped_leads"] = results

    print(f"✅ Scraper fetched {sum(len(v) for v in results.values())} total results.")
    return state


# ============================================================
# Node 3: Lead Finder (LLM Ranking)
# ============================================================
async def node_lead_finder(state: LeadPipelineState) -> LeadPipelineState:
    print("\n🔹 Running Lead Finder (LLM Ranking)...")

    # Build value proposition & customer profile
    state["value_prop"] = (
        f"{state.get('product_name', '')}: {state.get('description', '')}. "
        f"Key features include {', '.join(state.get('features', []))}."
    )

    state["customer_profile"] = (
        "Ideal customers include businesses in "
        + ", ".join(state.get('business_domains', []))
        + "."
    )

    # 🧩 Pass scraped data directly to the LLM agent
    scraped_data = state.get("scraped_leads", {})
    if not scraped_data:
        print("⚠️ No scraped company data found. Skipping Lead Finder.")
        return state

    # Save scraped data as a file (for lead_finder agent to use if needed)
    import json, os
    os.makedirs("data", exist_ok=True)
    with open("data/google_webscrap_results.json", "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, indent=2, ensure_ascii=False)

    # Run the Lead Finder agent
    ranked = await research_companies(state)
    state["ranked_leads"] = ranked or {}

    print("✅ Lead Finder completed ranking.")
    return state


# ============================================================
# Build the LangGraph
# ============================================================
# ============================================================
# Build the LangGraph (with Google Scraper Integration)
# ============================================================
def build_graph():
    """
    Constructs the Lead Research pipeline graph:
        Input Enhancer → Google Scraper → Lead Finder
    """

    memory = MemorySaver()
    graph_builder = StateGraph(LeadPipelineState)

    # -----------------------------
    # Register all nodes
    # -----------------------------
    graph_builder.add_node("input_enhancer", node_input_enhancer)
    graph_builder.add_node("google_scraper", node_google_scraper)
    graph_builder.add_node("lead_finder", node_lead_finder)

    # -----------------------------
    # Define flow connections
    # -----------------------------
    graph_builder.add_edge(START, "input_enhancer")        # Start → Input Enhancer
    graph_builder.add_edge("input_enhancer", "google_scraper")  # Input Enhancer → Google Scraper
    graph_builder.add_edge("google_scraper", "lead_finder")     # Google Scraper → Lead Finder
    graph_builder.add_edge("lead_finder", END)             # Lead Finder → End

    # -----------------------------
    # Compile and return LangGraph
    # -----------------------------
    graph = graph_builder.compile(checkpointer=memory)
    return graph



# ============================================================
# ✅ Main async entrypoint (API + Dev)
# ============================================================
async def main(input_data: dict):
    """
    Main pipeline function callable from API or CLI.
    """
    print("\n🚀 Starting LangGraph Lead Research Pipeline...")
    graph = build_graph()

    result = await graph.ainvoke(
        input_data,
        config={"configurable": {"thread_id": "session-1"}}
    )

    print("\n✅ Pipeline completed successfully!")
    print("📁 Results saved in: data/leads_full.json & data/leads_ranked.json")
    return result


# ============================================================
# Dev Test Runner
# ============================================================
if __name__ == "__main__":
    import json

    async def _run_dev():
        print("\n[DEV MODE] Running Lead Research pipeline test...\n")

        input_data = {
            "product_name": "AI Workflow Optimizer",
            "description": "Automates repetitive workflows and integrates with CRM and ERP using AI.",
            "features": [
                "Multi-agent orchestration",
                "Process automation",
                "CRM integration",
                "Custom workflow builder"
            ],
            "competitors": ["Zapier", "UiPath", "Make.com"]
        }

        result = await main(input_data)
        print("\n✅ Pipeline result summary:")
        print(json.dumps(result, indent=2))

    asyncio.run(_run_dev())
