"""
Disruption Injector calibrated against real FDA drug shortage records.
Maps historical FDA shortage events to corresponding drugs and manufacturers,
suppressing production capacity and creating downstream inventory supply shocks.
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STAGED_DIR = Path("data-ingestion/staged")


class DisruptionInjector:
    def __init__(self, shortages_path: str = None, drugs_path: str = None):
        self.shortages_path = Path(shortages_path) if shortages_path else STAGED_DIR / "shortages.json"
        self.drugs_path = Path(drugs_path) if drugs_path else STAGED_DIR / "drugs.json"
        
        self.shortages = []
        self.drug_map = {}  # drug_id -> drug_obj
        self.generic_to_drugs = {}  # generic_name_clean -> list of drug_ids
        self.active_disruptions = []

        self._load_datasets()

    def _load_datasets(self):
        """Loads and indexes staged shortage and drug datasets."""
        if not self.shortages_path.exists() or not self.drugs_path.exists():
            logger.warning(f"Datasets missing: {self.shortages_path} or {self.drugs_path}")
            return

        with open(self.drugs_path, "r", encoding="utf-8") as f:
            drugs = json.load(f)
            for d in drugs:
                d_id = d["drug_id"]
                self.drug_map[d_id] = d
                gen = d.get("generic_name", "").strip().lower()
                if gen not in self.generic_to_drugs:
                    self.generic_to_drugs[gen] = []
                self.generic_to_drugs[gen].append(d_id)

        with open(self.shortages_path, "r", encoding="utf-8") as f:
            self.shortages = json.load(f)

        # Precompute & index shortage matches per drug to make get_disruption_impact O(1)
        self.drug_shortage_match = {}
        for d_id, drug in self.drug_map.items():
            gen = drug.get("generic_name", "").strip().lower()
            matched = [
                s for s in self.shortages 
                if (s.get("generic_name", "").strip().lower() in gen) or (gen in s.get("generic_name", "").strip().lower())
            ]
            self.drug_shortage_match[d_id] = matched[0] if matched else None

        logger.info(f"Loaded {len(self.shortages):,} historical shortage events and {len(self.drug_map):,} drugs (pre-indexed).")

    def get_disruption_impact(self, drug_id: str, sim_day_offset: int, base_date: datetime = datetime(2024, 1, 1)) -> dict:
        """
        Evaluates whether a drug is experiencing a calibrated supply disruption at the simulated date.
        Returns:
            - is_disrupted: bool
            - supply_multiplier: float (0.0 to 1.0)
            - lead_time_penalty_factor: float (1.0 to 3.5)
            - reason: str
        """
        drug = self.drug_map.get(drug_id)
        if not drug:
            return {"is_disrupted": False, "supply_multiplier": 1.0, "lead_time_penalty_factor": 1.0, "reason": None}

        current_date = base_date + timedelta(days=sim_day_offset)
        gen = drug.get("generic_name", "").strip().lower()

        # O(1) indexed shortage lookup
        shortage = self.drug_shortage_match.get(drug_id)
        
        if shortage:
            # Calibrate cyclic shortage shock for matching formulations (e.g. 45-day disruption window every 180 days)
            cycle_pos = (sim_day_offset + hash(drug_id) % 60) % 180
            if cycle_pos < 45:  # In active shortage window
                severity = float(shortage.get("disruption_severity_score", 3.5))
                # Higher severity drops supply output significantly (down to 5-15% of normal)
                supply_mult = max(0.05, 1.0 - (severity * 0.22))
                lead_time_penalty = 1.0 + (severity * 0.45)
                return {
                    "is_disrupted": True,
                    "supply_multiplier": round(supply_mult, 3),
                    "lead_time_penalty_factor": round(lead_time_penalty, 2),
                    "shortage_id": shortage.get("shortage_id"),
                    "reason": shortage.get("reason", "Manufacturing and supply chain constraint"),
                    "severity_score": severity
                }

        return {
            "is_disrupted": False,
            "supply_multiplier": 1.0,
            "lead_time_penalty_factor": 1.0,
            "shortage_id": None,
            "reason": None,
            "severity_score": 0.0
        }


if __name__ == "__main__":
    injector = DisruptionInjector()
    # Test sample drug
    sample_drugs = list(injector.drug_map.keys())[:5]
    print("\n--- Disruption Calibration Sample Test (Day 15) ---")
    for d_id in sample_drugs:
        res = injector.get_disruption_impact(d_id, sim_day_offset=15)
        print(f"Drug: {d_id:<20} | Disrupted: {str(res['is_disrupted']):<5} | Supply Multiplier: {res['supply_multiplier']} | Lead Time Factor: {res['lead_time_penalty_factor']}x")

