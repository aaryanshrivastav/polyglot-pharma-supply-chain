"""
Initialize schemas, JSON validation rules, uniqueness constraints, and secondary indexes
for MongoDB and Neo4j polyglot database instances.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import pymongo
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Load configuration from .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:rootpassword@localhost:27017/pharma_supply_chain?authSource=admin")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pharma_supply_chain")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "pharma_secret")


# ------------------------------------------------------------------------------
# 1. MongoDB Schema & Validation Definitions
# ------------------------------------------------------------------------------
MONGO_COLLECTION_VALIDATORS = {
    "drugs": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["drug_id", "product_ndc", "brand_name", "generic_name", "storage_condition", "requires_cold_chain", "manufacturer_id"],
            "properties": {
                "drug_id": {"bsonType": "string", "description": "Unique drug identifier (must be string)"},
                "product_ndc": {"bsonType": "string", "description": "FDA NDC product code"},
                "brand_name": {"bsonType": "string"},
                "generic_name": {"bsonType": "string"},
                "dosage_form": {"bsonType": "string"},
                "route": {"bsonType": "string"},
                "requires_cold_chain": {"bsonType": "bool"},
                "is_biologic": {"bsonType": "bool"},
                "manufacturer_id": {"bsonType": "string"},
                "storage_condition": {
                    "bsonType": "object",
                    "required": ["temperature_category", "min_temp_celsius", "max_temp_celsius"],
                    "properties": {
                        "temperature_category": {"enum": ["ULTRA_COLD", "FROZEN", "REFRIGERATED", "CONTROLLED_ROOM_TEMP"]},
                        "min_temp_celsius": {"bsonType": ["double", "int"]},
                        "max_temp_celsius": {"bsonType": ["double", "int"]}
                    }
                }
            }
        }
    },
    "manufacturers": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["manufacturer_id", "name", "fei_number", "duns_number", "facility_address", "country"],
            "properties": {
                "manufacturer_id": {"bsonType": "string"},
                "name": {"bsonType": "string"},
                "fei_number": {"bsonType": "string"},
                "duns_number": {"bsonType": "string"},
                "facility_address": {"bsonType": "string"},
                "gmp_compliance_status": {"enum": ["COMPLIANT", "WARNING_LETTER", "UNDER_REVIEW"]}
            }
        }
    },
    "pharmacies": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["pharmacy_id", "npi", "name", "address", "state", "postal_code"],
            "properties": {
                "pharmacy_id": {"bsonType": "string"},
                "npi": {"bsonType": "string"},
                "name": {"bsonType": "string"},
                "state": {"bsonType": "string"},
                "postal_code": {"bsonType": "string"},
                "has_cold_storage": {"bsonType": "bool"}
            }
        }
    },
    "shortages": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["shortage_id", "generic_name", "status", "reason", "date_reported"],
            "properties": {
                "shortage_id": {"bsonType": "string"},
                "generic_name": {"bsonType": "string"},
                "status": {"enum": ["CURRENT", "RESOLVED"]},
                "disruption_severity_score": {"bsonType": ["double", "int"]}
            }
        }
    }
}


def init_mongo_schema():
    """Initializes MongoDB collections, JSON Schema validators, and secondary indexes."""
    logger.info(f"Connecting to MongoDB at {MONGO_URI} (DB: {MONGO_DB_NAME})...")
    client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[MONGO_DB_NAME]

    existing_collections = db.list_collection_names()
    logger.info(f"Existing MongoDB collections: {existing_collections}")

    for coll_name, validator_spec in MONGO_COLLECTION_VALIDATORS.items():
        if coll_name not in existing_collections:
            logger.info(f"Creating MongoDB collection '{coll_name}' with JSON Schema validation...")
            db.create_collection(coll_name, validator=validator_spec)
        else:
            logger.info(f"Updating validation schema for collection '{coll_name}'...")
            try:
                db.command("collMod", coll_name, validator=validator_spec)
            except Exception as e:
                logger.warning(f"Note on collMod for {coll_name}: {e}")

    # Build Indexes
    logger.info("Applying MongoDB indexes...")
    db.drugs.create_index("drug_id", unique=True)
    db.drugs.create_index("product_ndc", unique=True)
    db.drugs.create_index([("generic_name", pymongo.ASCENDING), ("requires_cold_chain", pymongo.ASCENDING)])
    db.drugs.create_index("manufacturer_id")

    db.manufacturers.create_index("manufacturer_id", unique=True)
    db.manufacturers.create_index("fei_number", unique=True)
    db.manufacturers.create_index("name")
    db.manufacturers.create_index([("state", pymongo.ASCENDING), ("country", pymongo.ASCENDING)])

    db.pharmacies.create_index("pharmacy_id", unique=True)
    db.pharmacies.create_index("npi", unique=True)
    db.pharmacies.create_index("state")
    db.pharmacies.create_index("postal_code")

    db.shortages.create_index("shortage_id", unique=True)
    db.shortages.create_index([("status", pymongo.ASCENDING), ("disruption_severity_score", pymongo.DESCENDING)])

    logger.info("MongoDB schema and indexing initialization completed successfully.")
    client.close()


# ------------------------------------------------------------------------------
# 2. Neo4j Graph Constraints & Indexes
# ------------------------------------------------------------------------------
NEO4J_SCHEMA_QUERIES = [
    # Uniqueness Constraints
    "CREATE CONSTRAINT mfr_id_unique IF NOT EXISTS FOR (m:Manufacturer) REQUIRE m.id IS UNIQUE;",
    "CREATE CONSTRAINT dist_id_unique IF NOT EXISTS FOR (d:Distributor) REQUIRE d.id IS UNIQUE;",
    "CREATE CONSTRAINT pharm_id_unique IF NOT EXISTS FOR (p:Pharmacy) REQUIRE p.id IS UNIQUE;",
    "CREATE CONSTRAINT drug_id_unique IF NOT EXISTS FOR (dr:Drug) REQUIRE dr.id IS UNIQUE;",
    "CREATE CONSTRAINT ingredient_name_unique IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.name IS UNIQUE;",

    # Secondary Search & Filter Indexes
    "CREATE INDEX drug_name_idx IF NOT EXISTS FOR (dr:Drug) ON (dr.brand_name, dr.generic_name);",
    "CREATE INDEX drug_cold_chain_idx IF NOT EXISTS FOR (dr:Drug) ON (dr.requires_cold_chain);",
    "CREATE INDEX mfr_name_idx IF NOT EXISTS FOR (m:Manufacturer) ON (m.name);",
    "CREATE INDEX pharm_location_idx IF NOT EXISTS FOR (p:Pharmacy) ON (p.state, p.city);"
]


def init_neo4j_schema():
    """Initializes Neo4j uniqueness constraints and secondary indexes."""
    logger.info(f"Connecting to Neo4j at {NEO4J_URI}...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        for q in NEO4J_SCHEMA_QUERIES:
            logger.info(f"Executing Cypher: {q}")
            session.run(q)

    logger.info("Neo4j graph constraints and index initialization completed successfully.")
    driver.close()


def init_all_schemas():
    """Executes schema initialization for both MongoDB and Neo4j."""
    print("================================================================================")
    print("       POLYGLOT SCHEMA INITIALIZER (MONGODB & NEO4J)                            ")
    print("================================================================================")
    
    try:
        init_mongo_schema()
    except Exception as e:
        logger.error(f"MongoDB Schema initialization failed: {e}")

    try:
        init_neo4j_schema()
    except Exception as e:
        logger.error(f"Neo4j Schema initialization failed: {e}")

    print("================================================================================")


if __name__ == "__main__":
    init_all_schemas()

