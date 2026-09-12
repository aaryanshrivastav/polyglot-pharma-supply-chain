"""
Load staged entities and power-law supply chain topology into Neo4j graph store:
- Nodes: Manufacturer, Distributor, Pharmacy, Drug, Ingredient
- Relationships: PRODUCES, CONTAINS, SUPPLIES, DISTRIBUTES_TO, SUBSTITUTABLE_WITH
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "pharma_secret")

STAGED_DIR = Path("data-ingestion/staged")
TOPOLOGY_FILE = STAGED_DIR / "topology_edges.json"
BATCH_SIZE = 1000


def batch_execute(session, query: str, data: list, batch_size: int = BATCH_SIZE):
    """Executes parameterized Cypher query with UNWIND batching."""
    for i in range(0, len(data), batch_size):
        chunk = data[i:i + batch_size]
        session.run(query, {"batch": chunk})


def load_neo4j():
    """Loads all nodes and relationships into Neo4j."""
    logger.info(f"Connecting to Neo4j at {NEO4J_URI}...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    # 1. Ensure constraints & schema are initialized
    from init_schemas import init_neo4j_schema
    init_neo4j_schema()

    # Load Staged Data
    logger.info("Reading staged datasets and topology...")
    with open(STAGED_DIR / "manufacturers.json", "r", encoding="utf-8") as f:
        mfrs = json.load(f)
    with open(STAGED_DIR / "pharmacies.json", "r", encoding="utf-8") as f:
        pharmacies = json.load(f)
    with open(STAGED_DIR / "drugs.json", "r", encoding="utf-8") as f:
        drugs = json.load(f)

    if not TOPOLOGY_FILE.exists():
        logger.info("Topology edges not found. Generating topology...")
        from generate_topology import generate_topology
        topology = generate_topology()
    else:
        with open(TOPOLOGY_FILE, "r", encoding="utf-8") as f:
            topology = json.load(f)

    distributors = topology.get("distributor_nodes", [])
    ingredients = topology.get("ingredient_nodes", [])
    edges = topology.get("edges", {})

    with driver.session() as session:
        # ----------------------------------------------------------------------
        # 2. Ingest Nodes
        # ----------------------------------------------------------------------
        logger.info(f"Ingesting {len(mfrs):,} Manufacturer nodes...")
        mfr_query = """
        UNWIND $batch AS row
        MERGE (m:Manufacturer {id: row.manufacturer_id})
        SET m.name = row.name,
            m.fei_number = row.fei_number,
            m.duns_number = row.duns_number,
            m.address = row.facility_address,
            m.city = row.city,
            m.state = row.state,
            m.country = row.country,
            m.latitude = row.latitude,
            m.longitude = row.longitude,
            m.gmp_compliance_status = row.gmp_compliance_status
        """
        batch_execute(session, mfr_query, mfrs)

        logger.info(f"Ingesting {len(distributors):,} Distributor nodes...")
        dist_query = """
        UNWIND $batch AS row
        MERGE (d:Distributor {id: row.distributor_id})
        SET d.name = row.name,
            d.facility_type = row.facility_type,
            d.city = row.city,
            d.state = row.state,
            d.latitude = row.latitude,
            d.longitude = row.longitude,
            d.has_cold_chain_storage = row.has_cold_chain_storage
        """
        batch_execute(session, dist_query, distributors)

        logger.info(f"Ingesting {len(pharmacies):,} Pharmacy nodes...")
        pharm_query = """
        UNWIND $batch AS row
        MERGE (p:Pharmacy {id: row.pharmacy_id})
        SET p.npi = row.npi,
            p.name = row.name,
            p.pharmacy_type = row.pharmacy_type,
            p.address = row.address,
            p.city = row.city,
            p.state = row.state,
            p.postal_code = row.postal_code,
            p.latitude = row.latitude,
            p.longitude = row.longitude,
            p.has_cold_storage = row.has_cold_storage,
            p.has_ultra_cold_freezer = row.has_ultra_cold_freezer
        """
        batch_execute(session, pharm_query, pharmacies)

        logger.info(f"Ingesting {len(drugs):,} Drug nodes...")
        drug_query = """
        UNWIND $batch AS row
        MERGE (dr:Drug {id: row.drug_id})
        SET dr.product_ndc = row.product_ndc,
            dr.brand_name = row.brand_name,
            dr.generic_name = row.generic_name,
            dr.dosage_form = row.dosage_form,
            dr.route = row.route,
            dr.requires_cold_chain = row.requires_cold_chain,
            dr.is_biologic = row.is_biologic,
            dr.min_temp_celsius = row.storage_condition.min_temp_celsius,
            dr.max_temp_celsius = row.storage_condition.max_temp_celsius,
            dr.temperature_category = row.storage_condition.temperature_category
        """
        batch_execute(session, drug_query, drugs)

        logger.info(f"Ingesting {len(ingredients):,} Ingredient nodes...")
        ing_query = """
        UNWIND $batch AS row
        MERGE (i:Ingredient {name: row.name})
        """
        batch_execute(session, ing_query, ingredients)

        # ----------------------------------------------------------------------
        # 3. Ingest Relationships
        # ----------------------------------------------------------------------
        logger.info(f"Ingesting {len(edges.get('PRODUCES', [])):,} PRODUCES relationships...")
        produces_query = """
        UNWIND $batch AS row
        MATCH (m:Manufacturer {id: row.source_id})
        MATCH (dr:Drug {id: row.target_id})
        MERGE (m)-[r:PRODUCES]->(dr)
        SET r.nda_anda = row.properties.nda_anda,
            r.is_biologic = row.properties.is_biologic
        """
        batch_execute(session, produces_query, edges.get("PRODUCES", []))

        logger.info(f"Ingesting {len(edges.get('CONTAINS', [])):,} CONTAINS relationships...")
        contains_query = """
        UNWIND $batch AS row
        MATCH (dr:Drug {id: row.source_id})
        MATCH (i:Ingredient {name: row.target_id})
        MERGE (dr)-[r:CONTAINS]->(i)
        SET r.strength = row.properties.strength
        """
        batch_execute(session, contains_query, edges.get("CONTAINS", []))

        logger.info(f"Ingesting {len(edges.get('SUPPLIES', [])):,} SUPPLIES relationships...")
        supplies_query = """
        UNWIND $batch AS row
        MATCH (m:Manufacturer {id: row.source_id})
        MATCH (d:Distributor {id: row.target_id})
        MERGE (m)-[r:SUPPLIES]->(d)
        SET r.lead_time_days = row.properties.lead_time_days,
            r.contract_tier = row.properties.contract_tier,
            r.sla_reliability_percent = row.properties.sla_reliability_percent
        """
        batch_execute(session, supplies_query, edges.get("SUPPLIES", []))

        logger.info(f"Ingesting {len(edges.get('DISTRIBUTES_TO', [])):,} DISTRIBUTES_TO relationships...")
        dist_rel_query = """
        UNWIND $batch AS row
        MATCH (d:Distributor {id: row.source_id})
        MATCH (p:Pharmacy {id: row.target_id})
        MERGE (d)-[r:DISTRIBUTES_TO]->(p)
        SET r.delivery_frequency = row.properties.delivery_frequency,
            r.min_transit_hours = row.properties.min_transit_hours,
            r.temperature_controlled_vehicle = row.properties.temperature_controlled_vehicle
        """
        batch_execute(session, dist_rel_query, edges.get("DISTRIBUTES_TO", []))

        logger.info(f"Ingesting {len(edges.get('SUBSTITUTABLE_WITH', [])):,} SUBSTITUTABLE_WITH relationships...")
        sub_query = """
        UNWIND $batch AS row
        MATCH (d1:Drug {id: row.source_id})
        MATCH (d2:Drug {id: row.target_id})
        MERGE (d1)-[r:SUBSTITUTABLE_WITH]->(d2)
        SET r.generic_compound = row.properties.generic_compound,
            r.equivalence_rating = row.properties.equivalence_rating
        """
        batch_execute(session, sub_query, edges.get("SUBSTITUTABLE_WITH", []))

        # Query verification stats
        node_counts = session.run("MATCH (n) RETURN head(labels(n)) AS label, count(n) AS count ORDER BY count DESC").data()
        rel_counts = session.run("MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count ORDER BY count DESC").data()

        print("\n================================================================================")
        print("       NEO4J GRAPH POPULATION VERIFICATION SUMMARY                             ")
        print("================================================================================")
        print("  NODE COUNTS BY LABEL:")
        for row in node_counts:
            print(f"    • :{row['label']:<15} {row['count']:,} nodes")

        print("\n  RELATIONSHIP COUNTS BY TYPE:")
        for row in rel_counts:
            print(f"    • -[:{row['type']:<20}]-> {row['count']:,} edges")
        print("================================================================================\n")

    driver.close()


if __name__ == "__main__":
    load_neo4j()

