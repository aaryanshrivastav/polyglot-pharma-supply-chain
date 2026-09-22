"""
Unit Tests: FDA Shortage Disruption Injector.
Validates O(1) matching index, disruption multiplier math, and penalty factors
in simulator/disruption_injector.py.
"""

import pytest
from simulator.disruption_injector import DisruptionInjector


@pytest.fixture(scope="module")
def disruption_injector():
    return DisruptionInjector()


@pytest.mark.unit
class TestDisruptionInjector:
    def test_init_when_staged_datasets_exist_should_load_and_preindex_matches(self, disruption_injector):
        # Arrange & Act
        injector = disruption_injector

        # Assert
        assert len(injector.shortages) > 0, "Expected non-empty shortages catalog"
        assert len(injector.drug_map) > 0, "Expected non-empty drug catalog"
        assert len(injector.drug_shortage_match) == len(injector.drug_map), "Expected 1:1 match index mapping"

    def test_get_disruption_impact_when_valid_drug_should_return_valid_schema_and_ranges(self, disruption_injector):
        # Arrange
        sample_drug_id = list(disruption_injector.drug_map.keys())[0]

        # Act
        impact = disruption_injector.get_disruption_impact(sample_drug_id, sim_day_offset=5)

        # Assert
        assert "is_disrupted" in impact
        assert "supply_multiplier" in impact
        assert "lead_time_penalty_factor" in impact
        assert 0.0 <= impact["supply_multiplier"] <= 1.0, "Supply multiplier must be normalized between 0.0 and 1.0"
        assert impact["lead_time_penalty_factor"] >= 1.0, "Lead time penalty factor cannot be less than 1.0"

    def test_get_disruption_impact_when_unknown_drug_should_return_undisrupted_baseline(self, disruption_injector):
        # Arrange
        unknown_drug_id = "DRUG-NONEXISTENT-999"

        # Act
        impact = disruption_injector.get_disruption_impact(unknown_drug_id, sim_day_offset=10)

        # Assert
        assert impact["is_disrupted"] is False
        assert impact["supply_multiplier"] == 1.0
        assert impact["lead_time_penalty_factor"] == 1.0
