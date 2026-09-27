import React, { useState, useEffect } from 'react';
import AppLayout from './components/layout/AppLayout';
import DashboardView from './pages/DashboardView';
import MapView from './pages/MapView';
import AnomaliesView from './pages/AnomaliesView';
import ForecastView from './pages/ForecastView';
import ReportsView from './pages/ReportsView';
import SettingsView from './pages/SettingsView';
import AIModelsView from './pages/AIModelsView';
import EventDetailModal from './components/dashboard/EventDetailModal';
import { 
  DASHBOARD_STATS, 
  ANOMALY_EVENTS,
  DEMO_METADATA 
} from './data/demoData';
import { aeroNexApi } from './services/api';

export default function App() {
  const [activeNav, setActiveNav] = useState('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [events, setEvents] = useState(ANOMALY_EVENTS);
  const [stats, setStats] = useState(DASHBOARD_STATS);
  const [selectedEvent, setSelectedEvent] = useState(ANOMALY_EVENTS[0]);
  const [forecastDay, setForecastDay] = useState(3);
  const [isPlaying, setIsPlaying] = useState(false);
  const [modalEvent, setModalEvent] = useState(null);
  const [backendOnline, setBackendOnline] = useState(true);
  const [dataMode, setDataMode] = useState('DEMO_DATA'); // 'DEMO_DATA' | 'REAL_NWP_DATA'
  const [dataProvenance, setDataProvenance] = useState(DEMO_METADATA.dataProvenance);

  const [isLoadingData, setIsLoadingData] = useState(true);
  const [isDetecting, setIsDetecting] = useState(false);
  const [detectionFeedback, setDetectionFeedback] = useState(null);
  const [activeScenario, setActiveScenario] = useState('all');

  // Synchronize with live FastAPI backend on mount or on user retry
  const fetchBackendData = async () => {
    setIsLoadingData(true);
    try {
      const health = await aeroNexApi.getHealth();

      if (health && health.status === 'healthy' && health.connected) {
        setBackendOnline(true);
        
        // Parallel fetch of overview KPIs and Anomaly Catalog
        const [overviewRes, anomaliesRes] = await Promise.all([
          aeroNexApi.getOverview(),
          aeroNexApi.getAnomalies(),
        ]);

        if (overviewRes && overviewRes.dashboard_cards && overviewRes.dashboard_cards.length > 0) {
          setStats(overviewRes.dashboard_cards);
          if (overviewRes.summary?.data_provenance) {
            setDataProvenance(overviewRes.summary.data_provenance);
          }
        }

        if (anomaliesRes && anomaliesRes.events && anomaliesRes.events.length > 0) {
          setEvents(anomaliesRes.events);
          setSelectedEvent(anomaliesRes.events[0]);
        }
      } else {
        setBackendOnline(false);
      }
    } catch (err) {
      console.warn('[AeroNex Frontend] Backend offline or unreachable, using local demo data.', err);
      setBackendOnline(false);
    } finally {
      setIsLoadingData(false);
    }
  };

  useEffect(() => {
    fetchBackendData();
  }, []);

  // Handle running detection pipeline for a specific scenario or horizon
  const handleRunDetection = async (scenarioId = 'all', leadTimeHours = 24) => {
    setIsDetecting(true);
    setDetectionFeedback(null);
    setActiveScenario(scenarioId);

    try {
      const res = await aeroNexApi.runDetectionPipeline({
        scenario: scenarioId === 'all' ? null : scenarioId,
        lead_time_hours: leadTimeHours,
        min_area_km2: 2500.0,
      });

      if (res && res.events) {
        setEvents(res.events);
        if (res.events.length > 0) {
          setSelectedEvent(res.events[0]);
        }
        
        // Update stats active-anomalies card
        setStats((prevStats) =>
          prevStats.map((item) => {
            if (item.id === 'active-anomalies') {
              return {
                ...item,
                value: String(res.total_anomalies_detected ?? res.events.length),
                subtext: scenarioId === 'all' ? 'Multi-Hazard Grid Run' : `Scenario: ${scenarioId}`,
              };
            }
            return item;
          })
        );

        setDetectionFeedback({
          type: 'success',
          message: `Detection execution complete: ${res.total_anomalies_detected} anomalies & ${res.total_footprints_extracted} footprints extracted.`,
          execution_time_ms: res.execution_time_ms,
          method: '3-Sigma Morphological Detector',
        });
      }
    } catch (err) {
      console.error('[AeroNex] Detection execution failed', err);
      setDetectionFeedback({
        type: 'error',
        message: `Detection pipeline execution failed: ${err.message || String(err)}`,
      });
    } finally {
      setIsDetecting(false);
    }
  };

  // Switch between Demo Mode and Real NWP Mode with explicit fallback
  const handleSwitchDataMode = async (targetMode) => {
    if (targetMode === 'REAL_NWP_DATA') {
      setIsDetecting(true);
      setDetectionFeedback(null);
      try {
        const res = await aeroNexApi.runNwpIngestion({
          dataset_id: 'gfs_sample_0p25_south_asia',
          source_mode: 'local',
          lead_time_hours: 24,
          region_id: 'south_asia',
          run_anomaly_detection: true,
        });

        if (res && res.success) {
          handleIngestionSuccess(res);
          setDetectionFeedback({
            type: 'success',
            message: `Real NWP Grid Ingested: ${res.anomalies_detected_count} anomalies detected from local NOAA GFS NetCDF4.`,
            execution_time_ms: res.execution_time_ms,
            method: 'Real NetCDF4 GFS Pipeline',
          });
        } else {
          throw new Error(res?.message || 'Ingestion returned failure status');
        }
      } catch (err) {
        console.warn('[AeroNex] Real NWP ingestion unavailable, preserving Demo Mode.', err);
        setDataMode('DEMO_DATA');
        setDetectionFeedback({
          type: 'error',
          message: `Real NWP Provider Unavailable (${err.message || 'Grid unreadable'}). Preserving Demo Mode.`,
        });
      } finally {
        setIsDetecting(false);
      }
    } else {
      handleResetDemo();
      setDetectionFeedback({
        type: 'success',
        message: 'Switched to Reproducible Synthetic Demonstration Mode.',
      });
    }
  };

  // Handle successful NWP Ingestion and Anomaly Run
  const handleIngestionSuccess = (result) => {
    if (!result || !result.success) return;

    setDataMode('REAL_NWP_DATA');
    setDataProvenance(result.data_provenance || 'LOCAL_NWP_NETCDF');

    if (result.anomalies && result.anomalies.length > 0) {
      setEvents(result.anomalies);
      setSelectedEvent(result.anomalies[0]);
    }

    // Refresh dashboard stats to reflect the newly ingested NWP dataset
    setStats((prevStats) =>
      prevStats.map((item) => {
        if (item.id === 'active-anomalies') {
          return {
            ...item,
            value: String(result.anomalies_detected_count ?? result.anomalies?.length ?? item.value),
            subtext: 'Detected from Real NWP Grid',
          };
        }
        if (item.id === 'latest-data') {
          return {
            ...item,
            value: 'NOAA GFS (0.25°)',
            subtext: result.dataset_id || 'NetCDF4 Analysis Grid',
          };
        }
        return item;
      })
    );
  };

  // Handle resetting back to Synthetic Demonstration Dataset
  const handleResetDemo = () => {
    setDataMode('DEMO_DATA');
    setDataProvenance(DEMO_METADATA.dataProvenance);
    setActiveScenario('all');
    setEvents(ANOMALY_EVENTS);
    setSelectedEvent(ANOMALY_EVENTS[0]);
    setStats(DASHBOARD_STATS);
    setForecastDay(3);
    setDetectionFeedback({
      type: 'success',
      message: 'Demo state reset: Loaded initial 6 benchmark extreme weather anomalies.',
    });
  };

  // Case-insensitive multi-attribute search filter across active dataset
  const filteredEvents = events.filter((evt) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      (evt.name && evt.name.toLowerCase().includes(q)) ||
      (evt.region && evt.region.toLowerCase().includes(q)) ||
      (evt.coordinatesDisplay && evt.coordinatesDisplay.toLowerCase().includes(q)) ||
      (evt.type && evt.type.toLowerCase().includes(q))
    );
  });

  const handleSelectEvent = (evt) => {
    setSelectedEvent(evt);
  };

  const handleViewModal = (evt) => {
    setModalEvent(evt || selectedEvent);
  };

  const handleCloseModal = () => {
    setModalEvent(null);
  };

  return (
    <AppLayout
      activeNav={activeNav}
      setActiveNav={setActiveNav}
      searchQuery={searchQuery}
      setSearchQuery={setSearchQuery}
      onSelectEvent={handleSelectEvent}
      filteredEvents={filteredEvents}
      anomalyCount={events.length}
      dataMode={dataMode}
      dataProvenance={dataProvenance}
      onDataModeChange={handleSwitchDataMode}
      onIngestionSuccess={handleIngestionSuccess}
      onResetDemo={handleResetDemo}
      backendOnline={backendOnline}
      onRetryBackend={fetchBackendData}
    >
      {activeNav === 'dashboard' && (
        <DashboardView
          stats={stats}
          events={filteredEvents.length > 0 ? filteredEvents : events}
          selectedEvent={selectedEvent}
          onSelectEvent={handleSelectEvent}
          onViewModal={handleViewModal}
          onViewAllAlerts={() => setActiveNav('anomalies')}
          onNavigateToAI={() => setActiveNav('ai-models')}
          forecastDay={forecastDay}
          setForecastDay={setForecastDay}
          isPlaying={isPlaying}
          setIsPlaying={setIsPlaying}
          dataMode={dataMode}
          onSwitchDataMode={handleSwitchDataMode}
          activeScenario={activeScenario}
          onSelectScenario={setActiveScenario}
          onRunDetection={handleRunDetection}
          onResetDemo={handleResetDemo}
          isDetecting={isDetecting}
          detectionFeedback={detectionFeedback}
          isLoadingData={isLoadingData}
        />
      )}

      {activeNav === 'map' && (
        <MapView
          events={filteredEvents.length > 0 ? filteredEvents : events}
          selectedEvent={selectedEvent}
          onSelectEvent={handleSelectEvent}
          onViewModal={handleViewModal}
          forecastDay={forecastDay}
          setForecastDay={setForecastDay}
          isPlaying={isPlaying}
          setIsPlaying={setIsPlaying}
        />
      )}

      {activeNav === 'anomalies' && (
        <AnomaliesView
          events={events}
          onSelectEvent={handleSelectEvent}
          onViewModal={handleViewModal}
          onSwitchToMap={() => setActiveNav('map')}
        />
      )}

      {activeNav === 'ai-models' && (
        <AIModelsView 
          events={filteredEvents.length > 0 ? filteredEvents : events}
          selectedEvent={selectedEvent}
          onSelectEvent={handleSelectEvent}
        />
      )}

      {activeNav === 'forecast' && (
        <ForecastView />
      )}

      {activeNav === 'reports' && (
        <ReportsView events={events} />
      )}

      {activeNav === 'settings' && (
        <SettingsView />
      )}

      {/* Global Event Diagnostic & Trajectory Modal */}
      {modalEvent && (
        <EventDetailModal 
          event={modalEvent} 
          onClose={handleCloseModal} 
        />
      )}
    </AppLayout>
  );
}
