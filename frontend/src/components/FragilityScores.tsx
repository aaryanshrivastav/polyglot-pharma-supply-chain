import React from 'react';
import { ManufacturerFragility } from '../types';

interface FragilityScoresProps {
  manufacturers: ManufacturerFragility[];
  onSelectManufacturer?: (mfg: ManufacturerFragility) => void;
  selectedId?: string | null;
}

export const FragilityScores: React.FC<FragilityScoresProps> = ({
  manufacturers,
  onSelectManufacturer,
  selectedId
}) => {
  return (
    <section className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 md:p-5">
      <div className="flex flex-wrap items-center justify-between pb-3 mb-4 border-b border-slate-200 gap-2">
        <div className="flex items-center gap-2">
          <span className="w-2 h-4 bg-amber-500 rounded-sm"></span>
          <h2 className="text-xs font-bold text-slate-800 tracking-wider uppercase font-mono">
            FRAGILITY SCORES BY MANUFACTURER
          </h2>
        </div>
        <span className="text-[11px] text-slate-500 font-mono-tabular">
          Threshold: <span className="font-semibold text-rose-600">&gt;75 Critical</span> •{' '}
          <span className="font-semibold text-amber-600">50–75 Elevated</span> •{' '}
          <span className="font-semibold text-slate-600">&lt;50 Stable</span>
        </span>
      </div>

      <div className="flex flex-col gap-3.5">
        {manufacturers.map((mfg) => {
          const isSelected = selectedId === mfg.id;
          const isCrit = mfg.score > 75;
          const isElev = mfg.score >= 50 && mfg.score <= 75;

          const dotColor = isCrit ? 'bg-rose-600' : isElev ? 'bg-amber-500' : 'bg-blue-600';
          const barColor = isCrit ? 'bg-rose-600' : isElev ? 'bg-amber-500' : 'bg-blue-600';
          const textColor = isCrit ? 'text-rose-700' : isElev ? 'text-amber-700' : 'text-blue-700';
          const badgeBg = isCrit ? 'bg-rose-50 border-rose-200 text-rose-700' : isElev ? 'bg-amber-50 border-amber-200 text-amber-700' : 'bg-blue-50 border-blue-200 text-blue-700';
          const badgeText = isCrit ? 'Crit' : isElev ? 'Elev' : 'Norm';

          return (
            <div
              key={mfg.id}
              onClick={() => onSelectManufacturer && onSelectManufacturer(mfg)}
              className={`flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-1.5 sm:gap-4 p-2 rounded-md hover:bg-slate-50 transition-colors cursor-pointer ${
                isSelected ? 'bg-amber-50/60 ring-1 ring-amber-300' : ''
              }`}
            >
              <div className="w-48 shrink-0 flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${dotColor}`}></span>
                <span className="font-semibold text-slate-900">{mfg.name}</span>
              </div>
              <div className="flex-1 bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div
                  className={`${barColor} h-full rounded-full transition-all duration-500`}
                  style={{ width: `${Math.min(100, Math.max(0, mfg.score))}%` }}
                ></div>
              </div>
              <div className="w-24 text-right shrink-0 font-mono-tabular">
                <span className={`text-sm font-bold ${textColor}`}>{mfg.score}</span>
                <span className="text-[11px] text-slate-400 font-normal">/100</span>
                <span className={`ml-1 text-[10px] font-semibold uppercase px-1 py-0.5 rounded border ${badgeBg}`}>
                  {badgeText}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

