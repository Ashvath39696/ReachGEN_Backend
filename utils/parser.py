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



class LeadFinderParser(BaseParser):
    """Parses the LLM output for ranked company results."""

    def parse(self, content: str):
        parsed_output = self.safe_json_load(content)
        if not parsed_output:
            parsed_output = {
                "high_priority": [],
                "medium_priority": [],
                "low_priority": []
            }
        return {
            "high_priority": parsed_output.get("high_priority", []),
            "medium_priority": parsed_output.get("medium_priority", []),
            "low_priority": parsed_output.get("low_priority", []),
            "messages": [content],
        }