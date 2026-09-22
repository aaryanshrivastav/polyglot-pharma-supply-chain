"""
System Tests: End-to-End Simulation Pipeline.
Validates end-to-end multi-day event generation, disruption injection,
and inventory event emission across pharmacies and drug portfolios.
"""

import pytest
from simulator.event_generator import PharmaSupplyChainSimulator


@pytest.mark.system
class TestSystemEndToEndPipeline:
    def test_run_simulation_when_executed_over_10_days_should_generate_expected_event_volume(self):
        # Arrange
        num_pharmacies = 30
        num_drugs = 15
        sim_days = 10
        expected_stock_events = num_pharmacies * num_drugs * sim_days  # 4,500

        sim = PharmaSupplyChainSimulator(
            num_pharmacies=num_pharmacies,
            num_drugs=num_drugs,
            sim_days=sim_days,
            time_dilation=0.0
        )

        # Act
        total_stock, total_shipment = sim.run_simulation()

        # Assert
        assert total_stock == expected_stock_events, f"Expected {expected_stock_events} stock events, got {total_stock}"
        assert total_shipment > 0, "Expected non-zero shipment telemetry events generated during simulation"
