import { ShortageRecord, ManufacturerFragility, SupplyChainEvent, SystemHealthStatus, PipelineStats } from './types';

export const INITIAL_SHORTAGES: ShortageRecord[] = [
  {
    id: 'DRUG-0001',
    drug_name: 'Fentanyl Citrate Injection',
    manufacturer: 'Hospira/Pfizer',
    status: 'CURRENT',
    date_reported: '2024-03-15',
    severity: 'CRITICAL',
    ndc_code: '0409-9093'
  },
  {
    id: 'DRUG-0002',
    drug_name: 'Lidocaine HCl Injection',
    manufacturer: 'Hikma Pharmaceuticals',
    status: 'CURRENT',
    date_reported: '2012-02-22',
    severity: 'HIGH',
    ndc_code: '0143-9524'
  },
  {
    id: 'DRUG-0003',
    drug_name: 'Metoprolol Succinate ER Tab',
    manufacturer: 'Teva Pharmaceuticals',
    status: 'RESOLVED',
    date_reported: '2026-08-31',
    severity: 'MODERATE',
    ndc_code: '0093-7679'
  },
  {
    id: 'DRUG-0004',
    drug_name: 'Clonazepam Tablet',
    manufacturer: 'Accord Healthcare',
    status: 'CURRENT',
    date_reported: '2023-03-10',
    severity: 'HIGH',
    ndc_code: '16729-137'
  },
  {
    id: 'DRUG-0005',
    drug_name: 'Promethazine HCl Injection',
    manufacturer: 'Hikma Pharmaceuticals',
    status: 'CURRENT',
    date_reported: '2023-11-21',
    severity: 'HIGH',
    ndc_code: '0143-9876'
  },
  {
    id: 'DRUG-0006',
    drug_name: 'Cisplatin Injection',
    manufacturer: 'Intas Pharmaceuticals',
    status: 'CURRENT',
    date_reported: '2023-02-14',
    severity: 'CRITICAL',
    ndc_code: '68001-283'
  }
];

export const INITIAL_MANUFACTURERS: ManufacturerFragility[] = [
  {
    id: 'MFG-HIKMA',
    node_id: 'EST-0002',
    name: 'Hikma Pharmaceuticals',
    score: 82,
    status: 'CRITICAL'
  },
  {
    id: 'MFG-HOSPIRA',
    node_id: 'EST-0001',
    name: 'Hospira/Pfizer',
    score: 76,
    status: 'CRITICAL'
  },
  {
    id: 'MFG-ACCORD',
    node_id: 'EST-0004',
    name: 'Accord Healthcare',
    score: 58,
    status: 'ELEVATED'
  },
  {
    id: 'MFG-TEVA',
    node_id: 'EST-0003',
    name: 'Teva Pharmaceuticals',
    score: 53,
    status: 'ELEVATED'
  },
  {
    id: 'MFG-SUN',
    node_id: 'EST-0005',
    name: 'Sun Pharmaceutical',
    score: 34,
    status: 'NORMAL'
  }
];

export const INITIAL_EVENTS: SupplyChainEvent[] = [
  {
    id: 'EVT-1',
    timestamp: '2026-10-06 21:12',
    type: 'DISRUPTION',
    message: 'Manufacturing halt reported: Hikma facility FEI-3002808'
  },
  {
    id: 'EVT-2',
    timestamp: '2026-10-06 20:48',
    type: 'RECOVERY',
    message: 'Teva resumes Metoprolol Succinate production, lot B-4419'
  },
  {
    id: 'EVT-3',
    timestamp: '2026-10-06 19:33',
    type: 'WARNING',
    message: 'Single-source dependency detected: Cisplatin (1 active mfg)'
  },
  {
    id: 'EVT-4',
    timestamp: '2026-10-06 18:05',
    type: 'INGESTION',
    message: '247 new FDA shortage records processed into staging'
  },
  {
    id: 'EVT-5',
    timestamp: '2026-10-06 17:20',
    type: 'ALERT',
    message: 'Betweenness centrality spike: node Hospira/Pfizer exceeds threshold'
  }
];

export const INITIAL_HEALTH: SystemHealthStatus = {
  service: 'polyglot-pharma-backend',
  status: 'HEALTHY',
  timestamp: new Date().toISOString(),
  databases: {
    redis: 'ONLINE',
    mongodb: 'ONLINE',
    cassandra: 'ONLINE',
    neo4j: 'ONLINE'
  },
  latencies: {
    redis_ms: 0.3,
    mongo_ms: 2.1,
    cassandra_ms: 4.7,
    neo4j_ms: 3.2
  }
};

export const INITIAL_STATS: PipelineStats = {
  drugs_tracked: 3000,
  active_shortages: 1635,
  shortages_ratio_pct: 54.5,
  manufacturers_monitored: 100,
  last_sync: '2026-10-06 21:43 UTC'
};

