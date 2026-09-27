import React from 'react';

export default function MapLegend({ activeLayer = 'temperature' }) {
  const layerLabels = {
    temperature: { title: 'Temperature Anomaly (°C)', min: '-10', mid: '0', max: '+10', ramp: 'from-[#168BFF] via-[#00D9F5] via-[#93A9C8] via-[#FFB020] to-[#FF4568]' },
    wind: { title: 'Wind Speed Anomaly (m/s)', min: '0', mid: '+15', max: '+35', ramp: 'from-[#93A9C8] via-[#00D9F5] via-[#FFB020] to-[#FF4568]' },
    pressure: { title: 'Sea Level Pressure (hPa)', min: '980', mid: '1005', max: '1025', ramp: 'from-[#FF4568] via-[#FFB020] via-[#93A9C8] to-[#168BFF]' },
    precipitation: { title: 'Precipitation Rate (mm/h)', min: '0', mid: '+20', max: '+60', ramp: 'from-[#071126] via-[#168BFF] via-[#00D9F5] to-[#FF4568]' }
  };
  const current = layerLabels[activeLayer] || layerLabels.temperature;

  return (
    <div className="bg-[#071126]/90 backdrop-blur-md border border-[#16274a] rounded-xl px-3 py-2 shadow-2xl text-left select-none w-56">
      <div className="text-[11px] font-semibold text-[#F4F7FF] mb-1.5 flex items-center justify-between">
        <span>{current.title}</span>
      </div>

      {/* Scientific Continuous Color Ramp */}
      <div className={`h-2 w-full rounded-full bg-gradient-to-r ${current.ramp} shadow-inner`}></div>

      {/* Axis Tick Marks */}
      <div className="flex justify-between text-[10px] font-mono text-[#93A9C8] mt-1 font-medium">
        <span>{current.min}</span>
        <span>{current.mid}</span>
        <span>{current.max}</span>
      </div>
    </div>
  );
}
