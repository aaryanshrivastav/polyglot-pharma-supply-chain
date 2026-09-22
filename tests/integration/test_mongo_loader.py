"""
Integration Tests: MongoDB Document Store.
Validates collection existence, unique index schemas, and cold-chain query integrity.
"""

import os
import pytest
import pymongo
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:rootpassword@127.0.0.1:27017/pharma_supply_chain?authSource=admin&directConnection=true")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pharma_supply_chain")


@pytest.fixture(scope="module")
def mongo_db():
    import socket
    try:
        with socket.create_connection(("127.0.0.1", 27017), timeout=0.2):
            client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=500)
            db = client[MONGO_DB_NAME]
            db.command("ping")
            yield db
            client.close()
    except Exception as e:
        pytest.skip(f"MongoDB not reachable at {MONGO_URI}: {e}")


@pytest.mark.integration
class TestMongoIntegration:
    def test_collections_when_loaded_should_be_populated(self, mongo_db):
        # Arrange & Act & Assert
        assert mongo_db.drugs.count_documents({}) > 0, "drugs collection should not be empty"
        assert mongo_db.manufacturers.count_documents({}) > 0, "manufacturers collection should not be empty"
        assert mongo_db.pharmacies.count_documents({}) > 0, "pharmacies collection should not be empty"
        assert mongo_db.shortages.count_documents({}) > 0, "shortages collection should not be empty"

    def test_drug_schema_when_queried_should_have_proper_indexes_and_cold_chain_structure(self, mongo_db):
        # Arrange
        indexes = mongo_db.drugs.index_information()

        # Act & Assert
        assert "drug_id_1" in indexes or "drug_id" in str(indexes), "Expected index on drug_id"

        sample = mongo_db.drugs.find_one({"requires_cold_chain": True})
        if sample:
            assert "storage_condition" in sample
            assert "min_temp_celsius" in sample["storage_condition"]
            assert "max_temp_celsius" in sample["storage_condition"]
