"""
Integration Tests: Cassandra ETL Daily Rollups Store.
Validates table schema, partitioned wide-column writes, and clustered primary key lookups.
"""

import os
from datetime import date
import pytest
from dotenv import load_dotenv

load_dotenv()

CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "pharma_telemetry")


@pytest.fixture(scope="module")
def cassandra_session():
    """Connects to live Cassandra instance."""
    import socket
    try:
        with socket.create_connection((CASSANDRA_HOST, CASSANDRA_PORT), timeout=0.2):
            from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
            from cassandra.policies import RoundRobinPolicy

            profile = ExecutionProfile(load_balancing_policy=RoundRobinPolicy(), request_timeout=2.0)
            cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT, execution_profiles={EXEC_PROFILE_DEFAULT: profile}, protocol_version=5, connect_timeout=0.5)
            session = cluster.connect(CASSANDRA_KEYSPACE)
            yield session
            cluster.shutdown()
    except Exception as e:
        pytest.skip(f"Cassandra is not reachable at {CASSANDRA_HOST}:{CASSANDRA_PORT}: {e}")


@pytest.mark.integration
class TestETLCassandraIntegration:
    def test_daily_rollups_table_when_keyspace_inspected_should_exist(self, cassandra_session):
        # Arrange & Act
        cql = f"""
            SELECT table_name FROM system_schema.tables
            WHERE keyspace_name = '{CASSANDRA_KEYSPACE}' AND table_name = 'daily_rollups';
        """
        rows = list(cassandra_session.execute(cql))

        # Assert
        assert len(rows) == 1, "daily_rollups table must exist in pharma_telemetry keyspace"
        assert rows[0].table_name == "daily_rollups"

    def test_rollup_insert_when_partition_written_should_be_retrievable_by_composite_key(self, cassandra_session):
        # Arrange
        test_drug = "TEST-DRUG--999"
        test_region = "Northeast"
        test_date = date(2026, 9, 1)

        insert_cql = cassandra_session.prepare("""
            INSERT INTO daily_rollups (
                drug_id, region, rollup_date, total_volume, avg_stock,
                event_count, stockout_count, avg_temperature, excursion_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """)
        cassandra_session.execute(insert_cql, (
            test_drug, test_region, test_date, 150, 45.5, 10, 2, 20.5, 0
        ))

        # Act
        select_cql = cassandra_session.prepare("""
            SELECT drug_id, region, rollup_date, total_volume, avg_stock, event_count, stockout_count, avg_temperature, excursion_count
            FROM daily_rollups
            WHERE drug_id = ? AND region = ? AND rollup_date = ?;
        """)
        row = cassandra_session.execute(select_cql, (test_drug, test_region, test_date)).one()

        # Assert
        assert row is not None
        assert row.drug_id == test_drug
        assert row.region == test_region
        assert row.rollup_date == test_date
        assert row.total_volume == 150
        assert row.avg_stock == 45.5
        assert row.event_count == 10
        assert row.stockout_count == 2

        # Teardown
        delete_cql = cassandra_session.prepare("DELETE FROM daily_rollups WHERE drug_id = ? AND region = ? AND rollup_date = ?;")
        cassandra_session.execute(delete_cql, (test_drug, test_region, test_date))
