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
    Parses the LLM output for the Input Enhancer Agent.

    Expected keys:
        - search_queries: list[str]
        - business_domains: list[str]
    """

    def parse(self, content: str):
        """Main parser logic for Input Enhancer agent."""
        parsed_output = self.safe_json_load(content)

        if not parsed_output:
            parsed_output = {"search_queries": [], "business_domains": []}
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue

                if line.startswith(("•", "-", "*")):
                    parsed_output["search_queries"].append(line.strip("•-* ").strip())

        return {
            "search_queries": parsed_output.get("search_queries", []),
            "business_domains": parsed_output.get("business_domains", []),
            "messages": [content],
        }
