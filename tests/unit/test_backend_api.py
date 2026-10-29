"""
Unit Tests: FastAPI Polyglot Backend Service.
Validates all polyglot database dispatch routes (Redis, MongoDB, Cassandra, Neo4j, ML modules),
response payloads, HTTP error codes, and structured latency telemetry middleware in backend/main.py.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


@pytest.mark.unit
class TestPolyglotBackendAPI:
    def test_health_check_when_invoked_should_return_200_and_structured_health_payload(self):
        # Arrange & Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "databases" in data
        assert data["service"] == "polyglot-pharma-backend"
        assert "X-Process-Time-Ms" in response.headers

    def test_get_live_stock_when_valid_pharmacy_and_drug_should_return_200_and_stock_metadata(self):
        # Arrange
        pharmacy_id = "PHARM-0001"
        drug_id = "DRUG-0093-7679"

        # Act
        response = client.get(f"/stock/{pharmacy_id}/{drug_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["pharmacy_id"] == pharmacy_id
        assert data["drug_id"] == drug_id
        assert "current_stock" in data
        assert "source" in data

    def test_get_live_stock_when_nonexistent_drug_should_return_404_not_found(self):
        # Arrange & Act
        response = client.get("/stock/PHARM-0001/NON-EXISTENT-DRUG-99999")

        # Assert
        assert response.status_code == 404

    def test_get_drug_details_when_valid_drug_id_should_return_200_and_monograph(self):
        # Arrange
        drug_id = "DRUG-0093-7679"

        # Act
        response = client.get(f"/drugs/{drug_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["drug_id"] == drug_id
        assert "generic_name" in data or "brand_name" in data

    def test_get_drug_details_when_nonexistent_drug_id_should_return_404_not_found(self):
        # Arrange
        unknown_drug_id = "NON-EXISTENT-DRUG-99999"

        # Act
        response = client.get(f"/drugs/{unknown_drug_id}")

        # Assert
        assert response.status_code == 404, "Expected HTTP 404 for unknown drug monograph query"

    def test_get_drug_trends_when_queried_should_return_200_and_time_series_records(self):
        # Arrange
        drug_id = "DRUG-0093-7679"
        range_days = 15

        # Act
        response = client.get(f"/trends/{drug_id}?range={range_days}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["drug_id"] == drug_id
        assert "trends" in data
        assert len(data["trends"]) > 0

    def test_get_drug_trends_when_nonexistent_drug_should_return_404_not_found(self):
        # Arrange & Act
        response = client.get("/trends/NON-EXISTENT-DRUG-99999")

        # Assert
        assert response.status_code == 404

    def test_get_spof_rankings_when_top_k_specified_should_return_200_and_ranked_bottlenecks(self):
        # Arrange
        top_k = 5

        # Act
        response = client.get(f"/network/spof?top_k={top_k}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "rankings" in data
        assert len(data["rankings"]) > 0
        top = data["rankings"][0]
        assert "node_id" in top
        assert "spof_risk_index" in top

    def test_simulate_node_disruption_when_valid_node_should_return_200_and_weighted_impact_score(self):
        # Arrange
        node_id = "EST-0001"
        payload = {"drug_id": "DRUG-0002-7597", "time_window_days": 30}

        # Act
        response = client.post(f"/simulate/disruption/{node_id}", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["failed_node_id"] == node_id
        assert "impact_score" in data
        assert data["impact_score"] > 0
        assert "affected_pharmacy_count" in data
        assert "severity_classification" in data

    def test_simulate_node_disruption_when_nonexistent_node_should_return_404_not_found(self):
        # Arrange & Act
        response = client.post("/simulate/disruption/NON-EXISTENT-NODE-99999")

        # Assert
        assert response.status_code == 404

    def test_get_root_cause_when_incident_reported_should_return_200_and_ranked_candidate_origin(self):
        # Arrange
        pharmacy_id = "PHARM-1649791633"
        drug_id = "DRUG-0002-7597"

        # Act
        response = client.get(f"/root-cause/{pharmacy_id}/{drug_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["query_pharmacy_id"] == pharmacy_id
        assert data["query_drug_id"] == drug_id
        assert "top_root_cause" in data
        assert "all_candidates" in data
        assert len(data["all_candidates"]) > 0

    def test_structured_logging_middleware_when_request_processed_should_inject_latency_header(self):
        # Arrange & Act
        response = client.get("/health")

        # Assert
        assert "X-Process-Time-Ms" in response.headers, "Response must include X-Process-Time-Ms header"
        latency_val = float(response.headers["X-Process-Time-Ms"])
        assert latency_val >= 0.0, "Latency measurement must be non-negative"

    def test_get_events_when_queried_should_return_recent_event_records(self):
        # Act
        response = client.get("/events?limit=5")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "events" in data
        assert len(data["events"]) > 0
        first_evt = data["events"][0]
        assert "id" in first_evt
        assert "type" in first_evt
        assert "message" in first_evt

    def test_record_event_when_posted_should_prepend_to_event_stream(self):
        # Arrange
        payload = {
            "type": "DISRUPTION",
            "message": "Cold-chain alert: temperature exceeded 8C in transit",
            "facility_or_drug": "DRUG-0093-7679"
        }

        # Act
        response = client.post("/events", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["event"]["type"] == "DISRUPTION"
        assert "Cold-chain alert" in data["event"]["message"]

    def test_get_network_topology_when_queried_should_return_nodes_and_edges(self):
        # Act
        response = client.get("/network/topology")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert data["node_count"] > 0
        assert data["edge_count"] > 0
        assert any(n["id"] == "EST-0001" for n in data["nodes"])
        assert any(n["id"] == "EST-0002" for n in data["nodes"])

    def test_get_demo_scenarios_when_queried_should_return_all_curated_scenarios(self):
        # Act
        response = client.get("/scenarios")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "scenarios" in data
        scenarios = data["scenarios"]
        assert "SCENARIO_A" in scenarios
        assert "SCENARIO_B" in scenarios
        assert "SCENARIO_C" in scenarios
        assert "SCENARIO_D" in scenarios
        assert scenarios["SCENARIO_A"]["target_node_id"] == "EST-0005"
        assert scenarios["SCENARIO_B"]["expected_drug_criticality"] == 1.7
        assert scenarios["SCENARIO_D"]["expected_impact_score"] == 65.0



