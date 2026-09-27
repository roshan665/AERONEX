import React from 'react';
import { 
  Flame, 
  AlertTriangle, 
  Snowflake, 
  Wind, 
  Gauge 
} from 'lucide-react';
import { ANOMALY_TYPE_COUNTS } from '../../data/demoData';

const ICON_MAP = {
  Cyclone: Flame,
  'Heat Wave': AlertTriangle,
  'Cold Wave': Snowflake,
  'Wind Anomaly': Wind,
  'Pressure Anomaly': Gauge,
};

export default function AnomalyTypeBreakdown() {
  return (
    <div className="bg-[#0d162a]/95 rounded-2xl p-4 sm:p-5 border border-[#182645] shadow-xl flex flex-col justify-between h-full">
      {/* Title */}
      <div className="text-xs sm:text-sm font-bold text-white tracking-tight pb-2.5 border-b border-[#16233e]">
        Anomaly Types
      </div>

      {/* Breakdown Rows */}
      <div className="space-y-3 mt-2.5">
        {ANOMALY_TYPE_COUNTS.map((item) => {
          const IconComponent = ICON_MAP[item.type] || AlertTriangle;

          return (
            <div key={item.type} className="flex items-center gap-3 text-xs">
              {/* Category Icon */}
              <div 
                className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0"
                style={{ backgroundColor: `${item.color}20`, color: item.color }}
              >
                <IconComponent className="w-3.5 h-3.5" />
              </div>

              {/* Label */}
              <span className="w-28 text-slate-300 font-medium truncate">
                {item.type}
              </span>

              {/* Horizontal Progress Bar */}
              <div className="flex-1 h-2 rounded-full bg-[#121c35] overflow-hidden">
                <div 
                  className="h-full rounded-full transition-all duration-500"
                  style={{ 
                    backgroundColor: item.color,
                    width: `${Math.min(100, item.count * 60)}%` 
                  }}
                />
              </div>

              {/* Count */}
              <span className="w-4 text-right font-mono font-bold text-slate-200">
                {item.count}
              </span>
            </div>
          );
        })}
      </div>

      {/* Footer subtle tag */}
      <div className="text-[10px] text-center text-slate-400 pt-2 border-t border-[#14213d]">
        5 global physical hazard profiles tracked
      </div>
    </div>
  );
}
