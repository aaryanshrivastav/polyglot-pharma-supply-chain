"""
ETL Rollup Job: Cassandra Raw Telemetry & Stock Events -> Daily Analytical Rollups.
Aggregates high-frequency raw events into `daily_rollups` partitioned by `((drug_id, region), rollup_date)`.
Uses plain Python + pandas for lightweight in-memory transformation without Spark overhead.
"""

import argparse
import json
import logging
import os
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
STAGED_DIR = PROJECT_ROOT / "data-ingestion" / "staged"

CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "pharma_telemetry")

# US State -> Region Mapping
STATE_TO_REGION = {
    # Northeast
    "ME": "Northeast", "NH": "Northeast", "VT": "Northeast", "MA": "Northeast",
    "RI": "Northeast", "CT": "Northeast", "NY": "Northeast", "NJ": "Northeast", "PA": "Northeast",
    # Midwest
    "OH": "Midwest", "MI": "Midwest", "IN": "Midwest", "IL": "Midwest",
    "WI": "Midwest", "MN": "Midwest", "IA": "Midwest", "MO": "Midwest",
    "ND": "Midwest", "SD": "Midwest", "NE": "Midwest", "KS": "Midwest",
    # South
    "DE": "South", "MD": "South", "DC": "South", "VA": "South",
    "WV": "South", "NC": "South", "SC": "South", "GA": "South",
    "FL": "South", "KY": "South", "TN": "South", "AL": "South",
    "MS": "South", "AR": "South", "LA": "South", "OK": "South", "TX": "South",
    # West
    "MT": "West", "ID": "West", "WY": "West", "CO": "West",
    "NM": "West", "AZ": "West", "UT": "West", "NV": "West",
    "WA": "West", "OR": "West", "CA": "West", "AK": "West", "HI": "West"
}


def load_node_region_map() -> dict:
    """Builds a mapping from node_id (pharmacy_id, etc.) to geographic region."""
    node_to_region = {}
    pharm_file = STAGED_DIR / "pharmacies.json"
    if pharm_file.exists():
        with open(pharm_file, "r", encoding="utf-8") as f:
            pharmacies = json.load(f)
            for p in pharmacies:
                state = p.get("state", "").upper()
                node_to_region[p["pharmacy_id"]] = STATE_TO_REGION.get(state, "National")
    return node_to_region


