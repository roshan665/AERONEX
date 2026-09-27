import React from 'react';
import WeatherMap from '../components/map/WeatherMap';
import EventDetails from '../components/dashboard/EventDetails';

export default function MapView({ 
  events, 
  selectedEvent, 
  onSelectEvent, 
  onViewModal,
  forecastDay,
  setForecastDay,
  isPlaying,
  setIsPlaying
}) {
  return (
    <div className="space-y-4 select-none">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-[#122040]">
        <div>
          <h2 className="text-lg font-bold text-[#F4F7FF] tracking-tight">
            Interactive Global Weather Map
          </h2>
          <p className="text-xs text-[#93A9C8]">
            Geospatial tracking of extreme anomalies, synoptic systems, and forecast footprints.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-[#93A9C8]">
          <span className="w-2 h-2 rounded-full bg-[#00D9F5] animate-pulse"></span>
          <span>Projection: WGS84 (EPSG:4326)</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Full-size Map Container */}
        <div className="lg:col-span-8">
          <WeatherMap 
            events={events}
            selectedEvent={selectedEvent}
            onSelectEvent={onSelectEvent}
            forecastDay={forecastDay}
            setForecastDay={setForecastDay}
            isPlaying={isPlaying}
            setIsPlaying={setIsPlaying}
          />
        </div>

        {/* Selected Event Telemetry Panel & Instructions */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          <EventDetails 
            selectedEvent={selectedEvent} 
            onViewModal={onViewModal} 
          />

          <div className="bg-[#0B1730] rounded-2xl p-4 sm:p-5 border border-[#16274a] text-xs space-y-2.5">
            <h4 className="font-bold text-[#F4F7FF] uppercase tracking-wider text-[11px] pb-1 border-b border-[#122040]">
              Geospatial Instructions
            </h4>
            <p className="text-[#93A9C8] leading-relaxed">
              • Click any marker or polygon on the map to inspect its real-time meteorological metrics.
            </p>
            <p className="text-[#93A9C8] leading-relaxed">
              • Toggle layers on the top-left overlay controller to inspect specific variable fields.
            </p>
            <p className="text-[#93A9C8] leading-relaxed">
              • Use the forecast scrubber to evaluate spatial evolution across Days 1–10.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
