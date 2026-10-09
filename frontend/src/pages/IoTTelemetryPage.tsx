import React, { useState, useEffect } from 'react';
import { fetchDrugTrends, subscribeEventsStream } from '../api';

interface ShipmentRow {
  sensorId: string;
  drugNdc: string;
  drugName: string;
  carrier: string;
  corridor: string;
  temp: number;
  tempDisplay?: string;
  battery: number;
  status: 'NOMINAL' | 'EXCURSION CRIT' | 'WARNING ELEV';
}

const FLEET_DATA: ShipmentRow[] = [
  {
    sensorId: 'IOT-TRK-8812',
    drugNdc: '0409-1166-02',
    drugName: 'Fentanyl Citrate',
    carrier: 'FedEx Custom Crit',
    corridor: 'I-80 W (Omaha → Denver)',
    temp: 3.8,
    battery: 94,
    status: 'NOMINAL'
  },
  {
    sensorId: 'IOT-TRK-9921',
    drugNdc: '0703-5147-01',
    drugName: 'Cisplatin Inj',
    carrier: 'World Courier',
    corridor: 'I-35 S (Memphis → DFW)',
    temp: 9.6,
    battery: 89,
    status: 'EXCURSION CRIT'
  },
  {
    sensorId: 'IOT-TRK-7740',
    drugNdc: '0069-4210-66',
    drugName: 'Lidocaine HCl',
    carrier: 'Amerisource Logistics',
    corridor: 'I-95 N (Richmond → Philly)',
    temp: 5.1,
    battery: 78,
    status: 'NOMINAL'
  },
  {
    sensorId: 'IOT-TRK-6302',
    drugNdc: '0093-0145-01',
    drugName: 'Metoprolol Succ',
    carrier: 'McKesson Direct',
    corridor: 'I-70 E (Kansas City → St. Louis)',
    temp: 21.2,
    tempDisplay: '21.2°C (CRT)',
    battery: 91,
    status: 'NOMINAL'
  },
  {
    sensorId: 'IOT-TRK-5521',
    drugNdc: '0591-0405-01',
    drugName: 'Clonazepam',
    carrier: 'DHL TempCare',
    corridor: 'I-10 W (Atlanta → New Orleans)',
    temp: 7.9,
    battery: 64,
    status: 'WARNING ELEV'
  },
  {
    sensorId: 'IOT-TRK-4409',
    drugNdc: '0069-3220-20',
    drugName: 'Promethazine Inj',
    carrier: 'Cardinal Express',
    corridor: 'I-94 W (Chicago → Mpls)',
    temp: 4.0,
    battery: 82,
    status: 'NOMINAL'
  }
];

