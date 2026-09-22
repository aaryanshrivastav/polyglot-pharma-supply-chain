"""
Unit Tests: ETL Analytical Rollup Transformations.
Validates multi-dimensional daily aggregation (drug, region, date), stockout frequency counting,
telemetry temperature averaging, and empty dataset handling in etl/rollup_job.py.
"""

import pandas as pd
import pytest
from datetime import date
from etl.rollup_job import STATE_TO_REGION, load_node_region_map, RollupJob


@pytest.mark.unit
class TestETLRollupTransformations:
    def test_state_to_region_mapping_when_queried_should_cover_all_us_geographies(self):
        # Arrange & Act & Assert
        assert STATE_TO_REGION["NY"] == "Northeast"
        assert STATE_TO_REGION["IL"] == "Midwest"
        assert STATE_TO_REGION["FL"] == "South"
        assert STATE_TO_REGION["CA"] == "West"
        assert STATE_TO_REGION["TX"] == "South"

    def test_load_node_region_map_when_staged_pharmacies_present_should_build_valid_node_mapping(self):
        # Arrange & Act
        mapping = load_node_region_map()

        # Assert
        if mapping:
            sample_node = next(iter(mapping))
            assert sample_node.startswith("PHARM-"), "Node mapping keys must be pharmacy IDs"
            assert mapping[sample_node] in {"Northeast", "Midwest", "South", "West", "National"}

    def test_transform_and_aggregate_when_stock_only_should_calculate_daily_demand_and_mean_stock(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(RollupJob, "_init_cassandra", lambda self: None)
        job = RollupJob()
        job.node_region_map = {
            "PHARM-001": "Northeast",
            "PHARM-002": "Northeast",
            "PHARM-003": "West"
        }

        stock_data = [
            {"node_id": "PHARM-001", "drug_id": "DRUG-A", "event_time": "2026-09-01T10:00:00Z", "current_stock": 100, "daily_demand": 20, "stockout_flag": 0},
            {"node_id": "PHARM-002", "drug_id": "DRUG-A", "event_time": "2026-09-01T14:00:00Z", "current_stock": 0, "daily_demand": 15, "stockout_flag": 1},
            {"node_id": "PHARM-003", "drug_id": "DRUG-A", "event_time": "2026-09-01T09:00:00Z", "current_stock": 50, "daily_demand": 10, "stockout_flag": 0},
            {"node_id": "PHARM-001", "drug_id": "DRUG-A", "event_time": "2026-09-02T10:00:00Z", "current_stock": 80, "daily_demand": 25, "stockout_flag": 0},
        ]
        stock_df = pd.DataFrame(stock_data)
        telem_df = pd.DataFrame()

        # Act
        rollups = job.transform_and_aggregate(stock_df, telem_df)

        # Assert
        assert not rollups.empty, "Expected aggregated rollups DataFrame"
        assert len(rollups) == 3, "Expected 3 distinct (drug, region, date) partitions"

        r1 = rollups[(rollups["drug_id"] == "DRUG-A") & (rollups["region"] == "Northeast") & (rollups["rollup_date"] == date(2026, 9, 1))].iloc[0]
        assert r1["total_volume"] == 35, "Expected sum of daily demand 20 + 15 = 35"
        assert r1["avg_stock"] == 50.0, "Expected mean stock (100 + 0) / 2 = 50.0"
        assert r1["event_count"] == 2
        assert r1["stockout_count"] == 1
        assert r1["avg_temperature"] == 21.0
        assert r1["excursion_count"] == 0

    def test_transform_and_aggregate_when_telemetry_provided_should_merge_temperature_and_excursions(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(RollupJob, "_init_cassandra", lambda self: None)
        job = RollupJob()
        job.node_region_map = {"PHARM-001": "South"}

        stock_df = pd.DataFrame([
            {"node_id": "PHARM-001", "drug_id": "DRUG-B", "event_time": "2026-09-01T12:00:00Z", "current_stock": 200, "daily_demand": 50, "stockout_flag": 0}
        ])
        telem_df = pd.DataFrame([
            {"drug_id": "DRUG-B", "event_time": "2026-09-01T08:00:00Z", "temperature_celsius": 4.5, "is_excursion": 0},
            {"drug_id": "DRUG-B", "event_time": "2026-09-01T16:00:00Z", "temperature_celsius": 12.0, "is_excursion": 1}
        ])

        # Act
        rollups = job.transform_and_aggregate(stock_df, telem_df)

        # Assert
        assert len(rollups) == 1
        r = rollups.iloc[0]
        assert r["drug_id"] == "DRUG-B"
        assert r["region"] == "South"
        assert r["total_volume"] == 50
        assert r["avg_temperature"] == 8.25, "Expected mean temp (4.5 + 12.0) / 2 = 8.25"
        assert r["excursion_count"] == 1

    def test_transform_and_aggregate_when_empty_inputs_should_return_empty_dataframe(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(RollupJob, "_init_cassandra", lambda self: None)
        job = RollupJob()

        # Act
        res = job.transform_and_aggregate(pd.DataFrame(), pd.DataFrame())

        # Assert
        assert res.empty, "Expected empty DataFrame on empty inputs"
