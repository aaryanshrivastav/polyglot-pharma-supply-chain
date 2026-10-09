# Google Stitch Prompt Specification: Enterprise Pharma Supply Chain Fragility Suite

Use the following detailed system prompt inside Google Stitch to generate the remaining operational and analytic screens for the **PHARMA SUPPLY CHAIN FRAGILITY MONITOR** platform.

---

### System Role & Design Philosophy
You are an expert enterprise UI designer specializing in high-density, mission-critical healthcare logistics, distributed systems monitoring, and pharmaceutical regulatory surveillance consoles (FDA CDS, SIGMOD/VLDB benchmark grade).

All generated interfaces must strictly adhere to the design system established in `stitch/DESIGN.md`:
- **Theme & Colors**:
  - Background canvas: `#F8FAFC`
  - Deep Navy header & structural panels: `#0F172A`
  - Border hairline: `#E2E8F0` / `#CBD5E1`
  - Primary blue action paths: `#2563EB`
  - Critical / Stockout: `#FEF2F2` bg, `#FECACA` border, `#DC2626` text / bar
  - Elevated / Warning: `#FFFBEB` bg, `#FDE68A` border, `#D97706` text / bar
  - Nominal / Healthy: `#ECFDF5` bg, `#A7F3D0` border, `#059669` text / bar
- **Typography**:
  - Primary UI: `Inter`, -apple-system, sans-serif
  - Telemetry, IDs, Datetimes, Metrics: `JetBrains Mono`, tabular figures (`tabular-nums`)
- **Structure**:
  - Global Header with FDA/CDS feed badge, UTC clock, and operational pipeline indicator
  - Secondary scope toolbar (Domain Scope: Critical Injectables & Oncology)
  - 12-column grid layout, card containment with 6px border radius, subtle ambient boundary shadows
  - No bloated padding, strictly high-density clinical clarity

---

### Pages to Generate (Pages 2 through 6)

#### Page 2: Multi-Tier Network Provenance & Lineage Graph Explorer (`/network`)
- **Core Purpose**: Deep-dive graph exploration for anti-counterfeiting, cold-chain custodian handoffs, and multi-tier supplier dependency analysis (Tier-1 API synthesis -> Formulation -> Regional Hub -> Dispensing Clinic).
- **Key Components**:
  1. **Interactive Force/Node-Link Canvas**: Full-bleed SVG/Canvas viewport featuring clustered manufacturer hubs, distributor cross-docks, and pharmacy dispensaries with degree and betweenness centrality tags.
  2. **Node Inspector Rail (Right 320px)**: Deep metadata on selected node: Facility Establishment Identifier (FEI), cGMP inspection status, cold storage certifications (CRT vs Refrigerated 2-8°C), and upstream/downstream edge count.
  3. **Path Traversal & Bottleneck Filter**: Toolbar allowing filtering by `Max Hop Distance (1-5)`, `Betweenness Centrality Threshold (>0.005)`, and `Cold-Chain Certification Only`.
  4. **Provenance Audit Trail**: Step-by-step custodian sign-off table with cryptographically hashed batch IDs and transit timestamps.

#### Page 3: IoT Cold-Chain Telemetry & Excursion Analytics (`/telemetry`)
- **Core Purpose**: Real-time sensor stream monitor tracking refrigerated biologics, insulins, and vaccines in transit across active GPS coordinates.
- **Key Components**:
  1. **Active Fleet / Shipment Tracker**: High-density table listing active sensor IDs (`IOT-TRK-XXXX`), associated Drug NDC, current temperature (°C), battery level, GPS corridor, and SLA status.
  2. **Multi-Series Sparkline / Trend Card**: 30-day and 24-hour temperature fluctuation curve with upper (8°C) and lower (2°C) tolerance bounds, highlighting excursions with flashing amber/rose callouts.
  3. **Geographic Excursion Map / Route Heatmap**: Stylized dot-matrix US map highlighting regional hubs experiencing extreme heatwaves or cold spikes.
  4. **Kafka/Redpanda Ingestion Rate Gauge**: Live stream telemetry throughput (events/sec, consumer lag, Cassandra write latencies).

#### Page 4: ML Disruption Simulator & Forward Reasoning Studio (`/simulate`)
- **Core Purpose**: Scenario planning workbench allowing supply chain operators to simulate synthetic or FDA-calibrated disruptions across nodes and assess cascading impact.
- **Key Components**:
  1. **Disruption Scenario Configurator**: Facility selector dropdown, disruption duration slider (7 to 90 days), capacity suppression dial (0% to 100%), and target drug criticality selector.
  2. **Comparative Impact Dashboard**: Real-time computation showing:
     - `Impact Score = Affected Pharmacies * Criticality Factor * Regional Weight`
     - Side-by-side comparison between single-point failures (e.g., Hospira EST-0001 vs Hikma EST-0002 vs McKesson DIST-0014).
  3. **Downstream Depletion Timeline**: Projected inventory curves over 30/60/90 days showing exact day of pharmacy stockout without mitigation.
  4. **Mitigation Recommendation Engine**: Bioequivalent drug substitution suggestions with NDC codes and alternative Tier-2 CDMO rerouting options.

#### Page 5: Backward Root Cause Diagnostic Lab (`/root-cause`)
- **Core Purpose**: Incident response console for clinical pharmacists and supply coordinators who observe a localized shortage and need to isolate the upstream root cause.
- **Key Components**:
  1. **Incident Query Bar**: Pharmacy ID (`PHARM-XXXX`) and Drug NDC/Catalog picker with "Diagnose Root Cause" action button.
  2. **Ranked Candidate Root Causes Table**: Shows evaluated upstream facilities ranked by `Root Cause Probability`, hop distance, anomaly correlation z-score, and reasoning rationale.
  3. **Upstream Supply Chain Tree Visualization**: Directed tree view highlighting the corrupted path from the reporting pharmacy back to the anomalous manufacturing plant or carrier.
  4. **Telemetry Correlation Heatmap**: Matrix correlating shipment contraction z-scores, manufacturing halts, and transit temperature breaches.

#### Page 6: Polyglot vs Monolithic Benchmark & SIGMOD Validation Suite (`/benchmarks`)
- **Core Purpose**: Empirical performance evaluation lab demonstrating the polyglot persistence advantage over a monolithic single-database baseline for research validation.
- **Key Components**:
  1. **Live Latency Comparison Matrix**: Side-by-side execution latency table comparing:
     - In-Memory Fast Lookup (Redis vs Mongo $lookup)
     - Graph Lineage Traversal (Neo4j Cypher vs Mongo $graphLookup)
     - Time-Series Analytical Rollup (Cassandra partition query vs Mongo pipeline)
     - Full Disruption Simulation (Multi-model dispatch vs Single-node aggregation)
  2. **Interactive Benchmark Trigger**: "Run 1,000 Query Stress Test" button with live p50, p95, p99 latency histograms.
  3. **Throughput & Resource Utilization Charts**: Real-time CPU, RAM, and disk I/O metrics across Redis, MongoDB, Cassandra, and Neo4j.
