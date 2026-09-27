import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { SEVERITY_DISTRIBUTION } from '../../data/demoData';

export default function SeverityChart() {
  const totalCount = SEVERITY_DISTRIBUTION.reduce((acc, curr) => acc + curr.value, 0);

  return (
    <div className="bg-[#0d162a]/95 rounded-2xl p-4 sm:p-5 border border-[#182645] shadow-xl flex flex-col justify-between h-full">
      {/* Title */}
      <div className="text-xs sm:text-sm font-bold text-white tracking-tight pb-2.5 border-b border-[#16233e]">
        Top Anomalies by Severity
      </div>

      {/* Donut and Legend Container */}
      <div className="flex items-center justify-between gap-2 mt-2 h-44 sm:h-48">
        {/* Donut Chart with Center Text */}
        <div className="relative w-1/2 h-full flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={SEVERITY_DISTRIBUTION}
                cx="50%"
                cy="50%"
                innerRadius={46}
                outerRadius={68}
                paddingAngle={4}
                dataKey="value"
                stroke="none"
              >
                {SEVERITY_DISTRIBUTION.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-[#0f172a] border border-[#203258] rounded-xl px-2.5 py-1.5 shadow-2xl text-xs">
                        <div className="font-semibold text-slate-100">{data.name} Severity</div>
                        <div className="text-[11px] text-slate-400">
                          {data.value} anomalies ({data.percentage}%)
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
            </PieChart>
          </ResponsiveContainer>

          {/* Absolute Center Counter */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-2xl font-extrabold text-white tracking-tight leading-none">
              {totalCount}
            </span>
            <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider mt-0.5">
              Total
            </span>
          </div>
        </div>

        {/* Legend List */}
        <div className="w-1/2 space-y-2.5 pl-2 text-xs select-none">
          {SEVERITY_DISTRIBUTION.map((item) => (
            <div key={item.name} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span 
                  className="w-2.5 h-2.5 rounded-full shrink-0 shadow-sm"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-slate-300 font-medium">{item.name}</span>
              </div>
              <span className="font-mono text-slate-400 text-[11px]">
                {item.value} ({item.percentage}%)
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Footer subtle tag */}
      <div className="text-[10px] text-center text-slate-400 pt-2 border-t border-[#14213d]">
        Categorized by composite meteorological deficit
      </div>
    </div>
  );
}
