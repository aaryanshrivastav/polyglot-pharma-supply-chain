"""
Redpanda / Kafka Event Stream Producer.
Publishes serialized JSON event batches to topics: `stock_events` and `shipment_events`.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "127.0.0.1:9092")
TOPIC_STOCK = "stock_events"
TOPIC_SHIPMENT = "shipment_events"


class StreamProducer:
    def __init__(self, brokers: str = KAFKA_BROKERS):
        self.brokers = brokers
        self.producer = None
        self._init_producer()

    def _init_producer(self):
        """Initializes confluent-kafka producer client with batching and compression."""
        logger.info(f"Connecting StreamProducer to Redpanda / Kafka at {self.brokers}...")
        try:
            from confluent_kafka import Producer
            from confluent_kafka.admin import AdminClient, NewTopic

            # Ensure topics exist
            admin = AdminClient({"bootstrap.servers": self.brokers})
            new_topics = [
                NewTopic(TOPIC_STOCK, num_partitions=3, replication_factor=1),
                NewTopic(TOPIC_SHIPMENT, num_partitions=3, replication_factor=1)
            ]
            fs = admin.create_topics(new_topics)
            for topic, f in fs.items():
                try:
                    f.result()
                    logger.info(f"Created Redpanda topic: '{topic}'")
                except Exception as e:
                    # Topic already exists or similar
                    pass

            conf = {
                "bootstrap.servers": self.brokers,
                "client.id": "pharma-stream-producer",
                "compression.type": "snappy",
                "queue.buffering.max.messages": 100000,
                "queue.buffering.max.kbytes": 2097152,
                "batch.num.messages": 1000,
                "linger.ms": 50,
                "acks": 1
            }
            self.producer = Producer(conf)
            logger.info("Confluent-Kafka producer initialized successfully.")
        except Exception as e:
            logger.warning(f"Error initializing Confluent-Kafka: {e}. Checking fallback...")
            try:
                from kafka import KafkaProducer
                self.producer = KafkaProducer(
                    bootstrap_servers=self.brokers.split(","),
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    acks=1
                )
                logger.info("Kafka-python fallback producer initialized.")
            except Exception as ex:
                logger.error(f"Failed to connect Kafka producer to {self.brokers}: {ex}")
                self.producer = None

    def delivery_report(self, err, msg):
        """Delivery report callback for confluent-kafka."""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")

    def publish_event(self, topic: str, key: str, value: dict):
        """Publishes a single event to a Kafka topic."""
        if not self.producer:
            return

        payload = json.dumps(value).encode("utf-8")
        key_bytes = key.encode("utf-8") if key else None

        if hasattr(self.producer, "produce"):  # confluent_kafka
            self.producer.produce(topic, key=key_bytes, value=payload, callback=self.delivery_report)
            self.producer.poll(0)
        else:  # kafka-python
            self.producer.send(topic, key=key_bytes, value=value)

    def publish_batch(self, stock_events: list, shipment_events: list):
        """Publishes a paired batch of stock and shipment events."""
        if not self.producer:
            logger.warning(f"Producer offline. Simulating publication of {len(stock_events)} stock & {len(shipment_events)} shipment events.")
            return

        t0 = time.time()
        for s in stock_events:
            key = f"{s['pharmacy_id']}:{s['drug_id']}"
            self.publish_event(TOPIC_STOCK, key, s)

        for sh in shipment_events:
            key = f"{sh['batch_id']}:{sh['drug_id']}"
            self.publish_event(TOPIC_SHIPMENT, key, sh)

        self.flush()
        elapsed = time.time() - t0
        total = len(stock_events) + len(shipment_events)
        throughput = total / max(0.001, elapsed)
        logger.info(f"Published batch of {total:,} events ({throughput:,.0f} msgs/sec) to Redpanda.")

    def flush(self, timeout: float = 5.0):
        """Flushes buffered messages."""
        if self.producer:
            if hasattr(self.producer, "flush"):
                self.producer.flush(timeout)

    def close(self):
        """Closes producer connection."""
        self.flush()
        logger.info("StreamProducer shut down cleanly.")


if __name__ == "__main__":
    producer = StreamProducer()
    test_stock = [{"event_id": "TEST-01", "pharmacy_id": "PHARM-TEST", "drug_id": "DRUG-TEST", "current_stock": 100}]
    test_shipment = [{"event_id": "TEST-02", "shipment_id": "SHP-TEST", "batch_id": "BAT-TEST", "drug_id": "DRUG-TEST", "temperature_celsius": 4.5}]
    producer.publish_batch(test_stock, test_shipment)
    producer.close()

