import React from 'react';
import { 
  Flame, 
  AlertTriangle, 
  Snowflake, 
  Wind, 
  Gauge, 
  CloudRain, 
  ChevronRight, 
  Compass,
  Cpu
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

export default function EventDetails({ selectedEvent, onViewModal }) {
  if (!selectedEvent) {
    return (
      <div className="bg-[#0B1730] rounded-2xl p-5 border border-[#16274a] shadow-xl text-center text-[#93A9C8] flex flex-col items-center justify-center min-h-[140px]">
        <Compass className="w-8 h-8 text-[#168BFF]/40 mb-2 animate-spin-slow" />
        <p className="text-xs font-medium">Select an anomaly event on the map or alerts list to inspect live telemetry.</p>
      </div>
    );
  }

  const IconComponent = ICON_MAP[selectedEvent.type] || AlertTriangle;
  const severityPill = SEVERITY_STYLES[selectedEvent.severity] || SEVERITY_STYLES.Low;
  const anomalyScore = selectedEvent.anomalyScore || selectedEvent.anomaly_score || '+3.5σ';
  const method = selectedEvent.detection_method || '3-Sigma Morphological Detector';
  const isDemo = selectedEvent.is_simulated !== false;
  const area = selectedEvent.estimatedArea || selectedEvent.estimated_area || '~ 250,000 km²';

  return (
    <div 
      onClick={() => onViewModal(selectedEvent)}
      className="bg-[#0B1730] rounded-2xl p-4 sm:p-5 border border-[#16274a] hover:border-[#168BFF]/50 shadow-xl flex flex-col justify-between select-none cursor-pointer transition-all duration-300 group"
    >
      {/* Top Section: Header & Satellite Vortex Graphic */}
      <div className="flex items-start justify-between gap-3">
        {/* Left Info: Icon, Event ID, Name & Severity */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-6 h-6 rounded-lg bg-[#A855F7]/15 border border-[#A855F7]/30 flex items-center justify-center text-[#A855F7]">
              <IconComponent className="w-3.5 h-3.5" />
            </div>
            <span className="font-mono text-[10px] text-[#00D9F5] font-bold px-1.5 py-0.5 rounded bg-[#101F3D] border border-[#1a2d52]">
              {selectedEvent.id}
            </span>
            <span className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded ${
              isDemo ? 'bg-[#FFB020]/15 text-[#FFB020]' : 'bg-[#00D9F5]/15 text-[#00D9F5]'
            }`}>
              {isDemo ? 'SYNTHETIC' : 'REAL NWP'}
            </span>
          </div>

          <div className="flex items-center gap-2 mt-1">
            <h4 className="text-sm font-bold text-[#F4F7FF] group-hover:text-white truncate">
              {selectedEvent.name}
            </h4>
            <span className={`text-[9px] uppercase font-extrabold px-1.5 py-0.2 rounded-md ${severityPill}`}>
              {selectedEvent.severity}
            </span>
            <ChevronRight className="w-3.5 h-3.5 text-[#93A9C8] group-hover:text-white group-hover:translate-x-0.5 transition-all" />
          </div>
        </div>

        {/* Right: Satellite Radar Vortex Visual Thumbnail */}
        <div className="relative w-12 h-12 rounded-xl overflow-hidden shrink-0 border border-[#A855F7]/30 shadow-md shadow-[#A855F7]/20 group-hover:scale-105 transition-transform duration-300">
          <img 
            src="/cyclone-vortex.jpg" 
            alt="Thermal Radar Satellite" 
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#0B1730]/40 to-transparent"></div>
        </div>
      </div>

      {/* Description Snippet */}
      <p className="text-[11px] text-[#93A9C8] line-clamp-2 mt-2 leading-relaxed">
        {selectedEvent.description || 'Anomalous meteorological departure detected in gridded numerical fields.'}
      </p>

      {/* Grid: 4 Telemetry Metrics */}
      <div className="grid grid-cols-4 gap-1.5 mt-2.5 pt-2.5 border-t border-[#122040]">
        <div>
          <div className="text-[9px] text-[#93A9C8] font-medium">Centroid</div>
          <div className="text-[11px] font-bold text-[#F4F7FF] font-mono mt-0.5 truncate">
            {selectedEvent.coordinatesDisplay || `${selectedEvent.lat}°, ${selectedEvent.lon}°`}
          </div>
        </div>

        <div>
          <div className="text-[9px] text-[#93A9C8] font-medium">Score</div>
          <div className="text-[11px] font-bold text-[#00D9F5] font-mono mt-0.5 truncate">
            {anomalyScore}
          </div>
        </div>

        <div>
          <div className="text-[9px] text-[#93A9C8] font-medium">Footprint</div>
          <div className="text-[11px] font-bold text-[#F4F7FF] font-mono mt-0.5 truncate">
            {area}
          </div>
        </div>

        <div>
          <div className="text-[9px] text-[#93A9C8] font-medium">Lead Win.</div>
          <div className="text-[11px] font-bold text-[#F4F7FF] font-mono mt-0.5 truncate">
            {selectedEvent.forecastWindow?.split('–')[0]?.trim() || 'Day 1'}
          </div>
        </div>
      </div>

      {/* Method & Action Footer */}
      <div className="mt-2.5 pt-2 border-t border-[#122040] flex items-center justify-between text-[10px]">
        <div className="flex items-center gap-1.5 text-[#93A9C8] truncate mr-2">
          <Cpu className="w-3 h-3 text-[#168BFF] shrink-0" />
          <span className="truncate">{method}</span>
        </div>
        <span className="text-[#00D9F5] group-hover:text-white flex items-center gap-0.5 shrink-0 font-medium transition-colors">
          Full Telemetry &rarr;
        </span>
      </div>
    </div>
  );
}
