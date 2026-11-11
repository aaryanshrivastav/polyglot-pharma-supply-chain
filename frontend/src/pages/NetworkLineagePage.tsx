import React, { useState, useEffect } from 'react';
import { ProvenanceAuditRecord } from '../types';
import { fetchTopology, fetchSpofRankings } from '../api';

const INITIAL_AUDIT_TRAIL: ProvenanceAuditRecord[] = [
  {
    step: 1,
    custodian: 'Zhejiang Hisun Bio API Lab',
    action: 'Cisplatin API Synthesis & Batch Seal',
    timestamp: '2026-10-01 04:12 UTC',
    location: 'Taizhou, China (FEI-300184)',
    hash: '0x8f4c...3e19',
    status: 'VERIFIED'
  },
  {
    step: 2,
    custodian: 'Intas Pharmaceuticals Formulation',
    action: 'Sterile Vials Formulation & Cryo-Seal',
    timestamp: '2026-10-02 11:45 UTC',
    location: 'Ahmedabad, India (FEI-300291)',
    hash: '0x3a9b...7d22',
    status: 'VERIFIED'
  },
  {
    step: 3,
    custodian: 'Air India Cargo / Polar Transport',
    action: 'Intercontinental Air Freight (2-8°C)',
    timestamp: '2026-10-03 20:10 UTC',
    location: 'JFK Intl Airport, NY',
    hash: '0x1c84...fa90',
    status: 'VERIFIED'
  },
  {
    step: 4,
    custodian: 'AmerisourceBergen Northeast DC',
    action: 'Cross-Dock Inbound Scan & Cryo-Depot',
    timestamp: '2026-10-04 08:30 UTC',
    location: 'Bethlehem, PA (DIST-0014)',
    hash: '0x99e2...0b41',
    status: 'FLAGGED'
  },
  {
    step: 5,
    custodian: "St. Jude Children's Hospital",
    action: 'Formulary Intake & Stockout Trigger',
    timestamp: '2026-10-05 14:15 UTC',
    location: 'Memphis, TN (PHARM-MEM-0042)',
    hash: '0x55d1...aa78',
    status: 'FLAGGED'
  }
];

interface GraphNodeDef {
  id: string;
  name: string;
  label: string;
  sub: string;
  tier: number; // 1: API, 2: Formulation, 3: Distributor, 4: Hospital
  cx: number;
  cy: number;
  centrality: number;
  coldChain: boolean;
}

const ALL_GRAPH_NODES: GraphNodeDef[] = [
  { id: 'API-ZHEJIANG', name: 'Zhejiang Hisun Bio API Lab', label: 'Zhejiang Hisun', sub: 'Cisplatin API (T-1)', tier: 1, cx: 100, cy: 90, centrality: 0.0041, coldChain: true },
  { id: 'API-TEVA', name: 'Teva Active API Synthesis', label: 'Teva Active API', sub: 'Generic Base (T-1)', tier: 1, cx: 100, cy: 240, centrality: 0.0032, coldChain: false },
  { id: 'EST-0002', name: 'Hikma Pharmaceuticals Columbus', label: 'Hikma (FEI-3002808)', sub: 'Lyophilization Line (T-2)', tier: 2, cx: 300, cy: 130, centrality: 0.0112, coldChain: true },
  { id: 'EST-0001', name: 'Hospira Inc. / Pfizer', label: 'Hospira Pfizer', sub: 'Sterile Vials Line (T-2)', tier: 2, cx: 300, cy: 260, centrality: 0.0084, coldChain: true },
  { id: 'DIST-0014', name: 'AmerisourceBergen Northeast DC', label: 'AmerisourceBergen DC', sub: 'Northeast Bridge (T-3)', tier: 3, cx: 500, cy: 110, centrality: 0.0112, coldChain: true },
  { id: 'DIST-0001', name: 'AmerisourceBergen Central Hub', label: 'AmerisourceBergen Hub', sub: 'Central Logistics (T-3)', tier: 3, cx: 500, cy: 230, centrality: 0.0076, coldChain: true },
  { id: 'PHARM-MEM-0042', name: "St. Jude Children's Research Hospital", label: 'St. Jude Pediatric', sub: 'Clinical Oncology (T-4)', tier: 4, cx: 700, cy: 110, centrality: 0.0012, coldChain: true },
  { id: 'PHARM-NYC-0012', name: 'New York Presbyterian Hospital', label: 'NY Presbyterian', sub: 'Formulary Center (T-4)', tier: 4, cx: 700, cy: 230, centrality: 0.0009, coldChain: false }
];

