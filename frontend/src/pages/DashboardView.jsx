import React from 'react';
import StatCard from '../components/dashboard/StatCard';
import WeatherMap from '../components/map/WeatherMap';
import RecentAlerts from '../components/dashboard/RecentAlerts';
import EventDetails from '../components/dashboard/EventDetails';
import WeatherHighlights from '../components/dashboard/WeatherHighlights';
import GlobalTempAnomalyChart from '../components/dashboard/GlobalTempAnomalyChart';
import ScenarioToolbar from '../components/dashboard/ScenarioToolbar';

import { Cpu, ArrowRight } from 'lucide-react';

export default function DashboardView({ 
  stats, 
  events, 
  selectedEvent, 
  onSelectEvent, 
  onViewModal, 
  onViewAllAlerts,
  onNavigateToAI,
  forecastDay,
  setForecastDay,
  isPlaying,
  setIsPlaying,
  dataMode = 'DEMO_DATA',
  onSwitchDataMode,
  activeScenario = 'all',
  onSelectScenario,
  onRunDetection,
  onResetDemo,
  isDetecting = false,
  detectionFeedback = null,
  isLoadingData = false,
}) {
  return (
    <div className="space-y-4 lg:space-y-5">
      {/* 0. Presentation Scenario & Detection Toolbar */}
      <ScenarioToolbar 
        dataMode={dataMode}
        onSwitchDataMode={onSwitchDataMode}
        activeScenario={activeScenario}
        onSelectScenario={onSelectScenario}
        onRunDetection={onRunDetection}
        onResetDemo={onResetDemo}
        isDetecting={isDetecting}
        detectionFeedback={detectionFeedback}
        forecastDay={forecastDay}
        setForecastDay={setForecastDay}
      />

      {/* 1. Top Row: 4 Colorful KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {isLoadingData ? (
          // Loading Skeletons
          Array.from({ length: 4 }).map((_, idx) => (
            <div key={`stat-skel-${idx}`} className="bg-[#0B1730] border border-[#16274a] rounded-2xl p-4 sm:p-5 h-28 animate-pulse flex flex-col justify-between">
              <div className="h-4 bg-[#122040] rounded w-1/2"></div>
              <div className="h-8 bg-[#162b55] rounded w-3/4"></div>
              <div className="h-3 bg-[#122040] rounded w-1/3"></div>
            </div>
          ))
        ) : (
          stats.map((item) => (
            <StatCard key={item.id} item={item} />
          ))
        )}
      </div>

      {/* AI & Uncertainty Quick Intelligence Banner */}
      <div className="bg-[#0B1936] border border-[#168BFF]/30 rounded-xl p-3.5 px-4 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[#168BFF]/20 text-[#00D9F5] rounded-lg shrink-0">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-white uppercase tracking-wider">AI Intelligence & Anomaly Scoring</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-[#00D6A0]/15 text-[#00D6A0] border border-[#00D6A0]/30">
                Phase 6 Active
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Empirical multi-component departure scoring (Z-score fusion) • Forecast uncertainty spread • Experimental ML baseline
            </p>
          </div>
        </div>

        <button
          onClick={onNavigateToAI}
          className="self-start md:self-auto px-3.5 py-1.5 rounded-lg text-xs font-bold bg-[#168BFF] hover:bg-[#3894FF] text-white flex items-center gap-1.5 transition cursor-pointer shadow-md shrink-0"
        >
          Open AI & Uncertainty Console
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* 2. Middle & Bottom Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-5 items-start">
        {/* Left Column (8 Columns on desktop): Main Weather Map + Highlights & Temp Anomaly */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          {/* Main Global Weather Map */}
          <WeatherMap 
            events={events}
            selectedEvent={selectedEvent}
            onSelectEvent={onSelectEvent}
            forecastDay={forecastDay}
            setForecastDay={setForecastDay}
            isPlaying={isPlaying}
            setIsPlaying={setIsPlaying}
          />

          {/* Sub-grid below map: Weather Highlights (left) & Global Temperature Anomaly (right) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <WeatherHighlights 
              events={events}
              selectedEvent={selectedEvent}
              onSelectEvent={onSelectEvent}
            />
            <GlobalTempAnomalyChart />
          </div>
        </div>

        {/* Right Column (4 Columns on desktop): Recent Alerts (top) & Selected Event Details (bottom) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          {/* Recent Alerts List */}
          <RecentAlerts 
            events={events}
            selectedEvent={selectedEvent}
            onSelectEvent={onSelectEvent}
            onViewAll={onViewAllAlerts}
          />

          {/* Selected Event Details Panel */}
          <EventDetails 
            selectedEvent={selectedEvent}
            onViewModal={onViewModal}
          />
        </div>
      </div>
    </div>
  );
}
