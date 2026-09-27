import React, { useState, useEffect } from 'react';
import { 
  ResponsiveContainer, 
  ComposedChart, 
  Line, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid 
} from 'recharts';
import { FORECAST_TIME_SERIES } from '../data/demoData';
import { 
  Info, 
  Compass,
  Navigation
} from 'lucide-react';
import { aeroNexApi } from '../services/api';

export default function ForecastView() {
  const [activeVar, setActiveVar] = useState('temperature');
  const [selectedTrackId, setSelectedTrackId] = useState('TRK-CYC-001');
  const [tracks, setTracks] = useState([]);
  const [trackDetail, setTrackDetail] = useState(null);
  const [uncertaintySummary, setUncertaintySummary] = useState(null);
  const [eventUncertainty, setEventUncertainty] = useState(null);
  const [ensembleDemoActive, setEnsembleDemoActive] = useState(false);

  const varOptions = [
    { id: 'temperature', label: '2m Temperature', unit: '°C' },
    { id: 'wind', label: '10m Wind Speed', unit: 'km/h' },
    { id: 'pressure', label: 'Mean Sea-Level Pressure', unit: 'hPa' },
    { id: 'precipitation', label: 'Accumulated Precipitation', unit: 'mm' },
  ];

  const currentVar = varOptions.find(v => v.id === activeVar) || varOptions[0];
  const [chartData, setChartData] = useState(FORECAST_TIME_SERIES[activeVar] || FORECAST_TIME_SERIES.temperature);
  const [forecastRunMetadata, setForecastRunMetadata] = useState(null);
  const [selectedLeadDay, setSelectedLeadDay] = useState(1);

  // Load forecast timeline and metadata from backend API
  useEffect(() => {
    let isMounted = true;
    aeroNexApi.getForecasts(activeVar).then((res) => {
      if (isMounted && res && res.timeline) {
        setChartData(res.timeline);
      }
    }).catch(err => {
      console.warn('[ForecastView] Timeseries fetch error:', err.message);
    });

    aeroNexApi.getForecastRun('GFS-20250426-00Z').then((res) => {
      if (isMounted && res) {
        setForecastRunMetadata(res);
      }
    }).catch(() => {});

    return () => { isMounted = false; };
  }, [activeVar]);

  // Load tracks and uncertainty from API
  useEffect(() => {
    aeroNexApi.getTracks().then((data) => {
      if (data && data.length > 0) setTracks(data);
    }).catch(console.warn);
  }, []);

  useEffect(() => {
    aeroNexApi.getTrackDetail(selectedTrackId).then((data) => {
      if (data) setTrackDetail(data);
    }).catch(console.warn);

    aeroNexApi.getEventUncertainty(selectedTrackId).then((data) => {
      if (data) setEventUncertainty(data);
    }).catch(console.warn);
  }, [selectedTrackId]);

  useEffect(() => {
    aeroNexApi.getUncertainty({ mode: ensembleDemoActive ? 'ensemble' : 'deterministic' }).then((data) => {
      if (data) setUncertaintySummary(data);
    }).catch(console.warn);
  }, [ensembleDemoActive]);

  return (
    <div className="space-y-5 select-none pb-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#122040]">
        <div>
          <h2 className="text-lg font-bold text-[#F4F7FF] tracking-tight flex items-center gap-2">
            Medium-Range Forecast Explorer & Uncertainty Bands
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-cyan-500/15 text-[#00D9F5] border border-cyan-500/30">
              Phase 6
            </span>
          </h2>
          <p className="text-xs text-[#93A9C8]">
            Evaluating forecast spread, deterministic trajectory history, and ensemble dispersion across Days 1–10.
          </p>
        </div>

        {/* Variable Switcher */}
        <div className="flex items-center gap-1.5 bg-[#0B1730] p-1.5 rounded-xl border border-[#16274a]">
          {varOptions.map((opt) => (
            <button
              key={opt.id}
              onClick={() => setActiveVar(opt.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeVar === opt.id 
                  ? 'bg-[#168BFF] text-white shadow-sm shadow-[#168BFF]/40' 
                  : 'text-[#93A9C8] hover:text-[#F4F7FF] hover:bg-[#101F3D]'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Forecast Run & Valid Time Telemetry Bar */}
      <div className="bg-[#0B1730] border border-[#16274a] rounded-2xl p-4 shadow-xl flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <div className="px-2.5 py-1 rounded-xl bg-[#168BFF]/15 border border-[#168BFF]/30 text-[#00D9F5] font-mono font-bold">
            {forecastRunMetadata?.forecast_id || 'GFS-20250426-00Z'}
          </div>
          <div className="text-[#93A9C8]">
            <span className="text-[#F4F7FF] font-semibold">Init:</span> {forecastRunMetadata?.initialization_time || '2025-04-26 00:00 UTC'}
          </div>
          <div className="text-[#93A9C8]">
            <span className="text-[#F4F7FF] font-semibold">Valid:</span> {
              chartData.find(item => item.lead_day === selectedLeadDay)?.valid_time || `2025-04-${26 + selectedLeadDay} 00:00 UTC`
            }
          </div>
          <div className="text-[#93A9C8]">
            <span className="text-[#F4F7FF] font-semibold">Lead:</span> <span className="text-[#00D9F5] font-mono font-bold">T+{selectedLeadDay * 24}h (Day {selectedLeadDay})</span>
          </div>
          <div className="text-[#93A9C8]">
            <span className="text-[#F4F7FF] font-semibold">Variable:</span> {currentVar.label} ({currentVar.unit})
          </div>
        </div>

        {/* Lead Day Quick Scrubber */}
        <div className="flex items-center gap-1 bg-[#071126] p-1 rounded-xl border border-[#142445]">
          <span className="text-[10px] text-[#93A9C8] font-mono uppercase px-1.5 font-bold">Horizon:</span>
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((d) => (
            <button
              key={`fd-${d}`}
              onClick={() => setSelectedLeadDay(d)}
              className={`w-6 h-6 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                selectedLeadDay === d
                  ? 'bg-[#168BFF] text-white shadow-sm'
                  : 'text-[#93A9C8] hover:text-white hover:bg-[#101F3D]'
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      {/* Mode & Uncertainty Banner */}
      <div className="p-4 rounded-2xl bg-[#0B1730] border border-[#16274a] shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-[#00D9F5] shrink-0 mt-0.5" />
          <div className="text-xs text-[#93A9C8] leading-relaxed">
            <span className="font-bold text-[#F4F7FF] block mb-0.5">
              Forecast Uncertainty Status: {ensembleDemoActive ? "5-Member Synthetic Ensemble Active" : "Deterministic Operational Mode"}
            </span>
            {uncertaintySummary?.message ? (
              <span>{uncertaintySummary.message}</span>
            ) : ensembleDemoActive ? (
              <span>Evaluating intra-ensemble variance across 5 perturbed members. Note that agreement drops from 100% on Day 1 to 60% on Day 5 as tracks diverge.</span>
            ) : (
              <span>Single deterministic GFS run. Ensemble variance is unavailable for single-member forecasts. Atmospheric predictability decays with lead time.</span>
            )}
          </div>
        </div>

        {/* Ensemble Demo Toggle */}
        <div className="flex items-center gap-2 shrink-0 bg-[#071126] p-1.5 rounded-xl border border-[#142445]">
          <span className="text-[11px] text-[#93A9C8] font-medium pl-1">Dataset Mode:</span>
          <button
            onClick={() => setEnsembleDemoActive(false)}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              !ensembleDemoActive 
                ? 'bg-[#168BFF] text-white shadow-sm' 
                : 'text-[#93A9C8] hover:text-white'
            }`}
          >
            Deterministic GFS
          </button>
          <button
            onClick={() => setEnsembleDemoActive(true)}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              ensembleDemoActive 
                ? 'bg-purple-600 text-white shadow-sm shadow-purple-500/30' 
                : 'text-[#93A9C8] hover:text-white'
            }`}
          >
            5-Member Ensemble Demo
          </button>
        </div>
      </div>

      {/* Main Large Multi-Variable Ensemble Chart */}
      <div className="bg-[#0B1730] rounded-2xl p-5 border border-[#16274a] shadow-2xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#122040] gap-2">
          <div>
            <h3 className="text-sm font-bold text-[#F4F7FF]">
              {currentVar.label} Envelope & Dispersion Analysis
            </h3>
            <span className="text-[11px] text-[#93A9C8] font-mono">
              Model Run: Apr 26, 2025 00:00 UTC • {ensembleDemoActive ? "Synthetic Ensemble Spread" : "Deterministic Lead-Time Skill Decay"}
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs select-none">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-[#168BFF]/20 border border-[#168BFF]/40"></span>
              <span className="text-[#93A9C8]">Uncertainty Band</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-0.5 bg-[#FF4568]"></span>
              <span className="text-[#F4F7FF]">Peak Anomaly</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-0.5 bg-[#00D9F5]"></span>
              <span className="text-[#F4F7FF]">Mean Curve</span>
            </div>
          </div>
        </div>

        <div className="h-64 sm:h-72 w-full mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#122040" vertical={false} />
              <XAxis dataKey="day" stroke="#93A9C8" fontSize={11} tickLine={false} />
              <YAxis 
                stroke="#93A9C8" 
                fontSize={11} 
                tickLine={false}
                tickFormatter={(v) => `${v}${currentVar.unit}`}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-[#071126] border border-[#16274a] rounded-xl p-3 shadow-2xl text-xs space-y-1">
                        <div className="font-bold text-[#F4F7FF] border-b border-[#122040] pb-1">{label}</div>
                        {payload.map((p, idx) => (
                          <div key={idx} className="flex justify-between gap-4 text-[11px]">
                            <span className="text-[#93A9C8]">{p.name}:</span>
                            <span className="font-mono font-bold text-[#F4F7FF]">{p.value} {currentVar.unit}</span>
                          </div>
                        ))}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Area 
                type="monotone" 
                dataKey="uncertaintyUpper" 
                name="Spread Upper" 
                stroke="none" 
                fill="#00D9F5" 
                fillOpacity={0.15} 
              />
              <Line 
                type="monotone" 
                dataKey="max" 
                name="Max Extreme" 
                stroke="#FF4568" 
                strokeWidth={2.5} 
                dot={{ r: 3 }}
              />
              <Line 
                type="monotone" 
                dataKey="globalAvg" 
                name="Global Avg" 
                stroke="#00D9F5" 
                strokeWidth={2} 
                dot={{ r: 3 }}
              />
              <Line 
                type="monotone" 
                dataKey="min" 
                name="Min Level" 
                stroke="#168BFF" 
                strokeWidth={1.5} 
                strokeDasharray="4 4"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Section 2: Phase 6 Track Evolution & Event History */}
      <div className="bg-[#0B1730] rounded-2xl p-5 border border-[#16274a] shadow-2xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#122040]">
          <div>
            <h3 className="text-sm font-bold text-[#F4F7FF] flex items-center gap-2">
              <Navigation className="w-4 h-4 text-[#00D9F5]" />
              Temporal Event Tracking & Footprint Evolution
            </h3>
            <p className="text-xs text-[#93A9C8]">
              Select a tracked anomaly series to evaluate centroid movement, area expansion/contraction, and detection continuity.
            </p>
          </div>

          {/* Track Selector Buttons */}
          <div className="flex items-center gap-1.5 overflow-x-auto">
            {tracks.map((trk) => {
              const isSelected = trk.track_id === selectedTrackId;
              return (
                <button
                  key={trk.track_id}
                  onClick={() => setSelectedTrackId(trk.track_id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all shrink-0 cursor-pointer ${
                    isSelected
                      ? 'bg-[#168BFF] text-white shadow-md shadow-[#168BFF]/40'
                      : 'bg-[#071126] text-[#93A9C8] hover:text-white border border-[#16274a]'
                  }`}
                >
                  {trk.track_id} ({trk.category})
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Track Diagnostic Stats */}
        {trackDetail && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div className="p-3 rounded-xl bg-[#071126] border border-[#16274a]">
                <span className="text-[10px] text-[#93A9C8] uppercase font-bold block">Event Name</span>
                <span className="text-xs font-bold text-[#F4F7FF] mt-1 block truncate">{trackDetail.name}</span>
              </div>
              <div className="p-3 rounded-xl bg-[#071126] border border-[#16274a]">
                <span className="text-[10px] text-[#93A9C8] uppercase font-bold block">Net Displacement</span>
                <span className="text-xs font-mono font-bold text-white mt-1 block">{trackDetail.net_displacement_km} km</span>
              </div>
              <div className="p-3 rounded-xl bg-[#071126] border border-[#16274a]">
                <span className="text-[10px] text-[#93A9C8] uppercase font-bold block">Mean Translation</span>
                <span className="text-xs font-mono font-bold text-[#38BDF8] mt-1 block">{trackDetail.mean_speed_kmh} km/h</span>
              </div>
              <div className="p-3 rounded-xl bg-[#071126] border border-[#16274a]">
                <span className="text-[10px] text-[#93A9C8] uppercase font-bold block">Max Surface Area</span>
                <span className="text-xs font-mono font-bold text-[#00D9F5] mt-1 block">{trackDetail.max_area_km2.toLocaleString()} km²</span>
              </div>
              <div className="p-3 rounded-xl bg-[#071126] border border-[#16274a]">
                <span className="text-[10px] text-[#93A9C8] uppercase font-bold block">Detected Frames</span>
                <span className="text-xs font-mono font-bold text-emerald-400 mt-1 block">
                  {trackDetail.total_detections} of {trackDetail.total_frames} Days
                </span>
              </div>
              {eventUncertainty && (
                <div className="p-3 rounded-xl bg-[#071126] border border-[#16274a]">
                  <span className="text-[10px] text-[#93A9C8] uppercase font-bold block">Uncertainty Mode</span>
                  <span className="text-xs font-mono font-bold text-[#A855F7] mt-1 block">
                    {eventUncertainty.uncertainty_mode === 'ENSEMBLE_SPREAD' ? 'Ensemble Spread' : 'Lyapunov Skill Decay'}
                  </span>
                </div>
              )}
            </div>

            {/* Scientific Caveat Label */}
            <div className="p-3 rounded-xl bg-[#081329] border border-[#142445] text-xs text-[#93A9C8] flex items-start gap-2">
              <Compass className="w-4 h-4 text-[#00D9F5] shrink-0 mt-0.5" />
              <span>
                {trackDetail.movement_notes || "Derived movement represents displacement of detected forecast footprint centroids across successive forecast frames; it does not constitute a verified physical storm track."}
              </span>
            </div>

            {/* Chronological Step History Table */}
            <div className="rounded-xl border border-[#16274a] overflow-hidden bg-[#071126]">
              <div className="px-4 py-2.5 bg-[#0B1730] border-b border-[#16274a] flex items-center justify-between text-xs font-bold text-[#F4F7FF]">
                <span>Sequential Multi-Day Forecast History</span>
                <span className="text-[11px] text-[#93A9C8] font-mono">Track: {trackDetail.track_id}</span>
              </div>

              <div className="divide-y divide-[#122040] text-xs">
                {trackDetail.points.map((pt) => {
                  const isDetected = pt.detection_status === 'DETECTED';

                  return (
                    <div key={pt.frame_index} className="px-4 py-2.5 flex items-center justify-between hover:bg-[#0c1836] transition-colors">
                      <div className="flex items-center gap-3">
                        <span className="w-14 font-mono font-bold text-[#F4F7FF] text-xs">
                          Day {pt.forecast_day}
                        </span>
                        <span className="text-[11px] font-mono text-[#93A9C8]">
                          T+{pt.step_hours}h
                        </span>

                        <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-md ${
                          isDetected 
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                            : pt.detection_status === 'DISSIPATED'
                            ? 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
                            : 'bg-amber-500/15 text-amber-400 border border-amber-500/20'
                        }`}>
                          {pt.detection_status}
                        </span>
                      </div>

                      {isDetected ? (
                        <div className="flex items-center gap-5 font-mono text-[11px] text-right">
                          <div>
                            <span className="text-[#93A9C8] block text-[9px] uppercase">Centroid</span>
                            <span className="text-[#F4F7FF]">{pt.coordinates_display}</span>
                          </div>
                          <div>
                            <span className="text-[#93A9C8] block text-[9px] uppercase">Area</span>
                            <span className="text-[#00D9F5]">{pt.estimated_area_km2?.toLocaleString()} km²</span>
                          </div>
                          {pt.speed_kmh !== null && (
                            <div>
                              <span className="text-[#93A9C8] block text-[9px] uppercase">Shift</span>
                              <span className="text-white">{pt.speed_kmh} km/h ({pt.bearing_cardinal})</span>
                            </div>
                          )}
                          {pt.area_change_pct !== null && (
                            <div>
                              <span className="text-[#93A9C8] block text-[9px] uppercase">Area Δ</span>
                              <span className={pt.area_change_pct >= 0 ? "text-red-400" : "text-emerald-400"}>
                                {pt.area_change_pct >= 0 ? `+${pt.area_change_pct}%` : `${pt.area_change_pct}%`}
                              </span>
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-[11px] text-[#64748b] italic">
                          {pt.detection_status === 'DISSIPATED' ? 'System dissipated below detection threshold' : 'Unassociated at this lead time'}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
