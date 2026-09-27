import React, { useState, useEffect } from 'react';
import { 
  X, 
  Wind, 
  Gauge, 
  AlertTriangle, 
  Flame,
  CloudRain,
  Snowflake,
  Navigation,
  Activity,
  ShieldAlert,
  Info,
  Cpu
} from 'lucide-react';
import { aeroNexApi } from '../../services/api';

const ICON_MAP = {
  Cyclone: Flame,
  'Heat Wave': AlertTriangle,
  'Cold Wave': Snowflake,
  'Wind Anomaly': Wind,
  'Pressure Anomaly': Gauge,
  Precipitation: CloudRain,
};

export default function EventDetailModal({ event, onClose }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [trackDetail, setTrackDetail] = useState(null);
  const [uncertaintyDetail, setUncertaintyDetail] = useState(null);
  const [aiScore, setAiScore] = useState(null);

  useEffect(() => {
    if (!event) return;

    let isMounted = true;

    // Map demo event id to track id
    const trackIdMap = {
      'evt-001': 'TRK-CYC-001',
      'evt-002': 'TRK-HEAT-002',
      'evt-003': 'TRK-COLD-003',
    };
    const trackId = trackIdMap[event.id] || 'TRK-CYC-001';

    Promise.all([
      aeroNexApi.getTrackDetail(trackId).catch(() => null),
      aeroNexApi.getEventUncertainty(event.id).catch(() => null),
      aeroNexApi.getAnomalyScore(event.id).catch(() => null)
    ]).then(([trk, unc, score]) => {
      if (isMounted) {
        setTrackDetail(trk);
        setUncertaintyDetail(unc);
        setAiScore(score);
        setLoading(false);
      }
    });

    return () => { isMounted = false; };
  }, [event]);

  if (!event) return null;

  const IconComponent = ICON_MAP[event.type] || AlertTriangle;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200 select-none">
      <div 
        className="relative w-full max-w-2xl bg-[#0B1730] border border-[#16274a] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-5 py-3.5 border-b border-[#122040] flex items-center justify-between bg-[#071126]">
          <div className="flex items-center gap-3">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${event.iconBg}`}>
              <IconComponent className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-[#F4F7FF] flex items-center gap-2">
                {event.name}
                <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${event.severityBadgeColor}`}>
                  {event.severity} Severity
                </span>
              </h2>
              <p className="text-xs text-[#93A9C8]">
                Event ID: <span className="font-mono text-[#00D9F5]">{event.id}</span> • {event.region}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 text-[#93A9C8] hover:text-white rounded-lg hover:bg-[#101F3D] transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 px-5 pt-3 pb-1 border-b border-[#122040] bg-[#081329] overflow-x-auto text-xs">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
              activeTab === 'overview'
                ? 'bg-[#168BFF] text-white shadow-sm shadow-[#168BFF]/40'
                : 'text-[#93A9C8] hover:text-white hover:bg-[#101F3D]'
            }`}
          >
            Overview & Telemetry
          </button>
          <button
            onClick={() => setActiveTab('track')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'track'
                ? 'bg-[#168BFF] text-white shadow-sm shadow-[#168BFF]/40'
                : 'text-[#93A9C8] hover:text-white hover:bg-[#101F3D]'
            }`}
          >
            <Navigation className="w-3.5 h-3.5" />
            Track Evolution
            {trackDetail && (
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-cyan-500/20 text-[#00D9F5] font-mono">
                {trackDetail.total_detections} frames
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('uncertainty')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'uncertainty'
                ? 'bg-[#168BFF] text-white shadow-sm shadow-[#168BFF]/40'
                : 'text-[#93A9C8] hover:text-white hover:bg-[#101F3D]'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            Forecast Uncertainty
            {uncertaintyDetail && (
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                uncertaintyDetail.is_available 
                  ? 'bg-emerald-500/20 text-emerald-400' 
                  : 'bg-amber-500/20 text-amber-400'
              }`}>
                {uncertaintyDetail.is_available ? '5-Member Ensemble' : 'Deterministic'}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('ai_scoring')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'ai_scoring'
                ? 'bg-[#168BFF] text-white shadow-sm shadow-[#168BFF]/40'
                : 'text-[#93A9C8] hover:text-white hover:bg-[#101F3D]'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            AI Score Attribution
            {aiScore && (
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-purple-500/20 text-purple-300 font-mono font-bold">
                {aiScore.overall_score_100}/100
              </span>
            )}
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 sm:p-6 overflow-y-auto space-y-4 text-sm flex-1">
          {/* TAB 1: OVERVIEW & TELEMETRY */}
          {activeTab === 'overview' && (
            <div className="space-y-4">
              {/* Scientific Description Box */}
              <div className="p-3.5 rounded-xl bg-[#071126] border border-[#142445] text-xs text-[#93A9C8] leading-relaxed">
                <span className="font-bold text-[#00D9F5] uppercase tracking-wider block mb-1">
                  Meteorological Synopsis
                </span>
                {event.description}
              </div>

              {/* Diagnostic Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-xl bg-[#101F3D] border border-[#16274a]">
                  <span className="text-[11px] text-[#93A9C8] block">Coordinates</span>
                  <span className="text-xs font-mono font-bold text-[#F4F7FF] mt-1 block">
                    {event.coordinatesDisplay}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-[#101F3D] border border-[#16274a]">
                  <span className="text-[11px] text-[#93A9C8] block">Forecast Window</span>
                  <span className="text-xs font-bold text-[#F4F7FF] mt-1 block">
                    {event.forecastWindow}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-[#101F3D] border border-[#16274a]">
                  <span className="text-[11px] text-[#93A9C8] block">Estimated Footprint</span>
                  <span className="text-xs font-mono font-bold text-[#00D9F5] mt-1 block">
                    {event.estimatedArea}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-[#101F3D] border border-[#16274a]">
                  <span className="text-[11px] text-[#93A9C8] block">Max Sustained Wind</span>
                  <span className="text-xs font-mono font-bold text-[#F4F7FF] mt-1 block">
                    {event.maxWind}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-[#101F3D] border border-[#16274a]">
                  <span className="text-[11px] text-[#93A9C8] block">Central Pressure</span>
                  <span className="text-xs font-mono font-bold text-[#F4F7FF] mt-1 block">
                    {event.centralPressure}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-[#101F3D] border border-[#16274a]">
                  <span className="text-[11px] text-[#93A9C8] block">Anomaly Deficit Score</span>
                  <span className="text-xs font-mono font-bold text-[#FFB020] mt-1 block">
                    {event.anomalyScore}
                  </span>
                </div>
              </div>

              {/* Action Advisory */}
              <div className="p-3.5 rounded-xl bg-[#FFB020]/10 border border-[#FFB020]/30 text-xs">
                <span className="font-bold text-[#FFB020] uppercase tracking-wider block mb-1">
                  Decision Support Notice (Demo Mode)
                </span>
                <p className="text-[#93A9C8] leading-snug">
                  This simulated event exhibits significant departure from the climatological baseline. In operational mode, this triggers automatic early warning dispatches to regional disaster mitigation councils.
                </p>
              </div>
            </div>
          )}

          {/* TAB 2: TRACK EVOLUTION & MOVEMENT */}
          {activeTab === 'track' && (
            <div className="space-y-4">
              {trackDetail ? (
                <>
                  {/* Summary Bar */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                    <div className="p-2.5 rounded-xl bg-[#071126] border border-[#16274a]">
                      <span className="text-[10px] text-[#93A9C8] uppercase font-bold block">Track Series</span>
                      <span className="text-xs font-mono font-bold text-[#00D9F5] mt-0.5 block">{trackDetail.track_id}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-[#071126] border border-[#16274a]">
                      <span className="text-[10px] text-[#93A9C8] uppercase font-bold block">Net Displacement</span>
                      <span className="text-xs font-mono font-bold text-white mt-0.5 block">{trackDetail.net_displacement_km} km</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-[#071126] border border-[#16274a]">
                      <span className="text-[10px] text-[#93A9C8] uppercase font-bold block">Mean Translation</span>
                      <span className="text-xs font-mono font-bold text-[#38BDF8] mt-0.5 block">{trackDetail.mean_speed_kmh} km/h</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-[#071126] border border-[#16274a]">
                      <span className="text-[10px] text-[#93A9C8] uppercase font-bold block">Max Surface Area</span>
                      <span className="text-xs font-mono font-bold text-[#FFB020] mt-0.5 block">{trackDetail.max_area_km2.toLocaleString()} km²</span>
                    </div>
                  </div>

                  {/* Scientific Caveat Label */}
                  <div className="p-3 rounded-xl bg-[#101F3D]/60 border border-[#16274a] text-[11px] text-[#93A9C8] flex items-start gap-2">
                    <Info className="w-4 h-4 text-[#00D9F5] shrink-0 mt-0.5" />
                    <span>
                      {trackDetail.movement_notes || "Derived movement represents displacement of detected forecast footprint centroids; it does not constitute a verified physical storm track."}
                    </span>
                  </div>

                  {/* Chronological Step History Table */}
                  <div className="rounded-xl border border-[#16274a] overflow-hidden bg-[#071126]">
                    <div className="px-3.5 py-2 bg-[#0B1730] border-b border-[#16274a] flex items-center justify-between text-xs font-bold text-[#F4F7FF]">
                      <span>Chronological Forecast Step History</span>
                      <span className="text-[11px] text-[#93A9C8] font-normal">10-Day Evaluation</span>
                    </div>

                    <div className="divide-y divide-[#122040] text-xs">
                      {trackDetail.points.map((pt) => {
                        const isDetected = pt.detection_status === 'DETECTED';

                        return (
                          <div key={pt.frame_index} className="px-3.5 py-2.5 flex items-center justify-between hover:bg-[#0c1836] transition-colors">
                            <div className="flex items-center gap-3">
                              <span className="w-12 font-mono font-bold text-[#F4F7FF] text-xs">
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
                              <div className="flex items-center gap-4 font-mono text-[11px] text-right">
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
                </>
              ) : (
                <div className="p-8 text-center text-[#93A9C8] text-xs">
                  Loading track evolution telemetry...
                </div>
              )}
            </div>
          )}

          {/* TAB 3: FORECAST UNCERTAINTY */}
          {activeTab === 'uncertainty' && (
            <div className="space-y-4">
              {uncertaintyDetail ? (
                <>
                  {/* Mode Banner */}
                  {uncertaintyDetail.is_available ? (
                    <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs">
                      <div className="flex items-center gap-2 text-emerald-400 font-bold mb-1">
                        <Activity className="w-4 h-4" />
                        <span>Multi-Member Ensemble Spread Available (5 Members)</span>
                      </div>
                      <p className="text-[#93A9C8] leading-relaxed">
                        {uncertaintyDetail.methodology_notes}
                      </p>
                    </div>
                  ) : (
                    <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs">
                      <div className="flex items-center gap-2 text-amber-400 font-bold mb-1">
                        <AlertTriangle className="w-4 h-4" />
                        <span>Deterministic Forecast — Ensemble Spread Unavailable</span>
                      </div>
                      <p className="text-[#93A9C8] leading-relaxed">
                        This is an individual deterministic NWP forecast run (1 member). True ensemble variance cannot be calculated without multi-member simulations. Uncertainty is communicated via atmospheric predictability decay limits.
                      </p>
                    </div>
                  )}

                  {/* If Ensemble Spread Exists: Daily Spread Table */}
                  {uncertaintyDetail.is_available && uncertaintyDetail.daily_spread?.length > 0 && (
                    <div className="rounded-xl border border-[#16274a] overflow-hidden bg-[#071126]">
                      <div className="px-3.5 py-2 bg-[#0B1730] border-b border-[#16274a] flex items-center justify-between text-xs font-bold text-[#F4F7FF]">
                        <span>Ensemble Member Dispersion by Lead Time</span>
                        <span className="text-[11px] text-[#00D9F5]">5-Member Perturbation</span>
                      </div>

                      <div className="divide-y divide-[#122040] text-xs">
                        {uncertaintyDetail.daily_spread.map((d) => (
                          <div key={d.forecast_day} className="px-3.5 py-2.5 flex items-center justify-between">
                            <div className="flex items-center gap-3 font-mono">
                              <span className="font-bold text-[#F4F7FF]">Day {d.forecast_day}</span>
                              <span className="text-[#93A9C8] text-[11px]">T+{d.step_hours}h</span>
                            </div>

                            <div className="flex items-center gap-5 text-right font-mono text-[11px]">
                              <div>
                                <span className="text-[#93A9C8] block text-[9px] uppercase">Agreement</span>
                                <span className={`font-bold ${d.member_agreement_pct >= 80 ? 'text-emerald-400' : 'text-amber-400'}`}>
                                  {d.member_agreement_pct}%
                                </span>
                              </div>
                              <div>
                                <span className="text-[#93A9C8] block text-[9px] uppercase">Spatial Spread</span>
                                <span className="text-white">±{d.centroid_spatial_dispersion_km} km</span>
                              </div>
                              <div>
                                <span className="text-[#93A9C8] block text-[9px] uppercase">Area IQR</span>
                                <span className="text-[#00D9F5]">±{d.area_iqr_km2.toLocaleString()} km²</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Standard Lead Time Decay Guide */}
                  <div className="rounded-xl border border-[#16274a] overflow-hidden bg-[#071126]">
                    <div className="px-3.5 py-2 bg-[#0B1730] border-b border-[#16274a] text-xs font-bold text-[#F4F7FF]">
                      Atmospheric Predictability & Lead-Time Skill Decay
                    </div>
                    <div className="p-3 text-xs space-y-2">
                      <div className="flex items-center justify-between p-2 rounded-lg bg-[#101F3D]">
                        <span className="font-bold text-emerald-400">Days 1–3 (0–72h)</span>
                        <span className="text-[11px] text-[#93A9C8]">High Confidence (Tight deterministic consensus)</span>
                        <span className="font-mono text-xs font-bold text-white">82% – 95%</span>
                      </div>
                      <div className="flex items-center justify-between p-2 rounded-lg bg-[#101F3D]">
                        <span className="font-bold text-amber-400">Days 4–6 (72–144h)</span>
                        <span className="text-[11px] text-[#93A9C8]">Moderate Confidence (Convective divergence begins)</span>
                        <span className="font-mono text-xs font-bold text-white">52% – 72%</span>
                      </div>
                      <div className="flex items-center justify-between p-2 rounded-lg bg-[#101F3D]">
                        <span className="font-bold text-red-400">Days 7–10 (144–240h)</span>
                        <span className="text-[11px] text-[#93A9C8]">Low / Trend-Only (High chaotic sensitivity)</span>
                        <span className="font-mono text-xs font-bold text-white">22% – 42%</span>
                      </div>
                    </div>
                  </div>

                  {/* Documented Limitations */}
                  {uncertaintyDetail.known_limitations?.length > 0 && (
                    <div className="p-3 rounded-xl bg-[#081329] border border-[#142445] text-xs text-[#93A9C8] space-y-1">
                      <span className="font-bold text-[#93A9C8] uppercase tracking-wider text-[10px] block">
                        Scientific Caveats & Limitations
                      </span>
                      {uncertaintyDetail.known_limitations.map((lim, idx) => (
                        <div key={idx} className="flex items-start gap-1.5 text-[11px]">
                          <span className="text-amber-400 font-bold">•</span>
                          <span>{lim}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div className="p-8 text-center text-[#93A9C8] text-xs">
                  Loading uncertainty profile...
                </div>
              )}
            </div>
          )}

          {/* TAB 4: AI SCORING & COMPONENT ATTRIBUTION */}
          {activeTab === 'ai_scoring' && (
            <div className="space-y-4">
              {aiScore ? (
                <>
                  {/* Composite Gauge Card */}
                  <div className="p-4 rounded-xl bg-[#071126] border border-[#142445] flex items-center justify-between">
                    <div>
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                        Composite Anomaly Departure Index
                      </span>
                      <div className="flex items-baseline gap-2 mt-1">
                        <span className="text-3xl font-black text-white font-mono">
                          {aiScore.overall_score_100}
                        </span>
                        <span className="text-xs font-bold text-slate-500">/ 100</span>
                        <span className={`ml-2 text-xs font-bold px-2.5 py-0.5 rounded-full border ${
                          aiScore.severity_tier === 'Extreme' ? 'bg-red-500/20 text-red-400 border-red-500/40' :
                          aiScore.severity_tier === 'High' ? 'bg-amber-500/20 text-amber-400 border-amber-500/40' :
                          'bg-blue-500/20 text-blue-400 border-blue-500/40'
                        }`}>
                          {aiScore.severity_tier} Severity Tier
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                        {aiScore.score_interpretation}
                      </p>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-[10px] text-slate-400 block">Method:</span>
                      <span className="text-xs font-mono font-semibold text-[#00D9F5]">
                        {aiScore.detection_method}
                      </span>
                    </div>
                  </div>

                  {/* Component Breakdown Cards */}
                  <div className="space-y-2">
                    <span className="text-xs font-bold text-white uppercase tracking-wider block">
                      Dimensionless Component Contributions (Weights & Normalization)
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      {Object.entries(aiScore.components || {}).map(([key, comp]) => (
                        <div key={key} className="p-3 bg-[#071126] border border-[#16274a] rounded-xl text-xs space-y-1.5">
                          <div className="flex items-center justify-between font-semibold text-white">
                            <span>{comp.display_name}</span>
                            <span className="font-mono text-[#00D9F5] font-bold">{comp.normalized_score.toFixed(2)}</span>
                          </div>
                          <div className="w-full bg-[#122040] rounded-full h-1.5 overflow-hidden">
                            <div 
                              className="h-full bg-gradient-to-r from-[#168BFF] to-[#00D9F5] rounded-full"
                              style={{ width: `${Math.round(comp.normalized_score * 100)}%` }}
                            />
                          </div>
                          <div className="flex justify-between text-[10px] text-slate-400">
                            <span>Weight: {(comp.weight * 100).toFixed(0)}%</span>
                            <span>Contribution: {comp.contribution_percent}%</span>
                          </div>
                          <p className="text-[10px] text-slate-400 leading-snug pt-1 border-t border-[#122040]">
                            {comp.interpretation}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Scientific Caveats */}
                  <div className="p-3 rounded-xl bg-[#081329] border border-[#142445] text-xs text-[#93A9C8] space-y-1">
                    <span className="font-bold text-amber-400 uppercase tracking-wider text-[10px] block">
                      Statistical Bounds & Limitations
                    </span>
                    {aiScore.score_limitations?.map((lim, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-[11px]">
                        <span className="text-amber-400 font-bold">•</span>
                        <span>{lim}</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="p-8 text-center text-[#93A9C8] text-xs">
                  Loading multi-component anomaly score...
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-[#122040] bg-[#071126] flex items-center justify-between text-xs">
          <span className="text-[11px] text-[#64748b]">
            AeroNex Intelligence Engine • Phase 6
          </span>
          <button 
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-[#168BFF] hover:bg-[#3894FF] text-xs font-bold text-white transition-all cursor-pointer shadow-md shadow-[#168BFF]/30"
          >
            Close Telemetry
          </button>
        </div>
      </div>
    </div>
  );
}
