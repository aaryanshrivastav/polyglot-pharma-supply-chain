"""
Parallel REST Endpoints for Single-Database (MongoDB) Baseline.
Provides side-by-side equivalent routes for Phase 8 empirical benchmark comparisons:
- GET  /baseline/stock/{pharmacy_id}/{drug_id}  -> Mongo Document Point-Lookup
- GET  /baseline/trends/{drug_id}               -> Mongo Date-Range Event Query
- POST /baseline/simulate/disruption/{node_id}  -> Mongo $graphLookup Traversal
- POST /baseline/seed                           -> Seed baseline collections
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from backend.baseline.mongo_baseline import mongo_baseline_engine

router = APIRouter(prefix="/baseline", tags=["MongoDB Single-DB Baseline"])


class BaselineDisruptionRequest(BaseModel):
    drug_id: Optional[str] = None
    time_window_days: Optional[int] = 30


@router.get("/stock/{pharmacy_id}/{drug_id}")
def baseline_get_stock(pharmacy_id: str, drug_id: str):
    """
    [BASELINE: MONGODB POINT LOOKUP]
    Point-lookup query on MongoDB baseline_inventory collection.
    Directly comparable to Redis GET /stock/{pharmacy_id}/{drug_id}.
    """
    return mongo_baseline_engine.get_stock(pharmacy_id=pharmacy_id, drug_id=drug_id)


@router.get("/trends/{drug_id}")
def baseline_get_trends(drug_id: str, range_days: int = Query(default=30, alias="range")):
    """
    [BASELINE: MONGODB TIME-SERIES AGGREGATION]
    Date-range analytical query over MongoDB baseline_daily_events collection.
    Directly comparable to Cassandra GET /trends/{drug_id}.
    """
    return mongo_baseline_engine.get_trends(drug_id=drug_id, range_days=range_days)


@router.post("/simulate/disruption/{node_id}")
def baseline_simulate_disruption(node_id: str, payload: Optional[BaselineDisruptionRequest] = None):
    """
    [BASELINE: MONGODB $graphLookup TRAVERSAL]
    Multi-hop downstream disruption traversal via MongoDB $graphLookup pipeline.
    Directly comparable to Neo4j POST /simulate/disruption/{node_id}.
    """
    drug_id = payload.drug_id if payload else None
    return mongo_baseline_engine.simulate_disruption(node_id=node_id, drug_id=drug_id)


@router.post("/seed")
def baseline_seed_data():
    """Seeds baseline MongoDB collections with identical dataset volume."""
    counts = mongo_baseline_engine.seed_baseline_collections()
    return {
        "status": "SUCCESS",
        "message": "MongoDB Baseline collections initialized",
        "seeded_counts": counts
    }

