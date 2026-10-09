export interface ShortageRecord {
  id: string;
  drug_name: string;
  generic_name?: string;
  manufacturer: string;
  status: 'CURRENT' | 'RESOLVED' | 'DISCONTINUED';
  date_reported: string;
  severity: 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW';
  ndc_code?: string;
}

export interface ManufacturerFragility {
  id: string;
  name: string;
  score: number; // 0 - 100
  status: 'CRITICAL' | 'ELEVATED' | 'NORMAL';
  spof_risk_index?: number;
  node_id?: string;
}

export interface SupplyChainEvent {
  id: string;
  timestamp: string;
  type: 'DISRUPTION' | 'RECOVERY' | 'WARNING' | 'INGESTION' | 'ALERT';
  message: string;
  facility_or_drug?: string;
}

export interface SystemHealthStatus {
  service: string;
  status: 'HEALTHY' | 'DEGRADED';
  timestamp: string;
  databases: {
    redis: 'ONLINE' | 'OFFLINE' | 'DEGRADED';
    mongodb: 'ONLINE' | 'OFFLINE' | 'DEGRADED';
    cassandra: 'ONLINE' | 'OFFLINE' | 'DEGRADED';
    neo4j: 'ONLINE' | 'OFFLINE' | 'DEGRADED';
  };
  latencies?: {
    redis_ms?: number;
    mongo_ms?: number;
    cassandra_ms?: number;
    neo4j_ms?: number;
  };
}

export interface PipelineStats {
  drugs_tracked: number;
  active_shortages: number;
  shortages_ratio_pct: number;
  manufacturers_monitored: number;
  last_sync: string;
}

export interface TopologyNode {
  id: string;
  label: string;
  type: 'mfg' | 'dist' | 'pharm';
  x: number;
  y: number;
  status: 'critical' | 'warning' | 'normal';
  centrality?: number;
}

export interface TopologyEdge {
  source: string;
  target: string;
  dashed?: boolean;
  alert?: boolean;
}

export type PageTab = 
  | 'operational-tower'
  | 'network-lineage'
  | 'iot-telemetry'
  | 'disruption-simulator'
  | 'root-cause-lab'
  | 'polyglot-benchmarks';

export interface ProvenanceAuditRecord {
  step: number;
  custodian: string;
  action: string;
  timestamp: string;
  location: string;
  hash: string;
  status: 'VERIFIED' | 'FLAGGED';
}

export interface SensorFleetItem {
  sensor_id: string;
  batch_id: string;
  drug_name: string;
  temperature: number;
  battery_pct: number;
  transit_corridor: string;
  status: 'NORMAL' | 'EXCURSION' | 'WARNING';
}


