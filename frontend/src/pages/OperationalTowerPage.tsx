import React from 'react';
import { ShortagesTable } from '../components/ShortagesTable';
import { FragilityScores } from '../components/FragilityScores';
import { EventLog } from '../components/EventLog';
import { TopologyGraph } from '../components/TopologyGraph';
import { HealthAndStats } from '../components/HealthAndStats';
import { ShortageRecord, ManufacturerFragility, SupplyChainEvent, SystemHealthStatus, PipelineStats } from '../types';

interface OperationalTowerPageProps {
  shortages: ShortageRecord[];
  manufacturers: ManufacturerFragility[];
  events: SupplyChainEvent[];
  health: SystemHealthStatus;
  stats: PipelineStats;
  selectedDrug: ShortageRecord | null;
  selectedNode: string | null;
  activeSimulation: any | null;
  activeRootCause: any | null;
  onSelectDrug: (drug: ShortageRecord) => void;
  onSelectManufacturer: (mfg: ManufacturerFragility) => void;
  onNodeClick: (nodeId: string) => void;
  onRefreshHealth: () => void;
}

export const OperationalTowerPage: React.FC<OperationalTowerPageProps> = ({
  shortages,
  manufacturers,
  events,
  health,
  stats,
  selectedDrug,
  selectedNode,
  activeSimulation,
  activeRootCause,
  onSelectDrug,
  onSelectManufacturer,
  onNodeClick,
  onRefreshHealth
}) => {
  return (
    <div className="flex flex-col lg:flex-row gap-5">
      {/* LEFT COLUMN (65% width) - Shortage Table, Fragility Bars, Event Log */}
      <div className="w-full lg:w-[65%] flex flex-col gap-5">
        <ShortagesTable
          shortages={shortages}
          selectedDrugId={selectedDrug?.id}
          onSelectDrug={onSelectDrug}
        />

        <FragilityScores
          manufacturers={manufacturers}
          selectedId={selectedNode}
          onSelectManufacturer={onSelectManufacturer}
        />

        {/* Active Disruption Inspection Card */}
        {activeSimulation && (
          <div className="bg-amber-50/80 border border-amber-200 rounded-lg p-4 text-xs shadow-xs">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-amber-200">
              <span className="font-bold text-amber-900 uppercase font-mono">
                ACTIVE SIMULATION: {activeSimulation.target_node_id || activeSimulation.failed_node_id}
              </span>
              <span className="font-mono font-bold text-rose-700">
                IMPACT SCORE: {activeSimulation.impact_score}
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-[11px] text-amber-950 font-mono">
              <div>
                Affected Pharmacies: <strong>{activeSimulation.affected_pharmacy_count}</strong>
              </div>
              <div>
                Critical Drugs: <strong>{activeSimulation.critical_drug_count || 1}</strong>
              </div>
              <div>
                Status: <strong>{activeSimulation.propagation_status || 'SIMULATED'}</strong>
              </div>
              <div>
                Calculated: <strong>{activeSimulation.calculated_at?.substring(11, 19) || 'RECENT'}</strong>
              </div>
            </div>
          </div>
        )}

        {/* Active Root Cause Diagnostic Card */}
        {activeRootCause && activeRootCause.top_root_cause && (
          <div className="bg-sky-50/90 border border-sky-200 rounded-lg p-4 text-xs shadow-xs">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-sky-200">
              <span className="font-bold text-sky-900 uppercase font-mono flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-sky-600"></span>
                ROOT CAUSE DIAGNOSIS: {activeRootCause.query_drug_id}
              </span>
              <span className="font-mono font-bold text-sky-800">
                PROBABILITY: {(activeRootCause.top_root_cause.root_cause_probability * 100).toFixed(0)}%
              </span>
            </div>
            <div className="text-[11px] text-sky-950 font-mono space-y-1">
              <div>
                Primary Culprit: <strong className="text-slate-900">{activeRootCause.top_root_cause.candidate_id}</strong> ({activeRootCause.top_root_cause.node_type})
              </div>
              <div>
                Traversed Path: <span className="text-slate-600">{activeRootCause.top_root_cause.path}</span>
              </div>
              <div>
                Rationale: <span className="italic">{activeRootCause.top_root_cause.rationale}</span>
              </div>
            </div>
          </div>
        )}

        <EventLog events={events} isStreaming={true} />
      </div>

      {/* RIGHT COLUMN (35% width) - Network Topology, System Health, Pipeline Stats */}
      <div className="w-full lg:w-[35%] flex flex-col gap-5">
        <TopologyGraph onNodeClick={onNodeClick} selectedNodeId={selectedNode} />

        <HealthAndStats
          health={health}
          stats={stats}
          onRefreshHealth={onRefreshHealth}
        />
      </div>
    </div>
  );
};
