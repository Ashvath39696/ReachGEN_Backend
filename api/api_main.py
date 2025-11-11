"""
API Main for ReachGen Graph Pipelines
-------------------------------------
FastAPI app exposing endpoints for:
- Lead Research Graph Pipeline (graph_builder_2)
Future: add /text_summarizer, /email_analyzer, etc.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from graphs.graph_builder_2 import main as lead_pipeline_main


# ------------------------------------------------------
# Initialize FastAPI
# ------------------------------------------------------
app = FastAPI(
    title="ReachGen AI API",
    version="1.0.0",
    description="FastAPI interface for LangGraph-based pipelines (Lead Research, Scrapers, Enhancers, etc.)"
)

# ------------------------------------------------------
# Input schema for Lead Research Pipeline
# ------------------------------------------------------
class LeadResearchInput(BaseModel):
    product_name: str = Field(..., example="AI Workflow Optimizer")
    description: str = Field(..., example="Automates repetitive workflows and integrates with CRM and ERP using AI.")
    features: Optional[List[str]] = Field(default=[], example=["Multi-agent orchestration", "CRM integration"])
    competitors: Optional[List[str]] = Field(default=[], example=["Zapier", "UiPath"])
    value_prop: Optional[str] = Field(default="AI automation for enterprises", example="Enhances productivity via intelligent workflow automation.")
    customer_profile: Optional[str] = Field(default="Medium to large enterprises seeking AI-driven workflow tools", example="B2B enterprises in automation, SaaS, CRM sectors")

# ------------------------------------------------------
# Endpoint: /run-lead-pipeline
# ------------------------------------------------------
@app.post("/run-lead-pipeline")
async def run_lead_pipeline(input_data: LeadResearchInput):
    """
    Trigger the LangGraph Lead Research Pipeline.
    Returns structured JSON with ranked leads.
    """
    try:
        print("\n⚡ Triggering Lead Research Pipeline via API...")
        result = await lead_pipeline_main(input_data.dict())
        return {"status": "success", "pipeline": "lead_research", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------
# Root route
# ------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "🚀 ReachGen AI API is running.",
        "available_endpoints": ["/run-lead-pipeline"],
        "next_steps": "Add more endpoints for text summarization, scraping, etc."
    }

# ------------------------------------------------------
# Run directly (Dev mode)
# ------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("api_main:app", host="0.0.0.0", port=8000, reload=True)
