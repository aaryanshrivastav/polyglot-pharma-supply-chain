# Polyglot Pharma Supply Chain Platform

> An enterprise-grade, polyglot persistence platform and streaming pipeline for pharmaceutical supply chain traceability, real-time IoT cold-chain telemetry monitoring, and provenance graph analysis.

---

## 🏛️ Architecture Overview

The system pairs specialized database engines with specific domain data characteristics rather than forcing heterogeneous supply chain data into a single monolithic model:

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

### Storage Model Breakdown

| Store / Service | Technology | Role in Architecture | Key Port(s) |
| :--- | :--- | :--- | :--- |
| **Redis** | `redis:7-alpine` | In-memory key-value cache for hot batch status & sub-ms queries | `6379` |
| **MongoDB** | `mongo:7` | Document store for flexible product catalogs, drug monographs & FDA compliance records | `27017` |
| **Cassandra** | `cassandra:5` | Distributed wide-column store for high-frequency IoT time-series telemetry | `9042` |
| **Neo4j** | `neo4j:5` | Graph database for multi-tier supplier networks, provenance & anti-counterfeiting lineage | `7474`, `7687` |
| **Redpanda** | `v24.1.8` | Ultra-fast Kafka-compatible broker handling IoT sensor streams with low resource overhead | `9092` |

---

## 📂 Project Structure

```
project-root/
├── docker-compose.yml     # Multi-container orchestration for all 5 data stores
├── .env.example           # Environment template with credentials & ports
├── .env                   # Local environment configuration
├── README.md              # Project documentation & operational guide
├── data-ingestion/        # Phase 0: External dataset loaders & preprocessors
├── db-loaders/            # Phase 1: Schema creation & initial database seeders
├── simulator/             # Phase 2: IoT sensor telemetry & event simulators
├── streaming/             # Phase 2: Stream processors & event consumers
├── etl/                   # Phase 3: Cross-database reconciliation & aggregation jobs
├── ml/                    # Phase 4: Temperature excursion & anomaly ML models
├── backend/               # Phase 5: FastAPI core API service
│   └── baseline/          # Phase 6: Monolithic baseline comparison service
├── frontend/              # Phase 7: Node.js / React dashboard
├── tests/                 # Phase 8: Unit, integration & benchmark tests
└── docs/                  # Architecture, benchmarks, papers & research
    ├── related_work.md    # Phase 0: Literature review
    ├── paper_target.md    # Phase 0: Academic venue alignment
    ├── architecture.md    # Phase 8: Detailed system architecture
    ├── benchmarks.md      # Phase 8: Empirical benchmarking protocols
    ├── limitations.md     # Phase 8: Scope and operational boundaries
    ├── charts/            # Phase 8: Generated evaluation plots
    └── paper/             # Phase 9: Research paper draft & camera-ready materials
```

---

## 🚀 Getting Started

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) (v24+) & [Docker Compose](https://docs.docker.com/compose/) (v2+)
- Python 3.11+
- Node.js 20+

### Setup & Startup

1. **Clone and Configure Environment**:
   ```bash
   cp .env.example .env
   ```

2. **Launch Polyglot Data Stores**:
   ```bash
   docker compose up -d
   ```

3. **Check Container Status**:
   ```bash
   docker compose ps
   ```

---

## 🔍 Service Health Verification

Run these verification commands to ensure all services are healthy and accepting connections:

### 1. Redis (In-Memory Cache)
```bash
docker compose exec redis redis-cli ping
# Expected output: PONG
```

### 2. MongoDB (Document Store)
```bash
docker compose exec mongodb mongosh -u root -p rootpassword --eval "db.adminCommand('ping')"
# Expected output: { ok: 1 }
```

### 3. Apache Cassandra (Time-Series Store)
```bash
docker compose exec cassandra cqlsh -e "DESCRIBE KEYSPACES;"
# Expected output: system_schema, system, system_distributed, ...
```

### 4. Neo4j (Graph Database)
- **Web Browser UI**: Open [http://localhost:7474](http://localhost:7474) (Credentials: `neo4j` / `pharma_secret`)
- **Cypher CLI**:
  ```bash
  docker compose exec neo4j cypher-shell -u neo4j -p pharma_secret "RETURN 'Neo4j is healthy' AS status;"
  ```

### 5. Redpanda (Kafka-compatible Streaming Broker)
```bash
# Check cluster status
docker compose exec redpanda rpk cluster info

# Create and list a test topic
docker compose exec redpanda rpk topic create test-healthcheck
docker compose exec redpanda rpk topic list
docker compose exec redpanda rpk topic delete test-healthcheck
```

