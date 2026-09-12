"""
Generate synthetic supply chain topology edges matching real-world power-law / scale-free network distributions.
Models high-degree manufacturer hubs and distributor routing to real dispensing pharmacies.
Output: data-ingestion/staged/topology_edges.json
"""

import json
import logging
import math
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STAGED_DIR = Path("data-ingestion/staged")
OUTPUT_PATH = STAGED_DIR / "topology_edges.json"

RANDOM_SEED = 42


def sample_zipf(alpha: float, n: int) -> int:
    """Sample from discrete Zipf distribution bounded in [1, n]."""
    u = random.random()
    # Compute discrete CDF for Zipf
    weights = [1.0 / (i ** alpha) for i in range(1, n + 1)]
    total = sum(weights)
    cum = 0.0
    for i, w in enumerate(weights, 1):
        cum += w / total
        if u <= cum:
            return i
    return n


def generate_distributors() -> list:
    """
    Synthesize regional pharmaceutical distribution hubs.
    Note: Public individual distributor inventory datasets do not exist in open FDA data.
    These nodes act as representative supply chain intermediaries.
    """
    distributor_templates = [
        ("DIST-0001", "AmerisourceBergen Northeast DC", "Bethlehem", "PA", 40.6259, -75.3705, True),
        ("DIST-0002", "McKesson Mid-Atlantic Hub", "Richmond", "VA", 37.5407, -77.4360, True),
        ("DIST-0003", "Cardinal Health Midwest Distribution", "Dublin", "OH", 40.0992, -83.1141, True),
        ("DIST-0004", "McKesson Southeast Regional DC", "Duluth", "GA", 34.0029, -84.1446, True),
        ("DIST-0005", "AmerisourceBergen South Central Center", "Carrollton", "TX", 32.9746, -96.8899, True),
        ("DIST-0006", "Cardinal Health Southwest Distribution Hub", "Phoenix", "AZ", 33.4484, -112.0740, True),
        ("DIST-0007", "McKesson Northern California DC", "Sacramento", "CA", 38.5816, -121.4944, True),
        ("DIST-0008", "AmerisourceBergen Southern California Facility", "Corona", "CA", 33.8753, -117.5664, True),
        ("DIST-0009", "Cardinal Health Pacific Northwest Hub", "Chehalis", "WA", 46.6623, -122.9640, True),
        ("DIST-0010", "McKesson Great Lakes Logistics Center", "Aurora", "IL", 41.7606, -88.3201, True),
        ("DIST-0011", "AmerisourceBergen Florida Cold-Chain DC", "Orlando", "FL", 28.5383, -81.3792, True),
        ("DIST-0012", "Cardinal Health Central Plains Hub", "Kansas City", "MO", 39.0997, -94.5786, False),
        ("DIST-0013", "McKesson Rocky Mountain Regional DC", "Denver", "CO", 39.7392, -104.9903, False),
        ("DIST-0014", "AmerisourceBergen Tri-State Center", "Newburgh", "NY", 41.5034, -74.0104, True),
        ("DIST-0015", "Cardinal Health Mid-South Facility", "La Vergne", "TN", 36.0156, -86.5819, False),
        ("DIST-0016", "McKesson New England Distribution", "Mansfield", "MA", 42.0334, -71.2192, True),
        ("DIST-0017", "AmerisourceBergen Gulf Coast Logistics", "Houston", "TX", 29.7604, -95.3698, True),
        ("DIST-0018", "Cardinal Health Carolinas DC", "Greensboro", "NC", 36.0726, -79.7920, False),
        ("DIST-0019", "McKesson Upper Midwest DC", "Minneapolis", "MN", 44.9778, -93.2650, True),
        ("DIST-0020", "AmerisourceBergen Speciality BioLogistics Center", "Memphis", "TN", 35.1495, -90.0490, True)
    ]

    distributors = []
    for d_id, name, city, state, lat, lon, cold_chain in distributor_templates:
        distributors.append({
            "distributor_id": d_id,
            "name": name,
            "facility_type": "REGIONAL_DISTRIBUTION_CENTER",
            "city": city,
            "state": state,
            "latitude": lat,
            "longitude": lon,
            "has_cold_chain_storage": cold_chain
        })
    return distributors


