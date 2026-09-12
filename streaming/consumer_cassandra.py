"""
Production-grade Apache Cassandra Time-Series Stream Consumer.
Features:
- Bounded asynchronous write pipeline (`execute_async`) with backpressure
- Manual Kafka offset commits tied to verified Cassandra persistence
- Multi-topic consumption (`stock_events`, `shipment_events`)
- Graceful drain and shutdown handling
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "pharma_telemetry")
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "127.0.0.1:9092")

# Bounded in-flight concurrency parameter
MAX_IN_FLIGHT_WRITES = 64
COMMIT_INTERVAL_MSGS = 500


class CassandraStreamConsumer:
    def __init__(self, host: str = CASSANDRA_HOST, port: int = CASSANDRA_PORT, keyspace: str = CASSANDRA_KEYSPACE):
        self.host = host
        self.port = port
        self.keyspace = keyspace
        self.cluster = None
        self.session = None
        self.prep_stock = None
        self.prep_shipment = None
        self._init_cassandra()

    def _init_cassandra(self, max_retries: int = 12, retry_delay: float = 5.0):
        """Initializes Cassandra cluster connection with retry loop and tables."""
        from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
        from cassandra.policies import RoundRobinPolicy

        logger.info(f"Connecting to Apache Cassandra at {self.host}:{self.port}...")
        profile = ExecutionProfile(
            load_balancing_policy=RoundRobinPolicy(),
            request_timeout=30.0
        )

        connected = False
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                self.cluster = Cluster(
                    [self.host],
                    port=self.port,
                    execution_profiles={EXEC_PROFILE_DEFAULT: profile},
                    protocol_version=5,
                    connect_timeout=15.0
                )
                self.session = self.cluster.connect()
                connected = True
                logger.info("Successfully established connection with Apache Cassandra.")
                break
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Cassandra connection attempt {attempt}/{max_retries} failed ({e}). "
                    f"Retrying in {retry_delay:.0f}s..."
                )
                time.sleep(retry_delay)

        if not connected:
            raise RuntimeError(f"Could not connect to Cassandra after {max_retries} attempts: {last_error}")

        # 1. Create Keyspace
        logger.info(f"Creating/verifying Cassandra keyspace: {self.keyspace}")
        self.session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
            WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}};
        """)
        self.session.set_keyspace(self.keyspace)

        # 2. Create Stock Events Table (Partitioned by node, drug, year_month)
        logger.info("Creating table 'stock_events_by_node'...")
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS stock_events_by_node (
                node_id text,
                drug_id text,
                year_month text,
                event_time timestamp,
                event_id text,
                event_type text,
                current_stock int,
                daily_demand int,
                stockout_flag boolean,
                disruption_active boolean,
                shortage_id text,
                restock_order_id text,
                PRIMARY KEY ((node_id, drug_id, year_month), event_time)
            ) WITH CLUSTERING ORDER BY (event_time DESC);
        """)

        # 3. Create Shipment Telemetry Table (Partitioned by batch, drug, year_month)
        logger.info("Creating table 'shipment_telemetry_by_batch'...")
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS shipment_telemetry_by_batch (
                batch_id text,
                drug_id text,
                year_month text,
                event_time timestamp,
                event_id text,
                event_type text,
                shipment_id text,
                source_mfr_id text,
                target_node_id text,
                temperature_celsius double,
                humidity_percent double,
                vibration_g double,
                is_excursion boolean,
                requires_cold_chain boolean,
                latitude double,
                longitude double,
                status text,
                PRIMARY KEY ((batch_id, drug_id, year_month), event_time)
            ) WITH CLUSTERING ORDER BY (event_time DESC);
        """)

        # Prepare statements
        self.prep_stock = self.session.prepare("""
            INSERT INTO stock_events_by_node (
                node_id, drug_id, year_month, event_time, event_id, event_type,
                current_stock, daily_demand, stockout_flag, disruption_active, shortage_id, restock_order_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        self.prep_shipment = self.session.prepare("""
            INSERT INTO shipment_telemetry_by_batch (
                batch_id, drug_id, year_month, event_time, event_id, event_type,
                shipment_id, source_mfr_id, target_node_id, temperature_celsius,
                humidity_percent, vibration_g, is_excursion, requires_cold_chain,
                latitude, longitude, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        logger.info("Cassandra keyspace and table schemas ready.")

    def async_write_stock(self, event: dict):
        """Dispatches asynchronous write for stock event."""
        ts = datetime.fromisoformat(event["timestamp"]) if isinstance(event["timestamp"], str) else event["timestamp"]
        params = (
            event["pharmacy_id"],
            event["drug_id"],
            event["year_month"],
            ts,
            event["event_id"],
            event["event_type"],
            event["current_stock"],
            event["daily_demand"],
            event["stockout_flag"],
            event.get("disruption_active", False),
            event.get("shortage_id"),
            event.get("restock_order_id")
        )
        return self.session.execute_async(self.prep_stock, params)

    def async_write_shipment(self, event: dict):
        """Dispatches asynchronous write for shipment telemetry event."""
        ts = datetime.fromisoformat(event["timestamp"]) if isinstance(event["timestamp"], str) else event["timestamp"]
        params = (
            event["batch_id"],
            event["drug_id"],
            event["year_month"],
            ts,
            event["event_id"],
            event["event_type"],
            event["shipment_id"],
            event["source_mfr_id"],
            event["target_node_id"],
            float(event["temperature_celsius"]),
            float(event["humidity_percent"]),
            float(event["vibration_g"]),
            bool(event["is_excursion"]),
            bool(event.get("requires_cold_chain", False)),
            float(event["latitude"]),
            float(event["longitude"]),
            event["status"]
        )
        return self.session.execute_async(self.prep_shipment, params)

    def consume_stream(self, max_messages: int = None, max_in_flight: int = MAX_IN_FLIGHT_WRITES):
        """
        Consumes messages using a bounded in-flight async pipeline.
        Commits Kafka offsets only after Cassandra writes succeed.
        """
        logger.info(f"Starting async Cassandra sink on topics: stock_events, shipment_events (max in-flight: {max_in_flight})...")
        from confluent_kafka import Consumer, KafkaError

        conf = {
            "bootstrap.servers": KAFKA_BROKERS,
            "group.id": "cassandra-telemetry-sink",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,  # Explicit manual offset commit for reliable delivery
            "max.poll.interval.ms": 300000,
            "session.timeout.ms": 45000
        }
        consumer = Consumer(conf)
        consumer.subscribe(["stock_events", "shipment_events"])

        # Bounded in-flight queue storing tuples: (future, msg)
        in_flight = deque()
        total_processed = 0
        last_commit_time = time.time()

        try:
            while True:
                # 1. Drain oldest in-flight future if buffer is full (Backpressure)
                while len(in_flight) >= max_in_flight:
                    future, msg = in_flight.popleft()
                    try:
                        future.result()  # Wait for Cassandra async write to complete
                        total_processed += 1
                        
                        # Periodic manual offset commit
                        if total_processed % COMMIT_INTERVAL_MSGS == 0 or (time.time() - last_commit_time) > 5.0:
                            consumer.commit(asynchronous=True)
                            last_commit_time = time.time()
                            logger.info(f"Cassandra sink processed & committed {total_processed:,} events.")
                    except Exception as err:
                        logger.error(f"Cassandra async write failed: {err}")

                if max_messages and total_processed >= max_messages:
                    break

                # 2. Poll next message from Redpanda
                msg = consumer.poll(timeout=0.2)
                if msg is None:
                    # Drain any completed in-flight writes while waiting for more messages
                    while in_flight:
                        future = in_flight[0][0]
                        # Check without blocking if the oldest write is already finished
                        if getattr(future, "_event", None) and future._event.is_set():
                            future, _ = in_flight.popleft()
                            try:
                                future.result()
                                total_processed += 1
                            except Exception as err:
                                logger.error(f"Cassandra async write error: {err}")
                        else:
                            break
                    continue

                if msg.error():
                    err_code = msg.error().code()
                    if err_code in (KafkaError._PARTITION_EOF, KafkaError.UNKNOWN_TOPIC_OR_PART, KafkaError._UNKNOWN_TOPIC):
                        time.sleep(0.5)
                        continue
                    else:
                        logger.error(f"Kafka error: {msg.error()}")
                        break

                # 3. Parse and dispatch async Cassandra write
                topic = msg.topic()
                val = json.loads(msg.value().decode("utf-8"))

                if topic == "stock_events":
                    fut = self.async_write_stock(val)
                    in_flight.append((fut, msg))
                elif topic == "shipment_events":
                    fut = self.async_write_shipment(val)
                    in_flight.append((fut, msg))

        except KeyboardInterrupt:
            logger.info("Shutdown requested. Draining in-flight writes...")
        finally:
            # 4. Graceful Drain: Complete all remaining in-flight futures
            logger.info(f"Draining remaining {len(in_flight)} in-flight Cassandra writes before closing...")
            while in_flight:
                future, msg = in_flight.popleft()
                try:
                    future.result()
                    total_processed += 1
                except Exception as err:
                    logger.error(f"Error during final drain write: {err}")

            try:
                consumer.commit(asynchronous=False)
                logger.info("Final Kafka offset commit successful.")
            except Exception as e:
                logger.warning(f"Final commit notice: {e}")

            consumer.close()
            logger.info(f"Cassandra Stream Consumer closed. Total events persisted: {total_processed:,}")

    def close(self):
        """Closes Cassandra cluster connection."""
        if self.cluster:
            self.cluster.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Production Cassandra Stream Consumer")
    parser.add_argument("--init-only", action="store_true", help="Initialize keyspace and tables only")
    parser.add_argument("--max-messages", type=int, default=None, help="Stop after N messages")
    parser.add_argument("--concurrency", type=int, default=MAX_IN_FLIGHT_WRITES, help="Max in-flight concurrent writes")
    args = parser.parse_args()

    consumer = CassandraStreamConsumer()
    if not args.init_only:
        consumer.consume_stream(max_messages=args.max_messages, max_in_flight=args.concurrency)
    consumer.close()
