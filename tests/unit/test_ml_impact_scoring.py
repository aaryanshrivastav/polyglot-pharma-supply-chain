"""
Unit Tests: Weighted Disruption Impact Scoring Module.
Validates downstream topological propagation, drug criticality heuristics,
and regional multiplier scoring in ml/impact_scoring.py.
"""

import pytest
from ml.impact_scoring import (
    compute_drug_criticality_factor,
    compute_node_disruption_impact,
    ImpactScoringEngine
)


@pytest.mark.unit
class TestDisruptionImpactScoring:
    def test_compute_drug_criticality_factor_when_sole_source_small_molecule_should_apply_1_5x_multiplier(self):
        # Arrange
        substitutables = {"DRUG-SUB-1", "DRUG-SUB-2"}
        biologics = set()

        # Act
        factor, rationale = compute_drug_criticality_factor("DRUG-SOLE-SOURCE", substitutables, biologics)

        # Assert
        assert factor == 1.5, "Expected 1.5x multiplier for sole-source drug"
        assert "Sole-source" in rationale

    def test_compute_drug_criticality_factor_when_sole_source_cold_chain_biologic_should_apply_1_7x_multiplier(self):
        # Arrange
        substitutables = set()
        biologics = {"DRUG-BIO-1"}

        # Act
        factor, rationale = compute_drug_criticality_factor("DRUG-BIO-1", substitutables, biologics)

        # Assert
        assert factor == 1.7, "Expected 1.7x multiplier for sole-source cold-chain biologic"
        assert "Maximum Criticality" in rationale

    def test_compute_drug_criticality_factor_when_multi_source_interchangeable_should_apply_1_0x_baseline(self):
        # Arrange
        substitutables = {"DRUG-MULTI-1"}
        biologics = set()

        # Act
        factor, rationale = compute_drug_criticality_factor("DRUG-MULTI-1", substitutables, biologics)

        # Assert
        assert factor == 1.0, "Expected 1.0x baseline for interchangeable multi-source drug"

    def test_compute_node_disruption_impact_when_distributor_fails_should_calculate_affected_pharmacy_score(self):
        # Arrange
        mfg_to_dist = {"EST-0001": ["DIST-001"]}
        dist_to_pharm = {"DIST-001": [f"PHARM-{i:03d}" for i in range(1, 51)]}  # 50 pharmacies
        substitutables = set()
        biologics = set()

        # Act
        impact = compute_node_disruption_impact(
            node_id="DIST-001",
            target_drug_id="DRUG-TEST",
            mfg_to_dist=mfg_to_dist,
            dist_to_pharm=dist_to_pharm,
            substitutable_drugs=substitutables,
            biologic_drugs=biologics
        )

        # Assert
        assert impact["affected_pharmacy_count"] == 50
        assert impact["drug_criticality_factor"] == 1.5
        assert impact["impact_score"] == 75.0, "50 pharmacies * 1.5 criticality * 1.0 region = 75.0"
        assert impact["severity_classification"] == "MODERATE_DISRUPTION"

    def test_impact_scoring_engine_when_dry_run_mode_should_evaluate_staged_topology(self):
        # Arrange
        engine = ImpactScoringEngine(dry_run=True)

        # Act
        res = engine.evaluate_node_failure("EST-0001", "DRUG-0002-7597")
        engine.close()

        # Assert
        assert res["failed_node_id"] == "EST-0001"
        assert res["impact_score"] > 0
        assert "affected_pharmacy_count" in res
