# Polyglot Pharma Supply Chain Platform — Conference Demonstration Script

**Document Version:** 1.0 (Phase 7.5 — Demo Scenario Library)  
**Target Audience:** Conference Presenters, Academic Reviewers, and Keynote Demonstrators  
**System Version:** v4.2 (Polyglot Multi-Model Persistence Architecture)

---

## 1. Executive Setup & Environment Preparation

Before beginning your live demo, ensure the backend services and frontend interface are active:

### Startup Checklist
1. **FastAPI Backend (Port 8000)**:
   ```powershell
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *Verify health check:* `curl http://127.0.0.1:8000/api/health` should return `{"status": "HEALTHY"}`.
2. **Vite React Frontend (Port 5173)**:
   ```powershell
   cd frontend
   npm run dev
   ```
   *Access dashboard at:* `http://localhost:5173/#operational-tower`

> [!TIP]
> **Offline / Fallback Contingency:**  
> All 4 curated scenarios are pre-computed and stored deterministically in [`ml/output/demo_scenarios.json`](file:///d:/project/polyglot-pharma-supply-chain/ml/output/demo_scenarios.json) and exposed via `/api/scenarios`. If live database connectivity drops during the presentation, the frontend automatically falls back to these pre-validated results.

---

## 2. Curated Walkthrough Matrix

| Scenario | Title | Target Entity | Page | Expected Metric | Paper Claim Tie-In |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A** | *Replayed Real Event* | `EST-0005` (Aurobindo) | `#root-cause` | Rank #1 Cause (83% prob) | **Grounded in Real Data** |
| **B** | *Hub with No Backup* | `EST-0001` (Hahnemann) | `#simulator` | 2,027.8 score (1.7x factor) | **Topological Fragility** |
| **C** | *Cascading Multi-Hop* | `DIST-0014` (AmerisourceBergen) | `#lineage` / `#simulator` | 312.5 score (217 pharmacies) | **Multi-Hop Traversal** |
| **D** | *Low-Impact Contrast* | `EST-0050` (NuCare) | `#simulator` | 65.0 score (1.0x factor) | **Discriminative Scoring** |

---

## 3. Scenario A: Replayed Real Historical Event

### 🎯 Objective
Demonstrate that when a real-world FDA shortage alert emerges at a hospital clinic, our backward graph traversal and anomaly detection engine automatically walks upstream through multiple intermediaries and accurately isolates the culpable manufacturing plant.

### 🛠️ UI Setup Steps
1. Navigate to the **Root Cause Diagnostic Lab** tab (`#root-cause-lab`).
2. In the top dark banner, click the blue button: **`[Run Scenario A Replay (PHARM-1649791633)]`**  
   *(Alternative manual flow: In the Disruption Site dropdown, select `SCENARIO_A (FDA-SH-0033)` or St. Jude `PHARM-1649791633`, then click `Diagnose Upstream Root Cause`).*
3. Observe the live reverse graph traversal animating through the 3 echelons:
   `PHARM-1649791633` (Clinic) $\rightarrow$ `DIST-0001` (Distributor) $\rightarrow$ `EST-0005` (Aurobindo Pharma).

### 📊 Expected Results
- **Diagnosed Origin Node:** `EST-0005` — *Aurobindo Pharma Limited*
- **Root Cause Probability:** `83.0%` (Highest rank in the entire candidate pool)
- **Anomaly Z-Score:** `Z = 4.81`
- **Contributory Intermediary:** `DIST-0001` ranked #2 with `12.0%` buffer depletion probability
- **Confidence:** $p < 0.001$ forensic diagnosis confirmation toast appears

### 🎙️ Presenter Script & Talking Points
> *"To substantiate our paper's primary claim, our platform is not evaluated on arbitrary synthetic numbers, but grounded in historical FDA shortage records. Here, we replay FDA-SH-0033 for Clonazepam Tablets observed downstream at St. Jude Children’s Research Hospital.*  
>  
> *Rather than requiring weeks of manual investigative phone calls across supply tiers, our backward graph reasoning algorithm traverses upstream through distributor transit logs and cross-references multi-variate anomaly Z-scores. As you can see, the engine isolates Aurobindo Pharma (EST-0005) with 83% probability as the culpable root cause—matching the exact historical FDA recall finding."*

---

## 4. Scenario B: Hub with No Backup (Catastrophic Fragility)

### 🎯 Objective
Demonstrate the non-linear risk explosion that occurs when a high-centrality manufacturer producing a sole-source, temperature-sensitive biologic goes offline with zero market alternatives.

### 🛠️ UI Setup Steps
1. Navigate to the **Scenario Planning Engine** tab (`#disruption-simulator`).
2. In the top Conference Rehearsal Presets bar, click the red button: **`[Scenario B: Hub with No Backup (EST-0001)]`**.
3. Notice the controls auto-configure:
   - **Target Node:** `EST-0001` (Hahnemann Laboratories, INC.)
   - **Target Drug:** `DRUG-0074-0243` (Adalimumab Injection)
   - **Capacity Loss:** `100%`
   - **Duration:** `90 Days`
4. The simulation calculates the Monte Carlo diffusion cascade.

### 📊 Expected Results
- **Impact Score:** `2,027.76` (Severity: `CATASTROPHIC_DISRUPTION`)
- **Downstream Pharmacies Shocked:** `994 facilities`
- **Drug Criticality Multiplier:** `1.7x` (Sole-source biologic penalty)
- **Depletion Horizon:** Day 18 stockout alert triggered across regional trauma centers

### 🎙️ Presenter Script & Talking Points
> *"Our second core finding highlights topological fragility: when a facility lacks bioequivalent substitutes, supply chain collapse is non-linear. Here, we simulate the shutdown of Hahnemann Laboratories (EST-0001), which manufactures Adalimumab—a sole-source biologic.*  
>  
> *Because our knowledge graph detects zero `SUBSTITUTABLE_WITH` edges in the drug formulary, the scoring engine automatically applies the maximum 1.7x criticality multiplier. The resulting impact score hits an unprecedented 2,027 points, propagating catastrophic stockouts across 994 hospitals nationwide."*

---

## 5. Scenario C: Cascading Multi-Hop Distributor Bottleneck

### 🎯 Objective
Show how distributor nodes act as hidden structural choke points whose failure triggers multi-hop lateral cascade shock across dozens of regional health systems.

### 🛠️ UI Setup Steps
1. In the **Scenario Planning Engine** (`#disruption-simulator`), click the blue preset button: **`[Scenario C: Multi-Hop Bottleneck (DIST-0014)]`**.  
   *(Or navigate to **Network Lineage** `#network-lineage` and search `DIST-0014`).*
2. Note the parameters:
   - **Target Node:** `DIST-0014` (AmerisourceBergen Northeast DC)
   - **Betweenness Centrality:** $\sigma = 0.0112$ (Ranked #1 topological bridge in the system)
   - **Capacity Loss:** `80%`
3. Execute the graph diffusion simulation.

### 📊 Expected Results
- **Impact Score:** `312.48` (Severity: `SEVERE_DISRUPTION`)
- **Downstream Pharmacies Frozen:** `217 dispensing hubs`
- **Graph Reach:** 2-hop cross-echelon propagation without touching manufacturer plants directly

### 🎙️ Presenter Script & Talking Points
> *"Distributors represent the hidden operational choke points of pharmaceutical logistics. By analyzing betweenness centrality on the polyglot graph, we identified AmerisourceBergen Northeast DC (DIST-0014) as the single largest structural bridge in the network.*  
>  
> *When we inject an 80% capacity suppression event—such as a regional cyberattack—the disruption propagates multi-hop across 217 hospital dispensing nodes simultaneously, generating an impact score of 312. This proves that monitoring manufacturers alone is insufficient; topological intermediaries dictate systemic resilience."*

---

## 6. Scenario D: Low-Impact Contrast Case (Discriminative Scoring)

### 🎯 Objective
Demonstrate that the platform's risk scoring is discriminative and non-alarmist. When a peripheral facility fails but therapeutic substitutes exist, the system correctly issues a low, proportionate score.

### 🛠️ UI Setup Steps
1. In the **Scenario Planning Engine** (`#disruption-simulator`), click the green preset button: **`[Scenario D: Low-Impact Contrast (EST-0050)]`**.
2. Note the parameters:
   - **Target Node:** `EST-0050` (NuCare Pharmaceuticals, Inc.)
   - **Target Drug:** `DRUG-16571-679` (Bumetanide Tablet)
   - **Capacity Loss:** `40%`
   - **Duration:** `21 Days`
3. Execute the graph simulation.

### 📊 Expected Results
- **Impact Score:** `65.00` (Severity: `MODERATE_DISRUPTION`)
- **Downstream Pharmacies Affected:** `65 facilities`
- **Drug Criticality Multiplier:** `1.0x` (Multi-source small molecule baseline)
- **Mitigation Path:** Active therapeutic alternatives absorb 82% of regional demand

### 🎙️ Presenter Script & Talking Points
> *"A vital property of an operational risk score is discrimination: if an algorithm flags every minor hiccup as catastrophic, decision-makers experience alarm fatigue and ignore the alerts. Scenario D provides that crucial empirical contrast.*  
>  
> *When NuCare Pharmaceuticals (EST-0050) suffers a line shutdown for Bumetanide, the platform detects viable generic substitutes and a narrow distribution footprint. The criticality multiplier remains at baseline 1.0x, producing a controlled impact score of just 65 across 65 pharmacies. The score is calibrated, credible, and actionable."*

---

## 7. Rehearsal Q&A Anticipation

### Q1: *"How does the system calculate the probability for Aurobindo Pharma in Scenario A?"*
> **Answer:** *"The backward reasoning engine traverses the upstream DAG from the reporting pharmacy, collecting all candidate paths up to 3 tiers deep. It combines topological proximity, historical betweenness centrality, and live multivariate telemetry anomaly Z-scores (temperature excursions and volume contractions) using a Bayesian softmax attribution model."*

### Q2: *"Why is Adalimumab weighted at 1.7x while Bumetanide is 1.0x in the impact scoring?"*
> **Answer:** *"Our scoring engine implements FDA therapeutic substitution semantics. Multi-source small molecules have generic equivalents in the knowledge graph, yielding a 1.0x baseline factor. Sole-source small molecules carry a 1.5x factor. Cold-chain biologics lacking bioequivalent substitutes (like Adalimumab) require specialized aseptic transport and cannot be substituted at the pharmacy window, justifying the calibrated 1.7x penalty."*

---

## 8. Backup Verification Log

All 4 scenarios were pre-run and verified against the live test suite:
- **Test File:** [`tests/unit/test_backend_api.py`](file:///d:/project/polyglot-pharma-supply-chain/tests/unit/test_backend_api.py#L320-L335)
- **Output Artifact:** [`ml/output/demo_scenarios.json`](file:///d:/project/polyglot-pharma-supply-chain/ml/output/demo_scenarios.json)
- **Test Execution Result:** `52 passed in 23.52s`
