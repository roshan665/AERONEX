import React, { useState } from 'react';
import { Sliders, CheckCircle2, RotateCcw } from 'lucide-react';

export default function SettingsView() {
  const [zScoreThreshold, setZScoreThreshold] = useState(2.5);
  const [minWindSpeed, setMinWindSpeed] = useState(17.5);
  const [minPressure, setMinPressure] = useState(990);
  const [minAreaKm2, setMinAreaKm2] = useState(2500);
  const [savedToast, setSavedToast] = useState(false);

  const handleSave = () => {
    setSavedToast(true);
    setTimeout(() => setSavedToast(false), 2500);
  };

  const handleReset = () => {
    setZScoreThreshold(2.5);
    setMinWindSpeed(17.5);
    setMinPressure(990);
    setMinAreaKm2(2500);
  };

  return (
    <div className="space-y-4 max-w-3xl select-none">
      <div className="pb-3 border-b border-[#122040]">
        <h2 className="text-lg font-bold text-[#F4F7FF] tracking-tight">
          System Configuration & Detection Thresholds
        </h2>
        <p className="text-xs text-[#93A9C8]">
          Tune mathematical sensitivities for statistical Z-score departures and physical spatial grouping.
        </p>
      </div>

      {savedToast && (
        <div className="p-3.5 rounded-xl bg-[#00D6A0]/15 border border-[#00D6A0]/30 text-[#00D6A0] text-xs flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-[#00D6A0]" />
          <span className="font-semibold">Configuration saved successfully. Anomaly detection thresholds updated.</span>
        </div>
      )}

      {/* Detection Parameters Card */}
      <div className="bg-[#0B1730] rounded-2xl p-5 border border-[#16274a] shadow-xl space-y-5">
        <h3 className="text-xs font-bold text-[#F4F7FF] uppercase tracking-wider flex items-center gap-2">
          <Sliders className="w-4 h-4 text-[#00D9F5]" />
          Algorithmic Sensitivity Sliders
        </h3>

        {/* Z-Score Departure Threshold */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-xs">
            <label className="font-semibold text-[#F4F7FF]">
              Climatological Z-Score Cutoff (Standard Deviations)
            </label>
            <span className="font-mono text-[#00D9F5] font-bold bg-[#101F3D] px-2.5 py-1 rounded-lg border border-[#16274a]">
              ±{zScoreThreshold}σ
            </span>
          </div>
          <input 
            type="range" 
            min="1.5" 
            max="4.5" 
            step="0.1" 
            value={zScoreThreshold}
            onChange={(e) => setZScoreThreshold(Number(e.target.value))}
            className="w-full h-1.5 bg-[#101F3D] rounded-lg appearance-none cursor-pointer accent-[#168BFF]"
          />
          <div className="flex justify-between text-[10px] text-[#93A9C8]">
            <span>1.5σ (Broad Detection)</span>
            <span>4.5σ (Only Catastrophic Extremes)</span>
          </div>
        </div>

        {/* Minimum Wind Speed Threshold */}
        <div className="space-y-2 pt-2 border-t border-[#122040]">
          <div className="flex justify-between items-center text-xs">
            <label className="font-semibold text-[#F4F7FF]">
              Gale-Force Wind Threshold (m/s)
            </label>
            <span className="font-mono text-[#00D6A0] font-bold bg-[#101F3D] px-2.5 py-1 rounded-lg border border-[#16274a]">
              {minWindSpeed} m/s (~{(minWindSpeed * 3.6).toFixed(0)} km/h)
            </span>
          </div>
          <input 
            type="range" 
            min="10.0" 
            max="35.0" 
            step="0.5" 
            value={minWindSpeed}
            onChange={(e) => setMinWindSpeed(Number(e.target.value))}
            className="w-full h-1.5 bg-[#101F3D] rounded-lg appearance-none cursor-pointer accent-[#00D6A0]"
          />
        </div>

        {/* Deep Low Pressure Core Threshold */}
        <div className="space-y-2 pt-2 border-t border-[#122040]">
          <div className="flex justify-between items-center text-xs">
            <label className="font-semibold text-[#F4F7FF]">
              Deep Low Pressure Core Threshold (hPa)
            </label>
            <span className="font-mono text-[#00D9F5] font-bold bg-[#101F3D] px-2.5 py-1 rounded-lg border border-[#16274a]">
              ≤ {minPressure} hPa
            </span>
          </div>
          <input 
            type="range" 
            min="960" 
            max="1010" 
            step="1" 
            value={minPressure}
            onChange={(e) => setMinPressure(Number(e.target.value))}
            className="w-full h-1.5 bg-[#101F3D] rounded-lg appearance-none cursor-pointer accent-[#00D9F5]"
          />
        </div>

        {/* Minimum Surface Area Polygon Threshold */}
        <div className="space-y-2 pt-2 border-t border-[#122040]">
          <div className="flex justify-between items-center text-xs">
            <label className="font-semibold text-[#F4F7FF]">
              Minimum Cluster Area Filter (km²)
            </label>
            <span className="font-mono text-[#FFB020] font-bold bg-[#101F3D] px-2.5 py-1 rounded-lg border border-[#16274a]">
              {minAreaKm2.toLocaleString()} km²
            </span>
          </div>
          <input 
            type="range" 
            min="500" 
            max="10000" 
            step="500" 
            value={minAreaKm2}
            onChange={(e) => setMinAreaKm2(Number(e.target.value))}
            className="w-full h-1.5 bg-[#101F3D] rounded-lg appearance-none cursor-pointer accent-[#FFB020]"
          />
        </div>

        {/* Save & Reset Actions */}
        <div className="pt-3 border-t border-[#122040] flex items-center justify-between">
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 text-xs text-[#93A9C8] hover:text-[#F4F7FF] transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Factory Baselines</span>
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 rounded-xl bg-[#168BFF] hover:bg-[#3894FF] text-white text-xs font-bold transition-all cursor-pointer shadow-md shadow-[#168BFF]/30"
          >
            Save Parameter Config
          </button>
        </div>
      </div>
    </div>
  );
}
