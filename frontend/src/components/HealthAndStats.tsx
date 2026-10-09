import React from 'react';
import { SystemHealthStatus, PipelineStats } from '../types';

interface HealthAndStatsProps {
  health: SystemHealthStatus;
  stats: PipelineStats;
  onRefreshHealth?: () => void;
}

export const HealthAndStats: React.FC<HealthAndStatsProps> = ({ health, stats, onRefreshHealth }) => {
  const isHealthy = health.status === 'HEALTHY';

  const dbList = [
    {
      name: 'REDIS (KV Store)',
      status: health.databases.redis,
      latency: health.latencies?.redis_ms ?? 0.3
    },
    {
      name: 'MONGODB (Document)',
      status: health.databases.mongodb,
      latency: health.latencies?.mongo_ms ?? 2.1
    },
    {
      name: 'CASSANDRA (Columnar)',
      status: health.databases.cassandra,
      latency: health.latencies?.cassandra_ms ?? 4.7
    },
    {
      name: 'NEO4J (Graph)',
      status: health.databases.neo4j,
      latency: health.latencies?.neo4j_ms ?? 3.2
    }
  ];

  return (
    <>
      {/* Section 5 — SYSTEM HEALTH */}
      <section className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 md:p-5">
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <span className="w-2 h-4 bg-emerald-600 rounded-sm"></span>
            <h2 className="text-xs font-bold text-slate-800 tracking-wider uppercase font-mono">
              SYSTEM HEALTH
            </h2>
          </div>
          <button
            onClick={onRefreshHealth}
            title="Click to re-check health"
            className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 transition-colors px-2 py-0.5 rounded border border-emerald-200 font-mono-tabular"
          >
            {isHealthy ? 'ALL HEALTHY' : 'DEGRADED'}
          </button>
        </div>

        <div className="flex flex-col gap-2 text-xs">
          {dbList.map((db) => {
            const isOnline = db.status === 'ONLINE';
            return (
              <div
                key={db.name}
                className="flex justify-between items-center bg-slate-50/80 px-3 py-2 rounded border border-slate-200 hover:bg-slate-100/70 transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      isOnline ? 'bg-emerald-500' : 'bg-rose-500'
                    }`}
                  ></span>
                  <span className="font-medium text-slate-800">{db.name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={`font-semibold text-[10px] px-1.5 py-0.5 rounded border ${
                      isOnline
                        ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
                        : 'text-rose-700 bg-rose-50 border-rose-200'
                    }`}
                  >
                    {isOnline ? 'CONNECTED' : 'OFFLINE'}
                  </span>
                  <span className="font-mono text-slate-500 text-[11px]">
                    {db.latency.toFixed(1)}ms
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Section 6 — PIPELINE STATS */}
      <section className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 md:p-5">
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <span className="w-2 h-4 bg-blue-600 rounded-sm"></span>
            <h2 className="text-xs font-bold text-slate-800 tracking-wider uppercase font-mono">
              PIPELINE STATS
            </h2>
          </div>
          <span className="text-[11px] text-slate-500 font-mono-tabular">24H CYCLE</span>
        </div>

        <div className="grid grid-cols-1 gap-2.5">
          {/* Stat 1: Drugs Tracked */}
          <div className="bg-slate-50 border border-slate-200 p-3 rounded-md flex justify-between items-center">
            <div>
              <div className="text-[11px] font-semibold text-slate-600 uppercase tracking-wide">
                Drugs Tracked
              </div>
              <div className="text-[11px] text-emerald-600 font-medium font-mono-tabular mt-0.5 flex items-center gap-1">
                <span className="material-symbols-outlined text-[13px]">trending_up</span> +12 added today
              </div>
            </div>
            <div className="text-right">
              <span className="text-2xl font-bold text-slate-900 font-mono-tabular">
                {stats.drugs_tracked.toLocaleString()}
              </span>
            </div>
          </div>

          {/* Stat 2: Active Shortages */}
          <div className="bg-rose-50/60 border border-rose-200/80 p-3 rounded-md flex justify-between items-center">
            <div>
              <div className="text-[11px] font-semibold text-rose-900 uppercase tracking-wide flex items-center gap-1.5">
                <span>Active Shortages</span>
                <span className="w-1.5 h-1.5 rounded-full bg-rose-600"></span>
              </div>
              <div className="text-[11px] text-rose-700 font-medium font-mono-tabular mt-0.5">
                {stats.shortages_ratio_pct.toFixed(1)}% total corpus
              </div>
            </div>
            <div className="text-right">
              <span className="text-2xl font-bold text-rose-700 font-mono-tabular">
                {stats.active_shortages.toLocaleString()}
              </span>
            </div>
          </div>

          {/* Stat 3: Manufacturers Monitored */}
          <div className="bg-slate-50 border border-slate-200 p-3 rounded-md flex justify-between items-center">
            <div>
              <div className="text-[11px] font-semibold text-slate-600 uppercase tracking-wide">
                Manufacturers Monitored
              </div>
              <div className="text-[11px] text-slate-500 font-medium font-mono-tabular mt-0.5">
                Global entities
              </div>
            </div>
            <div className="text-right">
              <span className="text-2xl font-bold text-slate-900 font-mono-tabular">
                {stats.manufacturers_monitored.toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

