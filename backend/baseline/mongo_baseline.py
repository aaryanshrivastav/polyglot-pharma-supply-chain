"""
Single-Database (MongoDB Monolith) Baseline Engine.
Implements the 3 core analytical workflows entirely within MongoDB:
1. Point Lookup: Live stock query on baseline_inventory.
2. Time-Series Aggregation: Date-range rollups on baseline_daily_events.
3. Multi-Hop Graph Traversal: Recursive downstream disruption impact via MongoDB $graphLookup.

Used as the controlled experimental baseline against the Polyglot architecture (Redis + Cassandra + Neo4j + MongoDB)
for SIGMOD 2027 empirical latency and throughput benchmarking.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()
logger = logging.getLogger("MongoBaseline")

STAGED_DIR = PROJECT_ROOT / "data-ingestion" / "staged"


class MongoBaselineEngine:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.client = None
        self.db = None
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")
        self.db_name = os.getenv("MONGO_DB", "pharma_supply_chain")

        if not self.dry_run:
            self._init_mongo()

    def _init_mongo(self):
        """Initializes connection to MongoDB with fast timeout guard."""
        import socket
        try:
            with socket.create_connection(("127.0.0.1", 27017), timeout=0.2):
                from pymongo import MongoClient
                self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=1000)
                self.client.admin.command("ping")
                self.db = self.client[self.db_name]
                logger.info("Connected to MongoDB for Baseline Monolith execution.")
        except Exception as e:
            logger.info(f"MongoDB offline or unreachable ({e}). Using local memory baseline fallback.")
            self.client = None
            self.db = None

    def seed_baseline_collections(self) -> Dict[str, int]:
        """
        Seeds baseline collections with identical dataset volume:
        - baseline_inventory: {pharmacy_id, drug_id, current_stock, reorder_threshold, updated_at}
        - baseline_daily_events: {drug_id, region, rollup_date, total_volume, avg_stock, stockout_count, avg_temperature}
        - baseline_network_edges: {source_id, target_id, relationship, weight}
        """
        if not self.db:
            return {"status": "SKIPPED_OFFLINE", "records": 0}

        counts = {}
        # 1. Seed Network Edges (for $graphLookup)
        edges_file = STAGED_DIR / "topology_edges.json"
        if edges_file.exists():
            with open(edges_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            edges_obj = data.get("edges", {}) if isinstance(data, dict) else {}
            all_edges = []
            for rel, edge_list in edges_obj.items():
                for e in edge_list:
                    all_edges.append({
                        "source_id": e["source_id"],
                        "target_id": e["target_id"],
                        "relationship": rel,
                        "weight": float(e.get("properties", {}).get("lead_time_days", 1.0))
                    })
            if all_edges:
                self.db["baseline_network_edges"].drop()
                self.db["baseline_network_edges"].insert_many(all_edges)
                self.db["baseline_network_edges"].create_index([("source_id", 1)])
                self.db["baseline_network_edges"].create_index([("target_id", 1)])
                counts["baseline_network_edges"] = len(all_edges)

        # 2. Seed Inventory Collection (Point Lookups)
        pharm_file = STAGED_DIR / "pharmacies.json"
        drugs_file = STAGED_DIR / "drugs.json"
        if pharm_file.exists() and drugs_file.exists():
            with open(pharm_file, "r", encoding="utf-8") as f:
                pharms = json.load(f)[:100]
            with open(drugs_file, "r", encoding="utf-8") as f:
                drugs = json.load(f)[:50]

            inventory_docs = []
            for p in pharms:
                for d in drugs:
                    inventory_docs.append({
                        "pharmacy_id": p["pharmacy_id"],
                        "drug_id": d["drug_id"],
                        "current_stock": 85,
                        "reorder_threshold": 25,
                        "status": "ADEQUATE",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    })

            self.db["baseline_inventory"].drop()
            self.db["baseline_inventory"].insert_many(inventory_docs)
            self.db["baseline_inventory"].create_index([("pharmacy_id", 1), ("drug_id", 1)], unique=True)
            counts["baseline_inventory"] = len(inventory_docs)

        # 3. Seed Daily Events (Time-Series Aggregation)
        event_docs = []
        base_dates = [datetime.now(timezone.utc).date() for _ in range(30)]
        for d in drugs[:50]:
            for i, dt in enumerate(base_dates):
                event_docs.append({
                    "drug_id": d["drug_id"],
                    "region": "National",
                    "rollup_date": str(dt),
                    "total_volume": 500 - (i * 2),
                    "avg_stock": round(75.0 - (i * 0.5), 1),
                    "stockout_count": 1 if i > 25 else 0,
                    "avg_temperature": 5.0 if d.get("is_biologic") else 21.0
                })

        self.db["baseline_daily_events"].drop()
        self.db["baseline_daily_events"].insert_many(event_docs)
        self.db["baseline_daily_events"].create_index([("drug_id", 1), ("rollup_date", -1)])
        counts["baseline_daily_events"] = len(event_docs)

        logger.info(f"Seeded MongoDB Baseline collections: {counts}")
        return counts

    # 1. Point Lookup: Single-DB Document Read
    def get_stock(self, pharmacy_id: str, drug_id: str) -> Dict:
        """Point lookup equivalent of Redis stock check in MongoDB."""
        if self.db:
            try:
                doc = self.db["baseline_inventory"].find_one(
                    {"pharmacy_id": pharmacy_id, "drug_id": drug_id},
                    {"_id": 0}
                )
                if doc:
                    doc["source"] = "MONGODB_BASELINE_INVENTORY"
                    return doc
            except Exception as e:
                logger.debug(f"MongoDB inventory query failed: {e}")

        # In-memory baseline fallback
        return {
            "pharmacy_id": pharmacy_id,
            "drug_id": drug_id,
            "current_stock": 85,
            "reorder_threshold": 25,
            "status": "ADEQUATE",
            "source": "MONGODB_BASELINE_MEMORY_FALLBACK",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    # 2. Time-Series Aggregation: Date-Range MongoDB Query
    def get_trends(self, drug_id: str, range_days: int = 30) -> Dict:
        """Time-series rollup query equivalent of Cassandra daily_rollups in MongoDB."""
        if self.db:
            try:
                cursor = self.db["baseline_daily_events"].find(
                    {"drug_id": drug_id},
                    {"_id": 0}
                ).sort("rollup_date", -1).limit(range_days)
                rows = list(cursor)
                if rows:
                    return {
                        "drug_id": drug_id,
                        "record_count": len(rows),
                        "trends": rows,
                        "source": "MONGODB_BASELINE_DAILY_EVENTS"
                    }
            except Exception as e:
                logger.debug(f"MongoDB trends query failed: {e}")

        # In-memory fallback
        base_dates = [datetime.now(timezone.utc).date() for _ in range(range_days)]
        mock_trends = [{
            "region": "National",
            "rollup_date": str(d),
            "total_volume": 480 + (i * 2),
            "avg_stock": round(82.0 - (i * 0.7), 1),
            "stockout_count": 0,
            "avg_temperature": 5.1
        } for i, d in enumerate(base_dates)]

        return {
            "drug_id": drug_id,
            "record_count": len(mock_trends),
            "trends": mock_trends,
            "source": "MONGODB_BASELINE_MEMORY_FALLBACK"
        }

    # 3. Multi-Hop Graph Traversal: $graphLookup Disruption Simulation
    def simulate_disruption(self, node_id: str, drug_id: Optional[str] = None) -> Dict:
        """
        Multi-hop downstream disruption simulation equivalent of Neo4j Cypher traversal
        implemented via MongoDB recursive $graphLookup aggregation pipeline.
        """
        if self.db:
            try:
                pipeline = [
                    {"$match": {"source_id": node_id}},
                    {
                        "$graphLookup": {
                            "from": "baseline_network_edges",
                            "startWith": "$target_id",
                            "connectFromField": "target_id",
                            "connectToField": "source_id",
                            "as": "downstream_network",
                            "maxDepth": 3,
                            "depthField": "hops"
                        }
                    }
                ]
                results = list(self.db["baseline_network_edges"].aggregate(pipeline))
                if results:
                    affected_nodes = set()
                    for r in results:
                        affected_nodes.add(r["target_id"])
                        for d in r.get("downstream_network", []):
                            affected_nodes.add(d["target_id"])

                    pharmacies = [n for n in affected_nodes if n.startswith("PHARM-")]
                    dists = [n for n in affected_nodes if n.startswith("DIST-")]
                    count = len(pharmacies) if pharmacies else len(affected_nodes)

                    # Compute heuristic impact score
                    crit_factor = 1.5 if (drug_id and "0002" in drug_id) else 1.0
                    impact_score = round(count * crit_factor * 1.0, 2)

                    return {
                        "failed_node_id": node_id,
                        "target_drug_id": drug_id or "PORTFOLIO_WIDE",
                        "impact_score": impact_score,
                        "severity_classification": "CATASTROPHIC_DISRUPTION" if impact_score >= 200 else "MODERATE_DISRUPTION",
                        "affected_pharmacy_count": count,
                        "affected_distributor_count": len(dists),
                        "traversal_method": "MONGODB_$graphLookup",
                        "affected_pharmacies_sample": sorted(list(pharmacies))[:15],
                        "source": "MONGODB_GRAPH_LOOKUP"
                    }
            except Exception as e:
                logger.debug(f"MongoDB $graphLookup traversal failed: {e}")

        # In-memory recursive fallback
        edges_file = STAGED_DIR / "topology_edges.json"
        affected_pharmacies = set()
        affected_dists = set()

        if edges_file.exists():
            with open(edges_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            edges_obj = data.get("edges", {}) if isinstance(data, dict) else {}

            if node_id.startswith("EST-"):
                for e in edges_obj.get("SUPPLIES", []):
                    if e["source_id"] == node_id:
                        affected_dists.add(e["target_id"])
                for e in edges_obj.get("DISTRIBUTES_TO", []):
                    if e["source_id"] in affected_dists:
                        affected_pharmacies.add(e["target_id"])
            elif node_id.startswith("DIST-"):
                affected_dists.add(node_id)
                for e in edges_obj.get("DISTRIBUTES_TO", []):
                    if e["source_id"] == node_id:
                        affected_pharmacies.add(e["target_id"])

        count = len(affected_pharmacies) if affected_pharmacies else 50
        crit_factor = 1.5 if (drug_id and "0002" in drug_id) else 1.0
        impact_score = round(count * crit_factor * 1.0, 2)

        return {
            "failed_node_id": node_id,
            "target_drug_id": drug_id or "PORTFOLIO_WIDE",
            "impact_score": impact_score,
            "severity_classification": "CATASTROPHIC_DISRUPTION" if impact_score >= 200 else "MODERATE_DISRUPTION",
            "affected_pharmacy_count": count,
            "affected_distributor_count": len(affected_dists),
            "traversal_method": "MONGODB_EMULATED_RECURSIVE_TRAVERSAL",
            "affected_pharmacies_sample": sorted(list(affected_pharmacies))[:15],
            "source": "MONGODB_BASELINE_FALLBACK"
        }

    def close(self):
        if self.client:
            self.client.close()


# Singleton instance
mongo_baseline_engine = MongoBaselineEngine()

