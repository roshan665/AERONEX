import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Bell, 
  ChevronDown, 
  Menu,
  Database,
  CheckCircle2,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { NOTIFICATIONS_FEED } from '../../data/demoData';
import { aeroNexApi } from '../../services/api';

export default function TopHeader({ 
  searchQuery, 
  setSearchQuery, 
  onSelectEvent, 
  filteredEvents = [], 
  onToggleMobileSidebar,
  dataMode: propDataMode,
  onDataModeChange,
  onIngestionSuccess,
  onResetDemo,
  backendOnline = true,
  onRetryBackend,
}) {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showNwpMenu, setShowNwpMenu] = useState(false);
  const [isSearchFocused, setIsSearchFocused] = useState(false);

  // Phase 5: Real NWP Ingestion state
  const [localDataMode, setLocalDataMode] = useState('DEMO_DATA'); // 'DEMO_DATA' or 'REAL_NWP_DATA'
  const dataMode = propDataMode !== undefined ? propDataMode : localDataMode;
  const setDataMode = (val) => {
    setLocalDataMode(val);
    if (onDataModeChange) onDataModeChange(val);
  };

  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestionResult, setIngestionResult] = useState(null);
  const [datasetList, setDatasetList] = useState([]);

  useEffect(() => {
    // Probe available datasets on mount
    aeroNexApi.getDatasets().then(data => {
      if (data && data.length) setDatasetList(data);
    }).catch(() => {});
  }, []);

  const handleTriggerRealNwp = async () => {
    setIsIngesting(true);
    setIngestionResult(null);
    try {
      const res = await aeroNexApi.runNwpIngestion({
        dataset_id: 'gfs_sample_0p25_south_asia',
        source_mode: 'local',
        lead_time_hours: 24,
        region_id: 'south_asia',
        run_anomaly_detection: true,
      });
      setIngestionResult(res);
      if (res.success) {
        setDataMode('REAL_NWP_DATA');
        if (onIngestionSuccess) {
          onIngestionSuccess(res);
        }
      }
    } catch (err) {
      setIngestionResult({ success: false, message: String(err) });
    } finally {
      setIsIngesting(false);
    }
  };

  return (
    <header className="h-20 px-4 lg:px-6 bg-[#050B1A]/95 backdrop-blur-md border-b border-[#122040] flex items-center justify-between gap-4 sticky top-0 z-30 select-none">
      {/* Left: Mobile Menu Toggle & Search Bar */}
      <div className="flex items-center gap-3 flex-1 max-w-xl">
        <button 
          onClick={onToggleMobileSidebar}
          className="lg:hidden p-2 text-[#93A9C8] hover:text-white rounded-xl hover:bg-[#0B1730]"
          aria-label="Toggle navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Global Search Bar with Ctrl + K Badge */}
        <div className="relative w-full">
          <div className="relative flex items-center">
            <Search className="absolute left-3.5 w-4 h-4 text-[#93A9C8] pointer-events-none" />
            <input 
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setIsSearchFocused(true)}
              onBlur={() => setTimeout(() => setIsSearchFocused(false), 200)}
              placeholder="Search regions, events, or coordinates..."
              className="w-full h-10 pl-10 pr-20 bg-[#0B1730] border border-[#16274a] rounded-xl text-xs sm:text-sm text-[#F4F7FF] placeholder-[#93A9C8]/70 focus:outline-none focus:border-[#168BFF] focus:ring-1 focus:ring-[#168BFF]/40 transition-all shadow-inner"
            />
            {/* Ctrl + K Shortcut Badge */}
            <div className="absolute right-3 hidden sm:flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-[#101F3D] border border-[#1a2d52] text-[10px] font-mono font-medium text-[#93A9C8]">
              <span>Ctrl + K</span>
            </div>
          </div>

          {/* Quick Search Autocomplete Results Dropdown */}
          {isSearchFocused && searchQuery.trim().length > 0 && (
            <div className="absolute top-12 left-0 right-0 bg-[#0B1730] border border-[#16274a] rounded-xl shadow-2xl p-2 z-50 max-h-64 overflow-y-auto">
              <div className="text-[10px] font-semibold text-[#93A9C8] uppercase tracking-wider px-2 py-1">
                Matching Weather Anomalies ({filteredEvents.length})
              </div>
              {filteredEvents.length === 0 ? (
                <div className="px-3 py-2 text-xs text-[#93A9C8]">
                  No matching anomalies found.
                </div>
              ) : (
                filteredEvents.map((evt) => (
                  <button
                    key={evt.id}
                    onMouseDown={() => {
                      onSelectEvent(evt);
                      setSearchQuery('');
                    }}
                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-[#101F3D] text-left transition-colors cursor-pointer"
                  >
                    <div>
                      <div className="text-xs font-semibold text-[#F4F7FF]">{evt.name}</div>
                      <div className="text-[11px] text-[#93A9C8]">{evt.region} • {evt.coordinatesDisplay}</div>
                    </div>
                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${evt.severityBadgeColor}`}>
                      {evt.severity}
                    </span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* Right: API Connectivity Pill, Data Mode Pill, Notification Bell, User Avatar */}
      <div className="flex items-center gap-2.5 sm:gap-4">
        {/* Backend Connectivity Status Pill */}
        <div 
          className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-xl border text-xs font-semibold select-none ${
            backendOnline 
              ? 'bg-[#00D6A0]/10 border-[#00D6A0]/30 text-[#00D6A0]' 
              : 'bg-[#FF4568]/10 border-[#FF4568]/30 text-[#FF4568]'
          }`}
          title={backendOnline ? 'FastAPI Backend Online (http://localhost:8000)' : 'FastAPI Backend Offline — Operating in Offline Demo Mode'}
        >
          <span className="relative flex h-2 w-2">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
              backendOnline ? 'bg-[#00D6A0]' : 'bg-[#FF4568]'
            }`} />
            <span className={`relative inline-flex rounded-full h-2 w-2 ${
              backendOnline ? 'bg-[#00D6A0]' : 'bg-[#FF4568]'
            }`} />
          </span>
          <span className="text-[11px] font-bold tracking-tight">
            {backendOnline ? 'API ONLINE' : 'API OFFLINE'}
          </span>
          {!backendOnline && onRetryBackend && (
            <button
              onClick={onRetryBackend}
              className="p-0.5 ml-0.5 hover:bg-[#FF4568]/20 rounded transition-colors text-[#FF4568] hover:text-white cursor-pointer"
              title="Click to retry connecting to backend"
            >
              <RefreshCw className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Data Mode & Provenance Trigger Pill */}
        <div className="relative">
          <button
            onClick={() => setShowNwpMenu(!showNwpMenu)}
            className="flex flex-col items-end p-1.5 px-2 rounded-xl hover:bg-[#0B1730] border border-transparent hover:border-[#16274a] transition-all cursor-pointer text-right group"
            title="Click to view NWP data provenance and ingestion controls"
          >
            <div className="flex items-center gap-1.5">
              <span className={`text-[10px] font-extrabold uppercase px-1.5 py-0.5 rounded border ${
                dataMode === 'REAL_NWP_DATA'
                  ? 'bg-[#00D9F5]/20 text-[#00D9F5] border-[#00D9F5]/40'
                  : 'bg-[#FFB020]/20 text-[#FFB020] border-[#FFB020]/40'
              }`}>
                {dataMode === 'REAL_NWP_DATA' ? 'REAL NWP' : 'SYNTHETIC DEMO'}
              </span>
              <ChevronDown className="w-3 h-3 text-[#93A9C8] group-hover:text-white ml-0.5" />
            </div>
            <div className="text-[10px] text-[#93A9C8] font-mono tracking-tight mt-0.5">
              {dataMode === 'REAL_NWP_DATA' ? 'NOAA GFS (0.25°)' : 'Apr 26, 2025 14:00 UTC'}
            </div>
          </button>

          {/* Phase 5: NWP Data Ingestion Popover Dropdown */}
          {showNwpMenu && (
            <div className="absolute right-0 top-14 w-84 sm:w-96 bg-[#0B1730] border border-[#16274a] rounded-2xl shadow-2xl p-4 z-50 animate-in fade-in duration-150 text-left">
              <div className="flex items-center justify-between pb-2.5 border-b border-[#122040]">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-[#00D9F5]" />
                  <span className="text-xs font-bold text-[#F4F7FF] uppercase tracking-wider">
                    NWP Data Provenance & Ingestion
                  </span>
                </div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                  dataMode === 'REAL_NWP_DATA'
                    ? 'bg-[#00D9F5]/20 text-[#00D9F5] border-[#00D9F5]/40'
                    : 'bg-[#FFB020]/20 text-[#FFB020] border-[#FFB020]/40'
                }`}>
                  {dataMode === 'REAL_NWP_DATA' ? 'REAL NWP ACTIVE' : 'DEMO MODE'}
                </span>
              </div>

              {/* Data Source Details */}
              <div className="mt-3 space-y-2 text-xs">
                <div className="p-2.5 rounded-xl bg-[#071126] border border-[#142445] space-y-1">
                  <div className="flex justify-between">
                    <span className="text-[#93A9C8]">Primary Provider:</span>
                    <span className="font-semibold text-[#F4F7FF]">NOAA NCEP GFS (0.25°)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#93A9C8]">Access Mechanism:</span>
                    <span className="font-mono text-[#00D9F5]">NOMADS GRIB Filter / NetCDF4</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#93A9C8]">Spatial Resolution:</span>
                    <span className="font-mono text-[#F4F7FF]">0.25° × 0.25° (~27 km)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#93A9C8]">Domain:</span>
                    <span className="text-[#F4F7FF]">South Asia [8°N–38°N, 65°E–95°E]</span>
                  </div>
                  {datasetList.length > 0 && (
                    <div className="flex justify-between border-t border-[#142445] pt-1">
                      <span className="text-[#93A9C8]">Local Archives:</span>
                      <span className="font-mono text-[#00D9F5]">{datasetList.length} verified</span>
                    </div>
                  )}
                </div>

                {/* Ingestion Action */}
                <div className="pt-2">
                  <button
                    onClick={handleTriggerRealNwp}
                    disabled={isIngesting}
                    className="w-full py-2 px-3 rounded-xl bg-[#168BFF] hover:bg-[#3894FF] disabled:opacity-50 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all cursor-pointer shadow-md shadow-[#168BFF]/30"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isIngesting ? 'animate-spin' : ''}`} />
                    <span>{isIngesting ? 'Ingesting Real NetCDF4 Grid...' : 'Run Real NWP Ingestion Pipeline'}</span>
                  </button>
                </div>

                {/* Ingestion Feedback Message */}
                {ingestionResult && (
                  <div className={`p-2.5 rounded-xl text-[11px] border mt-2 ${
                    ingestionResult.success 
                      ? 'bg-[#00D6A0]/10 border-[#00D6A0]/30 text-[#00D6A0]' 
                      : 'bg-[#FF4568]/10 border-[#FF4568]/30 text-[#FF4568]'
                  }`}>
                    <div className="flex items-center gap-1.5 font-bold">
                      {ingestionResult.success ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
                      <span>{ingestionResult.success ? 'Real NWP Ingestion Successful' : 'Ingestion Error'}</span>
                    </div>
                    <p className="mt-1 leading-snug text-[#93A9C8]">{ingestionResult.message}</p>
                    {ingestionResult.anomalies_detected_count !== undefined && (
                      <p className="font-mono text-[#F4F7FF] mt-1">
                        Detected Anomalies: {ingestionResult.anomalies_detected_count} • Footprints: {ingestionResult.footprints_extracted_count}
                      </p>
                    )}
                  </div>
                )}

                {/* Reset to Demo Mode */}
                {dataMode === 'REAL_NWP_DATA' && (
                  <button
                    onClick={() => {
                      setDataMode('DEMO_DATA');
                      setIngestionResult(null);
                      if (onResetDemo) onResetDemo();
                    }}
                    className="w-full mt-1 text-[11px] text-[#93A9C8] hover:text-white text-center py-1 transition-colors cursor-pointer"
                  >
                    Reset back to Synthetic Demo Data
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Separator */}
        <div className="hidden md:block w-px h-8 bg-[#122040]"></div>

        {/* Notifications Icon Button with Red Badge */}
        <div className="relative">
          <button 
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative w-10 h-10 rounded-xl bg-[#0B1730] hover:bg-[#101F3D] border border-[#16274a] text-[#93A9C8] hover:text-[#F4F7FF] flex items-center justify-center transition-all cursor-pointer shadow-sm"
            aria-label="View notifications"
          >
            <Bell className="w-4.5 h-4.5" />
            <span className="absolute -top-1 -right-1 w-4.5 h-4.5 bg-[#FF4568] text-white text-[10px] font-bold rounded-full flex items-center justify-center shadow-md shadow-[#FF4568]/40 border-2 border-[#050B1A]">
              3
            </span>
          </button>

          {/* Notifications Dropdown Panel */}
          {showNotifications && (
            <div className="absolute right-0 top-13 w-80 bg-[#0B1730] border border-[#16274a] rounded-2xl shadow-2xl p-3 z-50 animate-in fade-in duration-150">
              <div className="flex items-center justify-between pb-2 border-b border-[#122040] px-1">
                <span className="text-xs font-bold text-[#F4F7FF] uppercase tracking-wider">
                  System Alerts & Feed
                </span>
                <span className="text-[10px] text-[#00D9F5] font-semibold">3 unread</span>
              </div>
              <div className="mt-2 space-y-1.5 max-h-72 overflow-y-auto">
                {NOTIFICATIONS_FEED.map((n) => (
                  <div key={n.id} className="p-2.5 rounded-xl hover:bg-[#101F3D] transition-colors text-left border border-transparent hover:border-[#16274a]">
                    <div className="flex items-start justify-between gap-2">
                      <div className="text-xs font-semibold text-[#F4F7FF]">{n.title}</div>
                      <span className="text-[10px] text-[#93A9C8] shrink-0">{n.time}</span>
                    </div>
                    <p className="text-[11px] text-[#93A9C8] mt-1 leading-snug">{n.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User Profile Pill */}
        <div className="relative">
          <button 
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center gap-2.5 p-1 rounded-xl hover:bg-[#0B1730] border border-transparent hover:border-[#16274a] transition-all cursor-pointer group"
          >
            {/* User Avatar Circle */}
            <div className="w-9 h-9 rounded-full bg-[#168BFF] flex items-center justify-center text-xs font-bold text-white shadow-md shadow-[#168BFF]/30 shrink-0">
              PS
            </div>
            
            {/* User Name & Model Title */}
            <div className="hidden sm:flex flex-col text-left">
              <span className="text-xs font-bold text-[#F4F7FF] group-hover:text-white leading-tight">
                Prahlad Sahni
              </span>
              <span className="text-[10px] text-[#93A9C8] font-medium leading-tight">
                NWP Model (Sample Data)
              </span>
            </div>

            <ChevronDown className="w-3.5 h-3.5 text-[#93A9C8] group-hover:text-[#F4F7FF] ml-0.5" />
          </button>

          {/* Profile Dropdown */}
          {showProfileMenu && (
            <div className="absolute right-0 top-13 w-56 bg-[#0B1730] border border-[#16274a] rounded-xl shadow-2xl p-2 z-50 text-left">
              <div className="px-3 py-2 border-b border-[#122040]">
                <div className="text-xs font-bold text-[#F4F7FF]">Prahlad Sahni</div>
                <div className="text-[10px] text-[#93A9C8]">NWP Meteorologist (SIH 2024/2025)</div>
              </div>
              <div className="mt-1 space-y-0.5">
                <button 
                  onClick={() => setShowProfileMenu(false)}
                  className="w-full px-3 py-1.5 rounded-lg text-xs text-[#93A9C8] hover:text-[#F4F7FF] hover:bg-[#101F3D] text-left cursor-pointer"
                >
                  Researcher Profile
                </button>
                <button 
                  onClick={() => setShowProfileMenu(false)}
                  className="w-full px-3 py-1.5 rounded-lg text-xs text-[#93A9C8] hover:text-[#F4F7FF] hover:bg-[#101F3D] text-left cursor-pointer"
                >
                  NWP Ingestion Monitor
                </button>
                <button 
                  onClick={() => setShowProfileMenu(false)}
                  className="w-full px-3 py-1.5 rounded-lg text-xs text-[#FF4568] hover:bg-[#FF4568]/10 text-left cursor-pointer"
                >
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
