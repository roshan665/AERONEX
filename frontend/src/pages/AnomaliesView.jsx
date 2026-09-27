import React, { useState } from 'react';
import { 
  AlertTriangle, 
  Flame, 
  Snowflake, 
  Wind, 
  Gauge, 
  Filter, 
  Download, 
  ArrowUpRight,
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

export default function AnomaliesView({ 
  events = [], 
  onSelectEvent, 
  onViewModal, 
  onSwitchToMap 
}) {
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');

  const categories = ['ALL', 'Cyclone', 'Heat Wave', 'Cold Wave', 'Wind Anomaly', 'Pressure Anomaly', 'Precipitation'];
  const severities = ['ALL', 'High', 'Medium', 'Low'];

  const filtered = events.filter((evt) => {
    const matchesCat = selectedCategory === 'ALL' || evt.type === selectedCategory;
    const matchesSev = selectedSeverity === 'ALL' || evt.severity === selectedSeverity;
    return matchesCat && matchesSev;
  });

  const exportGeoJSON = () => {
    const geojsonData = {
      type: "FeatureCollection",
      features: filtered.map((e) => ({
        type: "Feature",
        id: e.id,
        properties: {
          name: e.name,
          type: e.type,
          severity: e.severity,
          region: e.region,
          forecastWindow: e.forecastWindow,
          estimatedArea: e.estimatedArea,
          maxWind: e.maxWind,
          centralPressure: e.centralPressure,
        },
        geometry: {
          type: "Polygon",
          coordinates: e.footprintPolygon ? [e.footprintPolygon.map(([lat, lon]) => [lon, lat])] : [],
        }
      }))
    };

    const blob = new Blob([JSON.stringify(geojsonData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `aeronex_anomalies_demo_${Date.now()}.geojson`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#122040]">
        <div>
          <h2 className="text-lg font-bold text-[#F4F7FF] tracking-tight">
            Extreme Weather Anomalies Registry
          </h2>
          <p className="text-xs text-[#93A9C8]">
            Catalog of tracked atmospheric depressions, thermal domes, and severe wind gradients.
          </p>
        </div>

        {/* Export Button */}
        <button
          onClick={exportGeoJSON}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#00D9F5]/15 hover:bg-[#00D9F5]/25 border border-[#00D9F5]/40 text-[#00D9F5] text-xs font-bold transition-all cursor-pointer self-start sm:self-auto shadow-sm"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export GeoJSON</span>
        </button>
      </div>

      {/* Filter Tabs Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#0B1730] p-3 rounded-2xl border border-[#16274a]">
        {/* Category Filters */}
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all shrink-0 cursor-pointer ${
                selectedCategory === cat 
                  ? 'bg-[#168BFF] text-white shadow-sm shadow-[#168BFF]/40' 
                  : 'text-[#93A9C8] hover:text-[#F4F7FF] hover:bg-[#101F3D]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Severity Filters */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#93A9C8] font-medium flex items-center gap-1">
            <Filter className="w-3 h-3 text-[#93A9C8]" />
            Severity:
          </span>
          <div className="flex items-center gap-1">
            {severities.map((sev) => (
              <button
                key={sev}
                onClick={() => setSelectedSeverity(sev)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-bold transition-all cursor-pointer ${
                  selectedSeverity === sev 
                    ? 'bg-[#F4F7FF] text-[#050B1A]' 
                    : 'text-[#93A9C8] hover:text-[#F4F7FF] bg-[#101F3D]'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Anomalies Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((evt) => {
          const IconComponent = ICON_MAP[evt.type] || AlertTriangle;

          return (
            <div 
              key={evt.id}
              className="bg-[#0B1730] rounded-2xl p-5 border border-[#16274a] hover:border-[#168BFF]/60 shadow-xl transition-all duration-300 flex flex-col justify-between group"
            >
              <div>
                {/* Card Header */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${evt.iconBg}`}>
                      <IconComponent className="w-4.5 h-4.5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-[#F4F7FF] group-hover:text-[#00D9F5] transition-colors">
                        {evt.name}
                      </h3>
                      <p className="text-xs text-[#93A9C8]">{evt.region}</p>
                    </div>
                  </div>
                  <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${evt.severityBadgeColor}`}>
                    {evt.severity}
                  </span>
                </div>

                {/* Synopsis */}
                <p className="text-xs text-[#93A9C8] mt-3 line-clamp-2 leading-relaxed">
                  {evt.description}
                </p>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-[#122040] text-xs">
                  <div>
                    <span className="text-[#93A9C8] text-[11px]">Coordinates:</span>
                    <p className="font-mono text-[#F4F7FF] font-bold mt-0.5">{evt.coordinatesDisplay}</p>
                  </div>
                  <div>
                    <span className="text-[#93A9C8] text-[11px]">Forecast Horizon:</span>
                    <p className="font-semibold text-[#F4F7FF] mt-0.5">{evt.forecastWindow}</p>
                  </div>
                  <div>
                    <span className="text-[#93A9C8] text-[11px]">Est. Footprint:</span>
                    <p className="font-mono text-[#00D9F5] font-bold mt-0.5">{evt.estimatedArea}</p>
                  </div>
                  <div>
                    <span className="text-[#93A9C8] text-[11px]">Anomaly Score:</span>
                    <p className="font-mono text-[#FFB020] font-bold mt-0.5">{evt.anomalyScore}</p>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 mt-5 pt-3 border-t border-[#122040]">
                <button
                  onClick={() => {
                    onSelectEvent(evt);
                    onSwitchToMap();
                  }}
                  className="flex-1 py-2 px-3 rounded-xl bg-[#168BFF]/20 hover:bg-[#168BFF]/40 border border-[#168BFF]/40 text-xs font-bold text-[#00D9F5] hover:text-white flex items-center justify-center gap-1 transition-all cursor-pointer"
                >
                  <span>Locate on Map</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => onViewModal(evt)}
                  className="py-2 px-3 rounded-xl bg-[#101F3D] hover:bg-[#16274a] border border-[#16274a] text-xs font-bold text-[#93A9C8] hover:text-white transition-all cursor-pointer"
                >
                  Full Telemetry
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
