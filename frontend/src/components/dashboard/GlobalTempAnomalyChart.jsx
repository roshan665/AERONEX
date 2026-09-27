import React from 'react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip 
} from 'recharts';
import { TrendingUp } from 'lucide-react';
import { GLOBAL_TEMP_ANOMALY_TREND } from '../../data/demoData';

export default function GlobalTempAnomalyChart() {
  const data = GLOBAL_TEMP_ANOMALY_TREND || [
    { month: "Jan", anomaly: 0.62 },
    { month: "Feb", anomaly: 0.71 },
    { month: "Mar", anomaly: 0.85 },
    { month: "Apr", anomaly: 0.80 },
    { month: "May", anomaly: 0.74 },
    { month: "Jun", anomaly: 0.78 },
    { month: "Jul", anomaly: 0.88 },
    { month: "Aug", anomaly: 0.82 },
    { month: "Sep", anomaly: 0.79 },
    { month: "Oct", anomaly: 0.84 },
    { month: "Nov", anomaly: 0.91 },
    { month: "Dec", anomaly: 0.86 },
  ];

  return (
    <div className="bg-[#0B1730] rounded-2xl p-4 sm:p-5 border border-[#16274a] shadow-xl flex flex-col justify-between select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-2 border-b border-[#122040]">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-[#168BFF]/15 flex items-center justify-center text-[#168BFF]">
            <TrendingUp className="w-3.5 h-3.5" />
          </div>
          <h3 className="text-xs sm:text-sm font-bold text-[#F4F7FF] tracking-tight">
            Global Temperature Anomaly
          </h3>
        </div>

        <div className="flex items-center gap-1.5 pl-8 sm:pl-0">
          <span className="text-xs font-bold text-[#FF4568]">
            +0.8°C
          </span>
          <span className="text-[10px] text-[#93A9C8]">
            vs. 1951–1980 average
          </span>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="w-full h-24 sm:h-28 mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
            <defs>
              <linearGradient id="globalTempStroke" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#A855F7" />
                <stop offset="50%" stopColor="#168BFF" />
                <stop offset="100%" stopColor="#00D9F5" />
              </linearGradient>
              <linearGradient id="globalTempArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#A855F7" stopOpacity={0.25} />
                <stop offset="100%" stopColor="#050B1A" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <XAxis 
              dataKey="month" 
              stroke="#93A9C8" 
              fontSize={9} 
              tickLine={false} 
              axisLine={false}
              dy={4}
            />
            <YAxis 
              stroke="#93A9C8" 
              fontSize={8} 
              tickLine={false} 
              axisLine={false}
              domain={['dataMin - 0.2', 'dataMax + 0.2']}
              tickFormatter={(val) => `+${val.toFixed(1)}`}
              hide
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload;
                  return (
                    <div className="bg-[#071126] border border-[#16274a] px-2.5 py-1.5 rounded-lg shadow-xl text-left">
                      <div className="text-[10px] font-semibold text-[#93A9C8]">{item.month} Anomaly</div>
                      <div className="text-xs font-bold text-[#00D9F5]">+{item.anomaly}°C</div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area 
              type="monotone" 
              dataKey="anomaly" 
              stroke="url(#globalTempStroke)" 
              strokeWidth={2}
              fill="url(#globalTempArea)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
