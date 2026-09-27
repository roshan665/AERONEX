import React from 'react';
import { 
  Sun, 
  Flame, 
  CloudRain, 
  Snowflake, 
  ArrowRight, 
  Wind,
  Gauge
} from 'lucide-react';

const HIGHLIGHT_ICONS = {
  Cyclone: Flame,
  'Heat Wave': Sun,
  Precipitation: CloudRain,
  'Cold Wave': Snowflake,
  'Wind Anomaly': Wind,
  'Pressure Anomaly': Gauge,
};

export default function WeatherHighlights({ events = [], selectedEvent, onSelectEvent }) {
  // Select 4 distinct notable events matching the reference
  const highlightEvents = events.slice(0, 4);

  return (
    <div className="bg-[#0B1730] rounded-2xl p-4 sm:p-5 border border-[#16274a] shadow-xl flex flex-col justify-between select-none">
      {/* Header */}
      <div className="flex items-center gap-2 pb-3 border-b border-[#122040]">
        <div className="w-6 h-6 rounded-md bg-[#FFB020]/15 flex items-center justify-center text-[#FFB020]">
          <Sun className="w-3.5 h-3.5" />
        </div>
        <h3 className="text-xs sm:text-sm font-bold text-[#F4F7FF] tracking-tight">
          Weather Highlights
        </h3>
      </div>

      {/* 4 Horizontal Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mt-3">
        {highlightEvents.map((evt) => {
          const isSelected = selectedEvent?.id === evt.id;
          const IconComponent = HIGHLIGHT_ICONS[evt.type] || HIGHLIGHT_ICONS[evt.categoryKey] || Flame;

          let iconStyle = 'bg-[#FF4568]/20 text-[#FF4568]';
          if (evt.type === 'Heat Wave') iconStyle = 'bg-[#FFB020]/20 text-[#FFB020]';
          if (evt.type === 'Precipitation') iconStyle = 'bg-[#00D6A0]/20 text-[#00D6A0]';
          if (evt.type === 'Cold Wave') iconStyle = 'bg-[#00D9F5]/20 text-[#00D9F5]';

          return (
            <div
              key={evt.id}
              onClick={() => onSelectEvent(evt)}
              className={`p-2.5 rounded-xl border transition-all duration-200 cursor-pointer flex flex-col justify-between group ${
                isSelected 
                  ? 'bg-[#101F3D] border-[#00D9F5]/70 shadow-md shadow-[#00D9F5]/10' 
                  : 'bg-[#0E1A33]/80 border-[#142445] hover:bg-[#101F3D] hover:border-[#1a3058]'
              }`}
            >
              {/* Top: Icon & Region */}
              <div className="flex items-center gap-2">
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${iconStyle}`}>
                  <IconComponent className="w-3.5 h-3.5" />
                </div>
                <div className="min-w-0">
                  <div className="text-[11px] font-bold text-[#F4F7FF] truncate group-hover:text-white leading-tight">
                    {evt.name}
                  </div>
                  <div className="text-[10px] text-[#93A9C8] truncate leading-tight mt-0.5">
                    {evt.region}
                  </div>
                </div>
              </div>

              {/* Bottom: Arrow */}
              <div className="flex justify-end mt-2 pt-1 border-t border-[#122040]/60">
                <ArrowRight className="w-3 h-3 text-[#93A9C8] group-hover:text-[#00D9F5] group-hover:translate-x-0.5 transition-all" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
