"""
ML & Graph Module: Weighted Downstream Impact Scoring.
Calculates a single defensible, weighted disruption impact score for any simulated node failure:
  impact_score = affected_pharmacy_count * drug_criticality_factor * regional_weight

Heuristic Definitions (Documented for Paper):
- drug_criticality_factor:
  * 1.5x: No generic/bioequivalent SUBSTITUTE_WITH alternative in the graph (sole source).
  * 1.7x: Sole source AND cold-chain/biologic dependent.
  * 1.0x: Multi-source drug with available market substitutes.
- regional_weight:
  * 1.2x: High-density population corridors (Northeast/West DC hubs).
  * 1.0x: Standard regional hub.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ImpactScoring")

OUTPUT_DIR = PROJECT_ROOT / "ml" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STAGED_DIR = PROJECT_ROOT / "data-ingestion" / "staged"


def load_downstream_topology_map() -> Tuple[Dict[str, List[str]], Dict[str, List[str]], Set[str], Set[str]]:
    """
    Loads topology and returns:
    - mfg_to_dist: {manufacturer_id -> [distributor_ids]}
    - dist_to_pharm: {distributor_id -> [pharmacy_ids]}
    - substitutable_drugs: set of drug_ids that have bioequivalent substitutes
    - biologic_drugs: set of biologic / cold-chain drug IDs
    """
    mfg_to_dist = {}
    dist_to_pharm = {}
    substitutable_drugs = set()
    biologic_drugs = set()

    # 1. Topology Edges
    edges_file = STAGED_DIR / "topology_edges.json"
    if edges_file.exists():
        with open(edges_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        edges_obj = data.get("edges", {}) if isinstance(data, dict) else {}

        # SUPPLIES (Mfg -> Dist)
        for e in edges_obj.get("SUPPLIES", []):
            mfg_to_dist.setdefault(e["source_id"], []).append(e["target_id"])

        # DISTRIBUTES_TO (Dist -> Pharm)
        for e in edges_obj.get("DISTRIBUTES_TO", []):
            dist_to_pharm.setdefault(e["source_id"], []).append(e["target_id"])

        # SUBSTITUTABLE_WITH
        for e in edges_obj.get("SUBSTITUTABLE_WITH", []):
            substitutable_drugs.add(e.get("source_id"))
            substitutable_drugs.add(e.get("target_id"))

    # 2. Biologic metadata from drugs.json
    drugs_file = STAGED_DIR / "drugs.json"
    if drugs_file.exists():
        with open(drugs_file, "r", encoding="utf-8") as f:
            drugs = json.load(f)
        for d in drugs:
            if d.get("is_biologic") or d.get("requires_cold_chain"):
                biologic_drugs.add(d["drug_id"])

    return mfg_to_dist, dist_to_pharm, substitutable_drugs, biologic_drugs


def compute_drug_criticality_factor(drug_id: Optional[str], substitutable_drugs: Set[str], biologic_drugs: Set[str]) -> Tuple[float, str]:
    """Evaluates drug criticality weighting based on substitutability and cold-chain status."""
    if not drug_id:
        return 1.2, "Default composite criticality across portfolio"

    has_substitute = drug_id in substitutable_drugs
    is_biologic = drug_id in biologic_drugs

    if not has_substitute and is_biologic:
        return 1.7, "Sole-source biologic with zero therapeutic substitutes (Maximum Criticality)"
    elif not has_substitute:
        return 1.5, "Sole-source drug with zero substitutable alternatives"
    elif is_biologic:
        return 1.2, "Multi-source biologic with cold-chain transport constraints"
    else:
        return 1.0, "Multi-source small-molecule drug with bioequivalent market alternatives"


def compute_node_disruption_impact(
    node_id: str,
    target_drug_id: Optional[str] = None,
    mfg_to_dist: Optional[Dict[str, List[str]]] = None,
    dist_to_pharm: Optional[Dict[str, List[str]]] = None,
    substitutable_drugs: Optional[Set[str]] = None,
    biologic_drugs: Optional[Set[str]] = None
) -> Dict:
    """
    Computes downstream impact score:
    impact_score = affected_pharmacy_count * drug_criticality_factor * regional_weight
    """
    if mfg_to_dist is None or dist_to_pharm is None:
        mfg_to_dist, dist_to_pharm, substitutable_drugs, biologic_drugs = load_downstream_topology_map()

    affected_distributors = set()
    affected_pharmacies = set()

    # Traverse downstream
    if node_id.startswith("EST-"):  # Manufacturer
        dists = mfg_to_dist.get(node_id, [])
        affected_distributors.update(dists)
        for d in dists:
            pharms = dist_to_pharm.get(d, [])
            affected_pharmacies.update(pharms)
    elif node_id.startswith("DIST-"):  # Distributor
        affected_distributors.add(node_id)
        pharms = dist_to_pharm.get(node_id, [])
        affected_pharmacies.update(pharms)
    elif node_id.startswith("PHARM-"):  # Single Pharmacy
        affected_pharmacies.add(node_id)
    else:
        # Fallback for generic node IDs
        affected_pharmacies.add(node_id)

    affected_pharmacy_count = len(affected_pharmacies)

    # Calculate Weights
    criticality_factor, crit_rationale = compute_drug_criticality_factor(target_drug_id, substitutable_drugs or set(), biologic_drugs or set())

    # Regional Weighting
    regional_weight = 1.2 if any(d in {"DIST-0001", "DIST-0014", "DIST-0011"} for d in affected_distributors) else 1.0

    # Final Impact Score
    impact_score = round(affected_pharmacy_count * criticality_factor * regional_weight, 2)

    # Classification
    if impact_score >= 200.0:
        severity = "CATASTROPHIC_DISRUPTION"
    elif impact_score >= 100.0:
        severity = "SEVERE_DISRUPTION"
    elif impact_score >= 40.0:
        severity = "MODERATE_DISRUPTION"
    else:
        severity = "LOCALIZED_IMPACT"

    result = {
        "failed_node_id": node_id,
        "target_drug_id": target_drug_id or "PORTFOLIO_WIDE",
        "impact_score": impact_score,
        "severity_classification": severity,
        "affected_pharmacy_count": affected_pharmacy_count,
        "affected_distributor_count": len(affected_distributors),
        "drug_criticality_factor": criticality_factor,
        "drug_criticality_rationale": crit_rationale,
        "regional_weight": regional_weight,
        "affected_distributors_sample": sorted(list(affected_distributors))[:10],
        "affected_pharmacies_sample": sorted(list(affected_pharmacies))[:15],
        "evaluated_at": datetime.now(timezone.utc).isoformat()
    }
    return result


class ImpactScoringEngine:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.mfg_to_dist, self.dist_to_pharm, self.substitutable_drugs, self.biologic_drugs = load_downstream_topology_map()
        self.mongo_client = None

        if not self.dry_run:
            self._init_mongo()

    def _init_mongo(self):
        try:
            from pymongo import MongoClient
            mongo_uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            self.mongo_client.admin.command("ping")
        except Exception as e:
            logger.debug(f"MongoDB offline for impact persistence: {e}")
            self.mongo_client = None

    def evaluate_node_failure(self, node_id: str, drug_id: Optional[str] = None) -> Dict:
        """Evaluates node failure impact and persists results."""
        impact = compute_node_disruption_impact(
            node_id=node_id,
            target_drug_id=drug_id,
            mfg_to_dist=self.mfg_to_dist,
            dist_to_pharm=self.dist_to_pharm,
            substitutable_drugs=self.substitutable_drugs,
            biologic_drugs=self.biologic_drugs
        )

        # MongoDB Persistence
        if self.mongo_client:
            try:
                db = self.mongo_client["pharma_supply_chain"]
                db["disruption_impacts"].update_one(
                    {"failed_node_id": node_id, "target_drug_id": impact["target_drug_id"]},
                    {"$set": impact},
                    upsert=True
                )
            except Exception as e:
                logger.debug(f"MongoDB error: {e}")

        # Local JSON Output
        out_file = OUTPUT_DIR / "impact_scores.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(impact, f, indent=2)

        return impact

    def close(self):
        if self.mongo_client:
            self.mongo_client.close()


def main():
    parser = argparse.ArgumentParser(description="Multi-Echelon Disruption Impact Scoring")
    parser.add_argument("--node-id", type=str, default="EST-0001", help="Target node to simulate as failed (e.g. EST-0001, DIST-0014)")
    parser.add_argument("--drug-id", type=str, default="DRUG-0002-7597", help="Optional target drug NDC/ID")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")
    args = parser.parse_args()

    engine = ImpactScoringEngine(dry_run=args.dry_run)
    res = engine.evaluate_node_failure(args.node_id, args.drug_id)

    print("\n" + "=" * 95)
    print("         PHASE 4: WEIGHTED MULTI-ECHELON DISRUPTION IMPACT SCORING")
    print("=" * 95)
    print(f"Simulated Failed Node: {res['failed_node_id']} | Target Drug: {res['target_drug_id']}")
    print("-" * 95)
    print(f"[*] Downstream Affected Pharmacies   : {res['affected_pharmacy_count']:,}")
    print(f"[*] Intermediate Distributors Impacted : {res['affected_distributor_count']:,}")
    print(f"[*] Drug Criticality Factor            : {res['drug_criticality_factor']}x ({res['drug_criticality_rationale']})")
    print(f"[*] Regional Corridor Weight           : {res['regional_weight']}x")
    print("-" * 95)
    print(f"[FINAL IMPACT SCORE] : {res['impact_score']:.2f} ({res['severity_classification']})")
    print("=" * 95 + "\n")
    engine.close()


if __name__ == "__main__":
    main()

