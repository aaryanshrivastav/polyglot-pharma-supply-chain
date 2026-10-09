import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Footer } from './components/Footer';

import { OperationalTowerPage } from './pages/OperationalTowerPage';
import { NetworkLineagePage } from './pages/NetworkLineagePage';
import { IoTTelemetryPage } from './pages/IoTTelemetryPage';
import { DisruptionSimulatorPage } from './pages/DisruptionSimulatorPage';
import { RootCauseLabPage } from './pages/RootCauseLabPage';
import { PolyglotBenchmarksPage } from './pages/PolyglotBenchmarksPage';

import {
  INITIAL_SHORTAGES,
  INITIAL_MANUFACTURERS,
  INITIAL_EVENTS,
  INITIAL_HEALTH,
  INITIAL_STATS
} from './mockData';
import { ShortageRecord, ManufacturerFragility, PageTab } from './types';
import {
  fetchHealth,
  fetchSpofRankings,
  simulateDisruption,
  fetchEvents,
  subscribeEventsStream,
  fetchShortages,
  fetchPipelineStats,
  fetchRootCause
} from './api';

export const App: React.FC = () => {
  // Navigation State
  const [activeTab, setActiveTab] = useState<PageTab>(() => {
    const hash = window.location.hash.replace('#', '') as PageTab;
    const validTabs: PageTab[] = [
      'operational-tower',
      'network-lineage',
      'iot-telemetry',
      'disruption-simulator',
      'root-cause-lab',
      'polyglot-benchmarks'
    ];
    return validTabs.includes(hash) ? hash : 'operational-tower';
  });

  // Shared Data State
  const [shortages, setShortages] = useState<ShortageRecord[]>(INITIAL_SHORTAGES);
  const [manufacturers, setManufacturers] = useState<ManufacturerFragility[]>(INITIAL_MANUFACTURERS);
  const [events, setEvents] = useState(INITIAL_EVENTS);
  const [health, setHealth] = useState(INITIAL_HEALTH);
  const [stats, setStats] = useState(INITIAL_STATS);

  const [selectedDrug, setSelectedDrug] = useState<ShortageRecord | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [activeSimulation, setActiveSimulation] = useState<any | null>(null);
  const [activeRootCause, setActiveRootCause] = useState<any | null>(null);

  // Sync tab with browser hash
  const handleTabChange = (tab: PageTab) => {
    setActiveTab(tab);
    window.location.hash = tab;
  };

  // Poll or fetch system health on load
  const refreshHealth = async () => {
    const liveHealth = await fetchHealth();
    if (liveHealth && liveHealth.databases) {
      setHealth({
        service: liveHealth.service || 'polyglot-pharma-backend',
        status: liveHealth.status || 'HEALTHY',
        timestamp: liveHealth.timestamp || new Date().toISOString(),
        databases: liveHealth.databases,
        latencies: {
          redis_ms: 0.3,
          mongo_ms: 2.1,
          cassandra_ms: 4.7,
          neo4j_ms: 3.2
        }
      });
    }
  };

  useEffect(() => {
    refreshHealth();

    // Fetch real pipeline stats
    fetchPipelineStats().then((data) => {
      if (data && data.drugs_tracked) {
        setStats(data);
      }
    });

    // Fetch real shortage records from backend
    fetchShortages(10).then((data) => {
      if (data && data.shortages && data.shortages.length > 0) {
        setShortages(data.shortages);
      }
    });

    // Fetch initial event history from backend
    fetchEvents(15).then((data) => {
      if (data && data.events && data.events.length > 0) {
        setEvents(data.events);
      }
    });

    // Subscribe to real-time Server-Sent Events (SSE) stream
    const unsubscribe = subscribeEventsStream((incomingEvt) => {
      setEvents((prev) => {
        if (prev.some((e) => e.id === incomingEvt.id)) {
          return prev;
        }
        return [incomingEvt, ...prev].slice(0, 50);
      });
    });

    // Check backend SPOF rankings to enrich manufacturer scores if available
    const enrichSPOF = async () => {
      const spof = await fetchSpofRankings(10);
      if (spof && spof.rankings && spof.rankings.length > 0) {
        const updated = INITIAL_MANUFACTURERS.map((m) => {
          const match = spof.rankings.find((r: any) => r.node_id === m.node_id);
          if (match) {
            return {
              ...m,
              spof_risk_index: match.spof_risk_index,
              score: Math.round(match.spof_risk_index * 80 + 15)
            };
          }
          return m;
        });
        setManufacturers(updated);
      }
    };

    enrichSPOF();

    return () => {
      unsubscribe();
    };
  }, []);

  const handleSelectDrug = async (drug: ShortageRecord) => {
    setSelectedDrug(drug);
    const testPharmId = 'PHARM-1649791633';
    const rca = await fetchRootCause(testPharmId, drug.id.startsWith('DRUG-') ? drug.id : 'DRUG-0002-7597');
    if (rca) {
      setActiveRootCause(rca);
      if (rca.top_root_cause) {
        setEvents((prev) => [
          {
            id: `EVT-${Date.now()}`,
            timestamp: new Date().toISOString().substring(11, 16),
            type: 'ALERT',
            message: `Root cause identified for ${drug.drug_name}: ${rca.top_root_cause.candidate_id} (${rca.top_root_cause.node_type}, prob ${(rca.top_root_cause.root_cause_probability * 100).toFixed(0)}%)`
          },
          ...prev
        ]);
      }
    }
  };

  const handleSelectManufacturer = async (mfg: ManufacturerFragility) => {
    setSelectedNode(mfg.id);
    if (mfg.node_id) {
      const sim = await simulateDisruption(mfg.node_id);
      if (sim) {
        setActiveSimulation(sim);
        setEvents((prev) => [
          {
            id: `EVT-${Date.now()}`,
            timestamp: new Date().toISOString().substring(11, 16),
            type: 'ALERT',
            message: `Disruption simulated for ${mfg.name}: Impact Score ${sim.impact_score || 0}`
          },
          ...prev
        ]);
      }
    }
  };

  const handleNodeClick = async (nodeId: string) => {
    setSelectedNode(nodeId);
    const sim = await simulateDisruption(nodeId);
    if (sim) {
      setActiveSimulation(sim);
      setEvents((prev) => [
        {
          id: `EVT-${Date.now()}`,
          timestamp: new Date().toISOString().substring(11, 16),
          type: 'ALERT',
          message: `Topology node ${nodeId} evaluated: Impact Score ${sim.impact_score || 0}`
        },
        ...prev
      ]);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F8FAFC] text-[#0F172A]">
      <Header
        lastSync={stats.last_sync}
        isLive={true}
        activeTab={activeTab}
        onTabChange={handleTabChange}
      />

      {/* Main Container with offset for fixed 3-tier header (approx 140px) */}
      <main className="max-w-[1720px] w-full mx-auto p-4 md:p-6 pt-36 md:pt-40 flex-1 flex flex-col gap-5">
        {activeTab === 'operational-tower' && (
          <OperationalTowerPage
            shortages={shortages}
            manufacturers={manufacturers}
            events={events}
            health={health}
            stats={stats}
            selectedDrug={selectedDrug}
            selectedNode={selectedNode}
            activeSimulation={activeSimulation}
            activeRootCause={activeRootCause}
            onSelectDrug={handleSelectDrug}
            onSelectManufacturer={handleSelectManufacturer}
            onNodeClick={handleNodeClick}
            onRefreshHealth={refreshHealth}
          />
        )}

        {activeTab === 'network-lineage' && <NetworkLineagePage />}

        {activeTab === 'iot-telemetry' && <IoTTelemetryPage />}

        {activeTab === 'disruption-simulator' && <DisruptionSimulatorPage />}

        {activeTab === 'root-cause-lab' && <RootCauseLabPage />}

        {activeTab === 'polyglot-benchmarks' && <PolyglotBenchmarksPage />}
      </main>

      <Footer />
    </div>
  );
};

export default App;
