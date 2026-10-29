# Benchmarking & Performance Methodology

## Scope
Defines comparative performance benchmarking methodology:
- **Polyglot Architecture vs. Monolithic Baseline**: Ingestion throughput, p95/p99 query latency, and resource footprint across diverse query workloads (lineage traversal, time-series aggregations, document lookups).
- **Workload Profiles**:
  - Write-heavy streaming ingestion (10k+ msgs/sec IoT telemetry)
  - Deep graph queries (k-hop upstream supplier tracing)
  - Real-time aggregation & cold-chain violation alerts

