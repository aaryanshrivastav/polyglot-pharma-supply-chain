import React from 'react';
import { ShortageRecord } from '../types';

interface ShortagesTableProps {
  shortages: ShortageRecord[];
  onSelectDrug?: (drug: ShortageRecord) => void;
  selectedDrugId?: string | null;
}

export const ShortagesTable: React.FC<ShortagesTableProps> = ({
  shortages,
  onSelectDrug,
  selectedDrugId
}) => {
  const criticalCount = shortages.filter((s) => s.severity === 'CRITICAL').length;

  return (
    <section className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden flex flex-col">
      {/* Card Header */}
      <div className="px-5 py-3.5 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2 bg-slate-50/70">
        <div className="flex items-center gap-2.5">
          <span className="w-2 h-4 bg-rose-600 rounded-sm"></span>
          <h2 className="text-xs font-bold text-slate-800 tracking-wider uppercase font-mono">
            ACTIVE SHORTAGES
          </h2>
          <span className="ml-1 text-[11px] text-slate-500 font-normal">
            Essential drug catalog surveillance
          </span>
        </div>
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-50 border border-rose-200 text-rose-700">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-600"></span>
          {criticalCount} critical incidents active
        </span>
      </div>

      {/* Table Responsive Container */}
      <div className="overflow-x-auto w-full">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="bg-slate-50/90 border-b border-slate-200 text-[11px] font-semibold text-slate-600 tracking-wider uppercase">
              <th className="py-2.5 px-4">Drug Name</th>
              <th className="py-2.5 px-4">Manufacturer</th>
              <th className="py-2.5 px-4">Status</th>
              <th className="py-2.5 px-4 font-mono-tabular">Date Reported</th>
              <th className="py-2.5 px-4">Severity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {shortages.map((item) => {
              const isSelected = selectedDrugId === item.id;
              return (
                <tr
                  key={item.id}
                  onClick={() => onSelectDrug && onSelectDrug(item)}
                  className={`hover:bg-slate-50/80 transition-colors cursor-pointer ${
                    isSelected ? 'bg-sky-50/50' : ''
                  }`}
                >
                  <td className="py-3 px-4 font-semibold text-slate-900 flex items-center gap-2">
                    <span>{item.drug_name}</span>
                  </td>
                  <td className="py-3 px-4 text-slate-600 font-medium">
                    {item.manufacturer}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium border ${
                        item.status === 'RESOLVED'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold'
                          : 'bg-slate-100 text-slate-700 border border-slate-200'
                      }`}
                    >
                      {item.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono-tabular text-slate-600 text-[11px]">
                    {item.date_reported}
                  </td>
                  <td className="py-3 px-4">
                    {item.severity === 'CRITICAL' && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-600"></span>
                        CRITICAL
                      </span>
                    )}
                    {item.severity === 'HIGH' && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-600"></span>
                        HIGH
                      </span>
                    )}
                    {item.severity === 'MODERATE' && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                        MODERATE
                      </span>
                    )}
                    {item.severity === 'LOW' && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-50 text-slate-700 border border-slate-200">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>
                        LOW
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
};

