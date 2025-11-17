"""
Parser Utilities
----------------
Reusable parser classes for handling LLM responses.

Each agent can have its own dedicated parser class.
Example:
    from utils.parser import InputEnhancerParser

    parsed = InputEnhancerParser().parse(response.content)
"""

import json
from supabase import create_client
from dotenv import load_dotenv
import os
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = "evaluation_runs"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class BaseParser:
    """Base parser with common utilities."""

    def safe_json_load(self, text: str):
        """Try parsing JSON safely; return None if invalid."""
        try:
            return json.loads(text)
        except Exception:
            return None


# ------------------------------------------------------------
# 🧠 Parser for Input Enhancer Agent
# ------------------------------------------------------------
class InputEnhancerParser(BaseParser):
    """
    Parses the LLM output for the Input Enhancer agent.
    Expected keys:
        - search_queries
        - business_domains
    """

    def parse(self, content: str):
        """Main parser logic for Input Enhancer agent."""
        import re, json

        # 1️⃣ Try to extract the JSON block (even if wrapped in ```json)
        match = re.search(r"\{[\s\S]*\}", content)
        parsed_output = None
        if match:
            try:
                parsed_output = json.loads(match.group(0))
            except Exception:
                parsed_output = None

        # 2️⃣ Fallback: extract bullet points if no valid JSON found
        if not parsed_output:
            parsed_output = {"search_queries": [], "business_domains": []}
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith(("•", "-", "*")):
                    parsed_output["search_queries"].append(line.strip("•-* ").strip())

        # 3️⃣ Return consistent structure
        return {
            "search_queries": parsed_output.get("search_queries", []),
            "business_domains": parsed_output.get("business_domains", []),
            "messages": [content],
        }



class LeadPipelineParser(BaseParser):

    def parse(self, pipeline_output: dict):
        """Extract the 4 evaluation outputs from the pipeline result"""

        result = pipeline_output.get("result", {})

        return {
            "product_name": result.get("product_name"),
            "description": result.get("description"),
            "features": result.get("features", []),
            "competitors": result.get("competitors", []),

            "search_queries": result.get("search_queries", []),
            "business_domains": result.get("business_domains", []),

            "scraped_leads": result.get("scraped_leads", {}),
            "ranked_leads": result.get("ranked_leads", {}),
        }

    def save(self, row: dict):
        """Insert into Supabase exactly like your Langfuse syncer"""
        try:
            response = (
                supabase
                .table(SUPABASE_TABLE)
                .insert(row)
                .execute()
            )
            print("🗄️ Saved evaluation row → Supabase")
            return response
        except Exception as e:
            print("❌ Error saving evaluation row:", e)
            return None