"""
API Main for ReachGen Graph Pipelines
-------------------------------------
FastAPI app exposing endpoints for:
- Lead Research Graph Pipeline (graph_builder_2)
- Supabase evaluation APIs
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from graphs.graph_builder_2 import main as lead_pipeline_main
from utils.parser import LeadPipelineParser

from dotenv import load_dotenv
from supabase import create_client, Client

# ------------------------------------------------------
# Load environment
# ------------------------------------------------------
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "evaluation_runs")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------------
# Initialize FastAPI
# ------------------------------------------------------
app = FastAPI(
    title="ReachGen AI API",
    version="1.1.0",
    description="FastAPI interface for LangGraph Lead Research Pipeline + Supabase evaluation"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------
# Input schema for Lead Research Pipeline
# ------------------------------------------------------
class LeadResearchInput(BaseModel):
    product_name: str = Field(..., example="AI Workflow Optimizer")
    description: str = Field(..., example="Automates workflows using AI.")
    features: Optional[List[str]] = Field(default=[], example=["Multi-agent orchestration", "CRM integration"])
    competitors: Optional[List[str]] = Field(default=[], example=["Zapier", "UiPath"])
    value_prop: Optional[str] = Field(default="AI automation for enterprises")
    customer_profile: Optional[str] = Field(default="Medium to large enterprises seeking automation")

class CategoryUpdate(BaseModel):
    trace_id: str
    category: str

class EvaluationUpdate(BaseModel):
    trace_id: str
    evaluation_status: str
    evaluation_comment: Optional[str] = None

# ------------------------------------------------------
# Endpoint: /run-lead-pipeline
# ------------------------------------------------------
@app.post("/run-lead-pipeline")
async def run_lead_pipeline(input_data: LeadResearchInput):
    try:
        # Run LangGraph pipeline
        result = await lead_pipeline_main(input_data.dict())

        # Save results into Supabase
        parser = LeadPipelineParser()
        row = parser.parse({"result": result})
        parser.save(row)

        return {"status": "success", "result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------
# Evaluation APIs (Supabase)
# ------------------------------------------------------

@app.get("/evaluation/runs")
def get_all_evaluations():
    """Fetch latest 50 evaluation rows from Supabase."""
    try:
        response = (
            supabase.table(SUPABASE_TABLE)
            .select(
                "id, created_at, product_name, category, evaluation_status, evaluation_comment, "
                "search_queries, business_domains, scraped_leads, ranked_leads"
            )
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        return response.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/evaluation/runs/category/{category}")
def get_by_category(category: str):
    """Filter runs by category."""
    try:
        response = (
            supabase.table(SUPABASE_TABLE)
            .select(
                "id, created_at, product_name, category, evaluation_status, evaluation_comment, "
                "search_queries, business_domains, scraped_leads, ranked_leads"
            )
            .eq("category", category)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluation/update-category")
def update_category(payload: CategoryUpdate):
    """Update category for a specific evaluation row."""
    try:
        result = (
            supabase.table(SUPABASE_TABLE)
            .update({"category": payload.category})
            .eq("id", payload.trace_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Evaluation row not found")

        return {"message": "✅ Category updated successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluation/update-evaluation")
def update_evaluation(payload: EvaluationUpdate):
    """Update evaluation status + comment."""
    try:
        result = (
            supabase.table(SUPABASE_TABLE)
            .update(
                {
                    "evaluation_status": payload.evaluation_status,
                    "evaluation_comment": payload.evaluation_comment,
                }
            )
            .eq("id", payload.trace_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Evaluation row not found")

        return {"message": "✅ Evaluation updated successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------
# Root route
# ------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "🚀 ReachGen AI API is running.",
        "available_endpoints": [
            "/run-lead-pipeline",
            "/evaluation/runs",
            "/evaluation/runs/category/{category}",
            "/evaluation/update-category",
            "/evaluation/update-evaluation"
        ]
    }

# ------------------------------------------------------
# Run directly (Dev Mode)
# ------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("api_main:app", host="127.0.0.1", port=8000, reload=True)
