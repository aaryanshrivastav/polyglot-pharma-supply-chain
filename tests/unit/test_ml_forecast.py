"""
Unit Tests: ML Shortage Risk Forecasting Module.
Validates time-series Exponential Smoothing / ARIMA inventory projections,
shortage probability scoring, and risk classification in ml/forecast_shortage.py.
"""

import pandas as pd
import pytest
from ml.forecast_shortage import calculate_shortage_risk, ShortageForecaster


@pytest.mark.unit
class TestShortageForecaster:
    def test_calculate_shortage_risk_when_stock_declining_steeply_should_return_high_or_critical_risk(self):
        # Arrange
        declining_stock_series = pd.Series([100.0, 85.0, 70.0, 55.0, 40.0, 25.0, 10.0, 5.0])
        horizon_days = 7
        safety_stock = 20.0

        # Act
        risk_score, risk_level, forecast = calculate_shortage_risk(
            series=declining_stock_series,
            horizon_days=horizon_days,
            safety_stock=safety_stock
        )

        # Assert
        assert 0.0 <= risk_score <= 1.0, "Risk score must be in range [0.0, 1.0]"
        assert risk_score >= 0.70, f"Expected critical risk for depleting inventory, got {risk_score}"
        assert risk_level in {"HIGH", "CRITICAL"}
        assert len(forecast) == horizon_days

    def test_calculate_shortage_risk_when_stock_abundant_and_stable_should_return_low_risk(self):
        # Arrange
        healthy_stock_series = pd.Series([500.0, 520.0, 490.0, 510.0, 505.0, 495.0, 500.0])
        horizon_days = 7
        safety_stock = 20.0

        # Act
        risk_score, risk_level, forecast = calculate_shortage_risk(
            series=healthy_stock_series,
            horizon_days=horizon_days,
            safety_stock=safety_stock
        )

        # Assert
        assert 0.0 <= risk_score <= 0.25, f"Expected low risk score, got {risk_score}"
        assert risk_level == "LOW"
        assert all(f > 100.0 for f in forecast), "Forecasted stock should remain well above safety stock"

    def test_calculate_shortage_risk_when_sparse_history_should_fallback_gracefully(self):
        # Arrange
        sparse_series = pd.Series([50.0])
        horizon_days = 5

        # Act
        risk_score, risk_level, forecast = calculate_shortage_risk(
            series=sparse_series,
            horizon_days=horizon_days,
            safety_stock=20.0
        )

        # Assert
        assert 0.0 <= risk_score <= 1.0
        assert len(forecast) == horizon_days

    def test_run_forecasting_when_dry_run_mode_should_complete_without_external_dependencies(self):
        # Arrange
        forecaster = ShortageForecaster(dry_run=True)

        # Act
        results = forecaster.run_forecasting(sample_size=10, horizon_days=7)
        forecaster.close()

        # Assert
        assert len(results) > 0, "Expected at least 1 scored drug record"
        r = results[0]
        assert "drug_id" in r
        assert "risk_score" in r
        assert "risk_level" in r
        assert "forecast_trajectory" in r
        assert len(r["forecast_trajectory"]) > 0
