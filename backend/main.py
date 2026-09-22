"""
FastAPI Backend Application for Polyglot Pharma Supply Chain Platform.
Exposes REST endpoints for analytical queries, root-cause diagnosis, and disruption impact simulation.
"""

import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ml.root_cause_analysis import RootCauseEngine
from ml.impact_scoring import ImpactScoringEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BackendAPI")

app = FastAPI(
    title="Polyglot Pharmaceutical Supply Chain Intelligence API",
    description="Empirical platform for real-time supply chain telemetry, graph traversal, and ML risk enrichment.",
    version="1.0.0"
)

# Enable CORS for frontend visualization dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ML engines in dry_run / fallback-resilient mode
root_cause_engine = RootCauseEngine(dry_run=False)
impact_engine = ImpactScoringEngine(dry_run=False)


class DisruptionSimulationRequest(BaseModel):
    drug_id: Optional[str] = None
    time_window_days: Optional[int] = 30


@app.get("/health")
def health_check():
    """Service health and liveness probe."""
    return {
        "status": "HEALTHY",
        "service": "polyglot-pharma-backend",
        "ml_modules": ["forecast_shortage", "spof_centrality", "anomaly_detection", "root_cause_analysis", "impact_scoring"]
    }


@app.get("/root-cause/{pharmacy_id}/{drug_id}")
def get_root_cause(pharmacy_id: str, drug_id: str):
    """
    Backward reasoning endpoint:
    Given a pharmacy and drug with an active alert or stockout, traverses upstream
    through the supply graph and returns ranked candidate root-cause failure nodes.
    """
    try:
        diagnosis = root_cause_engine.find_root_causes(pharmacy_id=pharmacy_id, drug_id=drug_id)
        return diagnosis
    except Exception as e:
        logger.error(f"Error computing root cause for {pharmacy_id}/{drug_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate/disruption/{node_id}")
def simulate_node_disruption(node_id: str, payload: Optional[DisruptionSimulationRequest] = None):
    """
    Forward reasoning & impact scoring endpoint:
    Given a simulated failed node (manufacturer or distributor), calculates
    the weighted impact score alongside the complete list of downstream affected facilities.
    """
    try:
        drug_id = payload.drug_id if payload else None
        impact = impact_engine.evaluate_node_failure(node_id=node_id, drug_id=drug_id)
        return impact
    except Exception as e:
        logger.error(f"Error simulating disruption for node {node_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

