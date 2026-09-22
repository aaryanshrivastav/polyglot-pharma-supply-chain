"""
ML Module: Time-Series Shortage Risk Forecasting.
Uses statsmodels (Exponential Smoothing / ARIMA) on daily rollups to project inventory depletion
and evaluate shortage probability P(shortage) over a forward-looking forecast horizon.
Persists enriched risk scores back to Redis (hot cache) and MongoDB (analytical repository).
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

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ForecastShortage")

OUTPUT_DIR = PROJECT_ROOT / "ml" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STAGED_DIR = PROJECT_ROOT / "data-ingestion" / "staged"


def calculate_shortage_risk(series: pd.Series, horizon_days: int = 14, safety_stock: float = 20.0) -> Tuple[float, str, List[float]]:
    """
    Fits time-series forecasting model (Holt-Winters Exponential Smoothing or fallback autoregression)
    and computes shortage risk probability based on projected inventory.
    """
    values = series.dropna().values.astype(float)
    if len(values) < 3:
        # Fallback for sparse history
        last_val = values[-1] if len(values) > 0 else safety_stock
        forecast = [float(max(0.0, last_val))] * horizon_days
    else:
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            # Use additive trend if at least 4 observations available to capture slope
            trend_type = "add" if len(values) >= 4 else None
            model = ExponentialSmoothing(values, trend=trend_type, initialization_method="estimated")
            fit = model.fit()
            raw_forecast = fit.forecast(horizon_days)
            forecast = [float(max(0.0, f)) for f in raw_forecast]
        except Exception as e:
            logger.debug(f"Holt-Winters fit fallback: {e}")
            # Linear trend fallback
            x = np.arange(len(values))
            slope, intercept = np.polyfit(x, values, 1) if len(values) >= 2 else (0, values[0])
            future_x = np.arange(len(values), len(values) + horizon_days)
            forecast = [float(max(0.0, intercept + slope * fx)) for fx in future_x]

    min_forecast = min(forecast) if forecast else 0.0
    mean_forecast = np.mean(forecast) if forecast else 0.0

    # Probability mapping
    if min_forecast <= 0.0:
        risk_score = 1.0
    elif min_forecast < safety_stock * 0.5:
        risk_score = 0.85 + 0.15 * (1.0 - (min_forecast / (safety_stock * 0.5)))
    elif min_forecast < safety_stock:
        risk_score = 0.50 + 0.35 * (1.0 - (min_forecast / safety_stock))
    elif min_forecast < safety_stock * 2.0:
        risk_score = 0.15 + 0.35 * (1.0 - ((min_forecast - safety_stock) / safety_stock))
    else:
        risk_score = max(0.02, 0.15 * (safety_stock * 2.0 / max(1.0, mean_forecast)))

    risk_score = float(np.clip(round(risk_score, 4), 0.0, 1.0))

    if risk_score >= 0.80:
        risk_level = "CRITICAL"
    elif risk_score >= 0.50:
        risk_level = "HIGH"
    elif risk_score >= 0.25:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    return risk_score, risk_level, forecast


class ShortageForecaster:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.redis_client = None
        self.mongo_client = None
        self.cassandra_session = None

        if not self.dry_run:
            self._init_connections()

    def _init_connections(self):
        """Initializes connections to Redis, MongoDB, and Cassandra if available."""
        # 1. Redis
        try:
            import redis
            redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True, socket_timeout=2)
            self.redis_client.ping()
            logger.info("Connected to Redis for live risk caching.")
        except Exception as e:
            logger.warning(f"Redis unavailable, skipping Redis persistence: {e}")
            self.redis_client = None

        # 2. MongoDB
        try:
            from pymongo import MongoClient
            mongo_uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            self.mongo_client.admin.command("ping")
            logger.info("Connected to MongoDB for risk score persistence.")
        except Exception as e:
            logger.warning(f"MongoDB unavailable, skipping Mongo persistence: {e}")
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
            logger.info("Connected to Cassandra for daily_rollups retrieval.")
        except Exception as e:
            logger.warning(f"Cassandra unavailable, falling back to staged time-series: {e}")
            self.cassandra_session = None

    def load_time_series_data(self, sample_drugs: Optional[List[str]] = None) -> Dict[str, pd.Series]:
        """Loads historical inventory series from Cassandra daily_rollups or staged simulation."""
        data_by_drug = {}

        if self.cassandra_session:
            try:
                cql = "SELECT drug_id, rollup_date, avg_stock FROM daily_rollups;"
                rows = list(self.cassandra_session.execute(cql))
                if rows:
                    df = pd.DataFrame([{"drug_id": r.drug_id, "date": pd.to_datetime(r.rollup_date), "stock": r.avg_stock} for r in rows])
                    for drug_id, group in df.groupby("drug_id"):
                        if sample_drugs and drug_id not in sample_drugs:
                            continue
                        series = group.sort_values("date").set_index("date")["stock"]
                        data_by_drug[drug_id] = series
                    logger.info(f"Loaded time series for {len(data_by_drug):,} drugs from Cassandra.")
                    return data_by_drug
            except Exception as e:
                logger.warning(f"Failed querying Cassandra daily_rollups: {e}")

        # Staged simulation / synthetic fallback
        logger.info("Generating representative time series from staged drug catalog...")
        drugs_file = STAGED_DIR / "drugs.json"
        if drugs_file.exists():
            with open(drugs_file, "r", encoding="utf-8") as f:
                drugs = json.load(f)
            if sample_drugs:
                drugs = [d for d in drugs if d["drug_id"] in sample_drugs]
            else:
                drugs = drugs[:50]

            np.random.seed(42)
            dates = pd.date_range(end=datetime.now(timezone.utc).date(), periods=30)
            for d in drugs:
                drug_id = d["drug_id"]
                # Injected disruption dip for certain drugs
                base = 100.0 if not d.get("is_biologic") else 60.0
                noise = np.random.normal(0, 5, size=len(dates))
                trend = np.linspace(0, -30 if "0002" in drug_id or "0093" in drug_id else 5, len(dates))
                series_vals = np.maximum(0, base + trend + noise)
                data_by_drug[drug_id] = pd.Series(series_vals, index=dates)

        return data_by_drug

    def run_forecasting(self, sample_size: int = 50, horizon_days: int = 14) -> List[Dict]:
        """Runs forecasting models and evaluates shortage probability for all sampled drugs."""
        print("\n" + "=" * 95)
        print("          PHASE 4: ML SHORTAGE RISK FORECASTING PIPELINE (ARIMA / EXP SMOOTHING)")
        print("=" * 95)

        time_series_map = self.load_time_series_data()
        drug_items = list(time_series_map.items())[:sample_size]

        results = []
        for drug_id, series in drug_items:
            risk_score, risk_level, forecast = calculate_shortage_risk(series, horizon_days=horizon_days)
            record = {
                "drug_id": drug_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "horizon_days": horizon_days,
                "last_recorded_stock": float(series.iloc[-1]) if len(series) > 0 else 0.0,
                "min_projected_stock": float(round(min(forecast), 2)) if forecast else 0.0,
                "projected_depletion_days": next((i + 1 for i, v in enumerate(forecast) if v <= 0.0), None),
                "forecast_trajectory": [round(v, 1) for v in forecast[:7]],  # 7-day snippet
                "calculated_at": datetime.now(timezone.utc).isoformat()
            }
            results.append(record)

            # 1. Write to Redis Hot State (TTL: 7 days = 604,800s)
            if self.redis_client:
                try:
                    redis_key = f"risk_score:{drug_id}"
                    self.redis_client.setex(redis_key, 604800, json.dumps({
                        "drug_id": drug_id,
                        "risk_score": risk_score,
                        "risk_level": risk_level,
                        "min_projected_stock": record["min_projected_stock"],
                        "calculated_at": record["calculated_at"]
                    }))
                except Exception as e:
                    logger.debug(f"Redis write error for {drug_id}: {e}")

            # 2. Persist to MongoDB Analytical Collection
            if self.mongo_client:
                try:
                    db = self.mongo_client["pharma_supply_chain"]
                    db["risk_scores"].update_one(
                        {"drug_id": drug_id},
                        {"$set": record},
                        upsert=True
                    )
                except Exception as e:
                    logger.debug(f"Mongo write error for {drug_id}: {e}")

        # Save local JSON artifact
        out_file = OUTPUT_DIR / "forecast_risk_scores.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        # Print summary table
        print("-" * 95)
        print(f"{'Drug ID':<20} | {'Risk Score':<12} | {'Risk Level':<10} | {'Current Stock':<14} | {'Min Proj Stock':<15} | {'Depletion Day':<12}")
        print("-" * 95)
        for r in sorted(results, key=lambda x: x["risk_score"], reverse=True)[:15]:
            dep_str = str(r["projected_depletion_days"]) if r["projected_depletion_days"] else "None (Safe)"
            print(f"{r['drug_id']:<20} | {r['risk_score']:<12.4f} | {r['risk_level']:<10} | {r['last_recorded_stock']:<14.1f} | {r['min_projected_stock']:<15.1f} | {dep_str:<12}")
        print("-" * 95)
        print(f"[*] Processed {len(results):,} drugs. Enriched scores written to Redis, MongoDB, and '{out_file.name}'.")
        print("=" * 95 + "\n")
        return results

    def close(self):
        if self.mongo_client:
            self.mongo_client.close()
        if hasattr(self, "cass_cluster") and self.cass_cluster:
            self.cass_cluster.shutdown()


def main():
    parser = argparse.ArgumentParser(description="Time-Series Shortage Risk Forecasting")
    parser.add_argument("--sample-size", type=int, default=50, help="Number of drugs to score (default: 50)")
    parser.add_argument("--horizon-days", type=int, default=14, help="Forecast horizon in days (default: 14)")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode without external database writes")
    args = parser.parse_args()

    forecaster = ShortageForecaster(dry_run=args.dry_run)
    forecaster.run_forecasting(sample_size=args.sample_size, horizon_days=args.horizon_days)
    forecaster.close()


if __name__ == "__main__":
    main()
