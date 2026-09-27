import React, { useState } from 'react';
import { 
  RotateCcw, 
  Activity, 
  Flame, 
  AlertTriangle, 
  Snowflake, 
  Layers, 
  Database, 
  CheckCircle2, 
  AlertCircle,
  Clock,
  Compass,
  Zap
} from 'lucide-react';

const SCENARIOS = [
  {
    id: 'cyclone',
    name: 'Tropical Cyclone Vortex',
    shortName: 'Cyclone Vortex',
    leadTime: 24,
    dayText: 'Day 1 (24h)',
    icon: Flame,
    color: 'text-red-400 border-red-500/40 bg-red-500/10',
    activeColor: 'bg-red-500 text-white shadow-lg shadow-red-500/30',
    description: 'Western Indian Ocean depression: 948 hPa central pressure deficit & 145 km/h eyewall winds.',
  },
  {
    id: 'heatwave',
    name: 'Severe Heat Dome',
    shortName: 'Heat Dome',
    leadTime: 48,
    dayText: 'Day 2 (48h)',
    icon: AlertTriangle,
    color: 'text-orange-400 border-orange-500/40 bg-orange-500/10',
    activeColor: 'bg-orange-500 text-white shadow-lg shadow-orange-500/30',
    description: 'Subtropical thermal ridge: +15°C temperature departure exceeding 3.8-sigma normal.',
  },
  {
    id: 'coldwave',
    name: 'Arctic Cold Wave Outbreak',
    shortName: 'Cold Wave',
    leadTime: 72,
    dayText: 'Day 3 (72h)',
    icon: Snowflake,
    color: 'text-cyan-400 border-cyan-500/40 bg-cyan-500/10',
    activeColor: 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/30',
    description: 'Siberian Arctic sector plunge: -28°C sub-zero freeze anomaly with -3.6 sigma departure.',
  },
  {
    id: 'all',
    name: 'Full Multi-Hazard Benchmark',
    shortName: 'All Hazards (5)',
    leadTime: 24,
    dayText: 'Benchmark (All)',
    icon: Layers,
    color: 'text-blue-400 border-blue-500/40 bg-blue-500/10',
    activeColor: 'bg-[#168BFF] text-white shadow-lg shadow-[#168BFF]/30',
    description: 'Complete multi-variable synoptic grid containing all 5 injected extreme weather phenomena simultaneously.',
  },
];