class RollupJob:
    def __init__(self, host: str = CASSANDRA_HOST, port: int = CASSANDRA_PORT, keyspace: str = CASSANDRA_KEYSPACE):
        self.host = host
        self.port = port
        self.keyspace = keyspace
        self.cluster = None
        self.session = None
        self.node_region_map = load_node_region_map()
        self._init_cassandra()

    def _init_cassandra(self):
        """Connects to Cassandra and ensures daily_rollups table exists."""
        from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
        from cassandra.policies import RoundRobinPolicy

        logger.info(f"Connecting to Cassandra at {self.host}:{self.port} (Keyspace: {self.keyspace})...")
        profile = ExecutionProfile(load_balancing_policy=RoundRobinPolicy(), request_timeout=30.0)
        self.cluster = Cluster([self.host], port=self.port, execution_profiles={EXEC_PROFILE_DEFAULT: profile}, protocol_version=5)
        self.session = self.cluster.connect()

        # Ensure keyspace exists
        self.session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
            WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}};
        """)
        self.session.set_keyspace(self.keyspace)

        # Create daily_rollups table
        logger.info("Ensuring 'daily_rollups' table schema exists...")
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS daily_rollups (
                drug_id text,
                region text,
                rollup_date date,
                total_volume int,
                avg_stock double,
                event_count int,
                stockout_count int,
                avg_temperature double,
                excursion_count int,
                PRIMARY KEY ((drug_id, region), rollup_date)
            ) WITH CLUSTERING ORDER BY (rollup_date DESC);
        """)

        self.prep_insert = self.session.prepare("""
            INSERT INTO daily_rollups (
                drug_id, region, rollup_date, total_volume, avg_stock,
                event_count, stockout_count, avg_temperature, excursion_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        logger.info("Cassandra connection & schema initialized.")

    def extract_stock_events(self) -> pd.DataFrame:
        """Extracts raw stock events from Cassandra into a Pandas DataFrame."""
        logger.info("Extracting stock events from Cassandra...")
        cql = "SELECT node_id, drug_id, event_time, current_stock, daily_demand, stockout_flag FROM stock_events_by_node;"
        try:
            rows = list(self.session.execute(cql))
            if not rows:
                logger.warning("No rows returned from stock_events_by_node.")
                return pd.DataFrame()
            
            data = [{
                "node_id": r.node_id,
                "drug_id": r.drug_id,
                "event_time": r.event_time,
                "current_stock": r.current_stock,
                "daily_demand": r.daily_demand,
                "stockout_flag": 1 if r.stockout_flag else 0
            } for r in rows]
            df = pd.DataFrame(data)
            logger.info(f"Extracted {len(df):,} raw stock events.")
            return df
        except Exception as e:
            logger.error(f"Error querying stock_events_by_node: {e}")
            return pd.DataFrame()

    def extract_shipment_telemetry(self) -> pd.DataFrame:
        """Extracts shipment telemetry events from Cassandra for temperature/excursion aggregation."""
        logger.info("Extracting shipment telemetry from Cassandra...")
        cql = "SELECT drug_id, event_time, temperature_celsius, is_excursion FROM shipment_telemetry_by_batch;"
        try:
            rows = list(self.session.execute(cql))
            if not rows:
                return pd.DataFrame()
            data = [{
                "drug_id": r.drug_id,
                "event_time": r.event_time,
                "temperature_celsius": r.temperature_celsius,
                "is_excursion": 1 if r.is_excursion else 0
            } for r in rows]
            df = pd.DataFrame(data)
            logger.info(f"Extracted {len(df):,} shipment telemetry records.")
            return df
        except Exception as e:
            logger.warning(f"Note on shipment telemetry extraction: {e}")
            return pd.DataFrame()

    def transform_and_aggregate(self, stock_df: pd.DataFrame, telemetry_df: pd.DataFrame) -> pd.DataFrame:
        """Performs rollup aggregation by (drug_id, region, rollup_date)."""
        if stock_df.empty:
            logger.warning("Stock DataFrame is empty, skipping aggregation.")
            return pd.DataFrame()

        logger.info("Mapping regions and aggregating daily rollups...")
        # 1. Map Region & Date
        stock_df["region"] = stock_df["node_id"].map(lambda nid: self.node_region_map.get(nid, "National"))
        stock_df["rollup_date"] = pd.to_datetime(stock_df["event_time"]).dt.date

        # 2. Stock Aggregations
        stock_agg = stock_df.groupby(["drug_id", "region", "rollup_date"]).agg(
            total_volume=("daily_demand", "sum"),
            avg_stock=("current_stock", "mean"),
            event_count=("current_stock", "count"),
            stockout_count=("stockout_flag", "sum")
        ).reset_index()

        # Round avg_stock
        stock_agg["avg_stock"] = stock_agg["avg_stock"].round(2)

        # 3. Telemetry Aggregations (if available)
        if not telemetry_df.empty:
            telemetry_df["rollup_date"] = pd.to_datetime(telemetry_df["event_time"]).dt.date
            telem_agg = telemetry_df.groupby(["drug_id", "rollup_date"]).agg(
                avg_temperature=("temperature_celsius", "mean"),
                excursion_count=("is_excursion", "sum")
            ).reset_index()
            telem_agg["avg_temperature"] = telem_agg["avg_temperature"].round(2)
            
            # Merge with stock_agg
            merged = pd.merge(stock_agg, telem_agg, on=["drug_id", "rollup_date"], how="left")
            merged["avg_temperature"] = merged["avg_temperature"].fillna(21.0)
            merged["excursion_count"] = merged["excursion_count"].fillna(0).astype(int)
        else:
            merged = stock_agg
            merged["avg_temperature"] = 21.0
            merged["excursion_count"] = 0

        logger.info(f"Generated {len(merged):,} daily rollup records across all regions.")
        return merged

    def load_rollups(self, rollup_df: pd.DataFrame, max_in_flight: int = 64):
        """Loads aggregated summary rows into Cassandra daily_rollups table using bounded async execution."""
        if rollup_df.empty:
            logger.warning("No rollup rows to insert.")
            return 0

        logger.info(f"Writing {len(rollup_df):,} rollup rows into Cassandra 'daily_rollups'...")
        in_flight = deque()
        inserted_count = 0
        t0 = time.time()

        for _, row in rollup_df.iterrows():
            params = (
                str(row["drug_id"]),
                str(row["region"]),
                row["rollup_date"],
                int(row["total_volume"]),
                float(row["avg_stock"]),
                int(row["event_count"]),
                int(row["stockout_count"]),
                float(row["avg_temperature"]),
                int(row["excursion_count"])
            )

            # Backpressure management
            while len(in_flight) >= max_in_flight:
                fut = in_flight.popleft()
                fut.result()
                inserted_count += 1

            fut = self.session.execute_async(self.prep_insert, params)
            in_flight.append(fut)

        # Drain remaining
        while in_flight:
            fut = in_flight.popleft()
            fut.result()
            inserted_count += 1

        elapsed = time.time() - t0
        logger.info(f"Successfully inserted {inserted_count:,} rollup rows in {elapsed:.2f}s ({inserted_count/max(0.01, elapsed):,.0f} rows/s).")
        return inserted_count

    def run_pipeline(self) -> int:
        """Executes full ETL aggregation pipeline."""
        print("=" * 80)
        print("          PHASE 3: DATA ENGINEERING ROLLUP AGGREGATION PIPELINE                ")
        print("=" * 80)
        stock_df = self.extract_stock_events()
        telem_df = self.extract_shipment_telemetry()
        rollup_df = self.transform_and_aggregate(stock_df, telem_df)
        inserted = self.load_rollups(rollup_df)
        print("=" * 80)
        print(f"  ETL Rollup Summary: {inserted:,} daily summary records populated into Cassandra.")
        print("=" * 80)
        return inserted

    def close(self):
        if self.cluster:
            self.cluster.shutdown()


if __name__ == "__main__":
    job = RollupJob()
    job.run_pipeline()
    job.close()

