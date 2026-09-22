"""
Unit Tests: Single-Database (MongoDB) Baseline Layer.
Validates parallel baseline routes, $graphLookup traversal, data seeding,
and response consistency in backend/baseline/routes.py.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.baseline.mongo_baseline import MongoBaselineEngine

client = TestClient(app)


@pytest.mark.unit
class TestBaselineSingleDatabaseAPI:
    def test_baseline_get_stock_when_queried_should_return_200_and_inventory_doc(self):
        # Arrange
        pharmacy_id = "PHARM-0001"
        drug_id = "DRUG-0002-7597"

        # Act
        response = client.get(f"/baseline/stock/{pharmacy_id}/{drug_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["pharmacy_id"] == pharmacy_id
        assert data["drug_id"] == drug_id
        assert "current_stock" in data
        assert "source" in data

    def test_baseline_get_trends_when_range_specified_should_return_200_and_event_series(self):
        # Arrange
        drug_id = "DRUG-0002-7597"
        range_days = 10

        # Act
        response = client.get(f"/baseline/trends/{drug_id}?range={range_days}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["drug_id"] == drug_id
        assert "trends" in data
        assert len(data["trends"]) > 0

    def test_baseline_simulate_disruption_when_node_fails_should_return_200_and_graphlookup_impact(self):
        # Arrange
        node_id = "EST-0001"
        payload = {"drug_id": "DRUG-0002-7597"}

        # Act
        response = client.post(f"/baseline/simulate/disruption/{node_id}", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["failed_node_id"] == node_id
        assert "impact_score" in data
        assert "affected_pharmacy_count" in data
        assert "traversal_method" in data

    def test_baseline_seed_endpoint_when_called_should_return_200_and_seed_status(self):
        # Arrange & Act
        response = client.post("/baseline/seed")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert "seeded_counts" in data

    def test_mongo_baseline_engine_when_dry_run_mode_should_execute_all_core_query_types(self):
        # Arrange
        engine = MongoBaselineEngine(dry_run=True)

        # Act
        stock = engine.get_stock("PHARM-0001", "DRUG-0001")
        trends = engine.get_trends("DRUG-0001", range_days=5)
        disruption = engine.simulate_disruption("EST-0001")
        engine.close()

        # Assert
        assert stock["pharmacy_id"] == "PHARM-0001"
        assert trends["record_count"] == 5
        assert disruption["impact_score"] > 0
        assert disruption["affected_pharmacy_count"] > 0