export const NetworkLineagePage: React.FC = () => {
  const [maxHops, setMaxHops] = useState<number>(3);
  const [centralityThreshold, setCentralityThreshold] = useState<string>('0.005');
  const [coldChainOnly, setColdChainOnly] = useState<boolean>(true);
  const [selectedNode, setSelectedNode] = useState<string>('EST-0002');
  const [topologyData, setTopologyData] = useState<any>(null);
  const [spofRankings, setSpofRankings] = useState<any[]>([]);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const numThreshold = parseFloat(centralityThreshold) || 0.005;

  // Minimum tier visible based on maxHops:
  // Hop 1: Only Tier 3 (Distributor) and Tier 4 (Clinic) [1 hop distance]
  // Hop 2: Tier 2 (Formulation), Tier 3, Tier 4 [2 hops distance]
  // Hop 3+: All 4 tiers [Full deep provenance]
  const minVisibleTier = maxHops === 1 ? 3 : maxHops === 2 ? 2 : 1;

  const loadNetworkData = async () => {
    setIsRefreshing(true);
    try {
      const [topo, spof] = await Promise.all([
        fetchTopology(),
        fetchSpofRankings(10)
      ]);
      if (topo) setTopologyData(topo);
      if (spof && spof.rankings) setSpofRankings(spof.rankings);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadNetworkData();
  }, []);

  // Compute facility inspector info based on selected node
  const getNodeDetails = (nodeId: string) => {
    const spofMatch = spofRankings.find((r) => r.node_id === nodeId);
    switch (nodeId) {
      case 'API-ZHEJIANG':
        return {
          name: 'Zhejiang Hisun Bio API Lab',
          fei: 'FEI-300184',
          tier: 'API Primary Synthesis (T-1)',
          centrality: '0.0041',
          gmp: 'cGMP Approved',
          risk: 'PRIMARY API SOURCE',
          drugs: ['Cisplatin Active Compound', 'Anthracycline Molecules']
        };
      case 'API-TEVA':
        return {
          name: 'Teva Active API Synthesis',
          fei: 'FEI-200918',
          tier: 'API Primary Synthesis (T-1)',
          centrality: '0.0032',
          gmp: 'cGMP Approved',
          risk: 'STABLE API SOURCE',
          drugs: ['Methotrexate USP', 'Fentanyl Base Citrate']
        };
      case 'EST-0001':
        return {
          name: 'Hospira Inc. / Pfizer (FEI-1002381)',
          fei: 'FEI-1002381',
          tier: 'Formulation & Sterile Vials (T-2)',
          centrality: spofMatch?.betweenness_centrality ? spofMatch.betweenness_centrality.toFixed(4) : '0.0084',
          gmp: 'VAI (Acceptable)',
          risk: 'CRITICAL SPOF (1.7x MULTIPLIER)',
          drugs: ['Adalimumab Injection', 'Fentanyl Citrate 100mcg', 'Methotrexate 50mg/2mL']
        };
      case 'DIST-0014':
        return {
          name: 'AmerisourceBergen Northeast DC (DIST-0014)',
          fei: 'FEI-2018894',
          tier: 'Regional Distribution Hub (T-3)',
          centrality: spofMatch?.betweenness_centrality ? spofMatch.betweenness_centrality.toFixed(4) : '0.0112',
          gmp: 'cGMP Compliant',
          risk: 'CRITICAL BOTTLENECK (TOP σ=0.0112)',
          drugs: ['Cisplatin Multi-Depot', 'Heparin Sodium', 'Lidocaine HCl', 'Pediatric Biologics']
        };
      case 'DIST-0001':
        return {
          name: 'AmerisourceBergen Central Hub (DIST-0001)',
          fei: 'FEI-2018801',
          tier: 'Regional Distribution Hub (T-3)',
          centrality: '0.0076',
          gmp: 'cGMP Compliant',
          risk: 'HIGH VOLUME CHOKE',
          drugs: ['Clonazepam Tablets', 'Emergency Vasopressors', 'Saline IV Bags']
        };
      case 'PHARM-MEM-0042':
        return {
          name: "St. Jude Children's Research Hospital",
          fei: 'PHARM-MEM-0042',
          tier: 'Clinical Dispensing Point (T-4)',
          centrality: '0.0012',
          gmp: 'Formulary Active',
          risk: 'DOWNSTREAM IMPACT SITE',
          drugs: ['Cisplatin Inj. (0 Vials - STOCKOUT)', 'Pediatric Biologics']
        };
      case 'PHARM-NYC-0012':
        return {
          name: 'New York Presbyterian Hospital',
          fei: 'PHARM-NYC-0012',
          tier: 'Clinical Dispensing Point (T-4)',
          centrality: '0.0009',
          gmp: 'Formulary Active',
          risk: 'SECONDARY IMPACT SITE',
          drugs: ['Oncology Formulations', 'ICU Sedatives']
        };
      case 'EST-0002':
      default:
        return {
          name: 'Hikma Pharmaceuticals Columbus (FEI-3002808)',
          fei: 'FEI-3002808',
          tier: 'Formulation & Fill-Finish (T-2)',
          centrality: spofMatch?.betweenness_centrality ? spofMatch.betweenness_centrality.toFixed(4) : '0.0112',
          gmp: 'OAI (Warning Letter)',
          risk: 'HIGH RISK (SOLE SOURCE)',
          drugs: ['Cisplatin Inj. 50mg/50mL', 'Lidocaine HCl Inj. 1%', 'Promethazine HCl']
        };
    }
  };

  const activeDetails = getNodeDetails(selectedNode);

  // Dynamic filter computations
  const visibleNodes = ALL_GRAPH_NODES.filter((n) => n.tier >= minVisibleTier);
  const chokeNodes = visibleNodes.filter((n) => n.centrality >= numThreshold);
  const activeNodeCount = maxHops === 1 ? 38 : maxHops === 2 ? 84 : maxHops === 3 ? 128 : 210;
  const activeEdgeCount = maxHops === 1 ? 64 : maxHops === 2 ? 172 : maxHops === 3 ? 312 : 486;

  // Filter audit records by maxHops
  const visibleAudit = INITIAL_AUDIT_TRAIL.filter((rec) => {
    const hopFromClinic = 5 - rec.step;
    return hopFromClinic <= maxHops;
  });

  return (
    <div className="flex flex-col gap-5">
      {/* Query & Topology Control Toolbar */}
      <section className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Left Controls */}
          <div className="flex flex-wrap items-center gap-3 text-xs">
            {/* Hop Distance */}
            <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
              <label className="font-semibold text-slate-500 uppercase font-mono text-[11px]" htmlFor="hop-select">
                Max Hop Distance:
              </label>
              <select
                id="hop-select"
                value={maxHops}
                onChange={(e) => setMaxHops(Number(e.target.value))}
                className="bg-white text-slate-900 font-mono text-xs px-2 py-0.5 rounded border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 font-bold"
              >
                <option value={1}>1 Hop (Direct Distribution)</option>
                <option value={2}>2 Hops (+ Formulation Line)</option>
                <option value={3}>3 Hops (+ Primary API)</option>
                <option value={4}>4 Hops (Deep Intermediary)</option>
                <option value={5}>5 Hops (Full E2E Genealogy)</option>
              </select>
            </div>

            {/* Centrality Filter */}
            <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
              <label className="font-semibold text-slate-500 uppercase font-mono text-[11px]" htmlFor="centrality-input">
                Betweenness Threshold:
              </label>
              <span className="font-mono text-slate-800 font-bold">&gt;=</span>
              <input
                id="centrality-input"
                type="text"
                value={centralityThreshold}
                onChange={(e) => setCentralityThreshold(e.target.value)}
                placeholder="0.005"
                className="w-20 bg-white text-slate-900 font-mono text-xs px-2 py-0.5 rounded text-center border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 font-bold"
              />
              <span className="text-slate-400 font-mono text-[10px]">σ(s,t|v)</span>
            </div>

            {/* Cold Chain Toggle */}
            <button
              onClick={() => setColdChainOnly(!coldChainOnly)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-mono text-xs transition-colors border ${
                coldChainOnly
                  ? 'bg-blue-50 border-blue-200 text-blue-700 font-semibold'
                  : 'bg-slate-50 border-slate-200 text-slate-600'
              }`}
            >
              <span className="material-symbols-outlined text-[16px] text-blue-600">ac_unit</span>
              <span>Cold-Chain Certified (2-8°C CRT)</span>
              <span className={`w-2 h-2 rounded-full ${coldChainOnly ? 'bg-blue-600' : 'bg-slate-300'}`}></span>
            </button>
          </div>

          {/* Right Summary & Action */}
          <div className="flex items-center gap-3">
            <div className="hidden xl:flex items-center gap-2 font-mono text-xs bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600">
              <span className="material-symbols-outlined text-[16px] text-blue-600">hub</span>
              <strong className="text-slate-900">{activeNodeCount}</strong> Active Nodes
              <span className="text-slate-300">/</span>
              <strong className="text-slate-900">{activeEdgeCount}</strong> Edges
              <span className="text-slate-300">/</span>
              <strong className="text-blue-600">{maxHops}</strong> Hops Horizon
            </div>
            <button
              onClick={loadNetworkData}
              disabled={isRefreshing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs shadow-xs transition-colors disabled:opacity-50"
            >
              <span className={`material-symbols-outlined text-[16px] ${isRefreshing ? 'animate-spin' : ''}`}>
                {isRefreshing ? 'progress_activity' : 'rebase_edit'}
              </span>
              <span>{isRefreshing ? 'Recomputing...' : 'Recompute Lineage Topology'}</span>
            </button>
          </div>
        </div>

        {/* Live Filter Telemetry Strip */}
        <div className="flex flex-wrap items-center justify-between text-xs font-mono pt-2 border-t border-slate-100 text-slate-500 gap-2">
          <div className="flex items-center gap-4">
            <span>
              FILTER STATUS:{' '}
              <strong className="text-slate-900">
                {minVisibleTier === 3 ? '1 Hop (Distributor -> Hospital)' : minVisibleTier === 2 ? '2 Hops (Mfg -> Dist -> Hospital)' : '3+ Hops (Full E2E DAG)'}
              </strong>
            </span>
            <span>•</span>
            <span>
              ACTIVE BOTTLENECK BRIDGES:{' '}
              <strong className={chokeNodes.length > 0 ? 'text-rose-600 font-bold' : 'text-emerald-600'}>
                {chokeNodes.length} nodes (σ ≥ {numThreshold})
              </strong>
            </span>
          </div>
          <span className="text-blue-600 font-semibold">Interactive Cypher DAG (Neo4j Protocol)</span>
        </div>
      </section>

      {/* Main 2-Column Split Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* LEFT 70% CANVAS: Graph & Audit Trail */}
        <div className="lg:col-span-8 xl:col-span-9 flex flex-col gap-5 min-w-0">
          {/* Topology Canvas Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden flex flex-col">
            <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-900 uppercase font-mono flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-blue-600 text-[18px]">account_tree</span>
                  Directed Multi-Tier API & Injectable Lineage ({maxHops} Hops Horizon)
                </span>
                <span className={`text-[11px] font-mono px-2 py-0.5 rounded font-bold border ${
                  chokeNodes.length > 0 ? 'bg-rose-50 border-rose-200 text-rose-700' : 'bg-emerald-50 border-emerald-200 text-emerald-700'
                }`}>
                  {chokeNodes.length > 0 ? `${chokeNodes.length} CRITICAL BOTTLENECK${chokeNodes.length > 1 ? 'S' : ''} (σ ≥ ${numThreshold})` : 'NO BOTTLENECKS (ALL σ < THRESHOLD)'}
                </span>
              </div>
              <div className="flex items-center gap-2 font-mono text-xs text-slate-500">
                <span className="text-[11px]">ZOOM 100% · CLICK NODES TO INSPECT</span>
              </div>
            </div>

            {/* Swimlane Headers */}
            <div className="grid grid-cols-4 bg-slate-100/70 text-center font-mono text-[11px] font-semibold text-slate-600 uppercase tracking-wider py-2 border-b border-slate-200">
              <div className={`flex items-center justify-center gap-1.5 transition-opacity ${minVisibleTier > 1 ? 'opacity-30' : 'opacity-100'}`}>
                <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                <span>Tier-1 API Synthesis {minVisibleTier > 1 && '(PRUNED)'}</span>
              </div>
              <div className={`flex items-center justify-center gap-1.5 transition-opacity ${minVisibleTier > 2 ? 'opacity-30' : 'opacity-100'}`}>
                <span className="w-2 h-2 rounded-full bg-rose-600"></span>
                <span>Formulation Line {minVisibleTier > 2 && '(PRUNED)'}</span>
              </div>
              <div className="flex items-center justify-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                <span>Regional Distribution</span>
              </div>
              <div className="flex items-center justify-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-slate-500"></span>
                <span>Clinical Point-of-Care</span>
              </div>
            </div>

            {/* Interactive Graph Swimlane Viewport */}
            <div className="relative w-full h-[380px] bg-white network-dot-grid p-4 overflow-hidden select-none">
              <svg className="w-full h-full" viewBox="0 0 800 340">
                {/* Swimlane Column Divider Lines */}
                <line x1="200" y1="0" x2="200" y2="340" stroke="#E2E8F0" strokeDasharray="3 3" strokeWidth="1" opacity={minVisibleTier > 1 ? 0.3 : 1} />
                <line x1="400" y1="0" x2="400" y2="340" stroke="#E2E8F0" strokeDasharray="3 3" strokeWidth="1" opacity={minVisibleTier > 2 ? 0.3 : 1} />
                <line x1="600" y1="0" x2="600" y2="340" stroke="#E2E8F0" strokeDasharray="3 3" strokeWidth="1" />

                {/* Connecting Edges: Tier 1 -> Tier 2 (Only visible if maxHops >= 3) */}
                {minVisibleTier <= 1 && (
                  <>
                    <path d="M 100 90 C 150 90, 250 120, 300 130" stroke="#94A3B8" strokeWidth="2" fill="none" />
                    <path d="M 100 240 C 150 240, 250 250, 300 260" stroke="#94A3B8" strokeWidth="2" fill="none" />
                  </>
                )}

                {/* Connecting Edges: Tier 2 -> Tier 3 (Only visible if maxHops >= 2) */}
                {minVisibleTier <= 2 && (
                  <>
                    <path d="M 300 130 C 350 130, 450 110, 500 110" stroke={0.0112 >= numThreshold ? '#E11D48' : '#94A3B8'} strokeWidth={0.0112 >= numThreshold ? 3 : 2} strokeDasharray={0.0112 >= numThreshold ? '4 2' : undefined} fill="none" />
                    <path d="M 300 260 C 350 260, 450 230, 500 230" stroke="#94A3B8" strokeWidth="2" fill="none" />
                  </>
                )}

                {/* Connecting Edges: Tier 3 -> Tier 4 (Always visible for maxHops >= 1) */}
                <path d="M 500 110 C 550 110, 650 110, 700 110" stroke="#94A3B8" strokeWidth="2" fill="none" />
                <path d="M 500 230 C 550 230, 650 230, 700 230" stroke="#94A3B8" strokeWidth="2" fill="none" />
                <path d="M 500 110 C 550 110, 650 230, 700 230" stroke="#CBD5E1" strokeWidth="1.5" strokeDasharray="3 3" fill="none" />

                {/* Render Nodes Dynamically */}
                {ALL_GRAPH_NODES.map((node) => {
                  const isVisible = node.tier >= minVisibleTier;
                  const isChoke = isVisible && node.centrality >= numThreshold;
                  const isSelected = selectedNode === node.id;
                  const isColdChainMatch = !coldChainOnly || node.coldChain;

                  return (
                    <g
                      key={node.id}
                      onClick={() => isVisible && setSelectedNode(node.id)}
                      className={`cursor-pointer transition-all duration-300 ${!isVisible ? 'opacity-20' : !isColdChainMatch ? 'opacity-40' : 'opacity-100'}`}
                    >
                      {/* Active Choke / Bottleneck Pulsing Aura */}
                      {isChoke && (
                        <circle
                          cx={node.cx}
                          cy={node.cy}
                          r={isSelected ? 22 : 18}
                          fill="none"
                          stroke="#E11D48"
                          strokeWidth="2"
                          strokeDasharray="4 2"
                        />
                      )}

                      {/* Selected Indicator Ring */}
                      {isSelected && (
                        <circle
                          cx={node.cx}
                          cy={node.cy}
                          r={20}
                          fill="none"
                          stroke="#2563EB"
                          strokeWidth="3"
                        />
                      )}

                      {/* Core Node Circle */}
                      <circle
                        cx={node.cx}
                        cy={node.cy}
                        r={isChoke ? 15 : 13}
                        fill={isChoke ? '#FEE2E2' : isSelected ? '#DBEAFE' : '#FFFFFF'}
                        stroke={isChoke ? '#E11D48' : isSelected ? '#2563EB' : '#475569'}
                        strokeWidth={isChoke ? 2.5 : 2}
                      />

                      {/* Node Label */}
                      <text
                        x={node.cx}
                        y={node.cy + 24}
                        textAnchor="middle"
                        className={`text-[10px] font-mono font-semibold ${
                          isChoke ? 'fill-rose-700 font-bold' : isSelected ? 'fill-blue-700 font-bold' : 'fill-slate-700'
                        }`}
                      >
                        {node.label}
                      </text>

                      {/* Betweenness Centrality Score Tag */}
                      <text
                        x={node.cx}
                        y={node.cy + 36}
                        textAnchor="middle"
                        className={`text-[9px] font-mono ${
                          isChoke ? 'fill-rose-600 font-bold' : 'fill-slate-400'
                        }`}
                      >
                        σ={node.centrality.toFixed(4)} {isChoke && '[SPOF]'}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>

          {/* Cryptographic 21 CFR Part 11 Provenance Audit Trail */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-600 text-[18px]">verified_user</span>
                <h3 className="font-mono text-xs font-bold text-slate-900 uppercase">
                  Cryptographic Custody Audit Trail (21 CFR Part 11) — {visibleAudit.length} Verified Events within {maxHops} Hops
                </h3>
              </div>
              <span className="text-[11px] font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded font-bold">
                CHAIN HASH INTEGRITY VERIFIED
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-50 text-[11px] font-semibold text-slate-500 uppercase font-mono border-b border-slate-200">
                    <th className="py-2 px-3">Step</th>
                    <th className="py-2 px-3">Custodian Entity</th>
                    <th className="py-2 px-3">Regulatory Action</th>
                    <th className="py-2 px-3 font-mono">Timestamp (UTC)</th>
                    <th className="py-2 px-3">Location</th>
                    <th className="py-2 px-3 font-mono">SHA-256 Hash</th>
                    <th className="py-2 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {visibleAudit.map((rec) => (
                    <tr key={rec.step} className="hover:bg-slate-50">
                      <td className="py-2.5 px-3 font-mono font-bold text-slate-900">0{rec.step}</td>
                      <td className="py-2.5 px-3 font-semibold text-slate-900">{rec.custodian}</td>
                      <td className="py-2.5 px-3">{rec.action}</td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-slate-500">{rec.timestamp}</td>
                      <td className="py-2.5 px-3 text-slate-600">{rec.location}</td>
                      <td className="py-2.5 px-3 font-mono text-blue-600 text-[11px]">{rec.hash}</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                            rec.status === 'VERIFIED'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : 'bg-rose-50 text-rose-700 border border-rose-200'
                          }`}
                        >
                          {rec.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* RIGHT 30% RAIL: Node Inspector Rail & Filtered SPOF List */}
        <div className="lg:col-span-4 xl:col-span-3 flex flex-col gap-4">
          {/* Node Inspector Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <span className="font-mono text-xs font-bold text-slate-900 uppercase">Node Inspector</span>
              <span className={`font-mono text-[11px] px-2 py-0.5 rounded border font-bold ${
                activeDetails.risk.includes('CRITICAL') || activeDetails.risk.includes('HIGH')
                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                  : 'bg-blue-50 text-blue-700 border-blue-200'
              }`}>
                {activeDetails.risk}
              </span>
            </div>

            <div className="flex flex-col gap-2 text-xs">
              <div>
                <span className="text-[11px] text-slate-400 font-mono">SELECTED FACILITY ({selectedNode}):</span>
                <h4 className="font-bold text-slate-900 text-sm">{activeDetails.name}</h4>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono pt-1">
                <div className="bg-slate-50 p-2 rounded border border-slate-200">
                  <span className="text-slate-500">FEI Identifier:</span>
                  <div className="font-bold text-slate-800">{activeDetails.fei}</div>
                </div>
                <div className="bg-slate-50 p-2 rounded border border-slate-200">
                  <span className="text-slate-500">Facility Tier:</span>
                  <div className="font-bold text-slate-800">{activeDetails.tier}</div>
                </div>
                <div className="bg-slate-50 p-2 rounded border border-slate-200">
                  <span className="text-slate-500">Betweenness Centrality:</span>
                  <div className="font-bold text-rose-600">{activeDetails.centrality} (σ)</div>
                </div>
                <div className="bg-slate-50 p-2 rounded border border-slate-200">
                  <span className="text-slate-500">GMP Status:</span>
                  <div className="font-bold text-amber-600">{activeDetails.gmp}</div>
                </div>
              </div>

              <div className="mt-2 pt-2 border-t border-slate-200 text-xs">
                <span className="text-[11px] text-slate-500 font-mono uppercase font-semibold">Supplied Clinical Catalog:</span>
                <ul className="mt-1 space-y-1 text-slate-700">
                  {activeDetails.drugs.map((drugName, idx) => (
                    <li key={idx} className="flex justify-between items-center bg-slate-50 px-2 py-1 rounded">
                      <span>{drugName}</span>
                      <span className="font-mono font-bold text-blue-600">Tracked</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Filtered SPOF Bottleneck Table */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <div className="flex items-center gap-1.5 font-mono text-xs font-bold text-slate-900 uppercase">
                <span className="material-symbols-outlined text-rose-600 text-[16px]">crisis_alert</span>
                <span>Filtered SPOF Rankings</span>
              </div>
              <span className="font-mono text-[10px] text-rose-600 font-bold bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                σ ≥ {numThreshold}
              </span>
            </div>

            <div className="flex flex-col gap-1.5 text-xs">
              {ALL_GRAPH_NODES
                .filter((n) => n.centrality >= numThreshold)
                .sort((a, b) => b.centrality - a.centrality)
                .map((n) => {
                  const isSelected = selectedNode === n.id;
                  return (
                    <div
                      key={n.id}
                      onClick={() => setSelectedNode(n.id)}
                      className={`p-2.5 rounded-lg border cursor-pointer transition-all flex items-center justify-between ${
                        isSelected
                          ? 'bg-blue-50 border-blue-400 ring-1 ring-blue-300'
                          : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      <div>
                        <div className="font-semibold text-slate-900 font-mono text-xs flex items-center gap-1.5">
                          {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>}
                          <span>{n.label}</span>
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono">{n.sub}</div>
                      </div>
                      <div className="text-right">
                        <span className="font-mono font-bold text-rose-600 text-xs">
                          {n.centrality.toFixed(4)}
                        </span>
                        <div className="text-[9px] font-mono text-slate-400">σ centrality</div>
                      </div>
                    </div>
                  );
                })}
              {ALL_GRAPH_NODES.filter((n) => n.centrality >= numThreshold).length === 0 && (
                <div className="p-3 text-center text-xs text-slate-400 font-mono">
                  No nodes meet threshold σ ≥ {numThreshold}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkLineagePage;
