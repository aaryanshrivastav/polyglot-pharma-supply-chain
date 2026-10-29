# System Limitations & Constraints

## Data & Topology Boundaries

### 1. Synthetic Distributor Nodes & Topology Edges
Public healthcare and regulatory records (openFDA and CMS NPPES) provide ground-truth establishment identifiers for manufacturers and dispensing pharmacies, but individual commercial drug wholesaler/distributor facility inventories and contract routes are proprietary (e.g., AmerisourceBergen, McKesson, Cardinal Health). 

Accordingly, intermediary `Distributor` nodes and multi-tier routing edges (`SUPPLIES`, `DISTRIBUTES_TO`) are synthesized using a **Power-Law / Zipfian degree distribution** (\(a = 1.6\)) to model empirical scale-free supply chain network properties (Perera et al., 2017; Tang et al., 2016). This design choice is documented as an intentional structural model rather than a data defect.

---

## Technical & Operational Architecture Boundaries

### 2. Multi-Model Eventual Consistency
The polyglot persistence architecture leverages MongoDB for document specifications, Apache Cassandra for IoT time-series telemetry, Neo4j for provenance graphs, and Redis for hot caching. Consistency across heterogeneous datastores is maintained via asynchronous event streaming (Redpanda/Kafka) with eventual consistency guarantees rather than distributed two-phase commit (2PC) transactions.

### 3. Local Developer Resource Footprint
Running 5 concurrent database engines and streaming brokers simultaneously requires ~4–6 GB of allocated RAM. In resource-constrained environments, heap sizes are capped via `.env` configuration (e.g., `CASSANDRA_MAX_HEAP=1024M`, `NEO4J_dbms_memory_heap_max__size=1G`).
