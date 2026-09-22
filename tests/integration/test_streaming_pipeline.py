"""
Integration Tests: Streaming Storage Sinks (Cassandra & Redis).
Validates keyspace schemas, wide-column clustering, and hot-state cache TTL.
"""

import os
import pytest
from dotenv import load_dotenv

load_dotenv()

CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "pharma_telemetry")
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


@pytest.mark.integration
class TestStreamingStorageIntegration:
    def test_cassandra_telemetry_keyspace_when_connected_should_contain_stock_and_telemetry_tables(self):
        # Arrange
        import socket
        try:
            with socket.create_connection((CASSANDRA_HOST, CASSANDRA_PORT), timeout=0.2):
                from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
                from cassandra.policies import RoundRobinPolicy

                prof = ExecutionProfile(load_balancing_policy=RoundRobinPolicy(), request_timeout=2.0)
                cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT, execution_profiles={EXEC_PROFILE_DEFAULT: prof}, protocol_version=5, connect_timeout=0.5)
                session = cluster.connect()
        except Exception as e:
            pytest.skip(f"Cassandra not reachable at {CASSANDRA_HOST}:{CASSANDRA_PORT}: {e}")

        # Act
        keyspaces = [k.name for k in cluster.metadata.keyspaces.values()]
        assert CASSANDRA_KEYSPACE in keyspaces, f"Keyspace {CASSANDRA_KEYSPACE} not found"

        session.set_keyspace(CASSANDRA_KEYSPACE)
        tables = cluster.metadata.keyspaces[CASSANDRA_KEYSPACE].tables.keys()

        # Assert
        assert "stock_events_by_node" in tables, "Expected stock_events_by_node table"
        assert "shipment_telemetry_by_batch" in tables, "Expected shipment_telemetry_by_batch table"
        cluster.shutdown()

    def test_redis_hot_state_cache_when_connected_should_support_hash_writes_and_ttl(self):
        # Arrange
        import socket
        try:
            with socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=0.2):
                import redis
                r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, socket_timeout=0.5)
                r.ping()
        except Exception as e:
            pytest.skip(f"Redis not reachable at {REDIS_HOST}:{REDIS_PORT}: {e}")

        # Act
        test_key = "stock:TEST_PHARM:TEST_DRUG"
        r.hset(test_key, mapping={"current_stock": "100", "daily_demand": "10", "stockout_flag": "0"})
        r.expire(test_key, 60)

        # Assert
        assert r.hget(test_key, "current_stock") == "100"
        assert r.ttl(test_key) > 0

        # Teardown
        r.delete(test_key)
        r.close()