def generate_topology():
    """Generates realistic scale-free supply chain graph topology."""
    random.seed(RANDOM_SEED)

    # 1. Load Staged Datasets
    logger.info("Loading staged datasets...")
    with open(STAGED_DIR / "manufacturers.json", "r", encoding="utf-8") as f:
        manufacturers = json.load(f)
    with open(STAGED_DIR / "pharmacies.json", "r", encoding="utf-8") as f:
        pharmacies = json.load(f)
    with open(STAGED_DIR / "drugs.json", "r", encoding="utf-8") as f:
        drugs = json.load(f)

    distributors = generate_distributors()
    num_mfrs = len(manufacturers)
    num_distributors = len(distributors)
    num_pharmacies = len(pharmacies)

    logger.info(f"Entities: {num_mfrs} Manufacturers, {num_distributors} Distributors, {num_pharmacies} Pharmacies, {len(drugs)} Drugs")

    # 2. Extract Ingredients & Drug-Ingredient relationships (CONTAINS) & PRODUCES
    ingredients_set = set()
    contains_edges = []
    produces_edges = []
    generic_to_drugs = defaultdict(list)

    for drug in drugs:
        d_id = drug["drug_id"]
        mfr_id = drug["manufacturer_id"]
        generic_name = drug.get("generic_name", "").strip().upper()

        # PRODUCES edge: Manufacturer -> Drug
        produces_edges.append({
            "source_type": "Manufacturer",
            "source_id": mfr_id,
            "relationship": "PRODUCES",
            "target_type": "Drug",
            "target_id": d_id,
            "properties": {
                "nda_anda": drug.get("marketing_category", "NDA"),
                "is_biologic": drug.get("is_biologic", False)
            }
        })

        # Track generic formulations for SUBSTITUTABLE_WITH
        if generic_name:
            generic_to_drugs[generic_name].append(d_id)

        # CONTAINS edge: Drug -> Ingredient
        for ing in drug.get("active_ingredients", []):
            ing_name = ing.get("name", "").strip().upper()
            if ing_name:
                ingredients_set.add(ing_name)
                contains_edges.append({
                    "source_type": "Drug",
                    "source_id": d_id,
                    "relationship": "CONTAINS",
                    "target_type": "Ingredient",
                    "target_id": ing_name,
                    "properties": {
                        "strength": ing.get("strength", "UNSPECIFIED")
                    }
                })

    # 3. Generate SUBSTITUTABLE_WITH edges (Equivalence across brands/generics)
    substitutable_edges = []
    for generic_name, drug_ids in generic_to_drugs.items():
        if len(drug_ids) > 1:
            for i in range(len(drug_ids)):
                for j in range(i + 1, min(i + 4, len(drug_ids))):
                    substitutable_edges.append({
                        "source_type": "Drug",
                        "source_id": drug_ids[i],
                        "relationship": "SUBSTITUTABLE_WITH",
                        "target_type": "Drug",
                        "target_id": drug_ids[j],
                        "properties": {
                            "generic_compound": generic_name,
                            "equivalence_rating": "AB"
                        }
                    })

    # 4. Generate SUPPLIES edges (Manufacturer -> Distributor) via Power-Law
    logger.info("Generating power-law SUPPLIES edges (Manufacturer -> Distributor)...")
    supplies_edges = []
    
    for idx, mfr in enumerate(manufacturers):
        mfr_id = mfr["manufacturer_id"]
        # Power-law degree: top tier-1 manufacturers supply most distributors
        rank_val = sample_zipf(alpha=1.6, n=num_distributors)
        degree = max(2, min(num_distributors - 2, (num_distributors + 1) - rank_val))
        
        # Ensure top 5 manufacturers have high degree
        if idx < 5:
            degree = max(degree, 15)

        selected_dist_indices = set(random.sample(range(num_distributors), k=degree))
        if idx < 5:
            selected_dist_indices.update([0, 1, 2, 3, 4])

        for dist_idx in selected_dist_indices:
            dist = distributors[dist_idx]
            lead_time = random.choice([1.0, 2.0, 3.0, 4.0])
            supplies_edges.append({
                "source_type": "Manufacturer",
                "source_id": mfr_id,
                "relationship": "SUPPLIES",
                "target_type": "Distributor",
                "target_id": dist["distributor_id"],
                "properties": {
                    "lead_time_days": lead_time,
                    "contract_tier": "PRIMARY" if idx < 15 else "SECONDARY",
                    "sla_reliability_percent": round(random.uniform(96.0, 99.8), 2)
                }
            })

    # 5. Generate DISTRIBUTES_TO edges (Distributor -> Pharmacy) via Power-Law
    logger.info("Generating power-law DISTRIBUTES_TO edges (Distributor -> Pharmacy)...")
    distributes_edges = []
    
    # Precompute weights for distributor selection (power-law hubs)
    dist_weights = [1.0 / (i ** 0.8) for i in range(1, num_distributors + 1)]
    
    for p_idx, pharmacy in enumerate(pharmacies):
        pharm_id = pharmacy["pharmacy_id"]
        p_state = pharmacy.get("state", "CA")

        matching_state_dists = [i for i, d in enumerate(distributors) if d["state"] == p_state]
        if not matching_state_dists:
            matching_state_dists = list(range(num_distributors))

        num_suppliers = random.choices([1, 2, 3], weights=[0.55, 0.35, 0.10], k=1)[0]
        chosen_dist_indices = set()
        
        if matching_state_dists:
            chosen_dist_indices.add(random.choice(matching_state_dists))

        while len(chosen_dist_indices) < num_suppliers:
            chosen = random.choices(range(num_distributors), weights=dist_weights, k=1)[0]
            chosen_dist_indices.add(chosen)

        for dist_idx in chosen_dist_indices:
            dist = distributors[dist_idx]
            distributes_edges.append({
                "source_type": "Distributor",
                "source_id": dist["distributor_id"],
                "relationship": "DISTRIBUTES_TO",
                "target_type": "Pharmacy",
                "target_id": pharm_id,
                "properties": {
                    "delivery_frequency": "DAILY" if pharmacy.get("has_cold_storage") else "BI_WEEKLY",
                    "min_transit_hours": float(random.choice([4.0, 8.0, 12.0, 24.0])),
                    "temperature_controlled_vehicle": True if dist["has_cold_chain_storage"] else False
                }
            })

    # 6. Assemble and Write Full Topology
    total_edges = (
        len(produces_edges) +
        len(contains_edges) +
        len(supplies_edges) +
        len(distributes_edges) +
        len(substitutable_edges)
    )

    topology_payload = {
        "metadata": {
            "generator": "generate_topology.py (Power-Law / Zipf Distribution)",
            "random_seed": RANDOM_SEED,
            "total_nodes": {
                "manufacturers": num_mfrs,
                "distributors": num_distributors,
                "pharmacies": num_pharmacies,
                "drugs": len(drugs),
                "ingredients": len(ingredients_set)
            },
            "total_edges": total_edges
        },
        "distributor_nodes": distributors,
        "ingredient_nodes": [{"name": ing} for ing in sorted(ingredients_set)],
        "edges": {
            "PRODUCES": produces_edges,
            "CONTAINS": contains_edges,
            "SUPPLIES": supplies_edges,
            "DISTRIBUTES_TO": distributes_edges,
            "SUBSTITUTABLE_WITH": substitutable_edges
        }
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(topology_payload, f, indent=2)

    logger.info("================================================================================")
    logger.info(f"  TOPOLOGY GENERATION COMPLETE: {OUTPUT_PATH.resolve()}")
    logger.info(f"  • Nodes: {num_mfrs} Mfrs, {num_distributors} Dists, {num_pharmacies} Pharms, {len(drugs)} Drugs, {len(ingredients_set)} Ingredients")
    logger.info(f"  • PRODUCES edges:        {len(produces_edges):,}")
    logger.info(f"  • CONTAINS edges:        {len(contains_edges):,}")
    logger.info(f"  • SUPPLIES edges:        {len(supplies_edges):,}")
    logger.info(f"  • DISTRIBUTES_TO edges:  {len(distributes_edges):,}")
    logger.info(f"  • SUBSTITUTABLE_WITH:    {len(substitutable_edges):,}")
    logger.info(f"  • TOTAL GRAPH EDGES:     {total_edges:,}")
    logger.info("================================================================================")
    return topology_payload


if __name__ == "__main__":
    generate_topology()
