# Related Work

## Cluster 1 — Polyglot Persistence Foundations

### "One Size Fits All": An Idea Whose Time Has Come and Gone
- **Authors:** Michael Stonebraker, Uğur Çetintemel
- **Venue/Publisher:** 21st International Conference on Data Engineering (ICDE), IEEE
- **Year:** 2005
- **DOI:** [10.1109/ICDE.2005.1](https://doi.org/10.1109/ICDE.2005.1)
- **Summary:** This landmark paper argues that the traditional monolithic RDBMS approach is fundamentally ill-suited for the growing diversity of data workloads, demonstrating that forcing heterogeneous applications into a single general-purpose engine causes significant performance degradation (40–60% in some cases). The authors predict a shift toward specialized database engines tailored to specific access patterns, laying the intellectual groundwork for what would later be called polyglot persistence.
- **Relevance:** Our system's core architectural thesis — that pharmaceutical supply chain data is best served by four specialized stores (KV, Document, Columnar, Graph) rather than one — directly extends this argument into a concrete domain-specific demonstration.

### Multi-model Databases: A New Journey to Handle the Variety of Data
- **Authors:** Jiaheng Lu, Irena Holubová
- **Venue/Publisher:** ACM Computing Surveys, Volume 52, Issue 3, Article 55
- **Year:** 2019
- **DOI:** [10.1145/3323214](https://doi.org/10.1145/3323214)
- **Summary:** This survey provides a systematic classification and multi-dimensional comparison of multi-model database management systems — platforms that support multiple data models (relational, document, graph, key-value) within a single engine. The authors identify open research problems in query language unification, cross-model optimization, and schema management that arise when data variety is handled within one platform versus across federated specialized stores.
- **Relevance:** Our polyglot design takes the opposite approach from monolithic multi-model DBMSs surveyed here: we deliberately use separate best-of-breed engines and demonstrate that the added integration complexity is justified by workload-specific performance gains for supply chain analytics.

### Selecting Databases for Polyglot Persistence Applications
- **Authors:** Noa Roy-Hubara, Peretz Shoval, Arnon Sturm
- **Venue/Publisher:** Data & Knowledge Engineering, Volume 137, Article 101950, Elsevier
- **Year:** 2021
- **DOI:** [10.1016/j.datak.2021.101950](https://doi.org/10.1016/j.datak.2021.101950)
- **Summary:** The authors propose a structured methodology for selecting appropriate database models in polyglot persistence applications, evaluating candidates against data-related, functional, and non-functional requirements rather than relying on ad hoc decisions. They formalize the selection process into a systematic framework that helps practitioners map application needs to the most suitable combination of database paradigms.
- **Relevance:** Our project's database selection (Redis for status lookups, MongoDB for drug metadata, Cassandra for time-series events, Neo4j for supply-chain graphs) follows the requirement-driven logic this paper formalizes — our benchmark results in Phase 7 empirically validate that the chosen mapping outperforms single-engine alternatives.

### A Review of Polyglot Persistence in the Big Data World
- **Authors:** Pwint Phyu Khine, Zhaoshun Wang
- **Venue/Publisher:** Information (MDPI), Volume 10, Issue 4, Article 141
- **Year:** 2019
- **DOI:** [10.3390/info10040141](https://doi.org/10.3390/info10040141)
- **Summary:** This review surveys the state of polyglot persistence in big data environments, cataloguing architectural patterns for integrating heterogeneous data stores and discussing the practical challenges of data synchronization, schema evolution, and cross-store query routing. The authors identify consistency management across stores as a key open problem for polyglot systems.
- **Relevance:** The cross-store consistency challenges highlighted here directly motivate our event-driven integration layer (Redpanda) and the saga-style coordination patterns we employ to maintain data coherence across four independent database engines.

---

## Cluster 2 — Distributed Data Consistency

### Sagas
- **Authors:** Hector Garcia-Molina, Kenneth Salem
- **Venue/Publisher:** Proceedings of the 1987 ACM SIGMOD International Conference on Management of Data, pp. 249–259
- **Year:** 1987
- **DOI:** [10.1145/38713.38742](https://doi.org/10.1145/38713.38742)
- **Summary:** Garcia-Molina and Salem introduced the Saga pattern to handle long-lived transactions (LLTs) without holding long-duration locks. A saga decomposes a global transaction into a sequence of smaller local transactions, each with a corresponding compensating transaction that semantically undoes its effects if a later step fails. This enables interleaving of concurrent operations while preserving a consistent recovery path.
- **Relevance:** Our polyglot system ingests disruption events that must be reflected consistently across four databases — the saga pattern directly informs how we coordinate writes to Redis, MongoDB, Cassandra, and Neo4j through the Redpanda event bus, with compensating actions for partial-failure recovery.

### Eventual Consistency Today: Limitations, Extensions, and Beyond
- **Authors:** Peter Bailis, Ali Ghodsi
- **Venue/Publisher:** ACM Queue, Volume 11, Issue 3
- **Year:** 2013
- **DOI:** [10.1145/2460276.2462076](https://doi.org/10.1145/2460276.2462076)
- **Summary:** This article provides a practitioner-oriented survey of eventual consistency models, explaining the trade-offs between strong and weak consistency guarantees in distributed data stores. The authors catalogue the spectrum of consistency levels (from linearizability to causal to eventual), examine real-world anomalies that arise under weak consistency, and discuss pragmatic extensions like read-your-writes and monotonic-reads sessions.
- **Relevance:** Our system deliberately chooses different consistency levels per store — strong consistency for Redis status lookups, eventual consistency for Cassandra time-series ingestion — and this paper provides the theoretical framework for justifying those per-workload consistency decisions.

---

## Cluster 3 — Pharmaceutical Supply-Chain Risk

### The Drug Shortage Crisis in the United States: Causes, Impact, and Management Strategies
- **Authors:** C. Lee Ventola
- **Venue/Publisher:** Pharmacy and Therapeutics (P&T), Volume 36, Issue 11, pp. 740–757
- **Year:** 2011
- **PMID:** 22346307 | **PMCID:** PMC3278171
- **Summary:** This widely cited review provides a comprehensive overview of the U.S. drug shortage crisis, cataloguing the primary root causes (manufacturing quality issues, sole-source dependency, economic disincentives for low-margin generics) and documenting the clinical and financial impacts on healthcare systems. It also evaluates management strategies ranging from inventory buffering to FDA notification requirements and therapeutic substitution protocols.
- **Relevance:** Ventola's root-cause taxonomy directly informs our synthetic event simulator's disruption categories (manufacturing failures, regulatory actions, raw-material shortages) and validates our use of FDA shortage data as a calibration target for realistic scenario generation.

### Pharmaceutical Supply Chain Reliability and Effects on Drug Shortages
- **Authors:** Emily L. Tucker, Mark S. Daskin
- **Venue/Publisher:** Computers & Industrial Engineering, Volume 169, Article 108258, Elsevier
- **Year:** 2022
- **DOI:** [10.1016/j.cie.2022.108258](https://doi.org/10.1016/j.cie.2022.108258)
- **Summary:** This paper presents the first quantitative model of pharmaceutical supply chain reliability, using closed-form expressions to estimate how supply chain configuration, disruption risk, and recovery speed jointly determine expected shortage rates. A case study on generic injectable oncology drugs shows that lean supply chains exhibit roughly 10% expected shortage rates, reducible to 4–5% through back-up suppliers or faster recovery mechanisms.
- **Relevance:** Tucker and Daskin's reliability framework provides the analytical foundation for our fragility scoring model; our system operationalizes similar concepts but implements them as real-time graph-based computations over streaming event data rather than static closed-form models.

### A Supply Chain View of the Resilient Enterprise
- **Authors:** Yossi Sheffi, James B. Rice Jr.
- **Venue/Publisher:** MIT Sloan Management Review, Volume 47, Issue 1, pp. 41–48
- **Year:** 2005
- **Link:** Available via [MIT Sloan Management Review](https://sloanreview.mit.edu/)
- **Summary:** Sheffi and Rice articulate how enterprises can build supply chain resilience through a combination of redundancy (safety stock, multiple suppliers) and flexibility (standardized processes, postponement strategies). They develop a disruption profile framework that categorizes events by probability and impact, arguing that flexible supply chains recover faster than those relying solely on redundant buffers.
- **Relevance:** The redundancy-vs-flexibility framework directly maps to our fragility scoring: our graph analysis identifies single-source dependencies (lack of redundancy) while our simulation engine models the recovery dynamics (flexibility) that Sheffi and Rice describe qualitatively.

---

## Cluster 4 — Supply-Chain Network Science

### Complex Interdependent Supply Chain Networks: Cascading Failure and Robustness
- **Authors:** Liang Tang, Ke Jing, Jie He, H. Eugene Stanley
- **Venue/Publisher:** Physica A: Statistical Mechanics and its Applications, Volume 443, pp. 58–69, Elsevier
- **Year:** 2016
- **DOI:** [10.1016/j.physa.2015.09.082](https://doi.org/10.1016/j.physa.2015.09.082)
- **Summary:** The authors model a supply chain as a two-layer interdependent network (an undirected cyber/information layer and a directed physical logistics layer) and study how node failures cascade through load redistribution under flow constraints. Their simulations reveal that even removing a small number of high-betweenness nodes triggers a first-order discontinuous phase transition, causing sudden large-scale network collapse rather than gradual degradation.
- **Relevance:** Our graph-based fragility analysis module implements a similar betweenness-centrality-driven vulnerability assessment but applies it specifically to pharmaceutical supply networks, using our Neo4j graph store to identify single-point-of-failure manufacturers and API suppliers.

### Structural Characteristics of Complex Supply Chain Networks
- **Authors:** Supun Perera, H. Niles Perera, Dharshana Kasthurirathna
- **Venue/Publisher:** 2017 Moratuwa Engineering Research Conference (MERCon), IEEE
- **Year:** 2017
- **Link:** Available via [IEEE Xplore](https://ieeexplore.ieee.org/document/7980507)
- **Summary:** This paper examines the structural properties of supply chain networks using complex network analysis techniques, computing degree distribution, clustering coefficients, and betweenness centrality to identify hub nodes and assess network robustness against targeted versus random disruptions. The authors demonstrate that real-world supply chain topologies exhibit scale-free properties, meaning a small number of highly connected nodes disproportionately determine network resilience.
- **Relevance:** The scale-free topology findings validate our approach of using centrality metrics to rank pharmaceutical supply chain entities by criticality, and their targeted-vs-random attack simulations parallel our scenario engine's disruption models.

### Network Science Approach to Modelling the Topology and Robustness of Supply Chain Networks: A Review and Perspective
- **Authors:** Supun Perera, Michael G. H. Bell, Michiel C. J. Bliemer
- **Venue/Publisher:** Applied Network Science, Volume 2, Article 33, Springer
- **Year:** 2017
- **DOI:** [10.1007/s41109-017-0053-0](https://doi.org/10.1007/s41109-017-0053-0)
- **Summary:** This review comprehensively surveys how network science techniques — including degree distribution analysis, centrality measures, community detection, and percolation theory — have been applied to model supply chain topology and assess robustness. The authors identify gaps in existing approaches, particularly the lack of empirically calibrated network models and the limited integration of dynamic disruption propagation into static topological analyses.
- **Relevance:** Our system addresses the key gap this review identifies: we build an empirically calibrated supply chain network (seeded from real FDA data) and combine static topological analysis (centrality scoring) with dynamic event simulation (cascading disruption propagation) in a single integrated platform.

---

## Cluster 5 — Cascading Failure and Resilience

### Systematic Review and Future Perspectives on Cascading Failures in Supply Chains: Modeling and Optimization
- **Authors:** Xiuwen Fu, Mengyao Tian, Xiangwei Liu, Shaomin Wu, Rui Peng
- **Venue/Publisher:** Reliability Engineering & System Safety, Volume 270, Article 112150, Elsevier
- **Year:** 2026
- **DOI:** [10.1016/j.ress.2025.112150](https://doi.org/10.1016/j.ress.2025.112150)
- **Summary:** This systematic review maps the current landscape of cascading failure research in supply chain networks, covering network metrics, failure-triggering factors, modeling methods (load-capacity, epidemic-spread, agent-based), and optimization strategies for mitigation. The authors identify critical gaps in network coupling realism, recovery optimization, and predictive risk modeling as priorities for future work.
- **Relevance:** Our project directly addresses several of the gaps this review identifies — particularly the integration of realistic disruption calibration (FDA data) with dynamic cascading failure simulation and an interactive intervention-testing interface.

### Resilient Supply Chain Network Design: A Systematic Literature Review
- **Authors:** Rajali Maharjan, Hironori Kato
- **Venue/Publisher:** Transport Reviews, Volume 42, Issue 6, pp. 739–761, Taylor & Francis
- **Year:** 2022
- **DOI:** [10.1080/01441647.2022.2080773](https://doi.org/10.1080/01441647.2022.2080773)
- **Summary:** Maharjan and Kato systematically review quantitative models for resilient supply chain network design, classifying approaches by resilience measures (connectivity, recovery time, service level), disruption types, and optimization formulations. They find that most models focus on facility location and supplier allocation under disruption scenarios but rarely incorporate real-time data feeds or graph-theoretic fragility metrics into their optimization.
- **Relevance:** Our system complements the optimization models surveyed here by providing the real-time fragility assessment layer that these models typically lack — our graph-based centrality analysis and event-driven monitoring can serve as inputs to the resilient network design frameworks they describe.

---

## Cluster 6 — Performance Evaluation

### Benchmarking Cloud Serving Systems with YCSB
- **Authors:** Brian F. Cooper, Adam Silberstein, Erwin Tam, Raghu Ramakrishnan, Russell Sears
- **Venue/Publisher:** 1st ACM Symposium on Cloud Computing (SoCC '10), ACM
- **Year:** 2010
- **DOI:** [10.1145/1807128.1807152](https://doi.org/10.1145/1807128.1807152)
- **Summary:** This paper introduces the Yahoo! Cloud Serving Benchmark (YCSB), a standardized framework for comparing the performance of cloud-scale data serving systems across configurable workload profiles (read-heavy, write-heavy, scan-intensive, and mixed). The framework defines a core set of operations and provides extensible client drivers, establishing the de facto standard methodology for evaluating throughput and latency across NoSQL database paradigms.
- **Relevance:** We adopt the YCSB methodology and extend it with domain-specific workload profiles (point lookups for drug-status checks, time-series range scans for shortage trend analysis, and multi-hop graph traversals for supply chain path queries) to empirically compare our four database engines under pharmaceutical supply chain access patterns.

### NoSQL Databases: MongoDB vs Cassandra
- **Authors:** Veronika Abramova, Jorge Bernardino
- **Venue/Publisher:** International C* Conference on Computer Science and Software Engineering (C3S2E '13), ACM
- **Year:** 2013
- **DOI:** [10.1145/2494444.2494447](https://doi.org/10.1145/2494444.2494447)
- **Summary:** This empirical study uses YCSB to compare MongoDB and Cassandra across standard workload mixes, measuring throughput and latency for insert, read, update, and scan operations at varying data scales. The results show that each system exhibits distinct performance characteristics: Cassandra excels in write-heavy distributed scenarios while MongoDB demonstrates advantages in read-intensive and ad-hoc query workloads.
- **Relevance:** This head-to-head document-vs-columnar comparison informs our architectural decision to use both paradigms — MongoDB for flexible drug metadata documents and Cassandra-style columnar storage for high-throughput time-series event ingestion — rather than forcing one engine to serve both access patterns.

---

## Gap Synthesis

The existing literature establishes that monolithic database architectures are poorly suited to heterogeneous workloads (Stonebraker & Çetintemel 2005; Lu & Holubová 2019), with practical methodologies emerging for polyglot database selection (Roy-Hubara et al. 2021; Khine & Wang 2019) and well-understood patterns for maintaining consistency across distributed stores (Garcia-Molina & Salem 1987; Bailis & Ghodsi 2013). Pharmaceutical supply chains are known to be structurally fragile due to manufacturing concentration and lean configurations (Ventola 2011; Tucker & Daskin 2022; Sheffi & Rice 2005). Network science has provided tools for analyzing this fragility through centrality measures, cascading failure models, and topological robustness assessment (Tang et al. 2016; Perera et al. 2017a, 2017b), with recent systematic reviews cataloguing the state of the art in cascading failure modeling (Fu et al. 2026) and resilient network design (Maharjan & Kato 2022). Standard benchmarking frameworks exist for evaluating NoSQL database performance across workload types (Cooper et al. 2010; Abramova & Bernardino 2013). However, no existing work brings all six threads together into a single integrated system: a polyglot-persistence platform that simultaneously models pharmaceutical supply chain topology as a graph for fragility analysis, stores streaming disruption events in a columnar store for time-series analytics, manages drug metadata in a document store, uses a key-value store for real-time status lookups, coordinates cross-store consistency via event-driven sagas, and is calibrated against real FDA shortage data. Our project fills this gap by demonstrating, through a working systems prototype with empirical benchmarks, that a purpose-built polyglot architecture can deliver both the analytical depth of graph-based fragility scoring and the operational performance of workload-matched storage engines, providing an early-warning capability for medication shortages that no single-paradigm system can efficiently support.
