"""
Load staged pharmaceutical datasets into MongoDB collections:
- drugs -> pharma_supply_chain.drugs
- manufacturers -> pharma_supply_chain.manufacturers
- pharmacies -> pharma_supply_chain.pharmacies
- shortages -> pharma_supply_chain.shortages
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import pymongo
from pymongo import UpdateOne

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:rootpassword@localhost:27017/pharma_supply_chain?authSource=admin")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pharma_supply_chain")
STAGED_DIR = Path("data-ingestion/staged")
BATCH_SIZE = 500


def load_mongo():
    """Ingests all staged JSON documents into MongoDB with bulk upserts."""
    logger.info(f"Connecting to MongoDB: {MONGO_URI} (Database: {MONGO_DB_NAME})")
    client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[MONGO_DB_NAME]

    # Verify server reachability
    db.command("ping")
    logger.info("Successfully connected to MongoDB server.")

    # 1. Load Manufacturers
    mfr_file = STAGED_DIR / "manufacturers.json"
    if mfr_file.exists():
        with open(mfr_file, "r", encoding="utf-8") as f:
            mfrs = json.load(f)
        logger.info(f"Loading {len(mfrs):,} manufacturers into 'manufacturers' collection...")
        ops = [UpdateOne({"manufacturer_id": m["manufacturer_id"]}, {"$set": m}, upsert=True) for m in mfrs]
        res = db.manufacturers.bulk_write(ops)
        logger.info(f"Manufacturers loaded: {db.manufacturers.count_documents({}):,} total documents.")

    # 2. Load Pharmacies
    pharm_file = STAGED_DIR / "pharmacies.json"
    if pharm_file.exists():
        with open(pharm_file, "r", encoding="utf-8") as f:
            pharmacies = json.load(f)
        logger.info(f"Loading {len(pharmacies):,} pharmacies into 'pharmacies' collection...")
        ops = [UpdateOne({"pharmacy_id": p["pharmacy_id"]}, {"$set": p}, upsert=True) for p in pharmacies]
        db.pharmacies.bulk_write(ops)
        logger.info(f"Pharmacies loaded: {db.pharmacies.count_documents({}):,} total documents.")

    # 3. Load Shortages
    short_file = STAGED_DIR / "shortages.json"
    if short_file.exists():
        with open(short_file, "r", encoding="utf-8") as f:
            shortages = json.load(f)
        logger.info(f"Loading {len(shortages):,} shortage records into 'shortages' collection...")
        ops = [UpdateOne({"shortage_id": s["shortage_id"]}, {"$set": s}, upsert=True) for s in shortages]
        db.shortages.bulk_write(ops)
        logger.info(f"Shortages loaded: {db.shortages.count_documents({}):,} total documents.")

    # 4. Load Drugs in batches
    drugs_file = STAGED_DIR / "drugs.json"
    if drugs_file.exists():
        with open(drugs_file, "r", encoding="utf-8") as f:
            drugs = json.load(f)
        logger.info(f"Loading {len(drugs):,} drugs into 'drugs' collection in batches of {BATCH_SIZE}...")
        for i in range(0, len(drugs), BATCH_SIZE):
            chunk = drugs[i:i + BATCH_SIZE]
            ops = [UpdateOne({"drug_id": d["drug_id"]}, {"$set": d}, upsert=True) for d in chunk]
            db.drugs.bulk_write(ops)
        logger.info(f"Drugs loaded: {db.drugs.count_documents({}):,} total documents.")

    # Print Summary
    print("================================================================================")
    print("       MONGODB INGESTION VERIFICATION SUMMARY                                   ")
    print("================================================================================")
    print(f"  • Database:              {MONGO_DB_NAME}")
    print(f"  • drugs collection:          {db.drugs.count_documents({}):,} records")
    print(f"  • manufacturers collection:  {db.manufacturers.count_documents({}):,} records")
    print(f"  • pharmacies collection:     {db.pharmacies.count_documents({}):,} records")
    print(f"  • shortages collection:      {db.shortages.count_documents({}):,} records")
    print("================================================================================\n")
    client.close()


if __name__ == "__main__":
    load_mongo()

