"""
Database Connection Manager and Client Factory for FastAPI Backend.
Manages connection pools for MongoDB, Cassandra, Neo4j, and Redis with health check diagnostics
and graceful fallback handling for local development / testing.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
STAGED_DIR = PROJECT_ROOT / "data-ingestion" / "staged"
OUTPUT_DIR = PROJECT_ROOT / "ml" / "output"

load_dotenv()
logger = logging.getLogger("DatabaseClients")


class DatabaseClients:
    def __init__(self):
        self.redis = None
        self.mongo = None
        self.cassandra = None
        self.cass_cluster = None
        self.neo4j = None

        # Environment Configurations
        self.redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))

        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")
        self.mongo_db_name = os.getenv("MONGO_DB", "pharma_supply_chain")

        self.cass_host = os.getenv("CASSANDRA_HOST", "127.0.0.1")
        self.cass_port = int(os.getenv("CASSANDRA_PORT", "9042"))
        self.cass_keyspace = os.getenv("CASSANDRA_KEYSPACE", "pharma_telemetry")

        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_pass = os.getenv("NEO4J_PASSWORD", "pharma_graph_pass")

        self.init_clients()

    def _is_port_open(self, host: str, port: int, timeout_sec: float = 0.2) -> bool:
        """Quick non-blocking TCP socket pre-check."""
        import socket
        try:
            with socket.create_connection((host, port), timeout=timeout_sec):
                return True
        except Exception:
            return False

    def init_clients(self):
        """Initializes all database drivers with timeout guards."""
        # 1. Redis
        if self._is_port_open(self.redis_host, self.redis_port):
            try:
                import redis
                self.redis = redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    decode_responses=True,
                    socket_timeout=1.5
                )
                self.redis.ping()
                logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
            except Exception as e:
                logger.warning(f"Redis connection failed ({e}). Fallback to local cache.")
                self.redis = None
        else:
            logger.info("Redis port offline. Using fast local cache fallback.")
            self.redis = None

        # 2. MongoDB
        if self._is_port_open("127.0.0.1", 27017):
            try:
                from pymongo import MongoClient
                self.mongo = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=1000)
                self.mongo.admin.command("ping")
                logger.info("Connected to MongoDB cluster.")
            except Exception as e:
                logger.warning(f"MongoDB connection failed ({e}). Fallback to staged files.")
                self.mongo = None
        else:
            logger.info("MongoDB port offline. Using staged JSON fallback.")
            self.mongo = None

        # 3. Cassandra
        if self._is_port_open(self.cass_host, self.cass_port):
            try:
                from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
                from cassandra.policies import RoundRobinPolicy
                profile = ExecutionProfile(load_balancing_policy=RoundRobinPolicy(), request_timeout=3.0)
                self.cass_cluster = Cluster(
                    [self.cass_host],
                    port=self.cass_port,
                    execution_profiles={EXEC_PROFILE_DEFAULT: profile},
                    protocol_version=5,
                    connect_timeout=1.0
                )
                self.cassandra = self.cass_cluster.connect(self.cass_keyspace)
                logger.info(f"Connected to Cassandra at {self.cass_host}:{self.cass_port} [{self.cass_keyspace}]")
            except Exception as e:
                logger.warning(f"Cassandra connection failed ({e}). Fallback to simulated rollups.")
                self.cassandra = None
        else:
            logger.info("Cassandra port offline. Using analytical time-series fallback.")
            self.cassandra = None

        # 4. Neo4j
        if self._is_port_open("127.0.0.1", 7687):
            try:
                from neo4j import GraphDatabase
                self.neo4j = GraphDatabase.driver(
                    self.neo4j_uri,
                    auth=(self.neo4j_user, self.neo4j_pass),
                    connection_timeout=1.0
                )
                self.neo4j.verify_connectivity()
                logger.info(f"Connected to Neo4j at {self.neo4j_uri}")
            except Exception as e:
                logger.warning(f"Neo4j connection failed ({e}). Fallback to staged graph.")
                self.neo4j = None
        else:
            logger.info("Neo4j port offline. Using staged topology fallback.")
            self.neo4j = None

    def get_health_status(self) -> Dict[str, str]:
        """Checks liveness of each database connection."""
        status = {}
        # Redis
        try:
            if self.redis and self.redis.ping():
                status["redis"] = "ONLINE"
            else:
                status["redis"] = "OFFLINE"
        except Exception:
            status["redis"] = "OFFLINE"

        # MongoDB
        try:
            if self.mongo:
                self.mongo.admin.command("ping")
                status["mongodb"] = "ONLINE"
            else:
                status["mongodb"] = "OFFLINE"
        except Exception:
            status["mongodb"] = "OFFLINE"

        # Cassandra
        try:
            if self.cassandra:
                self.cassandra.execute("SELECT release_version FROM system.local;").one()
                status["cassandra"] = "ONLINE"
            else:
                status["cassandra"] = "OFFLINE"
        except Exception:
            status["cassandra"] = "OFFLINE"

        # Neo4j
        try:
            if self.neo4j:
                self.neo4j.verify_connectivity()
                status["neo4j"] = "ONLINE"
            else:
                status["neo4j"] = "OFFLINE"
        except Exception:
            status["neo4j"] = "OFFLINE"

        return status

    def close(self):
        """Gracefully terminates all connection pools."""
        if self.redis:
            try:
                self.redis.close()
            except Exception:
                pass
        if self.mongo:
            try:
                self.mongo.close()
            except Exception:
                pass
        if self.cass_cluster:
            try:
                self.cass_cluster.shutdown()
            except Exception:
                pass
        if self.neo4j:
            try:
                self.neo4j.close()
            except Exception:
                pass


# Global singleton instance
db_manager = DatabaseClients()
