# System Architecture

## Overview
The Polyglot Pharma Supply Chain platform is an enterprise-grade, high-throughput distributed system designed to solve the critical challenges in pharmaceutical traceability, cold-chain integrity, and counterfeit detection through polyglot persistence.

```
                                 ┌─────────────────────────┐
                                 │   IoT Telemetry Stream  │
                                 │ (Sensors / GPS / Temp)  │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │  Redpanda (Kafka API)   │
                                 └───────┬─────────┬───────┘
                                         │         │
                       ┌─────────────────┘         └─────────────────┐
                       ▼                                             ▼
         ┌─────────────────────────┐                   ┌─────────────────────────┐
         │    Apache Cassandra     │                   │      Redis (Cache)      │
         │  Time-Series Telemetry  │                   │  Hot State & Fast Keys  │
         └─────────────────────────┘                   └─────────────────────────┘
                       ▲                                             ▲
                       │                                             │
                       └───────────────────┬─────────────────────────┘
                                           │
                                ┌──────────┴──────────┐
                                │   FastAPI Backend   │
                                └──────────┬──────────┘
                                           │
                       ┌───────────────────┴─────────────────────────┐
                       ▼                                             ▼
         ┌─────────────────────────┐                   ┌─────────────────────────┐
         │     MongoDB (Docs)      │                   │      Neo4j (Graph)      │
         │  Products/Batches/Specs │                   │ Lineage & Supply Graph  │
         └─────────────────────────┘                   └─────────────────────────┘
```

## Storage Model Mapping
1. **Redis 7**: In-memory caching, sub-millisecond lookup of current live batch location and cold-chain status.
2. **MongoDB 7**: Document store for dynamic batch records, FDA product metadata, compliance certificates, and audit documents.
3. **Apache Cassandra 5**: High-throughput distributed wide-column store for high-frequency IoT sensor telemetry (temperature, humidity, vibration).
4. **Neo4j 5**: Graph database modeling multi-tier pharmaceutical supply networks, drug provenance, custodian handoffs, and counterfeit detection paths.
5. **Redpanda**: Single-binary, lightweight C++ Kafka-compatible streaming engine for event streaming and pub/sub pipelines.

