import React from 'react';
import { Printer, ShieldCheck } from 'lucide-react';
import { DEMO_METADATA } from '../data/demoData';

export default function ReportsView({ events = [] }) {
  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-4 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#122040]">
        <div>
          <h2 className="text-lg font-bold text-[#F4F7FF] tracking-tight">
            Meteorological Situational Reports (SITREP)
          </h2>
          <p className="text-xs text-[#93A9C8]">
            Automated intelligence briefings for disaster planning and executive response teams.
          </p>
        </div>

        <button
          onClick={handlePrint}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#168BFF] hover:bg-[#3894FF] text-white text-xs font-bold transition-all cursor-pointer self-start sm:self-auto shadow-md shadow-[#168BFF]/30"
        >
          <Printer className="w-3.5 h-3.5" />
          <span>Print / Export PDF</span>
        </button>
      </div>

      {/* Main SITREP Briefing Document Card */}
      <div className="bg-[#0B1730] rounded-2xl p-6 border border-[#16274a] shadow-2xl max-w-4xl space-y-6">
        {/* Document Top Header */}
        <div className="flex justify-between items-start pb-4 border-b border-[#122040]">
          <div>
            <div className="text-[11px] font-mono uppercase font-bold text-[#00D9F5]">
              AERONEX METEOROLOGICAL INTELLIGENCE BULLETIN
            </div>
            <h1 className="text-xl font-extrabold text-[#F4F7FF] mt-1">
              Global Extreme Weather Anomaly Briefing
            </h1>
            <p className="text-xs text-[#93A9C8] mt-0.5">
              Cycle Valid: {DEMO_METADATA.currentUtcTimestamp} • Clearance: Unclassified Demonstration
            </p>
          </div>
          <div className="px-2.5 py-1 rounded-lg bg-[#FFB020]/15 border border-[#FFB020]/30 text-[#FFB020] text-xs font-bold uppercase">
            Demo Sample Run
          </div>
        </div>

        {/* Executive Summary */}
        <div>
          <h3 className="text-xs font-bold text-[#F4F7FF] uppercase tracking-wider mb-2">
            1. Executive Assessment
          </h3>
          <p className="text-xs text-[#93A9C8] leading-relaxed bg-[#071126] p-4 rounded-xl border border-[#142445]">
            Numerical Weather Prediction diagnostics identify <strong>{events.length} active extreme weather anomalies</strong> exceeding operational thresholds. Most critical is a high-intensity <strong>Tropical Cyclone</strong> propagating in the Western Indian Ocean with peak wind speeds estimated up to 150 km/h, and an expansive <strong>Heat Dome</strong> over Central Asia exhibiting temperature departures exceeding operational physical thresholds and spatial baseline standard deviations (+3.8σ).
          </p>
        </div>

        {/* Tabular Anomaly Summary */}
        <div>
          <h3 className="text-xs font-bold text-[#F4F7FF] uppercase tracking-wider mb-2">
            2. High-Priority Monitored Synoptic Entities
          </h3>
          <div className="overflow-x-auto rounded-xl border border-[#142445]">
            <table className="w-full text-xs text-left">
              <thead className="bg-[#071126] text-[#93A9C8] border-b border-[#142445] text-[11px] uppercase">
                <tr>
                  <th className="p-3">Entity Name</th>
                  <th className="p-3">Region</th>
                  <th className="p-3">Coordinates</th>
                  <th className="p-3">Severity</th>
                  <th className="p-3">Est. Footprint</th>
                  <th className="p-3">Max Wind</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#122040] bg-[#0B1730]">
                {events.map((evt) => (
                  <tr key={evt.id} className="hover:bg-[#101F3D] transition-colors">
                    <td className="p-3 font-semibold text-[#F4F7FF]">{evt.name}</td>
                    <td className="p-3 text-[#93A9C8]">{evt.region}</td>
                    <td className="p-3 font-mono text-[#93A9C8]">{evt.coordinatesDisplay}</td>
                    <td className="p-3">
                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${evt.severityBadgeColor}`}>
                        {evt.severity}
                      </span>
                    </td>
                    <td className="p-3 font-mono text-[#00D9F5]">{evt.estimatedArea}</td>
                    <td className="p-3 font-mono text-[#93A9C8]">{evt.maxWind}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Verification Footnote */}
        <div className="pt-4 border-t border-[#122040] flex items-center justify-between text-[11px] text-[#93A9C8]">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-[#00D6A0]" />
            <span>Automated Mathematical Detection Protocol Verified</span>
          </div>
          <span>Ref ID: AERONEX-SITREP-2025-04</span>
        </div>
      </div>
    </div>
  );
}