export const IoTTelemetryPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSensor, setSelectedSensor] = useState('IOT-TRK-9921');
  const [quarantined, setQuarantined] = useState(false);
  const [streamLogs, setStreamLogs] = useState<Array<{ time: string; tag: string; msg: string; color: string }>>([
    { time: '18:42:07', tag: 'INGEST:', msg: 'Sensor TRK-9921 payload received (Probe 1: 4.8°C)', color: 'text-sky-400' },
    { time: '18:42:08', tag: 'ALARM_EV:', msg: 'EXCURSION_AUDIT_LOG stored into 21 CFR P11 record', color: 'text-red-400' },
    { time: '18:42:09', tag: 'SYNC:', msg: 'Partition 12 offset 49811202 flushed to store', color: 'text-slate-400' }
  ]);
  const [cassandraMetrics, setCassandraMetrics] = useState({
    avgTemp: 4.8,
    excursionCount: 4,
    totalVolume: 1842,
    source: 'CASSANDRA_LIVE'
  });

  // Pull live Cassandra time-series trends on mount
  useEffect(() => {
    fetchDrugTrends('DRUG_001', 30).then((data) => {
      if (data && data.trends && data.trends.length > 0) {
        const latest = data.trends[0];
        setCassandraMetrics({
          avgTemp: latest.avg_temperature || 4.8,
          excursionCount: latest.excursion_count || 4,
          totalVolume: latest.total_volume || 1842,
          source: data.source || 'CASSANDRA_TIME_SERIES'
        });
      }
    });

    // Listen to live Server-Sent Events from Redpanda/FastAPI
    const unsubscribe = subscribeEventsStream((event) => {
      if (event && event.message) {
        setStreamLogs((prev) => [
          {
            time: new Date().toISOString().substring(11, 19),
            tag: event.type ? `${event.type}:` : 'INGEST:',
            msg: event.message,
            color: event.type === 'DISRUPTION' || event.type === 'ALERT' ? 'text-red-400' : 'text-sky-400'
          },
          ...prev.slice(0, 7)
        ]);
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const filteredFleet = FLEET_DATA.filter(
    (row) =>
      row.sensorId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.drugName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.drugNdc.includes(searchTerm)
  );

  return (
    <div className="flex flex-col w-full pb-8 gap-5">
      {/* Top Metrics KPI Banner */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {/* Tile 1 */}
        <div className="bg-white rounded-xl p-4 shadow-sm flex flex-col justify-between border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase text-slate-500 tracking-wider">Active Sensor Fleets</span>
            <span className="inline-flex items-center gap-1.5 text-xs font-mono text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse"></span>
              99.8% ONLINE
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold text-slate-900 tracking-tight">1,842</span>
            <span className="text-xs text-slate-500">Cellular/BLE Nodes</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs font-mono text-slate-500">
            <span>Mesh Relays: <strong className="text-slate-800">312</strong></span>
            <span>Gateway Ping: <strong className="text-slate-800">18ms</strong></span>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full mt-3 overflow-hidden">
            <div className="bg-[#316bf3] h-full rounded-full" style={{ width: '94%' }}></div>
          </div>
        </div>

        {/* Tile 2 */}
        <div className="bg-white rounded-xl p-4 shadow-sm flex flex-col justify-between border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase text-slate-500 tracking-wider">In-Transit Consignments</span>
            <span className="material-symbols-outlined text-slate-400 text-[18px]">local_shipping</span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold text-slate-900 tracking-tight">418</span>
            <span className="text-xs text-slate-500">Live Batches</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs font-mono text-slate-500">
            <span>Cold Chain (2-8°C): <strong className="text-slate-800">284</strong></span>
            <span>CRT (15-25°C): <strong className="text-slate-800">134</strong></span>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full mt-3 overflow-hidden">
            <div className="bg-[#131b2e] h-full rounded-full" style={{ width: '78%' }}></div>
          </div>
        </div>

        {/* Tile 3 */}
        <div className="bg-white rounded-xl p-4 shadow-sm flex flex-col justify-between border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase text-slate-500 tracking-wider">Thermal Excursion Tally</span>
            <span className="inline-flex items-center gap-1.5 text-xs font-mono bg-red-100 text-red-800 px-2 py-0.5 rounded font-bold border border-red-200">
              <span className="w-1.5 h-1.5 rounded-full bg-red-600 animate-ping"></span>
              SURVEILLANCE ACTION
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-3">
            <div className="flex items-baseline gap-1">
              <span className="font-mono text-2xl font-bold text-red-600 tracking-tight">4</span>
              <span className="text-[11px] text-red-700 uppercase font-bold">Critical</span>
            </div>
            <span className="text-slate-300 font-mono">/</span>
            <div className="flex items-baseline gap-1">
              <span className="font-mono text-2xl font-bold text-slate-800 tracking-tight">11</span>
              <span className="text-[11px] text-slate-500 uppercase">Warnings</span>
            </div>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs font-mono text-slate-500">
            <span>Threshold: <strong className="text-red-600">&gt; 8.0°C</strong></span>
            <span>Mean Exposure: <strong className="text-slate-800">26.4m</strong></span>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full mt-3 overflow-hidden flex">
            <div className="bg-red-600 h-full" style={{ width: '28%' }}></div>
            <div className="bg-amber-400 h-full" style={{ width: '52%' }}></div>
          </div>
        </div>

        {/* Tile 4 */}
        <div className="bg-white rounded-xl p-4 shadow-sm flex flex-col justify-between border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase text-slate-500 tracking-wider">Kafka / Redpanda Ingest</span>
            <span className="text-xs font-mono text-blue-600 flex items-center gap-1">
              <span className="material-symbols-outlined text-[15px]">sensors</span>
              HEALTHY
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold text-slate-900 tracking-tight">14,250</span>
            <span className="text-xs text-slate-500">events / sec</span>
          </div>
          <div className="mt-2 grid grid-cols-2 gap-2 text-xs font-mono text-slate-500">
            <div>Lag: <strong className="text-slate-800 font-mono">12ms</strong></div>
            <div className="text-right">Cassandra: <strong className="text-slate-800 font-mono">4.2ms</strong></div>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full mt-3 overflow-hidden">
            <div className="bg-emerald-500 h-full rounded-full" style={{ width: '99.2%' }}></div>
          </div>
        </div>
      </div>

      {/* Operational Focus Layout: 7 cols left / 5 cols right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left Column (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-5 min-w-0">
          {/* Card 1: Multi-Series Thermal Sparkline */}
          <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-200 flex flex-col gap-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-100">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-red-100 text-red-800 font-mono text-[11px] font-bold">
                    EXCURSION DETECTED
                  </span>
                  <span className="font-mono text-xs text-slate-500 font-medium">CONSIGNMENT TRACKER</span>
                </div>
                <h2 className="text-xl font-bold text-slate-900 tracking-tight">TRK-BIOLOGIC-9921</h2>
                <p className="text-xs text-slate-500">
                  Cisplatin Injection USP (50mg/50mL) • Oncology Sterile Injectable • Target Range: +2.0°C to +8.0°C
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 text-slate-700 font-mono text-xs">
                  <span className="material-symbols-outlined text-[15px] text-red-600">warning</span>
                  DFW TRANSIT HUB
                </span>
                <button
                  onClick={() => alert('CFR Part 11 Audit Record cryptographic signature: SHA256:0x8fa99c27b140')}
                  className="bg-slate-900 text-white px-3 py-1.5 rounded-lg text-xs hover:bg-slate-800 transition-colors flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[15px]">file_download</span>
                  <span>Audit Log</span>
                </button>
              </div>
            </div>

            {/* Excursion Callout Banner */}
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2.5">
              <span className="material-symbols-outlined text-red-600 text-[20px] shrink-0">crisis_alert</span>
              <div className="flex-1 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs">
                <div>
                  <span className="font-bold text-red-800 uppercase">Excursion Event #EX-402:</span>
                  <span className="text-slate-800 ml-1">
                    Peaked at <strong className="font-mono text-red-700">+9.6°C</strong> for <strong className="font-mono">42 minutes</strong> (Dry ice sublimation delay during customs ramp transfer).
                  </span>
                </div>
                <span className="font-mono text-slate-500 shrink-0">14:20 - 15:02 UTC</span>
              </div>
            </div>

            {/* SVG Thermal Telemetry Chart */}
            <div className="relative w-full bg-slate-50 rounded-lg p-3 border border-slate-200 flex flex-col gap-2">
              <div className="flex items-center justify-between text-xs font-mono text-slate-500">
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-red-600 inline-block"></span>
                    Thermal Probe (#P-01)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-slate-400 border-t border-dashed inline-block"></span>
                    Upper Limit (+8.0°C)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-blue-600 inline-block"></span>
                    Lower Limit (+2.0°C)
                  </span>
                </div>
                <div className="font-mono text-[11px]">24-HOUR TELEMETRY RUN</div>
              </div>

              <div className="w-full h-60 relative">
                <svg className="w-full h-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 800 240">
                  <defs>
                    <linearGradient id="excursionGrad" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="#ef4444" stopOpacity="0.35" />
                      <stop offset="100%" stopColor="#ef4444" stopOpacity="0.0" />
                    </linearGradient>
                    <linearGradient id="normalGrad" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="#316bf3" stopOpacity="0.15" />
                      <stop offset="100%" stopColor="#316bf3" stopOpacity="0.0" />
                    </linearGradient>
                  </defs>

                  {/* Grid Lines */}
                  <line stroke="#cbd5e1" strokeDasharray="3 3" strokeWidth="1" x1="0" x2="800" y1="20" y2="20" />
                  <text fill="#64748b" fontFamily="JetBrains Mono" fontSize="10" x="5" y="25">+10.0°C</text>

                  {/* 8.0°C Upper Limit */}
                  <line stroke="#dc2626" strokeDasharray="6 4" strokeWidth="1.5" x1="0" x2="800" y1="60" y2="60" />
                  <text fill="#dc2626" fontFamily="JetBrains Mono" fontSize="10" fontWeight="600" x="710" y="55">LIMIT +8.0°C</text>

                  {/* 5.0°C Baseline */}
                  <line stroke="#cbd5e1" strokeDasharray="3 3" strokeWidth="1" x1="0" x2="800" y1="120" y2="120" />
                  <text fill="#64748b" fontFamily="JetBrains Mono" fontSize="10" x="5" y="125">+5.0°C</text>

                  {/* 2.0°C Lower Limit */}
                  <line stroke="#316bf3" strokeDasharray="6 4" strokeWidth="1.5" x1="0" x2="800" y1="180" y2="180" />
                  <text fill="#316bf3" fontFamily="JetBrains Mono" fontSize="10" fontWeight="600" x="710" y="175">LIMIT +2.0°C</text>

                  {/* Shaded excursion block */}
                  <rect fill="#fee2e2" fillOpacity="0.5" height="200" rx="4" width="130" x="490" y="20" />

                  {/* Curves */}
                  <path
                    d="M 40,140 Q 90,135 140,132 T 240,138 T 340,130 T 440,136 L 490,120 Q 520,30 550,28 T 600,65 L 630,130 Q 690,134 740,132 L 770,130 L 770,220 L 40,220 Z"
                    fill="url(#normalGrad)"
                  />
                  <path
                    d="M 490,120 Q 520,30 550,28 T 600,65 L 610,80 L 610,220 L 490,220 Z"
                    fill="url(#excursionGrad)"
                  />
                  <path
                    d="M 40,140 C 90,135 110,130 150,132 C 200,135 230,142 270,138 C 310,134 350,128 390,130 C 430,132 460,138 490,120 C 515,100 530,30 550,28 C 570,26 585,45 605,75 C 620,105 635,128 660,130 C 700,134 730,132 770,124"
                    fill="none"
                    stroke="#dc2626"
                    strokeLinecap="round"
                    strokeWidth="2.5"
                  />
                  <path
                    d="M 40,140 C 90,135 110,130 150,132 C 200,135 230,142 270,138 C 310,134 350,128 390,130 C 430,132 460,138 490,120"
                    fill="none"
                    stroke="#316bf3"
                    strokeLinecap="round"
                    strokeWidth="2.5"
                  />
                  <path
                    d="M 612,85 C 625,110 638,128 660,130 C 700,134 730,132 770,124"
                    fill="none"
                    stroke="#316bf3"
                    strokeLinecap="round"
                    strokeWidth="2.5"
                  />

                  {/* Peak Marker */}
                  <circle cx="550" cy="28" fill="#dc2626" r="6" />
                  <circle cx="550" cy="28" fill="#dc2626" fillOpacity="0.3" r="12" />
                  <g transform="translate(520, 6)">
                    <rect fill="#131b2e" height="18" rx="3" width="76" x="0" y="0" />
                    <text fill="#ffffff" fontFamily="JetBrains Mono" fontSize="9" fontWeight="bold" textAnchor="middle" x="38" y="13">
                      9.6°C (PEAK)
                    </text>
                  </g>

                  {/* Latest Observation */}
                  <circle cx="770" cy="124" fill="#316bf3" r="5" />

                  {/* Time labels */}
                  <text fill="#64748b" fontFamily="JetBrains Mono" fontSize="9" x="40" y="235">18:00 (-24h)</text>
                  <text fill="#64748b" fontFamily="JetBrains Mono" fontSize="9" x="220" y="235">23:00</text>
                  <text fill="#64748b" fontFamily="JetBrains Mono" fontSize="9" x="380" y="235">06:00</text>
                  <text fill="#dc2626" fontFamily="JetBrains Mono" fontSize="9" fontWeight="bold" x="510" y="235">14:20 EXCURSION</text>
                  <text fill="#64748b" fontFamily="JetBrains Mono" fontSize="9" x="720" y="235">NOW (18:42)</text>
                </svg>
              </div>

              {/* Sensor stats ribbon */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 pt-2 border-t border-slate-200">
                <div className="bg-white p-2 rounded border border-slate-200 flex flex-col">
                  <span className="text-[10px] uppercase text-slate-500 font-semibold">Current Temp</span>
                  <span className="font-mono text-sm font-bold text-slate-900">4.8°C</span>
                </div>
                <div className="bg-white p-2 rounded border border-slate-200 flex flex-col">
                  <span className="text-[10px] uppercase text-slate-500 font-semibold">24h Min Temp</span>
                  <span className="font-mono text-sm font-bold text-blue-600">2.4°C</span>
                </div>
                <div className="bg-white p-2 rounded border border-slate-200 flex flex-col">
                  <span className="text-[10px] uppercase text-slate-500 font-semibold">24h Max Temp</span>
                  <span className="font-mono text-sm font-bold text-red-600">9.6°C</span>
                </div>
                <div className="bg-white p-2 rounded border border-slate-200 flex flex-col">
                  <span className="text-[10px] uppercase text-slate-500 font-semibold">Rel. Humidity</span>
                  <span className="font-mono text-sm font-bold text-slate-800">42% RH</span>
                </div>
                <div className="bg-white p-2 rounded border border-slate-200 flex flex-col">
                  <span className="text-[10px] uppercase text-slate-500 font-semibold">Battery Pack</span>
                  <span className="font-mono text-sm font-bold text-slate-800 flex items-center gap-1">
                    89% <span className="material-symbols-outlined text-[14px] text-emerald-600">battery_5_bar</span>
                  </span>
                </div>
                <div className="bg-white p-2 rounded border border-slate-200 flex flex-col">
                  <span className="text-[10px] uppercase text-slate-500 font-semibold">Tilt Sensor</span>
                  <span className="font-mono text-sm font-bold text-slate-800">0° Stable</span>
                </div>
              </div>
            </div>

            {/* Actions Ribbon */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
              <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
                <span className="material-symbols-outlined text-[16px]">qr_code_scanner</span>
                <span>SN: <strong className="text-slate-800">SN-LOG-TX901-A</strong></span>
                <span>•</span>
                <span>NIST CALIBRATION: <strong className="text-emerald-700">2024-Q3 PASS</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => alert('Cold restock requisition dispatched to AmerisourceBergen Central Hub.')}
                  className="bg-slate-100 text-slate-800 px-3 py-1.5 rounded-lg text-xs font-semibold hover:bg-slate-200 transition-colors"
                >
                  Dispatch Cold Restock
                </button>
                <button
                  onClick={() => setQuarantined(!quarantined)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                    quarantined
                      ? 'bg-amber-600 text-white'
                      : 'bg-red-600 text-white hover:bg-red-700'
                  }`}
                >
                  {quarantined ? 'Quarantine Active' : 'Flag Quarantine Protocol'}
                </button>
              </div>
            </div>
          </div>

          {/* Card 2: Active Sensor Fleet Table */}
          <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-200 flex flex-col gap-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Active Sensor Fleet & Consignments</h3>
                <p className="text-xs text-slate-500">Live streaming payload telemetry across regional multi-modal corridors</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Search NDC, Sensor ID..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="bg-slate-50 border border-slate-200 text-slate-900 rounded-lg px-3 py-1 text-xs w-48 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            <div className="overflow-x-auto w-full">
              <table className="w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold uppercase text-[10px] tracking-wider">
                    <th className="py-2.5 px-3">Sensor ID</th>
                    <th className="py-2.5 px-3">Drug NDC & Name</th>
                    <th className="py-2.5 px-3">Carrier / Route</th>
                    <th className="py-2.5 px-3">GPS Corridor</th>
                    <th className="py-2.5 px-3 text-right">Temp (°C)</th>
                    <th className="py-2.5 px-3 text-right">Battery</th>
                    <th className="py-2.5 px-3 text-center">SLA Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredFleet.map((row) => {
                    const isExcursion = row.status === 'EXCURSION CRIT';
                    const isWarning = row.status === 'WARNING ELEV';
                    const isSelected = selectedSensor === row.sensorId;

                    return (
                      <tr
                        key={row.sensorId}
                        onClick={() => setSelectedSensor(row.sensorId)}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-blue-50/70'
                            : isExcursion
                            ? 'bg-red-50/60 hover:bg-red-50'
                            : isWarning
                            ? 'bg-amber-50/50 hover:bg-amber-50'
                            : 'hover:bg-slate-50'
                        }`}
                      >
                        <td className="py-2 px-3 font-mono font-semibold">
                          <div className="flex items-center gap-1.5">
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                isExcursion
                                  ? 'bg-red-600 animate-ping'
                                  : isWarning
                                  ? 'bg-amber-500'
                                  : 'bg-blue-600'
                              }`}
                            ></span>
                            {row.sensorId}
                          </div>
                        </td>
                        <td className="py-2 px-3">
                          <div className="font-semibold text-slate-900">{row.drugName}</div>
                          <div className="font-mono text-[11px] text-slate-500">{row.drugNdc}</div>
                        </td>
                        <td className="py-2 px-3 text-slate-700">{row.carrier}</td>
                        <td className="py-2 px-3 font-mono text-slate-600 text-[11px]">{row.corridor}</td>
                        <td
                          className={`py-2 px-3 font-mono text-right font-bold ${
                            isExcursion ? 'text-red-600' : 'text-slate-800'
                          }`}
                        >
                          {row.tempDisplay || `${row.temp.toFixed(1)}°C`}
                        </td>
                        <td className="py-2 px-3 font-mono text-right text-slate-600">{row.battery}%</td>
                        <td className="py-2 px-3 text-center">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                              isExcursion
                                ? 'bg-red-100 text-red-800'
                                : isWarning
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-slate-100 text-slate-800'
                            }`}
                          >
                            {row.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
              <span>Displaying {filteredFleet.length} of 418 monitored transit units</span>
              <span className="font-mono text-[11px]">PAGE 1 / 70</span>
            </div>
          </div>
        </div>

        {/* Right Column (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-5 min-w-0">
          {/* Card 3: Corridor Telemetry & Hub Map */}
          <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-200 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900">Corridor Telemetry & Hub Map</h3>
                <p className="text-xs text-slate-500">US National Logistics Corridors • Live Routing Status</p>
              </div>
              <span className="px-2 py-0.5 bg-slate-100 rounded text-xs font-mono text-slate-700">
                GEO-REF: CONUS
              </span>
            </div>

            {/* Map Canvas */}
            <div className="relative w-full h-72 bg-[#131b2e] rounded-lg overflow-hidden p-3 flex flex-col justify-between">
              <svg className="absolute inset-0 w-full h-full pointer-events-none" fill="none" viewBox="0 0 500 320">
                {/* Background guides */}
                <path d="M 40,70 Q 150,50 300,75 T 470,60" opacity="0.3" stroke="#475569" strokeDasharray="2 4" strokeWidth="0.8" />
                <path d="M 50,150 Q 200,140 340,165 T 460,140" opacity="0.3" stroke="#475569" strokeDasharray="2 4" strokeWidth="0.8" />
                <path d="M 60,240 Q 220,230 360,250 T 450,230" opacity="0.3" stroke="#475569" strokeDasharray="2 4" strokeWidth="0.8" />

                {/* Major Corridors */}
                <line stroke="#316bf3" strokeLinecap="round" strokeWidth="2" x1="150" x2="240" y1="140" y2="130" />
                <line stroke="#316bf3" strokeLinecap="round" strokeWidth="2" x1="250" x2="310" y1="160" y2="160" />
                <line stroke="#316bf3" strokeLinecap="round" strokeWidth="2" x1="310" x2="250" y1="120" y2="80" />
                <line stroke="#316bf3" strokeLinecap="round" strokeWidth="2" x1="410" x2="435" y1="140" y2="115" />
                <line stroke="#64748b" strokeDasharray="4 4" strokeLinecap="round" strokeWidth="2" x1="370" x2="320" y1="210" y2="250" />

                {/* Critical Excursion Track */}
                <line stroke="#ef4444" strokeLinecap="round" strokeWidth="3" x1="320" x2="240" y1="185" y2="225" />
                <circle cx="260" cy="215" fill="#ef4444" r="4" />

                {/* Hubs */}
                <circle cx="310" cy="120" fill="#94a3b8" r="4" />
                <text fill="#cbd5e1" fontFamily="JetBrains Mono" fontSize="9" x="318" y="124">ORD</text>

                <circle cx="320" cy="185" fill="#316bf3" r="6" />
                <circle cx="320" cy="185" opacity="0.6" r="10" stroke="#316bf3" strokeWidth="1" />
                <text fill="#93c5fd" fontFamily="JetBrains Mono" fontSize="9" fontWeight="bold" x="332" y="189">MEM HUB</text>

                <circle cx="370" cy="210" fill="#94a3b8" r="5" />
                <text fill="#cbd5e1" fontFamily="JetBrains Mono" fontSize="9" x="378" y="214">ATL</text>

                <circle cx="240" cy="225" fill="#ef4444" r="8" />
                <circle cx="240" cy="225" opacity="0.75" r="16" stroke="#ef4444" strokeWidth="1.5" />
                <text fill="#fecaca" fontFamily="JetBrains Mono" fontSize="10" fontWeight="bold" x="180" y="242">DFW EXCURSION</text>
              </svg>

              {/* Map header info */}
              <div className="relative z-10 flex items-center justify-between">
                <span className="inline-flex items-center gap-1.5 bg-slate-900/80 px-2 py-0.5 rounded text-[10px] font-mono text-sky-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                  RADAR: CONGESTION LOW
                </span>
                <div className="flex items-center gap-2 text-[10px] font-mono text-slate-300">
                  <span className="bg-slate-900/80 px-2 py-0.5 rounded">DFW AP: 34°C AMB</span>
                  <span className="bg-slate-900/80 px-2 py-0.5 rounded">MEM: 28°C AMB</span>
                </div>
              </div>

              {/* Map footer info */}
              <div className="relative z-10 bg-slate-900/90 rounded p-2 flex items-center justify-between text-[11px] font-mono text-white">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-blue-500"></span>Nominal Corridor</span>
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>Active Excursion</span>
                </div>
                <span className="text-slate-400">4 ROUTED AIR-LEGS</span>
              </div>
            </div>

            {/* Hub status matrix */}
            <div className="grid grid-cols-2 gap-2 pt-1">
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">DFW SuperHub</span>
                  <span className="px-1.5 py-0.2 rounded bg-red-100 text-red-700 text-[10px] font-mono font-bold">EXCURSION</span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                  <span>Transit: <strong className="text-slate-800">4h 12m</strong></span>
                  <span>Delay: <strong className="text-red-600">+42m</strong></span>
                </div>
              </div>

              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">MEM World Log</span>
                  <span className="px-1.5 py-0.2 rounded bg-blue-100 text-blue-700 text-[10px] font-mono font-bold">CLEAR</span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                  <span>Throughput: <strong className="text-slate-800">118 u/h</strong></span>
                  <span>Temp: <strong className="text-slate-800">4.1°C</strong></span>
                </div>
              </div>

              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">ORD Cold Fac</span>
                  <span className="px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-700 text-[10px] font-mono font-bold">OPTIMAL</span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                  <span>Vault Free: <strong className="text-slate-800">64%</strong></span>
                  <span>Chiller: <strong className="text-slate-800">3.2°C</strong></span>
                </div>
              </div>

              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">ATL Cargo Hub</span>
                  <span className="px-1.5 py-0.2 rounded bg-slate-200 text-slate-700 text-[10px] font-mono font-bold">MONITORED</span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                  <span>Congestion: <strong className="text-slate-800">15m</strong></span>
                  <span>Reefer: <strong className="text-slate-800">7.9°C</strong></span>
                </div>
              </div>
            </div>
          </div>

          {/* Card 4: Redpanda Stream Diagnostic */}
          <div className="bg-[#131b2e] text-white rounded-xl p-5 shadow-sm border border-slate-800 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-400 text-[20px]">hub</span>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Stream Pipeline Telemetry</h3>
              </div>
              <span className="font-mono text-[11px] text-sky-300 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                REDPANDA v23.3
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-[#0d1c2e] p-3 rounded-lg flex flex-col border border-slate-800">
                <span className="text-[10px] uppercase text-slate-400 font-semibold">Partitions (0-15)</span>
                <span className="font-mono text-base text-white font-bold mt-0.5">16 / 16 Balanced</span>
                <span className="text-slate-400 text-[10px] mt-1 font-mono">Skew: 0.02%</span>
              </div>
              <div className="bg-[#0d1c2e] p-3 rounded-lg flex flex-col border border-slate-800">
                <span className="text-[10px] uppercase text-slate-400 font-semibold">Dropped Packets</span>
                <span className="font-mono text-base text-emerald-400 font-bold mt-0.5">0.0000%</span>
                <span className="text-slate-400 text-[10px] mt-1 font-mono">CRC32 Valid</span>
              </div>
              <div className="bg-[#0d1c2e] p-3 rounded-lg flex flex-col border border-slate-800">
                <span className="text-[10px] uppercase text-slate-400 font-semibold">Cassandra Write</span>
                <span className="font-mono text-base text-white font-bold mt-0.5">4.2 ms</span>
                <span className="text-slate-400 text-[10px] mt-1 font-mono">Quorum Commit</span>
              </div>
              <div className="bg-[#0d1c2e] p-3 rounded-lg flex flex-col border border-slate-800">
                <span className="text-[10px] uppercase text-slate-400 font-semibold">Redis Hot Cache</span>
                <span className="font-mono text-base text-sky-400 font-bold mt-0.5">0.2 ms</span>
                <span className="text-slate-400 text-[10px] mt-1 font-mono">14.2k ops/s</span>
              </div>
            </div>

            <div className="bg-[#0a121d] rounded-lg p-3 font-mono text-[11px] flex flex-col gap-1 text-slate-400 border border-slate-800 max-h-40 overflow-y-auto">
              {streamLogs.map((log, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <span className="text-slate-500">[{log.time}]</span>
                  <span className={`font-semibold ${log.color}`}>{log.tag}</span>
                  <span className="truncate">{log.msg}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default IoTTelemetryPage;
