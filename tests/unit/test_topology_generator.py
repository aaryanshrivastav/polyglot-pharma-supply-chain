"""
Unit Tests: Supply Chain Graph Topology Generator.
Validates Zipfian power-law degree sampling, distributor facility generation,
and coordinate bounds in db-loaders/generate_topology.py.
"""

import importlib.util
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Dynamically load module from hyphenated folder 'db-loaders' to avoid IDE import resolution errors
TOPOLOGY_GEN_PATH = PROJECT_ROOT / "db-loaders" / "generate_topology.py"
spec = importlib.util.spec_from_file_location("generate_topology", TOPOLOGY_GEN_PATH)
topology_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(topology_module)

sample_zipf = topology_module.sample_zipf
generate_distributors = topology_module.generate_distributors


@pytest.mark.unit
class TestTopologyGenerator:
    def test_sample_zipf_when_sampled_repeatedly_should_remain_strictly_within_bounds_and_exhibit_skew(self):
        # Arrange
        n = 20
        alpha = 1.6
        num_trials = 250

        # Act
        samples = [sample_zipf(alpha=alpha, n=n) for _ in range(num_trials)]

        # Assert
        assert all(1 <= s <= n for s in samples), f"All samples must be within [1, {n}]"
        rank_1_count = samples.count(1)
        rank_20_count = samples.count(20)
        assert rank_1_count >= rank_20_count, "Rank 1 items must be sampled with higher probability than Rank 20"

    def test_generate_distributors_when_initialized_should_produce_20_unique_regional_facilities(self):
        # Arrange & Act
        distributors = generate_distributors()

        # Assert
        assert len(distributors) == 20, "Expected exactly 20 primary regional distribution centers"
        ids = [d["distributor_id"] for d in distributors]
        assert len(ids) == len(set(ids)), "Distributor IDs must be strictly unique"

        for d in distributors:
            assert d["distributor_id"].startswith("DIST-"), f"Invalid distributor ID format: {d['distributor_id']}"
            assert -90.0 <= d["latitude"] <= 90.0, "Latitude must be within [-90.0, 90.0]"
            assert -180.0 <= d["longitude"] <= 180.0, "Longitude must be within [-180.0, 180.0]"
            assert isinstance(d["has_cold_chain_storage"], bool), "has_cold_chain_storage must be boolean"
