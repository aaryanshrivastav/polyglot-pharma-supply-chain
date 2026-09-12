"""
Redis In-Memory Hot State Stream Consumer.
Consumes `stock_events` from Redpanda, updating low-latency `stock:{pharmacy_id}:{drug_id}`
hashes with expiration TTLs and managing the `active_stockouts` real-time alert set.
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None) or None
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "127.0.0.1:9092")

DEFAULT_STOCK_TTL_SECONDS = 7 * 86400  # 7 days expiration


class RedisStreamConsumer:
    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT, db: int = REDIS_DB, password: str = REDIS_PASSWORD):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.redis_client = None
        self._init_redis()

    def _init_redis(self):
        """Initializes Redis client connection."""
        logger.info(f"Connecting to Redis at {self.host}:{self.port} (db={self.db})...")
        self.redis_client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True,
            socket_timeout=5
        )
        self.redis_client.ping()
        logger.info("Successfully connected to Redis instance.")

    def update_stock_state(self, event: dict, pipe=None):
        """Updates hot stock hash key and stockout alert set in Redis."""
        p_id = event["pharmacy_id"]
        d_id = event["drug_id"]
        key = f"stock:{p_id}:{d_id}"
        
        mapping = {
            "pharmacy_id": p_id,
            "drug_id": d_id,
            "current_stock": str(event["current_stock"]),
            "daily_demand": str(event["daily_demand"]),
            "stockout_flag": "1" if event["stockout_flag"] else "0",
            "disruption_active": "1" if event.get("disruption_active") else "0",
            "shortage_id": event.get("shortage_id") or "",
            "last_updated": event.get("timestamp") or ""
        }

        r = pipe if pipe else self.redis_client
        r.hset(key, mapping=mapping)
        r.expire(key, DEFAULT_STOCK_TTL_SECONDS)

        # Update active stockout alert set
        if event["stockout_flag"]:
            r.sadd("active_stockouts", key)
        else:
            r.srem("active_stockouts", key)

    def consume_stream(self, max_messages: int = None):
        """Consumes `stock_events` from Kafka and updates Redis in pipelined batches."""
        logger.info(f"Starting Redis stream consumer on topic: stock_events...")
        from confluent_kafka import Consumer, KafkaError

        conf = {
            "bootstrap.servers": KAFKA_BROKERS,
            "group.id": "redis-hot-state-sink",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "max.poll.interval.ms": 300000
        }
        consumer = Consumer(conf)
        consumer.subscribe(["stock_events"])

        count = 0
        pipe = self.redis_client.pipeline(transaction=False)
        
        try:
            while True:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    # Flush any pending pipelined commands and commit
                    if len(pipe) > 0:
                        pipe.execute()
                        consumer.commit(asynchronous=True)
                    continue
                if msg.error():
                    if msg.error().code() in (KafkaError._PARTITION_EOF, KafkaError.UNKNOWN_TOPIC_OR_PART, KafkaError._UNKNOWN_TOPIC):
                        time.sleep(0.5)
                        continue
                    else:
                        logger.error(f"Kafka error: {msg.error()}")
                        break

                val = json.loads(msg.value().decode("utf-8"))
                self.update_stock_state(val, pipe=pipe)
                count += 1

                if len(pipe) >= 500:
                    pipe.execute()
                    consumer.commit(asynchronous=True)

                if count % 1000 == 0:
                    logger.info(f"Redis sink updated & committed {count:,} stock keys.")

                if max_messages and count >= max_messages:
                    if len(pipe) > 0:
                        pipe.execute()
                        consumer.commit(asynchronous=False)
                    break
        except KeyboardInterrupt:
            logger.info("Stopping Redis stream consumer.")
        finally:
            if len(pipe) > 0:
                pipe.execute()
                try:
                    consumer.commit(asynchronous=False)
                except Exception:
                    pass
            consumer.close()

    def close(self):
        """Closes Redis connection."""
        if self.redis_client:
            self.redis_client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Redis Hot State Stream Consumer")
    parser.add_argument("--test-ping", action="store_true", help="Ping Redis and check key count")
    parser.add_argument("--max-messages", type=int, default=None, help="Stop after N messages")
    args = parser.parse_args()

    consumer = RedisStreamConsumer()
    if args.test_ping:
        keys_count = len(consumer.redis_client.keys("stock:*"))
        stockouts_count = consumer.redis_client.scard("active_stockouts")
        print(f"Redis Connected. Total stock keys: {keys_count:,} | Active stockouts: {stockouts_count:,}")
    else:
        consumer.consume_stream(max_messages=args.max_messages)
    consumer.close()

