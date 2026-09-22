"""
ML Module: Single Point of Failure (SPOF) & Betweenness Centrality Analysis.
Analyzes the multi-echelon supply chain topology using NetworkX graph algorithms to identify
vulnerable bottleneck distributor hubs and high-risk critical transit nodes.
Persists ranked SPOF risk metrics to MongoDB and local JSON.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple
import networkx as nx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SPOFCentrality")

OUTPUT_DIR = PROJECT_ROOT / "ml" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STAGED_DIR = PROJECT_ROOT / "data-ingestion" / "staged"


def build_supply_chain_graph(edges_data: List[Dict]) -> nx.DiGraph:
    """Builds a directed NetworkX graph from supply chain topology edges."""
    G = nx.DiGraph()
    for edge in edges_data:
        u = edge["source_id"]
        v = edge["target_id"]
        rel = edge.get("relationship", "SHIPS_TO")
        weight = float(edge.get("weight", 1.0))
        tier = edge.get("tier", "PRIMARY")
        G.add_edge(u, v, relationship=rel, weight=weight, tier=tier)
    return G


def compute_spof_metrics(G: nx.DiGraph, k_approx: int = 200) -> List[Dict]:
    """
    Calculates Betweenness Centrality, Degree Centralities, and composite SPOF Risk Index.
    Uses approximation for betweenness if the graph is large (>500 nodes).
    """
    num_nodes = G.number_of_nodes()
    logger.info(f"Computing graph metrics on network with {num_nodes:,} nodes and {G.number_of_edges():,} edges...")

    # 1. Degree Centralities
    in_degree = dict(G.in_degree())
    out_degree = dict(G.out_degree())

    # 2. Betweenness Centrality (approximated via sampling if graph is large)
    if num_nodes > 500:
        k_samples = min(k_approx, num_nodes)
        logger.info(f"Approximating betweenness centrality with k={k_samples} node samples...")
        betweenness = nx.betweenness_centrality(G, k=k_samples, normalized=True, weight="weight", seed=42)
    else:
        betweenness = nx.betweenness_centrality(G, normalized=True, weight="weight")

    # Max betweenness for scaling
    max_b = max(betweenness.values()) if betweenness else 1.0
    if max_b == 0.0:
        max_b = 1.0

    metrics_list = []
    for node in G.nodes():
        node_type = "Distributor" if node.startswith("DIST-") else ("Manufacturer" if node.startswith("EST-") else "Pharmacy")
        b_score = betweenness.get(node, 0.0)
        in_deg = in_degree.get(node, 0)
        out_deg = out_degree.get(node, 0)

        # Bottleneck Risk Index: 0.0 - 1.0 scale
        # Evaluates structural criticality: betweenness relative to max + throughput load
        spof_index = round(0.65 * (b_score / max_b) + 0.35 * min(1.0, (in_deg + out_deg) / 50.0), 4)

        if spof_index >= 0.70:
            classification = "CRITICAL_BOTTLENECK"
        elif spof_index >= 0.40:
            classification = "HIGH_CONCENTRATION"
        elif spof_index >= 0.15:
            classification = "MODERATE_DEPENDENCY"
        else:
            classification = "STANDARD_NODE"

        metrics_list.append({
            "node_id": node,
            "node_type": node_type,
            "betweenness_centrality": round(b_score, 6),
            "normalized_betweenness": round(b_score / max_b, 4),
            "in_degree": in_deg,
            "out_degree": out_deg,
            "spof_risk_index": spof_index,
            "classification": classification,
            "evaluated_at": datetime.now(timezone.utc).isoformat()
        })

    # Sort descending by SPOF risk index
    metrics_list.sort(key=lambda x: x["spof_risk_index"], reverse=True)
    return metrics_list


class SPOFAnalyzer:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.mongo_client = None
        self.neo4j_driver = None

        if not self.dry_run:
            self._init_connections()

    def _init_connections(self):
        # 1. MongoDB
        try:
            from pymongo import MongoClient
            mongo_uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            self.mongo_client.admin.command("ping")
            logger.info("Connected to MongoDB for SPOF scores persistence.")
        except Exception as e:
            logger.warning(f"MongoDB unavailable: {e}")
            self.mongo_client = None

        # 2. Neo4j
        try:
            from neo4j import GraphDatabase
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("NEO4J_PASSWORD", "pharma_graph_pass")
            self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            self.neo4j_driver.verify_connectivity()
            logger.info("Connected to Neo4j for live topology traversal.")
        except Exception as e:
            logger.warning(f"Neo4j unavailable, reading topology from staged JSON: {e}")
            self.neo4j_driver = None

    def load_topology_edges(self) -> List[Dict]:
        """Loads edges from Neo4j or staged topology_edges.json."""
        if self.neo4j_driver:
            try:
                with self.neo4j_driver.session() as session:
                    cypher = """
                        MATCH (a)-[r:SHIPS_TO|SUPPLIES]->(b)
                        RETURN a.id AS source_id, b.id AS target_id, type(r) AS relationship, r.weight AS weight, r.tier AS tier
                    """
                    records = session.run(cypher).data()
                    if records and len(records) > 0:
                        logger.info(f"Loaded {len(records):,} edges from Neo4j.")
                        return records
            except Exception as e:
                logger.warning(f"Querying Neo4j failed: {e}")

        # Staged topology fallback
        edges_file = STAGED_DIR / "topology_edges.json"
        if edges_file.exists():
            with open(edges_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            flat_edges = []
            if isinstance(data, dict):
                edges_obj = data.get("edges", {})
                if isinstance(edges_obj, dict):
                    # Filter for supply flow relationships
                    for rel_type in ["SUPPLIES", "DISTRIBUTES_TO"]:
                        flat_edges.extend(edges_obj.get(rel_type, []))
                elif isinstance(edges_obj, list):
                    flat_edges = edges_obj
            elif isinstance(data, list):
                flat_edges = data

            logger.info(f"Loaded {len(flat_edges):,} supply routing edges from staged topology_edges.json.")
            return flat_edges
        else:
            logger.warning("No topology edges file found. Creating synthetic supply topology...")
            # Synthetic 3-tier supply chain
            synthetic = []
            for m in range(1, 11):
                for d in range(1, 6):
                    synthetic.append({"source_id": f"EST-{m:04d}", "target_id": f"DIST-{d:03d}", "relationship": "SUPPLIES", "weight": 1.0})
            for d in range(1, 6):
                for p in range(1, 51):
                    synthetic.append({"source_id": f"DIST-{d:03d}", "target_id": f"PHARM-{p:04d}", "relationship": "SHIPS_TO", "weight": 1.0})
            return synthetic

    def run_analysis(self, top_k: int = 20) -> List[Dict]:
        print("\n" + "=" * 95)
        print("          PHASE 4: ML GRAPH SPOF (SINGLE POINT OF FAILURE) CENTRALITY PIPELINE")
        print("=" * 95)

        edges = self.load_topology_edges()
        G = build_supply_chain_graph(edges)
        rankings = compute_spof_metrics(G)

        # 1. Write to MongoDB
        if self.mongo_client:
            try:
                db = self.mongo_client["pharma_supply_chain"]
                coll = db["spof_scores"]
                for r in rankings:
                    coll.update_one({"node_id": r["node_id"]}, {"$set": r}, upsert=True)
                logger.info(f"Persisted {len(rankings):,} SPOF rankings to MongoDB collection 'spof_scores'.")
            except Exception as e:
                logger.debug(f"MongoDB persistence error: {e}")

        # 2. Save local JSON artifact
        out_file = OUTPUT_DIR / "spof_rankings.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(rankings, f, indent=2)

        # Print Top Bottlenecks
        print("-" * 95)
        print(f"{'Rank':<5} | {'Node ID':<15} | {'Type':<14} | {'SPOF Index':<12} | {'Betweenness':<14} | {'In/Out Degree':<15} | {'Classification':<20}")
        print("-" * 95)
        for i, r in enumerate(rankings[:top_k], 1):
            deg_str = f"{r['in_degree']} in / {r['out_degree']} out"
            print(f"{i:<5} | {r['node_id']:<15} | {r['node_type']:<14} | {r['spof_risk_index']:<12.4f} | {r['betweenness_centrality']:<14.6f} | {deg_str:<15} | {r['classification']:<20}")
        print("-" * 95)
        print(f"[*] Total evaluated nodes: {len(rankings):,}. Rankings saved to '{out_file.name}'.")
        print("=" * 95 + "\n")
        return rankings

    def close(self):
        if self.mongo_client:
            self.mongo_client.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()


def main():
    parser = argparse.ArgumentParser(description="Supply Chain SPOF Centrality Analysis")
    parser.add_argument("--top-k", type=int, default=20, help="Number of top bottleneck nodes to display (default: 20)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without database persistence")
    args = parser.parse_args()

    analyzer = SPOFAnalyzer(dry_run=args.dry_run)
    analyzer.run_analysis(top_k=args.top_k)
    analyzer.close()


if __name__ == "__main__":
    main()
