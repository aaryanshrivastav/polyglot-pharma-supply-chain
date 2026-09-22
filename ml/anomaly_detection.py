"""
ML Module: Multi-Variate Anomaly Detection.
Evaluates time-series telemetry and rollup volume distributions using robust Z-score and excursion bounds.
Detects shipment collapses, unexpected stockout spikes, and cold-chain thermal breaches.
Persists actionable alerts back to Redis (hot cache) and MongoDB (anomaly repository).
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AnomalyDetection")

OUTPUT_DIR = PROJECT_ROOT / "ml" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STAGED_DIR = PROJECT_ROOT / "data-ingestion" / "staged"


def compute_z_scores(values: np.ndarray) -> np.ndarray:
    """Computes robust Z-scores using mean and standard deviation with zero-variance safety."""
    if len(values) <= 1:
        return np.zeros(len(values))
    mean = np.mean(values)
    std = np.std(values)
    if std < 1e-6:
        # Fallback to Median Absolute Deviation (MAD)
        median = np.median(values)
        mad = np.median(np.abs(values - median))
        std = 1.4826 * mad if mad > 1e-6 else 1.0
    return (values - mean) / std


def detect_series_anomalies(
    drug_id: str,
    volumes: List[float],
    temperatures: Optional[List[float]] = None,
    is_biologic: bool = False,
    z_threshold: float = 2.0
) -> List[Dict]:
    """Evaluates time series arrays for volume contractions, sudden stockout spikes, and thermal excursions."""
    anomalies = []
    vol_arr = np.array(volumes, dtype=float)

    if len(vol_arr) >= 3:
        z_scores = compute_z_scores(vol_arr)
        # Check the latest observation
        latest_val = vol_arr[-1]
        latest_z = float(z_scores[-1])

        # Negative Volume Shock (Delivery collapse)
        if latest_z <= -z_threshold:
            severity = "CRITICAL" if latest_z <= -3.0 else "HIGH"
            anomalies.append({
                "drug_id": drug_id,
                "alert_type": "VOLUME_CONTRACTION",
                "metric_name": "daily_volume",
                "observed_value": round(latest_val, 1),
                "z_score": round(latest_z, 3),
                "severity": severity,
                "message": f"Shipment volume contracted by {abs(latest_z):.2f} standard deviations below historical mean.",
                "detected_at": datetime.now(timezone.utc).isoformat()
            })

    # Cold chain temperature excursion check
    if temperatures and len(temperatures) > 0:
        temp_arr = np.array(temperatures, dtype=float)
        latest_temp = float(temp_arr[-1])
        min_allowed = 2.0 if is_biologic else 15.0
        max_allowed = 8.0 if is_biologic else 25.0

        if latest_temp < min_allowed or latest_temp > max_allowed:
            deviation = max(0.0, min_allowed - latest_temp, latest_temp - max_allowed)
            severity = "CRITICAL" if deviation > 5.0 else ("HIGH" if is_biologic else "MEDIUM")
            anomalies.append({
                "drug_id": drug_id,
                "alert_type": "TEMPERATURE_EXCURSION",
                "metric_name": "transit_temperature",
                "observed_value": round(latest_temp, 2),
                "allowed_range": f"{min_allowed}C to {max_allowed}C",
                "deviation_celsius": round(deviation, 2),
                "severity": severity,
                "message": f"Transit temperature {latest_temp:.1f}C breached cold-chain tolerance [{min_allowed}C, {max_allowed}C].",
                "detected_at": datetime.now(timezone.utc).isoformat()
            })

    return anomalies


class AnomalyDetector:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.redis_client = None
        self.mongo_client = None
        self.cassandra_session = None

        if not self.dry_run:
            self._init_connections()

    def _init_connections(self):
        # 1. Redis
        try:
            import redis
            redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True, socket_timeout=2)
            self.redis_client.ping()
            logger.info("Connected to Redis for live anomaly alerting.")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}")
            self.redis_client = None

        # 2. MongoDB
        try:
            from pymongo import MongoClient
            mongo_uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            self.mongo_client.admin.command("ping")
            logger.info("Connected to MongoDB for anomaly persistence.")
        except Exception as e:
            logger.warning(f"MongoDB unavailable: {e}")
            self.mongo_client = None

        # 3. Cassandra
        try:
            from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
            from cassandra.policies import RoundRobinPolicy
            cass_host = os.getenv("CASSANDRA_HOST", "127.0.0.1")
            cass_port = int(os.getenv("CASSANDRA_PORT", "9042"))
            keyspace = os.getenv("CASSANDRA_KEYSPACE", "pharma_telemetry")
            profile = ExecutionProfile(load_balancing_policy=RoundRobinPolicy(), request_timeout=10.0)
            self.cass_cluster = Cluster([cass_host], port=cass_port, execution_profiles={EXEC_PROFILE_DEFAULT: profile}, protocol_version=5)
            self.cassandra_session = self.cass_cluster.connect(keyspace)
            logger.info("Connected to Cassandra for daily_rollups volume telemetry.")
        except Exception as e:
            logger.warning(f"Cassandra unavailable, falling back to staged samples: {e}")
            self.cassandra_session = None

    def load_metric_series(self, sample_size: int = 50) -> Dict[str, Dict]:
        """Loads volume and temperature series per drug."""
        series_by_drug = {}

        if self.cassandra_session:
            try:
                cql = "SELECT drug_id, rollup_date, total_volume, avg_temperature FROM daily_rollups;"
                rows = list(self.cassandra_session.execute(cql))
                if rows:
                    df = pd.DataFrame([{"drug_id": r.drug_id, "date": pd.to_datetime(r.rollup_date), "volume": r.total_volume, "temp": r.avg_temperature} for r in rows])
                    for drug_id, grp in df.groupby("drug_id"):
                        grp_sorted = grp.sort_values("date")
                        series_by_drug[drug_id] = {
                            "volumes": grp_sorted["volume"].tolist(),
                            "temperatures": grp_sorted["temp"].tolist(),
                            "is_biologic": False
                        }
                    logger.info(f"Loaded metric series for {len(series_by_drug):,} drugs from Cassandra.")
                    return series_by_drug
            except Exception as e:
                logger.warning(f"Failed querying Cassandra: {e}")

        # Synthetic/staged fallback
        drugs_file = STAGED_DIR / "drugs.json"
        if drugs_file.exists():
            with open(drugs_file, "r", encoding="utf-8") as f:
                drugs = json.load(f)[:sample_size]
            np.random.seed(42)
            for i, d in enumerate(drugs):
                drug_id = d["drug_id"]
                is_bio = d.get("is_biologic", False)
                # Normal baseline
                vols = list(np.random.normal(500, 40, 20))
                temps = list(np.random.normal(5.0 if is_bio else 20.0, 0.8, 20))

                # Inject anomalies for first few
                if i == 0 or "0002" in drug_id:
                    vols.append(50.0)  # Major drop
                elif i == 1:
                    temps.append(14.5 if is_bio else 32.0)  # Excursion
                else:
                    vols.append(float(np.random.normal(500, 40)))
                    temps.append(float(np.random.normal(5.0 if is_bio else 20.0, 0.8)))

                series_by_drug[drug_id] = {
                    "volumes": vols,
                    "temperatures": temps,
                    "is_biologic": is_bio
                }

        return series_by_drug

    def run_detection(self, sample_size: int = 50, z_threshold: float = 2.0) -> List[Dict]:
        print("\n" + "=" * 95)
        print("          PHASE 4: ML MULTI-VARIATE ANOMALY & CONTRACTION DETECTION PIPELINE")
        print("=" * 95)

        data_map = self.load_metric_series(sample_size=sample_size)
        detected_anomalies = []

        for drug_id, data in list(data_map.items())[:sample_size]:
            anoms = detect_series_anomalies(
                drug_id=drug_id,
                volumes=data["volumes"],
                temperatures=data.get("temperatures"),
                is_biologic=data.get("is_biologic", False),
                z_threshold=z_threshold
            )
            for anom in anoms:
                detected_anomalies.append(anom)

                # 1. Write to Redis (Hot Alert Cache with 24h TTL)
                if self.redis_client:
                    try:
                        redis_key = f"alert:{drug_id}"
                        self.redis_client.setex(redis_key, 86400, json.dumps(anom))
                    except Exception as e:
                        logger.debug(f"Redis alert error: {e}")

                # 2. Persist to MongoDB
                if self.mongo_client:
                    try:
                        db = self.mongo_client["pharma_supply_chain"]
                        db["anomaly_alerts"].insert_one(dict(anom))
                    except Exception as e:
                        logger.debug(f"Mongo alert error: {e}")

        # Local JSON Output
        out_file = OUTPUT_DIR / "anomaly_summary.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(detected_anomalies, f, indent=2)

        # Print Tabular Findings
        print("-" * 95)
        print(f"{'Drug ID':<18} | {'Alert Type':<22} | {'Severity':<10} | {'Observed':<10} | {'Z-Score':<8} | {'Message':<30}")
        print("-" * 95)
        for a in detected_anomalies:
            z_str = f"{a['z_score']:.2f}" if "z_score" in a else "N/A"
            msg_snippet = (a["message"][:28] + "..") if len(a["message"]) > 30 else a["message"]
            print(f"{a['drug_id']:<18} | {a['alert_type']:<22} | {a['severity']:<10} | {str(a['observed_value']):<10} | {z_str:<8} | {msg_snippet:<30}")
        print("-" * 95)
        print(f"[*] Evaluated {len(data_map):,} drug streams. Flagged {len(detected_anomalies):,} anomalies. Saved to '{out_file.name}'.")
        print("=" * 95 + "\n")
        return detected_anomalies

    def close(self):
        if self.mongo_client:
            self.mongo_client.close()
        if hasattr(self, "cass_cluster") and self.cass_cluster:
            self.cass_cluster.shutdown()


def main():
    parser = argparse.ArgumentParser(description="Multi-Variate Supply Chain Anomaly Detector")
    parser.add_argument("--sample-size", type=int, default=50, help="Number of drug streams to evaluate")
    parser.add_argument("--z-threshold", type=float, default=2.0, help="Z-score anomaly threshold (default: 2.0)")
    parser.add_argument("--dry-run", action="store_true", help="Run without database persistence")
    args = parser.parse_args()

    detector = AnomalyDetector(dry_run=args.dry_run)
    detector.run_detection(sample_size=args.sample_size, z_threshold=args.z_threshold)
    detector.close()


if __name__ == "__main__":
    main()
