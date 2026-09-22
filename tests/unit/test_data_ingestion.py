"""
Unit Tests: Data Ingestion & Storage Classification Rule Engine.
Validates temperature categorization, cold-chain dependency identification,
and metadata sanitization logic in data-ingestion/clean_and_stage.py.
"""

import importlib.util
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Dynamically load module from hyphenated folder 'data-ingestion' to avoid IDE import resolution errors
CLEAN_STAGE_PATH = PROJECT_ROOT / "data-ingestion" / "clean_and_stage.py"
spec = importlib.util.spec_from_file_location("clean_and_stage", CLEAN_STAGE_PATH)
clean_and_stage_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clean_and_stage_module)

classify_storage_temperature = clean_and_stage_module.classify_storage_temperature


@pytest.mark.unit
class TestDataIngestionClassification:
    def test_classify_storage_temperature_when_frozen_biologic_should_return_ultra_cold(self):
        # Arrange
        drug_name = "mRNA-1273 Spikevax COVID-19 Vaccine"
        dosage = "INJECTION, SUSPENSION"
        route = "INTRAMUSCULAR"
        storage_spec = "Store frozen between -80°C and -60°C"

        # Act
        classification = classify_storage_temperature(
            drug_name=drug_name,
            dosage_form=dosage,
            route=route,
            raw_storage=storage_spec
        )

        # Assert
        assert classification["temperature_category"] == "ULTRA_COLD", "Expected ULTRA_COLD category for mRNA vaccine"
        assert classification["min_temp_celsius"] == -80.0
        assert classification["max_temp_celsius"] == -60.0
        assert classification["requires_cold_chain"] is True

    def test_classify_storage_temperature_when_insulin_or_antibody_should_return_refrigerated(self):
        # Arrange
        drug_name = "Insulin Glargine Lantus"
        dosage = "INJECTION, SOLUTION"
        route = "SUBCUTANEOUS"
        storage_spec = "Refrigerate at 2°C to 8°C. Do not freeze."

        # Act
        classification = classify_storage_temperature(
            drug_name=drug_name,
            dosage_form=dosage,
            route=route,
            raw_storage=storage_spec
        )

        # Assert
        assert classification["temperature_category"] == "REFRIGERATED"
        assert classification["min_temp_celsius"] == 2.0
        assert classification["max_temp_celsius"] == 8.0
        assert classification["requires_cold_chain"] is True

    def test_classify_storage_temperature_when_solid_oral_tablet_should_return_controlled_room_temp(self):
        # Arrange
        drug_name = "Amoxicillin and Clavulanate Potassium"
        dosage = "TABLET, FILM COATED"
        route = "ORAL"
        storage_spec = "Store at controlled room temperature 20°C to 25°C (68°F to 77°F)"

        # Act
        classification = classify_storage_temperature(
            drug_name=drug_name,
            dosage_form=dosage,
            route=route,
            raw_storage=storage_spec
        )

        # Assert
        assert classification["temperature_category"] == "CONTROLLED_ROOM_TEMP"
        assert classification["min_temp_celsius"] == 15.0
        assert classification["max_temp_celsius"] == 25.0
        assert classification["requires_cold_chain"] is False
