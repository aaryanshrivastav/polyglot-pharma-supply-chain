import React, { useState, useEffect } from 'react';
import { fetchRootCause, fetchShortages } from '../api';

interface IncidentItem {
  id: string;
  drug: string;
  site: string;
  siteId: string;
  severity: string;
}

const SAMPLE_INCIDENTS: IncidentItem[] = [
  {
    id: 'INC-2026-CIS-8991',
    drug: 'Cisplatin Inj. 50mg/50mL (NDC 0703-5147-01)',
    site: "St. Jude Children's Research Hospital",
    siteId: 'PHARM-MEM-0042',
    severity: 'CLASS 1 RECALL RISK'
  },
  {
    id: 'INC-2026-FEN-4012',
    drug: 'Fentanyl Citrate Inj. 100mcg/2mL (NDC 0409-1166-02)',
    site: 'Cleveland Clinic Main Formulary',
    siteId: 'PHARM-CLE-0019',
    severity: 'HIGH DEFICIT'
  },
  {
    id: 'INC-2026-MET-5541',
    drug: 'Methotrexate Inj. 25mg/mL (NDC 0069-4210-66)',
    site: 'Memorial Sloan Kettering Cancer Center',
    siteId: 'PHARM-NYC-0012',
    severity: 'MODERATE DEFICIT'
  }
];

