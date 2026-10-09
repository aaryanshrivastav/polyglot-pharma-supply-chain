import React from 'react';
import { PageTab } from '../types';

interface HeaderProps {
  lastSync?: string;
  isLive?: boolean;
  activeTab: PageTab;
  onTabChange: (tab: PageTab) => void;
}

const NAV_TABS: { id: PageTab; label: string }[] = [
  { id: 'operational-tower', label: 'Operational Tower' },
  { id: 'network-lineage', label: 'Network Lineage' },
  { id: 'iot-telemetry', label: 'IoT Telemetry' },
  { id: 'disruption-simulator', label: 'Disruption Simulator' },
  { id: 'root-cause-lab', label: 'Root Cause Lab' },
  { id: 'polyglot-benchmarks', label: 'Polyglot Benchmarks' }
];

export const Header: React.FC<HeaderProps> = ({
  lastSync = '18:42:09 UTC',
  isLive = true,
  activeTab,
  onTabChange
}) => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 w-full shadow-sm">
      <div className="flex flex-col">
        {/* Tier 1: Authority Banner */}
        <div className="h-14 bg-[#131b2e] px-4 md:px-6 flex items-center justify-between text-white border-b border-[#1e293b]">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#316bf3] text-[22px]">shield_with_heart</span>
              <span className="text-xs md:text-sm uppercase tracking-wider text-white font-bold font-mono">
                PHARMA SUPPLY CHAIN FRAGILITY MONITOR
              </span>
            </div>
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-800 text-sky-300 text-[11px] font-mono border border-sky-500/30">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse"></span>
              FDA/CDS FEED LIVE
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-3 text-slate-300 font-mono text-[11px]">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                SYS ACTIVE
              </span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-100 font-semibold">{lastSync}</span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-400">NODE: US-EAST-01</span>
            </div>
            <div className="w-8 h-8 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center">
              <span className="material-symbols-outlined text-slate-200 text-[18px]">person</span>
            </div>
          </div>
        </div>

        {/* Tier 2: 6-Page Navigation Bar */}
        <div className="h-12 bg-white px-4 md:px-6 flex items-center justify-between border-b border-slate-200">
          <nav className="flex items-center gap-1 overflow-x-auto py-1 scrollbar-none">
            {NAV_TABS.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`px-3 py-1.5 text-xs rounded-md transition-colors whitespace-nowrap font-medium flex items-center ${
                    isActive
                      ? 'bg-[#316bf3] text-white font-semibold shadow-xs'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </nav>

          <div className="hidden lg:flex items-center gap-2 text-xs">
            <div className="flex items-center gap-1.5 bg-slate-50 px-2 py-1 rounded border border-slate-200 text-slate-500 font-mono text-[11px]">
              <span className="material-symbols-outlined text-[15px]">search</span>
              <span>FILTER REPOSITORY</span>
              <kbd className="bg-slate-200 px-1 py-0.5 rounded text-[10px] text-slate-700">⌘K</kbd>
            </div>
            <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-slate-100 text-slate-800 text-[11px] font-mono font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
              PROD-LIVE
            </span>
          </div>
        </div>

        {/* Tier 3: Domain Scope Sub-Toolbar */}
        <div className="w-full bg-[#f8fafc] px-4 md:px-6 py-2 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-4 text-slate-600">
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500 font-mono text-[11px] uppercase tracking-wider">Domain Scope:</span>
              <span className="font-semibold text-slate-900">Critical Injectables & Oncology</span>
            </div>
            <span className="text-slate-300 hidden sm:inline">•</span>
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500 font-mono text-[11px] uppercase tracking-wider">Surveillance:</span>
              <span className="font-mono text-slate-800 text-[11px]">USP &lt;659&gt; / EMA GMP Annex 1</span>
            </div>
            <span className="text-slate-300 hidden md:inline">•</span>
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500 font-mono text-[11px] uppercase tracking-wider">Active Incidents:</span>
              <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-mono text-[11px] font-bold">
                4 Critical
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 font-mono text-[11px]">
            <span className="text-slate-500">Audit Integrity:</span>
            <span className="text-blue-600 flex items-center gap-1 font-semibold">
              <span className="material-symbols-outlined text-[16px]">verified</span>
              VALIDATED CFR 21 P11
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
