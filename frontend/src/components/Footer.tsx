import React from 'react';

interface FooterProps {
  consoleId?: string;
  nodeStatus?: string;
}

export const Footer: React.FC<FooterProps> = ({
  consoleId = 'PSC-MONITOR-PROD-09',
  nodeStatus = 'NOMINAL'
}) => {
  return (
    <footer className="bg-white border-t border-slate-200 px-5 py-2.5 shrink-0 mt-auto">
      <div className="max-w-[1720px] mx-auto flex flex-col sm:flex-row justify-between items-center text-[11px] text-slate-500 gap-2">
        <div className="flex items-center gap-2">
          <span className="text-slate-400 uppercase font-medium">CONSOLE ID:</span>
          <span className="text-slate-800 font-mono font-semibold">{consoleId}</span>
          <span className="text-slate-300">|</span>
          <span className="text-slate-400 uppercase font-medium">NODE STATUS:</span>
          <span className="text-emerald-700 font-mono font-semibold">{nodeStatus}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span className="font-mono text-slate-600 text-[11px]">
            ENCRYPTED TLS 1.3 / FDA CDS FEEDS ONLINE
          </span>
        </div>
      </div>
    </footer>
  );
};

