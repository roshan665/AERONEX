import React from 'react';
import { 
  Bell, 
  ArrowRight, 
  ChevronRight, 
  Flame, 
  AlertTriangle, 
  Snowflake, 
  Wind, 
  Gauge, 
  CloudRain 
} from 'lucide-react';

const ICON_MAP = {
  Cyclone: Flame,
  'Heat Wave': AlertTriangle,
  'Cold Wave': Snowflake,
  'Wind Anomaly': Wind,
  'Pressure Anomaly': Gauge,
  Precipitation: CloudRain,
};

const SEVERITY_STYLES = {
  High: 'bg-[#FF4568] text-white',
  Medium: 'bg-[#FFB020] text-black font-extrabold',
  Low: 'bg-[#168BFF] text-white',
};

export default function RecentAlerts({ 
  events = [], 
  selectedEvent, 
  onSelectEvent,
  onViewAll
}) {
  return (
    <div className="bg-[#0B1730] rounded-2xl p-4 sm:p-5 border border-[#16274a] shadow-xl flex flex-col select-none">
      {/* Header */}
      <div className="flex items-center justify-between pb-3.5 border-b border-[#122040]">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[#168BFF]/15 border border-[#168BFF]/30 flex items-center justify-center text-[#168BFF]">
            <Bell className="w-3.5 h-3.5" />
          </div>
          <h3 className="text-sm font-bold text-[#F4F7FF] tracking-tight">
            Recent Alerts
          </h3>
        </div>

        <button 
          onClick={onViewAll}
          className="text-xs font-semibold text-[#00D9F5] hover:text-[#38e4fb] flex items-center gap-1 transition-colors cursor-pointer group"
        >
          <span>View All</span>
          <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
        </button>
      </div>

      {/* Alert Items List */}
      <div className="space-y-2 mt-3 overflow-y-auto max-h-[380px] pr-0.5">
        {events.length === 0 ? (
          <div className="py-8 text-center px-4 bg-[#071126]/60 rounded-xl border border-[#142445]">
            <AlertTriangle className="w-8 h-8 text-[#93A9C8]/40 mx-auto mb-2" />
            <div className="text-xs font-bold text-[#F4F7FF]">No Active Anomalies in View</div>
            <div className="text-[11px] text-[#93A9C8] mt-1 leading-snug">
              Adjust filters or click "Run Anomaly Detection" on the toolbar to identify extreme weather events.
            </div>
          </div>
        ) : (
          events.slice(0, 5).map((evt) => {
            const isSelected = selectedEvent?.id === evt.id;
            const IconComponent = ICON_MAP[evt.type] || AlertTriangle;
            const severityPill = SEVERITY_STYLES[evt.severity] || SEVERITY_STYLES.Low;

          // Custom circular icon styling per event
          let circleColor = 'bg-[#FF4568]/20 text-[#FF4568] border-[#FF4568]/40';
          if (evt.type === 'Heat Wave') circleColor = 'bg-[#FFB020]/20 text-[#FFB020] border-[#FFB020]/40';
          if (evt.type === 'Cold Wave') circleColor = 'bg-[#00D9F5]/20 text-[#00D9F5] border-[#00D9F5]/40';
          if (evt.type === 'Wind Anomaly') circleColor = 'bg-[#00D6A0]/20 text-[#00D6A0] border-[#00D6A0]/40';
          if (evt.type === 'Pressure Anomaly') circleColor = 'bg-[#A855F7]/20 text-[#A855F7] border-[#A855F7]/40';

          return (
            <div
              key={evt.id}
              onClick={() => onSelectEvent(evt)}
              className={`w-full p-2.5 rounded-xl border transition-all duration-200 text-left flex items-center justify-between gap-3 cursor-pointer group ${
                isSelected 
                  ? 'bg-[#101F3D] border-[#00D9F5]/70 shadow-lg shadow-[#00D9F5]/10' 
                  : 'bg-[#0E1A33]/80 border-[#142445] hover:bg-[#101F3D] hover:border-[#1a3058]'
              }`}
            >
              {/* Left: Circular Icon Badge */}
              <div className={`w-9 h-9 rounded-full border flex items-center justify-center shrink-0 ${circleColor}`}>
                <IconComponent className="w-4 h-4" />
              </div>

              {/* Middle: Title, Severity, Region, Coordinates */}
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-1.5">
                  <span className="text-xs font-bold text-[#F4F7FF] truncate group-hover:text-white">
                    {evt.name}
                  </span>
                  <span className={`text-[9px] uppercase font-extrabold px-1.5 py-0.2 rounded-md ${severityPill}`}>
                    {evt.severity}
                  </span>
                </div>

                <div className="text-[11px] font-medium text-[#93A9C8] truncate mt-0.5">
                  {evt.region}
                </div>

                <div className="text-[10px] text-[#93A9C8]/80 truncate font-mono">
                  Lat: {evt.lat > 0 ? `${evt.lat}°N` : `${Math.abs(evt.lat)}°S`}  Lon: {evt.lon > 0 ? `${evt.lon}°E` : `${Math.abs(evt.lon)}°W`} • Forecast: {evt.forecastWindow?.slice(0, 14)}...
                </div>
              </div>

              {/* Right: Timestamp & Chevron */}
              <div className="flex items-center gap-1 shrink-0 pl-1">
                <span className="text-[10px] text-[#93A9C8] font-mono">
                  {evt.updatedAgo}
                </span>
                <ChevronRight className="w-3.5 h-3.5 text-[#93A9C8] group-hover:text-white group-hover:translate-x-0.5 transition-all" />
              </div>
            </div>
          );
        }))}
      </div>
    </div>
  );
}
