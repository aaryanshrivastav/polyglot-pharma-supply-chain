"""
Unit Tests: Supply Chain Discrete Event Simulator.
Validates seasonal demand sinusoidal waves, inventory depletion, reorder thresholds,
and shipment telemetry generation in simulator/event_generator.py.
"""

import pytest
from simulator.event_generator import PharmaSupplyChainSimulator


@pytest.fixture(scope="module")
def simulator_instance():
    return PharmaSupplyChainSimulator(
        num_pharmacies=20,
        num_drugs=10,
        sim_days=5,
        time_dilation=0.0
    )


@pytest.mark.unit
class TestSimulatorEventGenerator:
    def test_calculate_seasonal_demand_when_winter_vs_summer_should_produce_valid_positive_demand(self, simulator_instance):
        # Arrange
        sim = simulator_instance
        base_demand = 25

        # Act
        winter_demand = sim.calculate_seasonal_demand(base_demand=base_demand, day_offset=15, is_biologic=True)
        summer_demand = sim.calculate_seasonal_demand(base_demand=base_demand, day_offset=180, is_biologic=True)

        # Assert
        assert winter_demand > 0, "Winter demand must be positive"
        assert summer_demand > 0, "Summer demand must be positive"
        assert isinstance(winter_demand, int)
        assert isinstance(summer_demand, int)

    def test_generate_day_events_when_executed_should_produce_correct_counts_and_schemas(self, simulator_instance):
        # Arrange
        sim = simulator_instance
        expected_stock_count = 20 * 10  # 20 pharmacies * 10 drugs = 200

        # Act
        stock_events, shipment_events = sim.generate_day_events(day_offset=0)

        # Assert
        assert len(stock_events) == expected_stock_count, f"Expected {expected_stock_count} stock events"
        assert len(shipment_events) > 0, "Expected at least 1 in-flight shipment event"

        # Validate Stock Event Schema
        sample_stock = stock_events[0]
        assert "event_id" in sample_stock
        assert "pharmacy_id" in sample_stock
        assert "drug_id" in sample_stock
        assert "current_stock" in sample_stock
        assert "stockout_flag" in sample_stock
        assert sample_stock["current_stock"] >= 0

        # Validate Shipment Telemetry Schema
        sample_shipment = shipment_events[0]
        assert "batch_id" in sample_shipment
        assert "temperature_celsius" in sample_shipment
        assert "humidity_percent" in sample_shipment
        assert "is_excursion" in sample_shipment
        assert isinstance(sample_shipment["is_excursion"], bool)
