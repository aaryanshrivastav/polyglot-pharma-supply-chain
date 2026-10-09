import React from 'react';
import { SupplyChainEvent } from '../types';

interface EventLogProps {
  events: SupplyChainEvent[];
  isStreaming?: boolean;
}

export const EventLog: React.FC<EventLogProps> = ({ events, isStreaming = true }) => {
  const getBadgeStyle = (type: SupplyChainEvent['type']) => {
    switch (type) {
      case 'DISRUPTION':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'RECOVERY':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'WARNING':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'INGESTION':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'ALERT':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <section className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 md:p-5">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <span className="w-2 h-4 bg-sky-600 rounded-sm"></span>
          <h2 className="text-xs font-bold text-slate-800 tracking-wider uppercase font-mono">
            EVENT LOG
          </h2>
        </div>
        <span className="text-[11px] font-medium text-slate-500 font-mono flex items-center gap-1.5">
          <span className={`w-1.5 h-1.5 rounded-full ${isStreaming ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`}></span>
          REAL-TIME STREAM
        </span>
      </div>

      <div className="divide-y divide-slate-100 text-xs">
        {events.map((evt) => (
          <div key={evt.id} className="py-2.5 flex flex-wrap items-center gap-2.5">
            <span className="font-mono text-[11px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
              [{evt.timestamp}]
            </span>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wide uppercase border ${getBadgeStyle(
                evt.type
              )}`}
            >
              {evt.type}
            </span>
            <span className="text-slate-700 font-medium">
              — {evt.message}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
};

