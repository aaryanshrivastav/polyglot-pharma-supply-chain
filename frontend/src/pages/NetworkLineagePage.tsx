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
    location: 'Bethlehem, PA (DIST-0001)',
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

export const NetworkLineagePage: React.FC = () => {
  const [maxHops, setMaxHops] = useState<number>(3);
  const [centralityThreshold, setCentralityThreshold] = useState<string>('0.005');
  const [coldChainOnly, setColdChainOnly] = useState<boolean>(true);
  const [selectedNode, setSelectedNode] = useState<string>('EST-0002');
  const [auditRecords] = useState<ProvenanceAuditRecord[]>(INITIAL_AUDIT_TRAIL);
  const [topologyData, setTopologyData] = useState<any>(null);
  const [spofRankings, setSpofRankings] = useState<any[]>([]);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

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
      case 'EST-0001':
        return {
          name: 'Hospira Inc. (FEI-1002381)',
          fei: 'FEI-1002381',
          tier: 'API & Formulation (T-1)',
          centrality: spofMatch?.betweenness_centrality ? spofMatch.betweenness_centrality.toFixed(4) : '0.0084',
          gmp: 'VAI (Acceptable)',
          risk: 'MODERATE RISK',
          drugs: ['Fentanyl Citrate 100mcg', 'Methotrexate 50mg/2mL']
        };
      case 'DIST-0001':
      case 'DIST-0014':
        return {
          name: 'AmerisourceBergen Central DC (DIST-0014)',
          fei: 'FEI-2018894',
          tier: 'Regional Distribution Hub (T-3)',
          centrality: spofMatch?.betweenness_centrality ? spofMatch.betweenness_centrality.toFixed(4) : '0.0112',
          gmp: 'cGMP Compliant',
          risk: 'CRITICAL SPOF',
          drugs: ['Cisplatin Multi-Depot', 'Heparin Sodium', 'Lidocaine HCl']
        };
      case 'PHARM-MEM-0042':
      case 'PHARM-0001':
        return {
          name: "St. Jude Children's Research Hospital",
          fei: 'PHARM-MEM-0042',
          tier: 'Clinical Dispensing (T-4)',
          centrality: '0.0012',
          gmp: 'Formulary Active',
          risk: 'DOWNSTREAM IMPACT',
          drugs: ['Cisplatin Inj. (0 Vials - STOCKOUT)', 'Pediatric Biologics']
        };
      case 'EST-0002':
      default:
        return {
          name: 'Hikma Pharmaceuticals Columbus (FEI-3002808)',
          fei: 'FEI-3002808',
          tier: 'Formulation & Fill-Finish (T-2)',
          centrality: spofMatch?.betweenness_centrality ? spofMatch.betweenness_centrality.toFixed(4) : '0.0112',
          gmp: 'OAI (Warning Letter)',
          risk: 'HIGH RISK',
          drugs: ['Cisplatin Inj. 50mg/50mL (Sole Source)', 'Lidocaine HCl Inj. 1%', 'Promethazine HCl']
        };
    }
  };

  const activeDetails = getNodeDetails(selectedNode);

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
                className="bg-white text-slate-900 font-mono text-xs px-2 py-0.5 rounded border border-slate-200 focus:outline-none"
              >
                <option value={1}>1 Hop</option>
                <option value={2}>2 Hops</option>
                <option value={3}>3 Hops</option>
                <option value={4}>4 Hops</option>
                <option value={5}>5 Hops (Full E2E)</option>
              </select>
            </div>

            {/* Centrality Filter */}
            <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
              <label className="font-semibold text-slate-500 uppercase font-mono text-[11px]" htmlFor="centrality-input">
                Betweenness:
              </label>
              <span className="font-mono text-slate-800 font-bold">&gt;</span>
              <input
                id="centrality-input"
                type="text"
                value={centralityThreshold}
                onChange={(e) => setCentralityThreshold(e.target.value)}
                className="w-16 bg-white text-slate-900 font-mono text-xs px-2 py-0.5 rounded text-center border border-slate-200 focus:outline-none"
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
              <strong className="text-slate-900">{topologyData?.node_count || 128}</strong> Nodes
              <span className="text-slate-300">/</span>
              <strong className="text-slate-900">{topologyData?.edge_count || 312}</strong> Edges
              <span className="text-slate-300">/</span>
              <strong className="text-blue-600">4</strong> Tiers
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
                  Directed Multi-Tier API & Injectable Lineage
                </span>
                <span className="bg-rose-50 border border-rose-200 text-rose-700 text-[11px] font-mono px-2 py-0.5 rounded font-bold">
                  1 CRITICAL BOTTLENECK
                </span>
              </div>
              <div className="flex items-center gap-2 font-mono text-xs text-slate-500">
                <button className="p-1 rounded hover:bg-slate-200 text-slate-700">
                  <span className="material-symbols-outlined text-[18px]">add</span>
                </button>
                <button className="p-1 rounded hover:bg-slate-200 text-slate-700">
                  <span className="material-symbols-outlined text-[18px]">remove</span>
                </button>
                <button className="p-1 rounded hover:bg-slate-200 text-slate-700">
                  <span className="material-symbols-outlined text-[18px]">center_focus_strong</span>
                </button>
                <span className="text-slate-300">|</span>
                <span className="text-[11px]">ZOOM 100%</span>
              </div>
            </div>

            {/* Swimlane Headers */}
            <div className="grid grid-cols-4 bg-slate-100/70 text-center font-mono text-[11px] font-semibold text-slate-600 uppercase tracking-wider py-2 border-b border-slate-200">
              <div className="flex items-center justify-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                Tier-1 API Synthesis
              </div>
              <div className="flex items-center justify-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-rose-600"></span>
                Formulation & Fill-Finish
              </div>
              <div className="flex items-center justify-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                Regional Distribution Hubs
              </div>
              <div className="flex items-center justify-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-slate-500"></span>
                Clinical Point-of-Care
              </div>
            </div>

            {/* Interactive Graph Swimlane Viewport */}
            <div className="relative w-full h-[380px] bg-white network-dot-grid p-4 overflow-hidden select-none">
              <svg className="w-full h-full" viewBox="0 0 800 340">
                {/* Swimlane Column Divider Lines */}
                <line x1="200" y1="0" x2="200" y2="340" stroke="#E2E8F0" strokeDasharray="3 3" strokeWidth="1" />
                <line x1="400" y1="0" x2="400" y2="340" stroke="#E2E8F0" strokeDasharray="3 3" strokeWidth="1" />
                <line x1="600" y1="0" x2="600" y2="340" stroke="#E2E8F0" strokeDasharray="3 3" strokeWidth="1" />

                {/* Connecting Edges */}
                <path d="M 100 90 C 150 90, 250 120, 300 120" stroke="#94A3B8" strokeWidth="2" fill="none" />
                <path d="M 100 240 C 150 240, 250 140, 300 140" stroke="#94A3B8" strokeWidth="2" fill="none" />
                {/* Critical Bottleneck Link */}
                <path d="M 300 130 C 350 130, 450 170, 500 170" stroke="#E11D48" strokeWidth="2.5" strokeDasharray="4 2" fill="none" />
                <path d="M 500 170 C 550 170, 650 110, 700 110" stroke="#94A3B8" strokeWidth="2" fill="none" />
                <path d="M 500 170 C 550 170, 650 230, 700 230" stroke="#94A3B8" strokeWidth="2" fill="none" />

                {/* Tier 1 Nodes */}
                <g onClick={() => setSelectedNode('API-ZHEJIANG')} className="cursor-pointer">
                  <circle cx="100" cy="90" r="14" fill="#FFFFFF" stroke="#0F172A" strokeWidth="2.5" />
                  <text x="100" y="125" textAnchor="middle" className="text-[10px] font-mono fill-slate-700 font-semibold">Zhejiang Hisun</text>
                </g>
                <g onClick={() => setSelectedNode('API-TEVA')} className="cursor-pointer">
                  <circle cx="100" cy="240" r="14" fill="#FFFFFF" stroke="#64748B" strokeWidth="2" />
                  <text x="100" y="275" textAnchor="middle" className="text-[10px] font-mono fill-slate-700 font-semibold">Teva Active API</text>
                </g>

                {/* Tier 2 Formulation Nodes (Critical Bottleneck) */}
                <g onClick={() => setSelectedNode('EST-0002')} className="cursor-pointer">
                  <circle cx="300" cy="130" r="18" fill="#FEE2E2" stroke="#FDA4AF" strokeWidth="1" />
                  <circle cx="300" cy="130" r="12" fill="#E11D48" stroke="#FFFFFF" strokeWidth="2" />
                  <text x="300" y="168" textAnchor="middle" className="text-[11px] font-mono fill-rose-700 font-bold">Hikma (FEI-3002808)</text>
                  <text x="300" y="180" textAnchor="middle" className="text-[9px] font-mono fill-rose-600 font-semibold">CRITICAL BOTTLENECK</text>
                </g>

                {/* Tier 3 Distributor Hub */}
                <g onClick={() => setSelectedNode('DIST-0001')} className="cursor-pointer">
                  <circle cx="500" cy="170" r="15" fill="#DBEAFE" stroke="#2563EB" strokeWidth="2.5" />
                  <text x="500" y="205" textAnchor="middle" className="text-[10px] font-mono fill-blue-800 font-semibold">AmerisourceBergen DC</text>
                </g>

                {/* Tier 4 Clinical Dispensing Nodes */}
                <g onClick={() => setSelectedNode('PHARM-MEM-0042')} className="cursor-pointer">
                  <circle cx="700" cy="110" r="13" fill="#FFFFFF" stroke="#DC2626" strokeWidth="2.5" />
                  <text x="700" y="140" textAnchor="middle" className="text-[10px] font-mono fill-rose-700 font-semibold">St. Jude Pediatric</text>
                </g>
                <g onClick={() => setSelectedNode('PHARM-NYC-0012')} className="cursor-pointer">
                  <circle cx="700" cy="230" r="13" fill="#FFFFFF" stroke="#059669" strokeWidth="2" />
                  <text x="700" y="260" textAnchor="middle" className="text-[10px] font-mono fill-slate-700 font-semibold">NY Presbyterian</text>
                </g>
              </svg>
            </div>
          </div>

          {/* Cryptographic 21 CFR Part 11 Provenance Audit Trail */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-600 text-[18px]">verified_user</span>
                <h3 className="font-mono text-xs font-bold text-slate-900 uppercase">
                  Cryptographic Custody Audit Trail (21 CFR Part 11)
                </h3>
              </div>
              <span className="text-[11px] font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
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
                  {auditRecords.map((rec) => (
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

        {/* RIGHT 30% RAIL: Node Inspector Rail */}
        <div className="lg:col-span-4 xl:col-span-3 flex flex-col gap-4">
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
        </div>
      </div>
    </div>
  );
};
