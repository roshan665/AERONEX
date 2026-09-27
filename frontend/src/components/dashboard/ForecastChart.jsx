import React, { useState, useEffect } from 'react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid 
} from 'recharts';
import { FORECAST_TIME_SERIES } from '../../data/demoData';
import { aeroNexApi } from '../../services/api';

export default function ForecastChart() {
  const [activeTab, setActiveTab] = useState('temperature');

  const tabs = [
    { id: 'temperature', label: 'Temperature', unit: '°C' },
    { id: 'wind', label: 'Wind', unit: 'km/h' },
    { id: 'pressure', label: 'Pressure', unit: 'hPa' },
    { id: 'precipitation', label: 'Precipitation', unit: 'mm' },
  ];

  const currentTabConfig = tabs.find(t => t.id === activeTab) || tabs[0];
  const [chartData, setChartData] = useState(FORECAST_TIME_SERIES[activeTab] || FORECAST_TIME_SERIES.temperature);

  useEffect(() => {
    let isMounted = true;
    aeroNexApi.getForecasts(activeTab).then(res => {
      if (isMounted && res && res.timeline) {
        setChartData(res.timeline);
      }
    }).catch(err => {
      console.warn('[ForecastChart] Using fallback timeseries:', err.message);
    });
    return () => { isMounted = false; };
  }, [activeTab]);

  return (
    <div className="bg-[#0d162a]/95 rounded-2xl p-4 sm:p-5 border border-[#182645] shadow-xl flex flex-col justify-between h-full">
      {/* Header and Variable Switcher Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-2.5 border-b border-[#16233e]">
        <h3 className="text-xs sm:text-sm font-bold text-white tracking-tight">
          Forecast Overview <span className="text-slate-400 font-normal">(Next 10 Days)</span>
        </h3>

        {/* Tab Buttons */}
        <div className="flex items-center gap-1 bg-[#0a1020] p-1 rounded-xl border border-[#192748] overflow-x-auto">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all shrink-0 cursor-pointer ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#121c35]'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Recharts Multi-Line Container */}
      <div className="w-full h-44 sm:h-48 mt-3">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 8, right: 12, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#16233e" vertical={false} />
            <XAxis 
              dataKey="day" 
              stroke="#64748b" 
              fontSize={10} 
              tickLine={false} 
              axisLine={{ stroke: '#1a2747' }}
            />
            <YAxis 
              stroke="#64748b" 
              fontSize={10} 
              tickLine={false} 
              axisLine={{ stroke: '#1a2747' }}
              tickFormatter={(v) => `${v}${currentTabConfig.unit}`}
            />
            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-[#0f172a] border border-[#203258] rounded-xl p-2.5 shadow-2xl text-xs">
                      <div className="font-semibold text-slate-200 mb-1">{label}</div>
                      {payload.map((entry, index) => (
                        <div key={`item-${index}`} className="flex items-center gap-2 text-[11px] py-0.5">
                          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                          <span className="text-slate-400">{entry.name}:</span>
                          <span className="font-mono font-medium text-slate-100">
                            {entry.value} {currentTabConfig.unit}
                          </span>
                        </div>
                      ))}
                    </div>
                  );
                }
                return null;
              }}
            />
            {/* Global Avg line */}
            <Line 
              type="monotone" 
              dataKey="globalAvg" 
              name="Global Avg" 
              stroke="#38bdf8" 
              strokeWidth={2}
              dot={{ r: 2.5, fill: '#38bdf8' }}
              activeDot={{ r: 5 }}
            />
            {/* Max line */}
            <Line 
              type="monotone" 
              dataKey="max" 
              name="Max" 
              stroke="#f97316" 
              strokeWidth={2}
              dot={{ r: 2.5, fill: '#f97316' }}
              activeDot={{ r: 5 }}
            />
            {/* Min line */}
            <Line 
              type="monotone" 
              dataKey="min" 
              name="Min" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={{ r: 2.5, fill: '#3b82f6' }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-5 mt-2 pt-2 border-t border-[#14213d] text-[11px] text-slate-400 select-none">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
          <span>Global Avg</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-orange-500"></span>
          <span>Max</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-blue-500"></span>
          <span>Min</span>
        </div>
      </div>
    </div>
  );
}
