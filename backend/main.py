"""
FastAPI Application for Polyglot Pharmaceutical Supply Chain Intelligence Platform.
Exposes database-backed endpoints, ML risk models, and graph-analytic traversal services
with high-resolution structured latency logging for SIGMOD benchmark validation.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.db_clients import db_manager
from ml.root_cause_analysis import rank_root_causes, load_upstream_topology_map, load_upstream_anomalies
from ml.impact_scoring import compute_node_disruption_impact, load_downstream_topology_map

# Structured Logger Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [API] %(message)s"
)
logger = logging.getLogger("PharmaBackend")

app = FastAPI(
    title="Polyglot Pharmaceutical Supply Chain Intelligence API",
    description="Empirical platform for real-time supply chain telemetry, multi-database query dispatching, graph traversal, and ML risk enrichment.",
    version="1.0.0"
)

# Enable CORS for local React/Dashboard development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STAGED_DIR = PROJECT_ROOT / "data-ingestion" / "staged"
OUTPUT_DIR = PROJECT_ROOT / "ml" / "output"

# Cache graph topologies for low-latency traversal
pharm_to_dist, dist_to_mfg = load_upstream_topology_map()
mfg_to_dist, dist_to_pharm, substitutable_drugs, biologic_drugs = load_downstream_topology_map()
anomaly_map = load_upstream_anomalies()


# ---------------------------------------------------------------------------
# Structured Latency & Telemetry Middleware (Critical for Phase 8 Benchmark)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000.0

    # Structured log line
    log_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "method": request.method,
        "path": request.url.path,
        "query_params": str(request.query_params),
        "status_code": response.status_code,
        "latency_ms": round(duration_ms, 3),
        "client_ip": request.client.host if request.client else "unknown"
    }
    logger.info(json.dumps(log_payload))
    response.headers["X-Process-Time-Ms"] = str(round(duration_ms, 3))
    return response


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------
class DisruptionSimulationRequest(BaseModel):
    drug_id: Optional[str] = None
    time_window_days: Optional[int] = 30


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """System health and multi-database connectivity status."""
    db_status = db_manager.get_health_status()
    overall = "HEALTHY" if any(v == "ONLINE" for v in db_status.values()) else "DEGRADED"
    return {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "databases": db_status,
        "service": "polyglot-pharma-backend",
        "version": "1.0.0"
    }


# 1. REDIS ENDPOINT: Live Hot Inventory & Real-Time Stock State
@app.get("/stock/{pharmacy_id}/{drug_id}")
def get_live_stock(pharmacy_id: str, drug_id: str):
    """
    [REDIS HOT CACHE]
    Fetches real-time stock levels, replenishment flags, and live shortage risk
    from in-memory Redis cache (sub-millisecond SLA).
    """
    redis_key = f"stock:{pharmacy_id}:{drug_id}"
    risk_key = f"risk_score:{drug_id}"
    alert_key = f"alert:{drug_id}"

    if db_manager.redis:
        try:
            val = db_manager.redis.get(redis_key)
            risk_val = db_manager.redis.get(risk_key)
            alert_val = db_manager.redis.get(alert_key)

            if val:
                stock_data = json.loads(val) if isinstance(val, str) and val.startswith("{") else {"current_stock": int(val)}
                stock_data["pharmacy_id"] = pharmacy_id
                stock_data["drug_id"] = drug_id
                stock_data["risk_score"] = json.loads(risk_val) if risk_val else None
                stock_data["active_alert"] = json.loads(alert_val) if alert_val else None
                stock_data["source"] = "REDIS_HOT_CACHE"
                return stock_data
        except Exception as e:
            logger.warning(f"Redis fetch error: {e}")

    # Resilient fallback for simulated / offline mode
    return {
        "pharmacy_id": pharmacy_id,
        "drug_id": drug_id,
        "current_stock": 78,
        "reorder_threshold": 25,
        "status": "ADEQUATE",
        "risk_score": {"risk_score": 0.12, "risk_level": "LOW"},
        "active_alert": None,
        "source": "SIMULATED_HOT_FALLBACK",
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


# 2. MONGODB ENDPOINT: Drug Catalog Document & Bioequivalence Metadata
@app.get("/drugs/{drug_id}")
def get_drug_details(drug_id: str):
    """
    [MONGODB DOCUMENT STORE]
    Queries rich drug monograph, storage requirements (cold-chain, CRT),
    active ingredients, and manufacturer facility details.
    """
    if db_manager.mongo:
        try:
            db = db_manager.mongo[db_manager.mongo_db_name]
            doc = db["drugs"].find_one({"drug_id": drug_id}, {"_id": 0})
            if doc:
                doc["source"] = "MONGODB_DOCUMENT_STORE"
                return doc
        except Exception as e:
            logger.warning(f"MongoDB query error: {e}")

    # Fallback to staged drugs.json
    drugs_file = STAGED_DIR / "drugs.json"
    if drugs_file.exists():
        with open(drugs_file, "r", encoding="utf-8") as f:
            drugs = json.load(f)
        for d in drugs:
            if d.get("drug_id") == drug_id:
                res = dict(d)
                res["source"] = "STAGED_JSON_FALLBACK"
                return res

    raise HTTPException(status_code=404, detail=f"Drug with ID '{drug_id}' not found in catalog.")


# 3. CASSANDRA ENDPOINT: Daily Analytical Rollups & Telemetry Trends
@app.get("/trends/{drug_id}")
def get_drug_trends(drug_id: str, range_days: int = Query(default=30, alias="range")):
    """
    [CASSANDRA TIME-SERIES]
    Queries partitioned daily analytical rollups (daily demand volume, average stock,
    stockout frequency, and cold-chain temperature trends) across geographic regions.
    """
    if db_manager.cassandra:
        try:
            cql = """
                SELECT region, rollup_date, total_volume, avg_stock, event_count, stockout_count, avg_temperature, excursion_count
                FROM daily_rollups
                WHERE drug_id = ?;
            """
            rows = list(db_manager.cassandra.execute(cql, (drug_id,)))
            if rows:
                trend_records = [{
                    "region": r.region,
                    "date": str(r.rollup_date),
                    "total_volume": r.total_volume,
                    "avg_stock": round(r.avg_stock, 1),
                    "event_count": r.event_count,
                    "stockout_count": r.stockout_count,
                    "avg_temperature": round(r.avg_temperature, 1),
                    "excursion_count": r.excursion_count
                } for r in rows[:range_days]]

                return {
                    "drug_id": drug_id,
                    "record_count": len(trend_records),
                    "trends": trend_records,
                    "source": "CASSANDRA_DAILY_ROLLUPS"
                }
        except Exception as e:
            logger.warning(f"Cassandra query error: {e}")

    # Simulated Fallback
    base_dates = [datetime.now(timezone.utc).date() for _ in range(range_days)]
    mock_trends = [{
        "region": "National",
        "date": str(d),
        "total_volume": 450 + (i * 2),
        "avg_stock": round(80.0 - (i * 0.8), 1),
        "event_count": 50,
        "stockout_count": 1 if i > 20 else 0,
        "avg_temperature": 5.2,
        "excursion_count": 0
    } for i, d in enumerate(base_dates)]

    return {
        "drug_id": drug_id,
        "record_count": len(mock_trends),
        "trends": mock_trends,
        "source": "SIMULATED_CASSANDRA_FALLBACK"
    }


# 4. SPOF GRAPH CENTRALITY ENDPOINT: Top Bottleneck Distribution Hubs
@app.get("/network/spof")
def get_spof_rankings(top_k: int = Query(default=20, ge=1, le=100)):
    """
    [GRAPH ANALYTICS & SPOF]
    Returns ranked intermediate distributor hubs and high-betweenness single points of failure.
    """
    if db_manager.mongo:
        try:
            db = db_manager.mongo[db_manager.mongo_db_name]
            scores = list(db["spof_scores"].find({}, {"_id": 0}).sort("spof_risk_index", -1).limit(top_k))
            if scores:
                return {
                    "total_ranked": len(scores),
                    "rankings": scores,
                    "source": "MONGODB_SPOF_COLLECTION"
                }
        except Exception as e:
            logger.warning(f"MongoDB SPOF fetch error: {e}")

    # Local JSON / ML Output Fallback
    spof_file = OUTPUT_DIR / "spof_rankings.json"
    if spof_file.exists():
        with open(spof_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "total_ranked": len(data[:top_k]),
            "rankings": data[:top_k],
            "source": "ML_OUTPUT_FILE_SPOF"
        }

    # Hardcoded topological baseline
    return {
        "total_ranked": 3,
        "rankings": [
            {"node_id": "DIST-0014", "node_type": "Distributor", "spof_risk_index": 1.000, "betweenness_centrality": 0.0112, "classification": "CRITICAL_BOTTLENECK"},
            {"node_id": "DIST-0011", "node_type": "Distributor", "spof_risk_index": 0.933, "betweenness_centrality": 0.0101, "classification": "CRITICAL_BOTTLENECK"},
            {"node_id": "DIST-0010", "node_type": "Distributor", "spof_risk_index": 0.710, "betweenness_centrality": 0.0062, "classification": "CRITICAL_BOTTLENECK"}
        ],
        "source": "STATIC_TOPOLOGY_BASELINE"
    }


# 5. FORWARD REASONING ENDPOINT: Disruption Simulation + Weighted Impact Score
@app.post("/simulate/disruption/{node_id}")
def simulate_disruption(node_id: str, payload: Optional[DisruptionSimulationRequest] = None):
    """
    [FORWARD REASONING & WEIGHTED IMPACT SCORING]
    Simulates failure of an upstream facility (manufacturer or distributor) and returns:
      impact_score = affected_pharmacy_count * drug_criticality_factor * regional_weight
    alongside the full affected downstream nodes list.
    """
    drug_id = payload.drug_id if payload else None
    try:
        impact = compute_node_disruption_impact(
            node_id=node_id,
            target_drug_id=drug_id,
            mfg_to_dist=mfg_to_dist,
            dist_to_pharm=dist_to_pharm,
            substitutable_drugs=substitutable_drugs,
            biologic_drugs=biologic_drugs
        )
        return impact
    except Exception as e:
        logger.error(f"Error simulating disruption for {node_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# 6. BACKWARD REASONING ENDPOINT: Root Cause Analysis
@app.get("/root-cause/{pharmacy_id}/{drug_id}")
def get_root_cause(pharmacy_id: str, drug_id: str):
    """
    [BACKWARD REASONING & ROOT CAUSE DIAGNOSIS]
    Given a pharmacy node observing a shortage, traverses upstream through reversed
    supply paths and cross-references anomaly telemetry to identify the primary failure node.
    """
    try:
        ranked_candidates = rank_root_causes(
            pharmacy_id=pharmacy_id,
            drug_id=drug_id,
            pharm_to_dist=pharm_to_dist,
            dist_to_mfg=dist_to_mfg,
            anomaly_map=anomaly_map
        )
        return {
            "query_pharmacy_id": pharmacy_id,
            "query_drug_id": drug_id,
            "diagnosed_at": datetime.now(timezone.utc).isoformat(),
            "top_root_cause": ranked_candidates[0] if ranked_candidates else None,
            "all_candidates": ranked_candidates
        }
    except Exception as e:
        logger.error(f"Error diagnosing root cause for {pharmacy_id}/{drug_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
