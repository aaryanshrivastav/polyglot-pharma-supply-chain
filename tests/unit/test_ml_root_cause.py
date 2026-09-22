"""
Unit Tests: Backward Reasoning & Root Cause Analysis Module.
Validates reverse graph traversal, anomaly signal correlation,
and origin node ranking in ml/root_cause_analysis.py.
"""

import pytest
from ml.root_cause_analysis import rank_root_causes, RootCauseEngine


@pytest.mark.unit
class TestRootCauseAnalysis:
    def test_rank_root_causes_when_distributor_has_high_anomaly_should_rank_distributor_first(self):
        # Arrange
        pharm_to_dist = {"PHARM-001": ["DIST-001", "DIST-002"]}
        dist_to_mfg = {"DIST-001": ["EST-0001"], "DIST-002": ["EST-0002"]}
        anomaly_map = {
            "DIST-001": 0.95,
            "DIST-002": 0.10,
            "EST-0001": 0.20,
            "EST-0002": 0.10
        }

        # Act
        ranked = rank_root_causes(
            pharmacy_id="PHARM-001",
            drug_id="DRUG-TEST",
            pharm_to_dist=pharm_to_dist,
            dist_to_mfg=dist_to_mfg,
            anomaly_map=anomaly_map
        )

        # Assert
        assert len(ranked) >= 2
        top_candidate = ranked[0]
        assert top_candidate["candidate_id"] == "DIST-001"
        assert top_candidate["node_type"] == "Distributor"
        assert top_candidate["root_cause_probability"] > 0.70
        assert top_candidate["hop_distance"] == 1

    def test_rank_root_causes_when_manufacturer_has_catastrophic_anomaly_should_rank_manufacturer_first(self):
        # Arrange
        pharm_to_dist = {"PHARM-001": ["DIST-001"]}
        dist_to_mfg = {"DIST-001": ["EST-0001", "EST-0002"]}
        anomaly_map = {"DIST-001": 0.20, "EST-0001": 0.99, "EST-0002": 0.05}

        # Act
        ranked = rank_root_causes(
            pharmacy_id="PHARM-001",
            drug_id="DRUG-TEST",
            pharm_to_dist=pharm_to_dist,
            dist_to_mfg=dist_to_mfg,
            anomaly_map=anomaly_map
        )

        # Assert
        top_candidate = ranked[0]
        assert top_candidate["candidate_id"] == "EST-0001"
        assert top_candidate["node_type"] == "Manufacturer"
        assert top_candidate["hop_distance"] == 2

    def test_root_cause_engine_when_dry_run_mode_should_diagnose_staged_incidents(self):
        # Arrange
        engine = RootCauseEngine(dry_run=True)

        # Act
        res = engine.find_root_causes("PHARM-1649791633", "DRUG-0002-7597")
        engine.close()

        # Assert
        assert res["query_pharmacy_id"] == "PHARM-1649791633"
        assert len(res["all_candidates"]) > 0
        assert res["top_root_cause"] is not None