export default function ScenarioToolbar({
  dataMode = 'DEMO_DATA',
  onSwitchDataMode,
  activeScenario = 'all',
  onSelectScenario,
  onRunDetection,
  onResetDemo,
  isDetecting = false,
  detectionFeedback = null,
  forecastDay = 3,
  setForecastDay,
}) {
  const [selectedLeadHours, setSelectedLeadHours] = useState(24);

  const currentScenario = SCENARIOS.find(s => s.id === activeScenario) || SCENARIOS[3];

  const handleScenarioClick = (sc) => {
    if (onSelectScenario) {
      onSelectScenario(sc.id);
    }
    setSelectedLeadHours(sc.leadTime);
    if (setForecastDay) {
      setForecastDay(Math.min(10, Math.max(1, Math.round(sc.leadTime / 24))));
    }
  };

  const handleExecute = () => {
    if (isDetecting) return;
    if (onRunDetection) {
      onRunDetection(activeScenario, selectedLeadHours);
    }
  };

  return (
    <div className="bg-[#0B1730] border border-[#16274a] rounded-2xl p-4 sm:p-5 shadow-2xl select-none space-y-4">
      {/* Top Bar: Data Mode Status Pill + Switcher & Reset Button */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3.5 border-b border-[#122040]">
        <div className="flex items-center gap-2.5 flex-wrap">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border shadow-sm backdrop-blur-md transition-all">
            <span className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                dataMode === 'REAL_NWP_DATA' ? 'bg-[#00D9F5]' : 'bg-[#FFB020]'
              }`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${
                dataMode === 'REAL_NWP_DATA' ? 'bg-[#00D9F5]' : 'bg-[#FFB020]'
              }`}></span>
            </span>
            <span className={dataMode === 'REAL_NWP_DATA' ? 'text-[#00D9F5]' : 'text-[#FFB020]'}>
              {dataMode === 'REAL_NWP_DATA' ? 'REAL NWP MODE' : 'DEMO MODE (SYNTHETIC)'}
            </span>
          </div>

          <span className="text-xs text-[#93A9C8] hidden sm:inline">
            {dataMode === 'REAL_NWP_DATA' 
              ? 'NOAA NCEP GFS 0.25° NetCDF4 Analysis Domain' 
              : 'Reproducible Physical Benchmark (SIH 2025 Evaluation)'}
          </span>
        </div>

        {/* Action Buttons: Toggle Mode & Reset */}
        <div className="flex items-center gap-2 self-start md:self-auto">
          {dataMode === 'DEMO_DATA' ? (
            <button
              onClick={() => onSwitchDataMode && onSwitchDataMode('REAL_NWP_DATA')}
              className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#102040] hover:bg-[#162e5c] text-[#00D9F5] border border-[#00D9F5]/30 hover:border-[#00D9F5]/60 transition-all flex items-center gap-1.5 cursor-pointer"
              title="Switch to Real NWP Mode (loads offline NetCDF4 GFS analysis)"
            >
              <Database className="w-3.5 h-3.5 text-[#00D9F5]" />
              <span>Load Real NWP Grid</span>
            </button>
          ) : (
            <button
              onClick={() => onSwitchDataMode && onSwitchDataMode('DEMO_DATA')}
              className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#102040] hover:bg-[#162e5c] text-[#FFB020] border border-[#FFB020]/30 hover:border-[#FFB020]/60 transition-all flex items-center gap-1.5 cursor-pointer"
              title="Switch to Synthetic Demo Scenarios"
            >
              <RotateCcw className="w-3.5 h-3.5 text-[#FFB020]" />
              <span>Switch to Demo Mode</span>
            </button>
          )}

          <button
            onClick={onResetDemo}
            className="px-3 py-1.5 rounded-xl text-xs font-medium text-[#93A9C8] hover:text-white bg-[#071126] hover:bg-[#101F3D] border border-[#16274a] transition-all flex items-center gap-1.5 cursor-pointer"
            title="Reset to default 6-event demo catalog state"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Demo</span>
          </button>
        </div>
      </div>

      {/* Main Controls: Scenario Selector & Run Detection Action */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Scenario Selection Tabs */}
        <div className="space-y-1.5 flex-1">
          <div className="text-[11px] font-semibold text-[#93A9C8] uppercase tracking-wider flex items-center gap-1.5">
            <Compass className="w-3 h-3 text-[#168BFF]" />
            <span>Select Demonstration Scenario</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {SCENARIOS.map((sc) => {
              const isSelected = activeScenario === sc.id;
              const IconComp = sc.icon;

              return (
                <button
                  key={sc.id}
                  onClick={() => handleScenarioClick(sc)}
                  className={`p-2.5 rounded-xl border text-left transition-all duration-200 cursor-pointer flex flex-col justify-between gap-1.5 ${
                    isSelected 
                      ? `${sc.activeColor} border-transparent ring-2 ring-white/20` 
                      : `bg-[#071126] hover:bg-[#101F3D] border-[#16274a] text-[#93A9C8] hover:text-white`
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="text-xs font-bold truncate">{sc.shortName}</span>
                    <IconComp className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-white' : ''}`} />
                  </div>
                  <span className={`text-[10px] font-mono ${isSelected ? 'text-white/80' : 'text-[#93A9C8]/70'}`}>
                    {sc.dayText}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Lead Time & Execute Button */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-end gap-3 lg:border-l lg:border-[#122040] lg:pl-4 shrink-0">
          <div>
            <label className="text-[11px] font-semibold text-[#93A9C8] uppercase tracking-wider block mb-1.5 flex items-center justify-between gap-1">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-[#168BFF]" />
                <span>Lead Horizon</span>
              </span>
              <span className="text-[10px] text-[#00D9F5] font-mono font-normal">Day {forecastDay}</span>
            </label>
            <select
              value={selectedLeadHours}
              onChange={(e) => {
                const val = Number(e.target.value);
                setSelectedLeadHours(val);
                if (setForecastDay) setForecastDay(Math.min(10, Math.max(1, Math.round(val / 24))));
              }}
              className="h-10 px-3 bg-[#071126] border border-[#16274a] rounded-xl text-xs font-mono text-[#F4F7FF] focus:outline-none focus:border-[#168BFF] cursor-pointer"
            >
              <option value={24}>T+24h (Day 1)</option>
              <option value={48}>T+48h (Day 2)</option>
              <option value={72}>T+72h (Day 3)</option>
              <option value={96}>T+96h (Day 4)</option>
              <option value={120}>T+120h (Day 5)</option>
            </select>
          </div>

          <button
            onClick={handleExecute}
            disabled={isDetecting}
            className="h-10 px-5 rounded-xl bg-[#168BFF] hover:bg-[#3894FF] disabled:opacity-50 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-[#168BFF]/30 transition-all cursor-pointer shrink-0"
          >
            {isDetecting ? (
              <>
                <Activity className="w-4 h-4 animate-spin text-white" />
                <span>Running Detection Pipeline...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 text-cyan-200 fill-cyan-200" />
                <span>Run Anomaly Detection</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Scenario Description Pill */}
      <div className="p-2.5 rounded-xl bg-[#071126] border border-[#122040] text-xs text-[#93A9C8] flex items-center gap-2">
        <span className="font-semibold text-[#F4F7FF] shrink-0">Active Scenario:</span>
        <span className="truncate">{currentScenario.description}</span>
      </div>

      {/* Feedback Banner (Success / Error / Progress) */}
      {detectionFeedback && (
        <div className={`p-3 rounded-xl border text-xs flex items-center justify-between gap-3 animate-in fade-in duration-200 ${
          detectionFeedback.type === 'success'
            ? 'bg-[#00D6A0]/10 border-[#00D6A0]/30 text-[#00D6A0]'
            : 'bg-[#FF4568]/10 border-[#FF4568]/30 text-[#FF4568]'
        }`}>
          <div className="flex items-center gap-2">
            {detectionFeedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0" />
            )}
            <span>{detectionFeedback.message}</span>
          </div>

          {detectionFeedback.execution_time_ms && (
            <span className="font-mono text-[11px] text-[#F4F7FF] shrink-0">
              ⚡ {detectionFeedback.execution_time_ms.toFixed(1)} ms • {detectionFeedback.method || '3-Sigma Morphological Detector'}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
