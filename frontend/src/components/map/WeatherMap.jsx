import React, { useState, useEffect, useRef } from 'react';
import { 
  MapContainer, 
  TileLayer, 
  CircleMarker, 
  Polygon, 
  Polyline, 
  Marker,
  Tooltip, 
  useMap 
} from 'react-leaflet';
import L from 'leaflet';
import { 
  Plus, 
  Minus, 
  Crosshair, 
  Navigation,
  Globe, 
  Maximize2, 
  Minimize2, 
  ChevronUp, 
  ChevronDown,
  Layers as LayersIcon,
  Flame, 
  Wind, 
  Gauge, 
  CloudRain, 
  Radio 
} from 'lucide-react';
import MapLegend from './MapLegend';
import ForecastControls from './ForecastControls';

// Custom 'L' center icon for tropical cyclones / low pressure centers
const createLowPressureIcon = () => {
  return L.divIcon({
    className: 'custom-low-center',
    html: `
      <div style="
        width: 32px; 
        height: 32px; 
        border-radius: 50%; 
        background: rgba(255, 69, 104, 0.35); 
        border: 2px solid #FF4568; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        color: #ffffff; 
        font-weight: 800; 
        font-size: 14px; 
        font-family: 'Inter', sans-serif;
        box-shadow: 0 0 15px rgba(255, 69, 104, 0.7);
        backdrop-filter: blur(4px);
      ">
        L
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
};

// Smooth Camera Controller
function MapCameraController({ selectedEvent, triggerRecenter }) {
  const map = useMap();

  useEffect(() => {
    if (selectedEvent && selectedEvent.lat && selectedEvent.lon) {
      map.flyTo([selectedEvent.lat, selectedEvent.lon], 4.2, {
        duration: 1.2,
        easeLinearity: 0.25,
      });
    }
  }, [selectedEvent, map]);

  useEffect(() => {
    if (triggerRecenter) {
      map.flyTo([15, 65], 2.8, { duration: 1.0 });
    }
  }, [triggerRecenter, map]);

  return null;
}

// Custom Right Stack Navigation Controls (+, -, Crosshair, Compass)
function CustomMapControls({ onRecenter }) {
  const map = useMap();

  return (
    <div className="absolute top-4 right-4 z-[1000] flex flex-col gap-1.5 select-none pointer-events-auto">
      <button
        onClick={() => map.zoomIn()}
        className="w-8 h-8 rounded-lg bg-[#071126]/90 hover:bg-[#101F3D] border border-[#16274a] text-[#93A9C8] hover:text-[#F4F7FF] flex items-center justify-center shadow-xl transition-all cursor-pointer"
        aria-label="Zoom in"
        title="Zoom in"
      >
        <Plus className="w-4 h-4" />
      </button>
      <button
        onClick={() => map.zoomOut()}
        className="w-8 h-8 rounded-lg bg-[#071126]/90 hover:bg-[#101F3D] border border-[#16274a] text-[#93A9C8] hover:text-[#F4F7FF] flex items-center justify-center shadow-xl transition-all cursor-pointer"
        aria-label="Zoom out"
        title="Zoom out"
      >
        <Minus className="w-4 h-4" />
      </button>
      <button
        onClick={onRecenter}
        className="w-8 h-8 rounded-lg bg-[#071126]/90 hover:bg-[#101F3D] border border-[#16274a] text-[#00D9F5] hover:text-white flex items-center justify-center shadow-xl transition-all cursor-pointer mt-1"
        aria-label="Reset view"
        title="Reset view"
      >
        <Crosshair className="w-4 h-4" />
      </button>
      <button
        onClick={onRecenter}
        className="w-8 h-8 rounded-lg bg-[#071126]/90 hover:bg-[#101F3D] border border-[#16274a] text-[#93A9C8] hover:text-[#F4F7FF] flex items-center justify-center shadow-xl transition-all cursor-pointer"
        aria-label="Align North"
        title="Align North"
      >
        <Navigation className="w-3.5 h-3.5 -rotate-45" />
      </button>
    </div>
  );
}

export default function WeatherMap({ 
  events = [], 
  selectedEvent, 
  onSelectEvent,
  forecastDay = 3,
  setForecastDay,
  isPlaying,
  setIsPlaying
}) {
  const [recenterCounter, setRecenterCounter] = useState(0);
  const [mapType, setMapType] = useState('satellite'); // 'map' or 'satellite'
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isLayersOpen, setIsLayersOpen] = useState(true);
  const mapContainerRef = useRef(null);

  // Layer Visibility State
  const [layers, setLayers] = useState({
    temperature: true,
    wind: true,
    pressure: false,
    precipitation: false,
    footprints: true,
    forecastTrack: true,
  });

  const toggleLayer = (layerKey) => {
    setLayers((prev) => ({ ...prev, [layerKey]: !prev[layerKey] }));
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  return (
    <div 
      ref={mapContainerRef}
      className={`relative w-full rounded-2xl overflow-hidden border border-[#16274a] bg-[#0B1730] shadow-2xl transition-all duration-300 flex flex-col ${
        isFullscreen ? 'fixed inset-4 z-50 h-[calc(100vh-2rem)]' : 'h-[460px] sm:h-[490px] lg:h-[510px]'
      }`}
    >
      {/* Header Bar Inside Map Card */}
      <div className="h-14 px-4 sm:px-5 bg-[#071126]/95 border-b border-[#122040] flex items-center justify-between z-20 shrink-0 select-none">
        {/* Left: Globe Icon, Title, Live Badge */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#168BFF]/15 border border-[#168BFF]/30 flex items-center justify-center text-[#168BFF]">
            <Globe className="w-4.5 h-4.5" />
          </div>
          <span className="text-sm font-bold text-[#F4F7FF] tracking-tight">
            Global Weather
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#00D6A0]/15 text-[#00D6A0] border border-[#00D6A0]/30 text-[11px] font-bold shadow-sm shadow-[#00D6A0]/20">
            <span className="w-1.5 h-1.5 rounded-full bg-[#00D6A0] animate-pulse"></span>
            Live
          </span>
        </div>

        {/* Right: Map / Satellite Segmented Toggle & Fullscreen Button */}
        <div className="flex items-center gap-3">
          {/* Segmented Map / Satellite Switcher */}
          <div className="flex items-center bg-[#0B1730] p-1 rounded-xl border border-[#16274a]">
            <button
              onClick={() => setMapType('map')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                mapType === 'map'
                  ? 'bg-[#168BFF] text-white shadow-sm shadow-[#168BFF]/40'
                  : 'text-[#93A9C8] hover:text-[#F4F7FF]'
              }`}
            >
              Map
            </button>
            <button
              onClick={() => setMapType('satellite')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                mapType === 'satellite'
                  ? 'bg-[#168BFF] text-white shadow-sm shadow-[#168BFF]/40'
                  : 'text-[#93A9C8] hover:text-[#F4F7FF]'
              }`}
            >
              Satellite
            </button>
          </div>

          {/* Fullscreen Toggle */}
          <button
            onClick={toggleFullscreen}
            className="w-8 h-8 rounded-lg bg-[#0B1730] hover:bg-[#101F3D] border border-[#16274a] text-[#93A9C8] hover:text-white flex items-center justify-center transition-all cursor-pointer shadow-sm"
            aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
            title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Map Body Container */}
      <div className="relative flex-1 w-full overflow-hidden">
        {/* Floating Layers Panel (Top-Left over Map) */}
        <div className="absolute top-4 left-4 z-[1000] select-none pointer-events-auto max-w-[210px]">
          <div className="bg-[#071126]/90 backdrop-blur-md border border-[#16274a] rounded-2xl shadow-2xl p-3 text-left transition-all">
            <button 
              onClick={() => setIsLayersOpen(!isLayersOpen)}
              className="w-full flex items-center justify-between text-xs font-bold text-[#F4F7FF] hover:text-white pb-2 border-b border-[#122040] cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <LayersIcon className="w-3.5 h-3.5 text-[#00D9F5]" />
                <span>Layers</span>
              </div>
              {isLayersOpen ? (
                <ChevronUp className="w-3.5 h-3.5 text-[#93A9C8]" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5 text-[#93A9C8]" />
              )}
            </button>

            {isLayersOpen && (
              <div className="space-y-2 mt-2.5 text-xs text-[#93A9C8]">
                {/* Temperature Anomaly */}
                <label className="flex items-center gap-2.5 cursor-pointer hover:text-white transition-colors">
                  <input 
                    type="checkbox" 
                    checked={layers.temperature}
                    onChange={() => toggleLayer('temperature')}
                    className="w-3.5 h-3.5 rounded border-[#16274a] bg-[#0B1730] text-[#168BFF] focus:ring-0 cursor-pointer accent-[#168BFF]"
                  />
                  <div className="w-5 h-5 rounded-full bg-[#FF4568]/20 flex items-center justify-center text-[#FF4568] shrink-0">
                    <Flame className="w-3 h-3" />
                  </div>
                  <span className="text-[11px] font-medium truncate">Temperature Anomaly</span>
                </label>

                {/* Wind (850 hPa) */}
                <label className="flex items-center gap-2.5 cursor-pointer hover:text-white transition-colors">
                  <input 
                    type="checkbox" 
                    checked={layers.wind}
                    onChange={() => toggleLayer('wind')}
                    className="w-3.5 h-3.5 rounded border-[#16274a] bg-[#0B1730] text-[#168BFF] focus:ring-0 cursor-pointer accent-[#168BFF]"
                  />
                  <div className="w-5 h-5 rounded-full bg-[#00D9F5]/20 flex items-center justify-center text-[#00D9F5] shrink-0">
                    <Wind className="w-3 h-3" />
                  </div>
                  <span className="text-[11px] font-medium truncate">Wind (850 hPa)</span>
                </label>

                {/* Pressure (MSLP) */}
                <label className="flex items-center gap-2.5 cursor-pointer hover:text-white transition-colors">
                  <input 
                    type="checkbox" 
                    checked={layers.pressure}
                    onChange={() => toggleLayer('pressure')}
                    className="w-3.5 h-3.5 rounded border-[#16274a] bg-[#0B1730] text-[#168BFF] focus:ring-0 cursor-pointer accent-[#168BFF]"
                  />
                  <div className="w-5 h-5 rounded-full bg-[#A855F7]/20 flex items-center justify-center text-[#A855F7] shrink-0">
                    <Gauge className="w-3 h-3" />
                  </div>
                  <span className="text-[11px] font-medium truncate">Pressure (MSLP)</span>
                </label>

                {/* Precipitation */}
                <label className="flex items-center gap-2.5 cursor-pointer hover:text-white transition-colors">
                  <input 
                    type="checkbox" 
                    checked={layers.precipitation}
                    onChange={() => toggleLayer('precipitation')}
                    className="w-3.5 h-3.5 rounded border-[#16274a] bg-[#0B1730] text-[#168BFF] focus:ring-0 cursor-pointer accent-[#168BFF]"
                  />
                  <div className="w-5 h-5 rounded-full bg-[#00D6A0]/20 flex items-center justify-center text-[#00D6A0] shrink-0">
                    <CloudRain className="w-3 h-3" />
                  </div>
                  <span className="text-[11px] font-medium truncate">Precipitation</span>
                </label>

                {/* Anomaly Footprints */}
                <label className="flex items-center gap-2.5 cursor-pointer hover:text-white transition-colors pt-1 border-t border-[#122040]/80">
                  <input 
                    type="checkbox" 
                    checked={layers.footprints}
                    onChange={() => toggleLayer('footprints')}
                    className="w-3.5 h-3.5 rounded border-[#16274a] bg-[#0B1730] text-[#168BFF] focus:ring-0 cursor-pointer accent-[#168BFF]"
                  />
                  <div className="w-5 h-5 rounded-full bg-[#FFB020]/20 flex items-center justify-center text-[#FFB020] shrink-0">
                    <Radio className="w-3 h-3" />
                  </div>
                  <span className="text-[11px] font-medium truncate">Anomaly Footprints</span>
                </label>

                {/* Forecast Track */}
                <label className="flex items-center gap-2.5 cursor-pointer hover:text-white transition-colors">
                  <input 
                    type="checkbox" 
                    checked={layers.forecastTrack}
                    onChange={() => toggleLayer('forecastTrack')}
                    className="w-3.5 h-3.5 rounded border-[#16274a] bg-[#0B1730] text-[#168BFF] focus:ring-0 cursor-pointer accent-[#168BFF]"
                  />
                  <div className="w-5 h-5 rounded-full bg-[#00D9F5]/20 flex items-center justify-center text-[#00D9F5] shrink-0">
                    <span className="w-2.5 h-0.5 border-t border-dashed border-[#00D9F5]"></span>
                  </div>
                  <span className="text-[11px] font-medium truncate">Forecast Track</span>
                </label>
              </div>
            )}
          </div>
        </div>

        {/* Floating Bottom Left: Legend */}
        <div className="absolute bottom-4 left-4 z-[1000] pointer-events-auto">
          <MapLegend activeLayer="temperature" />
        </div>

        {/* Floating Bottom Right: Forecast Controls */}
        <div className="absolute bottom-4 right-4 z-[1000] pointer-events-auto">
          <ForecastControls 
            forecastDay={forecastDay}
            setForecastDay={setForecastDay}
            isPlaying={isPlaying}
            setIsPlaying={setIsPlaying}
          />
        </div>

        {/* Leaflet Map Canvas */}
        <MapContainer
          center={[15, 65]}
          zoom={3}
          minZoom={1.5}
          maxZoom={12}
          zoomControl={false}
          attributionControl={false}
          className="w-full h-full"
        >
          <CustomMapControls onRecenter={() => setRecenterCounter(c => c + 1)} />
          <MapCameraController 
            selectedEvent={selectedEvent} 
            triggerRecenter={recenterCounter} 
          />

          {/* Dynamic Basemap Layer */}
          {mapType === 'satellite' ? (
            <>
              {/* High-res Satellite Imagery */}
              <TileLayer
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                maxZoom={18}
              />
              {/* Dark CartoDB Labels on top of satellite */}
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png"
                subdomains="abcd"
                maxZoom={19}
                opacity={0.85}
              />
            </>
          ) : (
            /* CartoDB Dark Matter Basemap */
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              subdomains="abcd"
              maxZoom={19}
            />
          )}

          {/* Map Anomaly Overlays */}
          {events.map((evt) => {
            const isSelected = selectedEvent?.id === evt.id;

            return (
              <React.Fragment key={evt.id}>
                {/* 1. Geospatial Footprint Polygon */}
                {layers.footprints && Array.isArray(evt.footprintPolygon) && evt.footprintPolygon.length >= 3 && (
                  <Polygon
                    positions={evt.footprintPolygon}
                    pathOptions={{
                      color: evt.color || '#FF4568',
                      weight: isSelected ? 2.5 : 1.5,
                      fillColor: evt.color || '#FF4568',
                      fillOpacity: isSelected ? 0.38 : 0.22,
                      dashArray: '5, 5',
                    }}
                    eventHandlers={{
                      click: () => onSelectEvent(evt),
                    }}
                  >
                    <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
                      <div className="text-xs font-bold text-[#F4F7FF]">
                        {evt.name} ({evt.region})
                      </div>
                      <div className="text-[10px] text-[#00D9F5] font-mono">
                        Footprint: {evt.estimatedArea}
                      </div>
                    </Tooltip>
                  </Polygon>
                )}

                {/* 2. Forecast Trajectory Track Line & Waypoints */}
                {layers.forecastTrack && Array.isArray(evt.forecastTrack) && evt.forecastTrack.length >= 2 && (
                  <>
                    <Polyline
                      positions={evt.forecastTrack}
                      pathOptions={{
                        color: isSelected ? '#00D9F5' : '#38BDF8',
                        weight: isSelected ? 2.5 : 1.8,
                        dashArray: '6, 6',
                        opacity: isSelected ? 0.95 : 0.7,
                      }}
                    />
                    {isSelected && evt.forecastTrack.map((pt, ptIdx) => (
                      <CircleMarker
                        key={`track-pt-${evt.id}-${ptIdx}`}
                        center={pt}
                        radius={4}
                        pathOptions={{
                          color: '#ffffff',
                          weight: 1.5,
                          fillColor: '#00D9F5',
                          fillOpacity: 1.0,
                        }}
                      >
                        <Tooltip direction="top" offset={[0, -6]} opacity={0.9}>
                          <span className="text-[10px] font-mono font-bold text-[#F4F7FF]">
                            Day {ptIdx + 1} Centroid ({pt[0].toFixed(1)}°, {pt[1].toFixed(1)}°)
                          </span>
                        </Tooltip>
                      </CircleMarker>
                    ))}
                  </>
                )}

                {/* 3. Outer Ambient Halo Pulse Marker & Center Marker */}
                {evt.lat != null && evt.lon != null && !isNaN(evt.lat) && !isNaN(evt.lon) && (
                  <>
                    <CircleMarker
                      center={[evt.lat, evt.lon]}
                      radius={evt.radius || 32}
                      pathOptions={{
                        color: evt.color || '#FF4568',
                        weight: 1,
                        fillColor: evt.color || '#FF4568',
                        fillOpacity: isSelected ? 0.25 : 0.12,
                      }}
                      eventHandlers={{
                        click: () => onSelectEvent(evt),
                      }}
                    />

                {/* 4. Center Marker: If Cyclone, display 'L' Low Center marker */}
                {evt.type === 'Cyclone' ? (
                  <Marker
                    position={[evt.lat, evt.lon]}
                    icon={createLowPressureIcon()}
                    eventHandlers={{
                      click: () => onSelectEvent(evt),
                    }}
                  >
                    <Tooltip direction="top" offset={[0, -16]} opacity={0.95}>
                      <div className="text-xs font-bold text-[#F4F7FF] flex items-center gap-1.5">
                        <span>{evt.name}</span>
                        <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-[#FF4568] text-white">
                          {evt.severity}
                        </span>
                      </div>
                      <div className="text-[10px] text-[#93A9C8] mt-0.5">
                        {evt.coordinatesDisplay} • {evt.forecastWindow}
                      </div>
                    </Tooltip>
                  </Marker>
                ) : (
                  /* Standard Glowing CircleMarker */
                  <CircleMarker
                    center={[evt.lat, evt.lon]}
                    radius={isSelected ? 10 : 7}
                    pathOptions={{
                      color: '#ffffff',
                      weight: 2,
                      fillColor: evt.color || '#168BFF',
                      fillOpacity: 1.0,
                    }}
                    eventHandlers={{
                      click: () => onSelectEvent(evt),
                    }}
                  >
                    <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
                      <div className="text-xs font-bold text-[#F4F7FF] flex items-center gap-1.5">
                        <span>{evt.name}</span>
                        <span className="text-[10px] uppercase font-mono px-1 py-0.2 rounded bg-black/60 text-[#00D9F5]">
                          {evt.severity}
                        </span>
                      </div>
                      <div className="text-[10px] text-[#93A9C8] mt-0.5">
                        {evt.coordinatesDisplay} • {evt.forecastWindow}
                      </div>
                    </Tooltip>
                  </CircleMarker>
                )}
                  </>
                )}
              </React.Fragment>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
