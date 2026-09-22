"""
Pytest configuration and shared fixtures for the Polyglot Pharma Supply Chain test suite.
"""

import json
import os
import sys
from pathlib import Path
import pytest
from dotenv import load_dotenv

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()


@pytest.fixture(scope="session")
def sample_staged_drug():
    """Returns a representative staged drug document."""
    return {
        "drug_id": "DRUG-0093-7679",
        "product_ndc": "0093-7679",
        "brand_name": "Etonogestrel and Ethinyl Estradiol",
        "generic_name": "Etonogestrel and Ethinyl Estradiol",
        "dosage_form": "INSERT, EXTENDED RELEASE",
        "route": "VAGINAL",
        "active_ingredients": [
            {"name": "ETONOGESTREL", "strength": ".12 mg/d"},
            {"name": "ETHINYL ESTRADIOL", "strength": ".015 mg/d"}
        ],
        "storage_condition": {
            "temperature_category": "CONTROLLED_ROOM_TEMP",
            "temp_range_desc": "Controlled Room Temperature (15°C to 25°C)",
            "min_temp_celsius": 15.0,
            "max_temp_celsius": 25.0,
            "humidity_max_percent": 65.0,
            "requires_cold_chain": False
        },
        "requires_cold_chain": False,
        "is_biologic": False,
        "manufacturer_id": "EST-0001",
        "labeler_name": "Teva Pharmaceuticals USA, Inc."
    }


@pytest.fixture(scope="session")
def sample_cold_chain_drug():
    """Returns a cold-chain dependent biological drug."""
    return {
        "drug_id": "DRUG-0002-7597",
        "product_ndc": "0002-7597",
        "brand_name": "Humalog",
        "generic_name": "Insulin Lispro",
        "dosage_form": "INJECTION, SOLUTION",
        "route": "SUBCUTANEOUS",
        "active_ingredients": [
            {"name": "INSULIN LISPRO", "strength": "100 [iU]/mL"}
        ],
        "storage_condition": {
            "temperature_category": "REFRIGERATED",
            "temp_range_desc": "Refrigerated (2°C to 8°C)",
            "min_temp_celsius": 2.0,
            "max_temp_celsius": 8.0,
            "humidity_max_percent": 60.0,
            "requires_cold_chain": True
        },
        "requires_cold_chain": True,
        "is_biologic": True,
        "manufacturer_id": "EST-0002",
        "labeler_name": "Eli Lilly and Company"
    }


@pytest.fixture(scope="session")
def sample_shortage_record():
    """Returns a representative FDA shortage record."""
    return {
        "shortage_id": "FDA-SH-0001",
        "generic_name": "Amoxicillin Oral Powder for Suspension",
        "brand_name": "Amoxil",
        "status": "CURRENT",
        "reason": "Demand Increase for the Drug / Manufacturing Delay",
        "date_reported": "10/28/2022",
        "disruption_severity_score": 4.5
    }

