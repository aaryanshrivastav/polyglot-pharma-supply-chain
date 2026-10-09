import React, { useState } from 'react';

interface TopologyGraphProps {
  onNodeClick?: (nodeId: string) => void;
  selectedNodeId?: string | null;
}

export const TopologyGraph: React.FC<TopologyGraphProps> = ({ onNodeClick, selectedNodeId }) => {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  return (
    <section className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 md:p-5 flex flex-col">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <span className="w-2 h-4 bg-indigo-600 rounded-sm"></span>
          <h2 className="text-xs font-bold text-slate-800 tracking-wider uppercase font-mono">
            NETWORK TOPOLOGY
          </h2>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-emerald-700 font-medium bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
          GRAPH ACTIVE
        </div>
      </div>

      {/* Clean, Enterprise Node-Link Topology Graph */}
      <div className="relative w-full aspect-square border border-slate-200 rounded-md bg-white p-2 flex items-center justify-center network-dot-grid overflow-hidden shadow-inner">
        <svg
          className="w-full h-full relative z-10 select-none cursor-pointer"
          fill="none"
          viewBox="0 0 240 240"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="linkAlertGrad" x1="0%" x2="100%" y1="0%" y2="0%">
              <stop offset="0%" stopColor="#E11D48"></stop>
              <stop offset="100%" stopColor="#F59E0B"></stop>
            </linearGradient>
          </defs>

          {/* Network Topology Links */}
          <line
            stroke="url(#linkAlertGrad)"
            strokeDasharray="4 2"
            strokeWidth="2.5"
            x1="60"
            x2="160"
            y1="70"
            y2="60"
          ></line>
          <line stroke="#CBD5E1" strokeWidth="1.5" x1="60" x2="40" y1="70" y2="150"></line>
          <line stroke="#93C5FD" strokeWidth="2" x1="60" x2="110" y1="70" y2="130"></line>
          <line stroke="#CBD5E1" strokeWidth="1.5" x1="160" x2="200" y1="60" y2="120"></line>
          <line stroke="#FBBF24" strokeWidth="2" x1="160" x2="110" y1="60" y2="130"></line>
          <line stroke="#CBD5E1" strokeWidth="1.5" x1="110" x2="90" y1="130" y2="190"></line>
          <line stroke="#CBD5E1" strokeWidth="1.5" x1="110" x2="170" y1="130" y2="185"></line>
          <line stroke="#E2E8F0" strokeWidth="1.5" x1="40" x2="90" y1="150" y2="190"></line>
          <line stroke="#E2E8F0" strokeWidth="1.5" x1="200" x2="170" y1="120" y2="185"></line>
          <line stroke="#E2E8F0" strokeWidth="1.5" x1="170" x2="90" y1="185" y2="190"></line>
          <line stroke="#E2E8F0" strokeWidth="1.5" x1="60" x2="105" y1="70" y2="35"></line>
          <line stroke="#E2E8F0" strokeWidth="1.5" x1="160" x2="105" y1="60" y2="35"></line>

          {/* Secondary Nodes (Suppliers & Depots) */}
          <circle
            cx="40"
            cy="150"
            fill="#FFFFFF"
            r="5"
            stroke="#0284C7"
            strokeWidth="2.5"
            className="hover:stroke-sky-600 transition-colors"
            onClick={() => onNodeClick && onNodeClick('DIST-0014')}
          ></circle>
          <circle
            cx="200"
            cy="120"
            fill="#FFFFFF"
            r="5"
            stroke="#0284C7"
            strokeWidth="2.5"
            className="hover:stroke-sky-600 transition-colors"
            onClick={() => onNodeClick && onNodeClick('DIST-0011')}
          ></circle>
          <circle
            cx="110"
            cy="130"
            fill="#F8FAFC"
            r="6"
            stroke="#2563EB"
            strokeWidth="2.5"
            className="hover:stroke-blue-700 transition-colors"
            onClick={() => onNodeClick && onNodeClick('HUB-CENTRAL')}
          ></circle>
          <circle
            cx="90"
            cy="190"
            fill="#FFFFFF"
            r="4.5"
            stroke="#64748B"
            strokeWidth="2"
            onClick={() => onNodeClick && onNodeClick('PHARM-0001')}
          ></circle>
          <circle
            cx="170"
            cy="185"
            fill="#FFFFFF"
            r="4.5"
            stroke="#64748B"
            strokeWidth="2"
            onClick={() => onNodeClick && onNodeClick('PHARM-0002')}
          ></circle>
          <circle
            cx="105"
            cy="35"
            fill="#FFFFFF"
            r="4"
            stroke="#94A3B8"
            strokeWidth="2"
            onClick={() => onNodeClick && onNodeClick('DEPOT-NORTH')}
          ></circle>

          {/* Core Node 1: HOSPIRA (Critical Centrality) */}
          <g
            onClick={() => onNodeClick && onNodeClick('HOSPIRA')}
            onMouseEnter={() => setHoveredNode('HOSPIRA')}
            onMouseLeave={() => setHoveredNode(null)}
            className="cursor-pointer transition-transform hover:scale-105"
          >
            <circle
              cx="60"
              cy="70"
              fill="#FEE2E2"
              r={selectedNodeId === 'HOSPIRA' ? 16 : 13}
              stroke="#FDA4AF"
              strokeWidth="1"
            ></circle>
            <circle
              cx="60"
              cy="70"
              fill="#E11D48"
              r="8"
              stroke="#FFFFFF"
              strokeWidth="2"
            ></circle>
            <rect
              fill="#FFFFFF"
              height="16"
              rx="3"
              stroke="#E11D48"
              strokeWidth="1"
              width="70"
              x="25"
              y="42"
            ></rect>
            <text
              fill="#9F1239"
              fontFamily="'JetBrains Mono', monospace"
              fontSize="8.5"
              fontWeight="700"
              textAnchor="middle"
              x="60"
              y="53.5"
            >
              HOSPIRA
            </text>
          </g>

          {/* Core Node 2: HIKMA (High Fragility) */}
          <g
            onClick={() => onNodeClick && onNodeClick('HIKMA')}
            onMouseEnter={() => setHoveredNode('HIKMA')}
            onMouseLeave={() => setHoveredNode(null)}
            className="cursor-pointer transition-transform hover:scale-105"
          >
            <circle
              cx="160"
              cy="60"
              fill="#FEF3C7"
              r={selectedNodeId === 'HIKMA' ? 16 : 13}
              stroke="#FDE68A"
              strokeWidth="1"
            ></circle>
            <circle
              cx="160"
              cy="60"
              fill="#D97706"
              r="8"
              stroke="#FFFFFF"
              strokeWidth="2"
            ></circle>
            <rect
              fill="#FFFFFF"
              height="16"
              rx="3"
              stroke="#D97706"
              strokeWidth="1"
              width="52"
              x="134"
              y="32"
            ></rect>
            <text
              fill="#92400E"
              fontFamily="'JetBrains Mono', monospace"
              fontSize="8.5"
              fontWeight="700"
              textAnchor="middle"
              x="160"
              y="43.5"
            >
              HIKMA
            </text>
          </g>
        </svg>

        {/* Graph Footer HUD */}
        <div className="absolute bottom-2 left-2 right-2 flex justify-between items-center text-[10px] font-mono-tabular text-slate-600 bg-white/95 px-2.5 py-1.5 rounded border border-slate-200 backdrop-blur-sm shadow-xs">
          <span>
            NODES: <strong className="text-slate-800">8</strong>
          </span>
          <span>
            EDGES: <strong className="text-slate-800">12</strong>
          </span>
          <span className="text-rose-700 font-semibold">MAX DEGREE: HOSPIRA</span>
        </div>
      </div>
    </section>
  );
};

