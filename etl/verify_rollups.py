"""
Verification and Trend Visualizer for Cassandra daily_rollups.
Queries the analytical daily_rollups table to verify data integrity and print summary trends.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("VerifyRollups")

CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "pharma_telemetry")


def verify_rollups(drug_id: str = None, region: str = None, limit: int = 15):
    from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
    from cassandra.policies import RoundRobinPolicy

    profile = ExecutionProfile(load_balancing_policy=RoundRobinPolicy(), request_timeout=30.0)
    cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT, execution_profiles={EXEC_PROFILE_DEFAULT: profile}, protocol_version=5)
    session = cluster.connect(CASSANDRA_KEYSPACE)

    print("\n" + "=" * 95)
    print("              PHASE 3 ETL AUDIT: CASSANDRA DAILY_ROLLUPS VERIFICATION")
    print("=" * 95)

    try:
        # 1. Total Rollup Count Check
        count_row = session.execute("SELECT count(*) FROM daily_rollups;").one()
        total_records = count_row[0] if count_row else 0
        print(f"[*] Total Daily Rollup Records in '{CASSANDRA_KEYSPACE}.daily_rollups': {total_records:,}")

        if total_records == 0:
            print("[!] Table is currently empty. Run 'python etl/rollup_job.py' first.")
            cluster.shutdown()
            return False

        # 2. If specific drug_id & region provided, query exact partition
        if drug_id and region:
            print(f"\n[*] Querying Partition: drug_id='{drug_id}', region='{region}' (Limit: {limit})")
            cql = session.prepare("""
                SELECT drug_id, region, rollup_date, total_volume, avg_stock, event_count, stockout_count, avg_temperature, excursion_count
                FROM daily_rollups
                WHERE drug_id = ? AND region = ?
                LIMIT ?;
            """)
            rows = list(session.execute(cql, (drug_id, region, limit)))
        else:
            # Sample rollups across partitions
            print(f"\n[*] Sampling Top {limit} Rollup Records:")
            cql = f"""
                SELECT drug_id, region, rollup_date, total_volume, avg_stock, event_count, stockout_count, avg_temperature, excursion_count
                FROM daily_rollups
                LIMIT {limit};
            """
            rows = list(session.execute(cql))

        # Format tabular output
        print("-" * 95)
        print(f"{'Drug ID':<18} | {'Region':<10} | {'Date':<10} | {'Volume':<7} | {'Avg Stock':<10} | {'Events':<6} | {'Stockouts':<9} | {'Avg Temp':<8}")
        print("-" * 95)
        for r in rows:
            print(f"{r.drug_id:<18} | {r.region:<10} | {str(r.rollup_date):<10} | {r.total_volume:<7} | {r.avg_stock:<10.1f} | {r.event_count:<6} | {r.stockout_count:<9} | {r.avg_temperature:<6.1f}C")
        print("-" * 95)

        # 3. Quick aggregate check
        distinct_drugs = session.execute("SELECT DISTINCT drug_id, region FROM daily_rollups;").all()
        print(f"[*] Unique (Drug, Region) Analytical Partitions: {len(distinct_drugs):,}")

        print("\n[SUCCESS] Phase 3 Cassandra Rollups table verified and operational.")
        print("=" * 95 + "\n")
        cluster.shutdown()
        return True

    except Exception as e:
        logger.error(f"Error during rollup verification: {e}", exc_info=True)
        cluster.shutdown()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Cassandra Daily Rollups")
    parser.add_argument("--drug-id", type=str, default=None, help="Target drug ID to filter")
    parser.add_argument("--region", type=str, default=None, help="Target region to filter (e.g. Northeast, Midwest)")
    parser.add_argument("--limit", type=int, default=15, help="Number of rows to display")
    args = parser.parse_args()

    success = verify_rollups(drug_id=args.drug_id, region=args.region, limit=args.limit)
    sys.exit(0 if success else 1)