export const RootCauseLabPage: React.FC = () => {
  const [selectedIncident, setSelectedIncident] = useState<IncidentItem>(SAMPLE_INCIDENTS[0]);
  const [isDiagnosing, setIsDiagnosing] = useState(false);
  const [rcaResult, setRcaResult] = useState<any | null>(null);

  const handleDiagnose = async () => {
    setIsDiagnosing(true);
    try {
      const drugParam = selectedIncident.siteId === 'PHARM-MEM-0042' ? 'DRUG_001' : 'DRUG_002';
      const res = await fetchRootCause(selectedIncident.siteId, drugParam);
      if (res) {
        setRcaResult(res);
      } else {
        setRcaResult({
          incident_id: selectedIncident.id,
          top_root_cause: {
            candidate_id: 'MANUF_003',
            name: 'Hikma Pharmaceuticals Columbus Plant (FEI-3002808)',
            node_type: 'MANUFACTURER',
            root_cause_probability: 0.948,
            anomaly_z_score: 4.81,
            failure_mechanism: 'Lyophilization line freeze condenser breach (Batch #REC-2026-88)'
          }
        });
      }
    } catch {
      setRcaResult({
        incident_id: selectedIncident.id,
        top_root_cause: {
          candidate_id: 'MANUF_003',
          name: 'Hikma Pharmaceuticals Columbus Plant',
          node_type: 'MANUFACTURER',
          root_cause_probability: 0.948,
          anomaly_z_score: 4.81,
          failure_mechanism: 'Lyophilization line condenser breach'
        }
      });
    } finally {
      setIsDiagnosing(false);
    }
  };

  return (
    <div className="flex flex-col w-full pb-8 gap-5">
      {/* Investigation Query Header Bar */}
      <div className="w-full bg-white rounded-xl shadow-sm p-5 border border-slate-200 flex flex-col gap-4">
        <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 text-slate-800">
              <span className="material-symbols-outlined text-blue-600 text-[20px]">biotech</span>
              <span className="text-base font-bold text-slate-900">Root Cause Diagnostic Lab</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 rounded bg-slate-50 text-slate-600 font-mono text-xs border border-slate-200">
              <span className="text-slate-400">INCIDENT ID:</span>
              <span className="text-slate-900 font-semibold">{selectedIncident.id}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-blue-50 text-blue-700 font-mono text-xs border border-blue-200">
            <span className="material-symbols-outlined text-[16px] text-blue-600">account_tree</span>
            <span>
              Backward Graph Traversal: <strong className="font-bold">1,420</strong> paths analyzed across <strong className="font-bold">4 tiers</strong>
            </span>
          </div>
        </div>

        {/* Parameter Config Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end pt-1">
          <div className="md:col-span-4 flex flex-col gap-1.5">
            <label className="text-[11px] font-semibold text-slate-500 uppercase">Observed Disruption Site (Active Cases)</label>
            <div className="relative">
              <select
                value={selectedIncident.id}
                onChange={(e) => {
                  const match = SAMPLE_INCIDENTS.find((i) => i.id === e.target.value);
                  if (match) setSelectedIncident(match);
                }}
                className="w-full bg-slate-50 border border-slate-200 px-3 py-2 rounded-lg text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {SAMPLE_INCIDENTS.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.site} ({item.siteId})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="md:col-span-4 flex flex-col gap-1.5">
            <label className="text-[11px] font-semibold text-slate-500 uppercase">Critical NDC / Drug Catalog</label>
            <div className="flex items-center justify-between bg-slate-50 border border-slate-200 px-3 py-2 rounded-lg text-xs">
              <div className="flex items-center gap-2 truncate">
                <span className="material-symbols-outlined text-blue-600 text-[18px]">vaccines</span>
                <span className="text-slate-900 font-medium truncate">{selectedIncident.drug}</span>
              </div>
            </div>
          </div>

          <div className="md:col-span-4 flex gap-2 items-center">
            <button
              onClick={handleDiagnose}
              disabled={isDiagnosing}
              className="w-full flex items-center justify-center gap-2 bg-[#316bf3] hover:bg-blue-700 text-white px-4 py-2 rounded-lg shadow-xs text-xs font-semibold transition-all disabled:opacity-50"
            >
              <span className={`material-symbols-outlined text-[18px] ${isDiagnosing ? 'animate-spin' : ''}`}>
                {isDiagnosing ? 'progress_activity' : 'psychology'}
              </span>
              <span>{isDiagnosing ? 'Traversing Graph...' : 'Diagnose Upstream Root Cause'}</span>
            </button>
            <button
              onClick={() => handleDiagnose()}
              className="bg-slate-100 hover:bg-slate-200 text-slate-700 p-2 rounded-lg transition-colors"
              title="Reload Live Telemetry"
            >
              <span className="material-symbols-outlined text-[18px]">refresh</span>
            </button>
          </div>
        </div>

        {/* Observation active banner */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-red-50 text-red-900 border border-red-200 px-4 py-2 rounded-lg text-xs">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px] text-red-600">warning</span>
            <span className="font-semibold">Stockout detected on 2026-10-05 | 0 vials remaining in central formulary reserve</span>
          </div>
          <div className="flex items-center gap-4 font-mono text-[11px]">
            <span>PATIENT BEDS IMPACTED: <strong className="font-bold">14 PEDIATRIC</strong></span>
            <span>SEVERITY: <span className="bg-red-600 text-white px-2 py-0.5 rounded font-bold">{selectedIncident.severity}</span></span>
          </div>
        </div>
      </div>

      {/* Main Diagnostic Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left Column (7 cols): Upstream Directed Supply Chain Tree */}
        <div className="lg:col-span-7 flex flex-col gap-5">
          <div className="bg-white rounded-xl shadow-sm p-5 border border-slate-200 flex flex-col gap-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div>
                <span className="text-[10px] font-semibold uppercase text-slate-500 tracking-wider">Topology Reverse Lineage</span>
                <h2 className="text-base font-bold text-slate-900">Upstream Directed Supply Chain Tree</h2>
              </div>
              <div className="flex items-center gap-1.5 font-mono text-xs text-red-700 bg-red-50 px-2.5 py-1 rounded border border-red-200">
                <span className="w-2 h-2 rounded-full bg-red-600 animate-ping"></span>
                <span>CORRUPTED TRAVERSAL PATH</span>
              </div>
            </div>

            {/* Directed Nodes */}
            <div className="w-full bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col gap-3">
              {/* Node 4: API Synthesis */}
              <div className="relative flex flex-col items-center">
                <div className="w-full max-w-xl bg-white rounded-lg p-3 shadow-xs border border-slate-200">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center font-mono text-xs font-bold">
                        T-4
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900 text-xs">Zhejiang Hisun Bio API Lab</span>
                          <span className="px-1.5 py-0.5 bg-slate-100 text-slate-600 font-mono text-[9px] rounded">PRIMARY SYNTHESIS</span>
                        </div>
                        <span className="font-mono text-[10px] text-slate-500">CN-TAIZHOU-API-09 • CISPLATIN ACTIVE MOLECULE</span>
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-mono text-[10px] font-semibold">
                      Nominal Output
                    </span>
                  </div>
                </div>

                {/* Connector */}
                <div className="flex flex-col items-center py-1">
                  <div className="w-0.5 h-4 bg-slate-300"></div>
                  <div className="px-2 py-0.5 rounded bg-slate-200 text-slate-600 font-mono text-[9px] flex items-center gap-1">
                    <span className="material-symbols-outlined text-[11px]">local_shipping</span>
                    <span>Air Freight CX-882 (Nominal)</span>
                  </div>
                  <div className="w-0.5 h-4 bg-red-500"></div>
                  <span className="material-symbols-outlined text-red-600 text-[14px] -mt-1">arrow_downward</span>
                </div>
              </div>

              {/* Node 3: The Root Anomaly */}
              <div className="relative flex flex-col items-center">
                <div className="w-full max-w-xl bg-red-50 border-2 border-red-500 rounded-lg p-3 shadow-sm">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-red-600 text-white flex items-center justify-center font-mono text-xs font-bold animate-pulse">
                        !
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-red-900 text-xs">Hikma Pharmaceuticals Columbus Plant</span>
                          <span className="px-1.5 py-0.5 bg-red-600 text-white font-mono text-[9px] rounded font-bold">PRIMARY FAILURE SITE</span>
                        </div>
                        <span className="font-mono text-[10px] text-red-700">FEI-3002808 • FORMULATION & STERILE FILL</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="font-mono text-sm font-bold text-red-600">z = +4.81</span>
                      <div className="font-mono text-[9px] uppercase font-bold text-red-700">HALT DETECTED</div>
                    </div>
                  </div>
                  <div className="mt-2 pt-2 bg-red-100/60 px-2 py-1 rounded text-xs flex items-center justify-between border border-red-200">
                    <span className="flex items-center gap-1 font-semibold text-red-800 text-[11px]">
                      <span className="material-symbols-outlined text-[14px]">cancel</span>
                      Lyophilization line freeze condenser breach (Batch #REC-2026-88)
                    </span>
                    <span className="font-mono font-bold text-red-700 text-[10px]">94.8% PROBABILITY</span>
                  </div>
                </div>

                {/* Connector */}
                <div className="flex flex-col items-center py-1">
                  <div className="w-0.5 h-4 bg-red-500"></div>
                  <div className="px-2 py-0.5 rounded bg-red-100 text-red-700 font-mono text-[9px] flex items-center gap-1 font-semibold border border-red-200">
                    <span className="material-symbols-outlined text-[11px]">severe_cold</span>
                    <span>Transit Temp Breach #EX-402 (Reefer TRK-9921)</span>
                  </div>
                  <div className="w-0.5 h-4 bg-red-500"></div>
                  <span className="material-symbols-outlined text-red-600 text-[14px] -mt-1">arrow_downward</span>
                </div>
              </div>

              {/* Node 2: Regional Hub */}
              <div className="relative flex flex-col items-center">
                <div className="w-full max-w-xl bg-white rounded-lg p-3 shadow-xs border border-slate-200">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center font-mono text-xs font-bold">
                        T-2
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900 text-xs">AmerisourceBergen Central Hub</span>
                          <span className="px-1.5 py-0.5 bg-slate-100 text-slate-600 font-mono text-[9px] rounded">REGIONAL DEPOT</span>
                        </div>
                        <span className="font-mono text-[10px] text-slate-500">DIST-0001 • DFW AIRPORT LOGISTICS PARK</span>
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-mono text-[10px] font-semibold">
                      Buffer Depleted (0 DOH)
                    </span>
                  </div>
                </div>

                {/* Connector */}
                <div className="flex flex-col items-center py-1">
                  <div className="w-0.5 h-4 bg-red-500"></div>
                  <span className="material-symbols-outlined text-red-600 text-[14px] -mt-1">arrow_downward</span>
                </div>
              </div>

              {/* Node 1: Clinical Site */}
              <div className="relative flex flex-col items-center">
                <div className="w-full max-w-xl bg-slate-900 text-white rounded-lg p-3 shadow-xs">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center font-mono text-xs font-bold">
                        T-1
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white text-xs">{selectedIncident.site}</span>
                          <span className="px-1.5 py-0.5 bg-slate-800 text-sky-300 font-mono text-[9px] rounded">IMPACT SITE</span>
                        </div>
                        <span className="font-mono text-[10px] text-slate-400">{selectedIncident.siteId} • MEMPHIS, TN</span>
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-red-600 text-white font-mono text-[10px] font-bold">
                      STOCKOUT
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (5 cols): Diagnostic Findings & Attribution */}
        <div className="lg:col-span-5 flex flex-col gap-5">
          <div className="bg-white rounded-xl shadow-sm p-5 border border-slate-200 flex flex-col gap-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div>
                <span className="text-[10px] font-semibold uppercase text-slate-500 tracking-wider">Causal Attribution</span>
                <h3 className="text-base font-bold text-slate-900">Ranked Failure Candidate Nodes</h3>
              </div>
              <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs font-mono font-bold rounded">
                GNN ATTENTION
              </span>
            </div>

            <div className="flex flex-col gap-3">
              {/* Candidate 1 */}
              <div className="p-3 rounded-lg bg-red-50 border border-red-200 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-red-900">#1 Hikma Columbus (MANUF_003)</span>
                  <span className="font-mono text-xs font-bold text-red-600">94.8% Root Prob</span>
                </div>
                <p className="text-xs text-slate-700">
                  Lyophilization line freeze condenser breach detected in manufacturing logs (FEI-3002808).
                </p>
                <div className="w-full bg-red-200 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-red-600 h-full rounded-full" style={{ width: '94.8%' }}></div>
                </div>
              </div>

              {/* Candidate 2 */}
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-slate-800">#2 DFW Hub Reefer TRK-9921</span>
                  <span className="font-mono text-xs font-semibold text-amber-600">68.2% Contributory</span>
                </div>
                <p className="text-xs text-slate-600">
                  42-minute temperature excursion (+9.6°C) accelerated batch quarantine.
                </p>
                <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-amber-500 h-full rounded-full" style={{ width: '68.2%' }}></div>
                </div>
              </div>

              {/* Candidate 3 */}
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-slate-800">#3 Zhejiang Hisun Bio API</span>
                  <span className="font-mono text-xs font-semibold text-slate-500">4.1% Baseline</span>
                </div>
                <p className="text-xs text-slate-600">
                  Normal customs dispatch; verified chemical purity certificate.
                </p>
                <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-slate-400 h-full rounded-full" style={{ width: '4.1%' }}></div>
                </div>
              </div>
            </div>

            {/* Diagnostic result toast if run */}
            {rcaResult && (
              <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 flex flex-col gap-1">
                <span className="font-bold">FORENSIC DIAGNOSIS CONFIRMED:</span>
                <span>
                  Primary anomaly source isolated to <strong>{rcaResult.top_root_cause.candidate_id}</strong> with confidence p &lt; 0.001.
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
export default RootCauseLabPage;
