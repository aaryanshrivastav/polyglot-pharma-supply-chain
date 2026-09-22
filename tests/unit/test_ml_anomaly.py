"""
Unit Tests: Multi-Variate Anomaly Detection Module.
Validates robust Z-score calculation, delivery volume contractions,
and cold-chain thermal excursions in ml/anomaly_detection.py.
"""

import numpy as np
import pytest
from ml.anomaly_detection import compute_z_scores, detect_series_anomalies, AnomalyDetector


@pytest.mark.unit
class TestMultiVariateAnomalyDetector:
    def test_compute_z_scores_when_constant_vs_variable_series_should_handle_zero_variance(self):
        # Arrange
        constant_vals = np.array([10.0, 10.0, 10.0, 10.0, 10.0])
        variable_vals = np.array([100.0, 105.0, 95.0, 100.0, 20.0])

        # Act
        z_const = compute_z_scores(constant_vals)
        z_var = compute_z_scores(variable_vals)

        # Assert
        assert len(z_const) == 5
        assert np.all(np.abs(z_const) < 1e-3), "Constant series should have ~0 Z-scores without division by zero"
        assert z_var[-1] < -1.5, "Last point should exhibit a negative drop in Z-score"

    def test_detect_series_anomalies_when_volume_collapses_should_flag_volume_contraction(self):
        # Arrange
        vols = [100.0, 102.0, 98.0, 101.0, 99.0, 100.0, 10.0]  # Collapse to 10
        drug_id = "DRUG-TEST-001"

        # Act
        anomalies = detect_series_anomalies(drug_id=drug_id, volumes=vols, z_threshold=2.0)

        # Assert
        assert len(anomalies) >= 1
        vol_alert = next((a for a in anomalies if a["alert_type"] == "VOLUME_CONTRACTION"), None)
        assert vol_alert is not None, "Expected VOLUME_CONTRACTION alert"
        assert vol_alert["z_score"] < -2.0
        assert vol_alert["severity"] in {"HIGH", "CRITICAL"}
        assert vol_alert["drug_id"] == drug_id

    def test_detect_series_anomalies_when_biologic_exceeds_8c_should_flag_temperature_excursion(self):
        # Arrange
        vols = [100.0, 100.0, 100.0]
        temps = [4.0, 5.0, 15.5]  # 15.5°C violates 2°C-8°C refrigerated range
        drug_id = "DRUG-INSULIN-BIO"

        # Act
        anomalies = detect_series_anomalies(
            drug_id=drug_id,
            volumes=vols,
            temperatures=temps,
            is_biologic=True
        )

        # Assert
        assert len(anomalies) == 1
        temp_alert = anomalies[0]
        assert temp_alert["alert_type"] == "TEMPERATURE_EXCURSION"
        assert temp_alert["observed_value"] == 15.5
        assert temp_alert["severity"] in {"HIGH", "CRITICAL"}

    def test_run_detection_when_dry_run_mode_should_evaluate_streams_without_database_errors(self):
        # Arrange
        detector = AnomalyDetector(dry_run=True)

        # Act
        anomalies = detector.run_detection(sample_size=10, z_threshold=2.0)
        detector.close()

        # Assert
        assert isinstance(anomalies, list)
