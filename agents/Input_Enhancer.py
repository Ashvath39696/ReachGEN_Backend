# Input_Enhancer.py
"""
UserInputEnhancer Agent
-----------------------
Standalone LangGraph + OpenAI agent that:
1. Takes basic product details as input.
2. Generates:
   - Optimized search queries for finding potential customers.
   - Relevant business domains / industries for the product.
"""

from typing import TypedDict, Annotated, List, Optional

from config.llm_client import LLMClient
from utils.parser import InputEnhancerParser

from dotenv import load_dotenv
load_dotenv()
import os

import pathlib
ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]  # points to D:\my_marai
PROMPT_PATH = ROOT_DIR / "prompts" / "input_enhancer.txt"

# -----------------------------
# 1. Configure Environment
# -----------------------------

# Initialize OpenAI model (you can use gpt-4o-mini or gpt-4-turbo)
llm = LLMClient().get_client()

# -----------------------------
# 2. Define State Schema
# -----------------------------
class EnhancerState(TypedDict):
    product_name: str
    description: str
    features: Optional[List[str]]
    competitors: Optional[List[str]]
    search_queries: List[str]
    business_domains: List[str]

# -----------------------------
# 3. Define the Main Node Logic
# -----------------------------
def generate_queries_and_domains(state: EnhancerState):

    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()


    prompt = template.format(
    product_name=state.get("product_name"),
    description=state.get("description"),
    features=", ".join(state.get("features", [])),
    competitors=", ".join(state.get("competitors", []))
   )


    response = llm.invoke(prompt)

    parser = InputEnhancerParser()
    parsed_output = parser.parse(response.content)

    return parsed_output

