import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Layers, 
  AlertTriangle, 
  Info, 
  CheckCircle2, 
  TrendingUp, 
  Gauge, 
  BarChart3, 
  Sparkles
} from 'lucide-react';
import { aeroNexApi } from '../services/api';

export default function AIModelsView({ events = [], selectedEvent, onSelectEvent }) {
  // Model state
  const [_registeredModels, setRegisteredModels] = useState([]);
  const [activeModelId, setActiveModelId] = useState('deterministic_baseline');
  const [modelStatus, setModelStatus] = useState(null);
  const [isSwitchingModel, setIsSwitchingModel] = useState(false);

  // Scoring state
  const [currentEventId, setCurrentEventId] = useState(selectedEvent?.id || events[0]?.id || 'evt-001');
  const [scoreData, setScoreData] = useState(null);
  const [isLoadingScore, setIsLoadingScore] = useState(false);

  // Evaluation benchmark state
  const [benchmarkData, setBenchmarkData] = useState(null);

  // Uncertainty series state
  const [uncertaintyVar, setUncertaintyVar] = useState('temperature');
  const [uncertaintyMode, setUncertaintyMode] = useState('ensemble'); // 'ensemble' | 'deterministic'
  const [selectedLeadDay, setSelectedLeadDay] = useState(3);
  const [uncertaintySeries, setUncertaintySeries] = useState(null);
  const [isLoadingUncertainty, setIsLoadingUncertainty] = useState(false);

  // Sync event from props
  useEffect(() => {
    if (selectedEvent?.id && selectedEvent.id !== currentEventId) {
      setCurrentEventId(selectedEvent.id);
    }
  }, [selectedEvent?.id, currentEventId]);

  // Initial fetch of models, benchmark, and score
  useEffect(() => {
    let isMounted = true;

    async function loadInitialAIData() {
      try {
        const [modelsRes, statusRes, evalRes] = await Promise.all([
          aeroNexApi.getModels(),
          aeroNexApi.getModelStatus(),
          aeroNexApi.getEvaluationBenchmark(24, 100)
        ]);

        if (!isMounted) return;

        if (modelsRes && modelsRes.models) {
          setRegisteredModels(modelsRes.models);
          setActiveModelId(modelsRes.active_model_id || 'deterministic_baseline');
        }
        if (statusRes) {
          setModelStatus(statusRes);
        }
        if (evalRes) {
          setBenchmarkData(evalRes);
        }
      } catch (err) {
        console.warn('[AIModelsView] Error loading AI data:', err);
      }
    }

    loadInitialAIData();

    return () => { isMounted = false; };
  }, []);

  // Fetch Anomaly Score when currentEventId changes
  useEffect(() => {
    let isMounted = true;
    if (!currentEventId) return;

    async function fetchScore() {
      setIsLoadingScore(true);
      try {
        const res = await aeroNexApi.getAnomalyScore(currentEventId);
        if (isMounted && res) {
          setScoreData(res);
        }
      } catch (err) {
        console.warn(`[AIModelsView] Score fetch failed for ${currentEventId}:`, err);
      } finally {
        if (isMounted) setIsLoadingScore(false);
      }
    }

    fetchScore();

    return () => { isMounted = false; };
  }, [currentEventId]);

  // Fetch Forecast Uncertainty Series when variable or mode changes
  useEffect(() => {
    let isMounted = true;

    async function fetchUncertainty() {
      setIsLoadingUncertainty(true);
      try {
        const res = await aeroNexApi.getUncertaintySeries(uncertaintyVar, uncertaintyMode);
        if (isMounted && res) {
          setUncertaintySeries(res);
        }
      } catch (err) {
        console.warn('[AIModelsView] Uncertainty series fetch failed:', err);
      } finally {
        if (isMounted) setIsLoadingUncertainty(false);
      }
    }

    fetchUncertainty();

    return () => { isMounted = false; };
  }, [uncertaintyVar, uncertaintyMode]);

  // Handle Model Activation
  const handleSelectModel = async (modelId) => {
    if (modelId === activeModelId || isSwitchingModel) return;
    setIsSwitchingModel(true);
    try {
      const updated = await aeroNexApi.selectModel(modelId);
      if (updated) {
        setActiveModelId(modelId);
        setModelStatus(prev => ({
          ...prev,
          active_model_id: modelId,
          active_model_name: updated.model_name || modelId,
          operational_status: updated.status || 'ACTIVE'
        }));
      }
    } catch (err) {
      console.error('[AIModelsView] Model selection error:', err);
    } finally {
      setIsSwitchingModel(false);
    }
  };

  // Handle Event Selector
  const handleEventChange = (e) => {
    const id = e.target.value;
    setCurrentEventId(id);
    const found = events.find(ev => ev.id === id);
    if (found && onSelectEvent) {
      onSelectEvent(found);
    }
  };

  const activeEvent = events.find(ev => ev.id === currentEventId) || events[0] || {};
  const currentLeadPoint = uncertaintySeries?.timeline?.find(p => p.lead_day === selectedLeadDay) || uncertaintySeries?.timeline?.[0];

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Header Banner & Scientific Disclaimer */}
      <div className="bg-[#0B1936] border border-[#122040] rounded-2xl p-6 relative overflow-hidden shadow-lg">
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-[#168BFF]/10 via-[#A855F7]/10 to-transparent rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2.5 bg-[#168BFF]/15 border border-[#168BFF]/30 rounded-xl text-[#00D9F5]">
                <Cpu className="w-6 h-6" />
              </div>
              <h1 className="text-2xl font-bold text-white tracking-wide">
                AI/ML Intelligence, Anomaly Scoring & Forecast Uncertainty
              </h1>
            </div>
            <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">
              Modular scientific intelligence layer decoupling empirical multi-component anomaly scoring from 
              unsupervised machine-learning baselines and multi-horizon ensemble dispersion analytics.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-[#00D6A0]/15 text-[#00D6A0] border border-[#00D6A0]/30">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Operational Fallback Active
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-[#A855F7]/15 text-[#A855F7] border border-[#A855F7]/30">
              <Sparkles className="w-3.5 h-3.5" />
              Phase 6 Validated
            </span>
          </div>
        </div>

        {/* Scientific Transparency Alert Box */}
        <div className="mt-5 p-4 bg-[#122040]/70 border border-[#168BFF]/30 rounded-xl flex items-start gap-3 text-xs text-slate-300">
          <Info className="w-5 h-5 text-[#00D9F5] shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-white">
              Meteorological Transparency & Non-Fabrication Protocol:
            </p>
            <p className="leading-relaxed text-slate-300">
              Anomaly detection identifies mathematical departures from climatological baselines in gridded fields; it does <strong>not</strong> constitute prognostic forecasting of future events. Unsupervised models (Isolation Forest) are evaluated on controlled synthetic perturbation benchmarks to demonstrate software pipelines, and must not be interpreted as real-world operational skill without verified historical reanalysis observations.
            </p>
          </div>
        </div>
      </div>

      {/* 2. AI Model Status & Selection Registry */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-[#168BFF]" />
            <h2 className="text-lg font-bold text-white tracking-wide">Model Management & Registry</h2>
          </div>
          <div className="text-xs text-slate-400">
            Active Engine: <span className="font-semibold text-[#00D9F5]">{modelStatus?.active_model_name || activeModelId}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Card 1: Deterministic Baseline */}
          <div className={`p-5 rounded-xl border transition-all duration-200 relative flex flex-col justify-between ${
            activeModelId === 'deterministic_baseline'
              ? 'bg-[#0B1936] border-[#00D6A0] shadow-[0_0_20px_rgba(0,214,160,0.15)]'
              : 'bg-[#0B1936]/60 border-[#122040] hover:border-slate-600'
          }`}>
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-[#00D6A0]/20 text-[#00D6A0] border border-[#00D6A0]/40">
                  Operational Baseline
                </span>
                <span className="text-xs font-mono text-slate-400">v1.0.0</span>
              </div>
              <h3 className="text-base font-bold text-white mb-1">Deterministic Physical Thresholds</h3>
              <p className="text-xs text-slate-300 leading-relaxed mb-4">
                3-sigma climatological departures and WMO barometric deficit thresholds. Serves as robust operational fallback.
              </p>
              
              <div className="space-y-1.5 text-xs text-slate-400 border-t border-[#122040] pt-3">
                <div className="flex justify-between">
                  <span>Type:</span> <span className="text-slate-200 font-medium">Physical Heuristics</span>
                </div>
                <div className="flex justify-between">
                  <span>Inference Latency:</span> <span className="text-[#00D6A0] font-mono font-medium">~1.8 ms</span>
                </div>
                <div className="flex justify-between">
                  <span>Operational Status:</span> <span className="text-emerald-400 font-medium">Production Ready</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => handleSelectModel('deterministic_baseline')}
              disabled={activeModelId === 'deterministic_baseline' || isSwitchingModel}
              className={`mt-4 w-full py-2 px-3 rounded-lg text-xs font-bold transition flex items-center justify-center gap-2 ${
                activeModelId === 'deterministic_baseline'
                  ? 'bg-[#00D6A0]/20 text-[#00D6A0] border border-[#00D6A0]/40 cursor-default'
                  : 'bg-[#168BFF] hover:bg-[#168BFF]/80 text-white shadow-md'
              }`}
            >
              {activeModelId === 'deterministic_baseline' ? (
                <><CheckCircle2 className="w-4 h-4" /> Active Operational Model</>
              ) : (
                'Activate Baseline'
              )}
            </button>
          </div>

          {/* Card 2: Experimental Isolation Forest */}
          <div className={`p-5 rounded-xl border transition-all duration-200 relative flex flex-col justify-between ${
            activeModelId === 'isolation_forest_v1'
              ? 'bg-[#0B1936] border-[#168BFF] shadow-[0_0_20px_rgba(22,139,255,0.18)]'
              : 'bg-[#0B1936]/60 border-[#122040] hover:border-slate-600'
          }`}>
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-[#168BFF]/20 text-[#00D9F5] border border-[#168BFF]/40">
                  Experimental ML
                </span>
                <span className="text-xs font-mono text-slate-400">v1.0.0</span>
              </div>
              <h3 className="text-base font-bold text-white mb-1">Isolation Forest Baseline</h3>
              <p className="text-xs text-slate-300 leading-relaxed mb-4">
                Unsupervised decision-tree ensemble partitioning an 8-dimensional normalized feature space.
              </p>
              
              <div className="space-y-1.5 text-xs text-slate-400 border-t border-[#122040] pt-3">
                <div className="flex justify-between">
                  <span>Feature Schema:</span> <span className="text-slate-200 font-medium">8 Features (v1.0.0)</span>
                </div>
                <div className="flex justify-between">
                  <span>Training Dataset:</span> <span className="text-amber-400 font-mono text-[11px]">SYNTHETIC_BENCHMARK</span>
                </div>
                <div className="flex justify-between">
                  <span>Inference Latency:</span> <span className="text-[#00D9F5] font-mono font-medium">~14.6 ms</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => handleSelectModel('isolation_forest_v1')}
              disabled={activeModelId === 'isolation_forest_v1' || isSwitchingModel}
              className={`mt-4 w-full py-2 px-3 rounded-lg text-xs font-bold transition flex items-center justify-center gap-2 ${
                activeModelId === 'isolation_forest_v1'
                  ? 'bg-[#168BFF]/20 text-[#00D9F5] border border-[#168BFF]/40 cursor-default'
                  : 'bg-[#168BFF] hover:bg-[#168BFF]/80 text-white shadow-md'
              }`}
            >
              {activeModelId === 'isolation_forest_v1' ? (
                <><CheckCircle2 className="w-4 h-4" /> Active Experimental Model</>
              ) : (
                'Select ML Model'
              )}
            </button>
          </div>

          {/* Card 3: Spatiotemporal Research Extension Point */}
          <div className="p-5 rounded-xl border border-[#122040] bg-[#071126]/60 opacity-80 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-purple-500/20 text-purple-300 border border-purple-500/40">
                  Research Roadmap
                </span>
                <span className="text-xs font-mono text-slate-500">v0.1.0-stub</span>
              </div>
              <h3 className="text-base font-bold text-slate-300 mb-1">Spatiotemporal ConvLSTM / U-Net</h3>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                Documented architectural extension point for 4D recurrent spatiotemporal attention segmentation.
              </p>
              
              <div className="space-y-1.5 text-xs text-slate-400 border-t border-[#122040] pt-3">
                <div className="flex justify-between">
                  <span>Tensor Contract:</span> <span className="text-slate-300 font-mono text-[11px]">(B, 10, 4, 96, 161)</span>
                </div>
                <div className="flex justify-between">
                  <span>Prerequisite Data:</span> <span className="text-slate-300">ERA5 / IMD Reanalysis</span>
                </div>
                <div className="flex justify-between">
                  <span>Deployment:</span> <span className="text-purple-400 font-medium">Planned Phase 8</span>
                </div>
              </div>
            </div>

            <div className="mt-4 py-2 px-3 rounded-lg text-xs font-medium text-slate-500 bg-[#122040]/30 border border-[#122040] text-center">
              Extension Point (Not Operational)
            </div>
          </div>
        </div>
      </div>

      {/* 3. Section B: Anomaly Scoring & Multi-Component Attribution */}
      <div className="bg-[#0B1936] border border-[#122040] rounded-2xl p-6 shadow-md space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#122040]">
          <div>
            <div className="flex items-center gap-2">
              <Gauge className="w-5 h-5 text-[#00D9F5]" />
              <h2 className="text-lg font-bold text-white tracking-wide">Multi-Component Anomaly Scoring & Attribution</h2>
              {isLoadingScore && (
                <span className="text-[10px] text-[#00D9F5] font-mono animate-pulse">
                  (Evaluating...)
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Dimensionless fusion across physical magnitude, spatial scale, temporal persistence, and observational quality.
            </p>
          </div>

          {/* Event Selector Dropdown */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Select Anomaly:</span>
            <select
              value={currentEventId}
              onChange={handleEventChange}
              className="bg-[#071126] border border-[#168BFF]/40 text-xs text-white rounded-lg px-3 py-1.5 focus:outline-none focus:border-[#00D9F5]"
            >
              {events.map(ev => (
                <option key={ev.id} value={ev.id}>
                  {ev.name} ({ev.type}) — {ev.id}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Score Overview Row */}
        {scoreData && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-center">
            {/* Main Score Gauge Box */}
            <div className="bg-[#071126] border border-[#122040] rounded-xl p-5 text-center flex flex-col items-center justify-center relative overflow-hidden">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Composite Anomaly Index
              </div>
              <div className="text-5xl font-black text-white tracking-tight flex items-baseline gap-1 my-1">
                <span className={
                  scoreData.overall_score_100 >= 75 ? 'text-[#FF4568]' :
                  scoreData.overall_score_100 >= 50 ? 'text-amber-400' :
                  'text-[#00D9F5]'
                }>
                  {scoreData.overall_score_100}
                </span>
                <span className="text-sm font-bold text-slate-500">/ 100</span>
              </div>

              <div className="flex items-center gap-2 mt-2">
                <span className={`px-2.5 py-0.5 rounded text-xs font-bold uppercase tracking-wider ${
                  scoreData.severity_tier === 'Extreme' ? 'bg-red-500/20 text-red-400 border border-red-500/40' :
                  scoreData.severity_tier === 'High' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                  'bg-blue-500/20 text-blue-400 border border-blue-500/40'
                }`}>
                  {scoreData.severity_tier} Severity
                </span>
              </div>

              <div className="mt-3 text-[11px] text-slate-400 bg-[#122040]/50 px-2.5 py-1 rounded">
                Non-probabilistic departure index
              </div>
            </div>

            {/* Score Drivers & Interpretation */}
            <div className="lg:col-span-3 bg-[#071126]/60 border border-[#122040] rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  Primary Score Drivers
                </span>
                <span className="text-xs text-slate-400">
                  Method: <span className="text-slate-200 font-mono text-[11px]">{scoreData.detection_method}</span>
                </span>
              </div>

              <div className="flex flex-wrap gap-2">
                {scoreData.primary_contributing_variables.map((v, i) => (
                  <span key={i} className="px-3 py-1 bg-[#168BFF]/15 border border-[#168BFF]/40 rounded-full text-xs font-semibold text-[#00D9F5] flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#00D9F5]"></span>
                    {v}
                  </span>
                ))}
              </div>

              <p className="text-xs text-slate-300 leading-relaxed pt-1">
                {scoreData.score_interpretation}
              </p>

              <div className="flex items-center gap-4 text-xs text-slate-400 pt-2 border-t border-[#122040]/80">
                <div>
                  Event: <span className="text-white font-medium">{activeEvent.name || currentEventId}</span>
                </div>
                <div>
                  Region: <span className="text-white font-medium">{activeEvent.region || 'Indian Ocean'}</span>
                </div>
                <div>
                  Lead Window: <span className="text-white font-medium">{activeEvent.forecast_window || 'Day 1 – 5'}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Component Decomposition Cards */}
        {scoreData && scoreData.components && (
          <div className="space-y-3">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Granular Component Breakdown (Dimensionless Scale [0.0 – 1.0])
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {Object.entries(scoreData.components).map(([key, comp]) => {
                const pct = Math.round(comp.normalized_score * 100);
                return (
                  <div key={key} className="p-4 bg-[#071126] border border-[#122040] rounded-xl flex flex-col justify-between space-y-2">
                    <div>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-semibold text-white">{comp.display_name}</span>
                        <span className="font-mono text-[#00D9F5] font-bold">{comp.normalized_score.toFixed(2)}</span>
                      </div>
                      
                      {/* Progress bar */}
                      <div className="w-full bg-[#122040] rounded-full h-1.5 overflow-hidden my-2">
                        <div 
                          className="h-full bg-gradient-to-r from-[#168BFF] to-[#00D9F5] rounded-full transition-all duration-300"
                          style={{ width: `${pct}%` }}
                        />
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span>Weight: {(comp.weight * 100).toFixed(0)}%</span>
                        <span>Share: <strong className="text-slate-200">{comp.contribution_percent}%</strong></span>
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-400 leading-snug pt-2 border-t border-[#122040]">
                      {comp.interpretation}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* 4. Section C: Scientific Model Evaluation Benchmark */}
      <div className="bg-[#0B1936] border border-[#122040] rounded-2xl p-6 shadow-md space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#122040]">
          <div>
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-[#A855F7]" />
              <h2 className="text-lg font-bold text-white tracking-wide">Model Evaluation & Benchmark Comparison</h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Empirical metrics computed against synthetic ground-truth masks with independent seed (T+24h).
            </p>
          </div>

          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
            <Info className="w-3.5 h-3.5" />
            Synthetic Benchmark Evaluation
          </span>
        </div>

        {/* Comparison Table */}
        {benchmarkData && benchmarkData.summary_table && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#071126] text-slate-400 uppercase text-[10px] tracking-wider border-b border-[#122040]">
                <tr>
                  <th className="py-3 px-4">Candidate Model</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Precision</th>
                  <th className="py-3 px-4">Recall (Detection)</th>
                  <th className="py-3 px-4">F1 Score</th>
                  <th className="py-3 px-4">Footprint IoU</th>
                  <th className="py-3 px-4">False-Pos Rate</th>
                  <th className="py-3 px-4">Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#122040]">
                {benchmarkData.summary_table.map((row, idx) => (
                  <tr key={idx} className="hover:bg-[#122040]/30 transition">
                    <td className="py-3 px-4 font-bold text-white flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${row.status === 'OPERATIONAL' ? 'bg-[#00D6A0]' : 'bg-[#168BFF]'}`} />
                      {row.model_name}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        row.status === 'OPERATIONAL' 
                          ? 'bg-[#00D6A0]/15 text-[#00D6A0] border border-[#00D6A0]/30'
                          : 'bg-[#168BFF]/15 text-[#00D9F5] border border-[#168BFF]/30'
                      }`}>
                        {row.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-emerald-400 font-semibold">{(row.precision * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4 font-mono text-blue-400 font-semibold">{(row.recall * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4 font-mono text-purple-400 font-bold">{(row.f1_score * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4 font-mono text-cyan-400 font-medium">{(row.iou * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4 font-mono text-slate-300">{(row.fpr * 100).toFixed(2)}%</td>
                    <td className="py-3 px-4 font-mono text-slate-400">{row.latency_ms} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Comparative Analysis & Caveats */}
        {benchmarkData && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="p-4 bg-[#071126] border border-[#122040] rounded-xl text-xs space-y-2">
              <span className="font-bold text-white block">Objective Meteorological Comparison:</span>
              <p className="text-slate-300 leading-relaxed">
                {benchmarkData.comparative_analysis}
              </p>
            </div>

            <div className="p-4 bg-[#071126] border border-[#122040] rounded-xl text-xs space-y-1.5">
              <span className="font-bold text-amber-400 block flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" /> Evaluation Boundary Limitations:
              </span>
              <ul className="list-disc list-inside text-slate-400 space-y-1 text-[11px] leading-relaxed">
                {benchmarkData.scientific_caveats?.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* 5. Section D: Forecast Uncertainty & Multi-Member Dispersion */}
      <div className="bg-[#0B1936] border border-[#122040] rounded-2xl p-6 shadow-md space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#122040]">
          <div>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-[#00D6A0]" />
              <h2 className="text-lg font-bold text-white tracking-wide">Forecast Uncertainty & Multi-Horizon Dispersion</h2>
              {isLoadingUncertainty && (
                <span className="text-[10px] text-[#00D6A0] font-mono animate-pulse">
                  (Computing...)
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Descriptive ensemble standard deviation and quantiles (p10 – p90) across lead times.
            </p>
          </div>

          {/* Mode Toggle Controls */}
          <div className="flex items-center gap-3">
            <div className="flex rounded-lg bg-[#071126] p-1 border border-[#122040]">
              <button
                onClick={() => setUncertaintyMode('ensemble')}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                  uncertaintyMode === 'ensemble'
                    ? 'bg-[#168BFF] text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Ensemble Demo (5 Members)
              </button>
              <button
                onClick={() => setUncertaintyMode('deterministic')}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                  uncertaintyMode === 'deterministic'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Deterministic Run (Unavailable State)
              </button>
            </div>
          </div>
        </div>

        {/* Variable & Lead Time Selectors */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-[#071126] p-3 rounded-xl border border-[#122040]">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 mr-1">Variable:</span>
            {['temperature', 'wind', 'pressure'].map((v) => (
              <button
                key={v}
                onClick={() => setUncertaintyVar(v)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition ${
                  uncertaintyVar === v
                    ? 'bg-[#00D9F5]/20 text-[#00D9F5] border border-[#00D9F5]/40'
                    : 'bg-[#122040]/50 text-slate-400 hover:text-white'
                }`}
              >
                {v}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">Forecast Horizon:</span>
            <div className="flex items-center gap-1.5">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((d) => (
                <button
                  key={d}
                  onClick={() => setSelectedLeadDay(d)}
                  className={`w-7 h-7 rounded text-xs font-mono font-bold transition flex items-center justify-center ${
                    selectedLeadDay === d
                      ? 'bg-[#168BFF] text-white'
                      : 'bg-[#122040]/40 text-slate-400 hover:text-white'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
            <span className="text-xs text-slate-400 font-mono">Day {selectedLeadDay} ({selectedLeadDay * 24}h)</span>
          </div>
        </div>

        {/* Uncertainty Content Display: Available vs Unavailable Empty State */}
        {uncertaintyMode === 'deterministic' ? (
          <div className="p-8 bg-[#071126] border border-amber-500/30 rounded-xl text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/30 flex items-center justify-center mx-auto text-amber-400">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-white">Forecast Uncertainty Spread Unavailable</h3>
            <p className="text-xs text-slate-300 max-w-xl mx-auto leading-relaxed">
              {uncertaintySeries?.empty_state_explanation || 
                "No multi-member ensemble forecast is configured for this variable. The active data originates from a single deterministic model run. Ensemble spread and member quantiles require a multi-member operational forecast (e.g. GEFS 31-member run)."
              }
            </p>
            <div className="text-[11px] text-slate-500 pt-2">
              Guidance: Synoptic forecast error inherently compounds with lead time (Day 5+ predictability decay).
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* KPI Cards for Selected Horizon */}
            {currentLeadPoint && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 bg-[#071126] border border-[#122040] rounded-xl text-center">
                  <div className="text-[11px] text-slate-400 uppercase tracking-wider mb-1">Ensemble Mean</div>
                  <div className="text-2xl font-black text-white font-mono">
                    {currentLeadPoint.ensemble_mean} <span className="text-xs font-normal text-slate-400">{currentLeadPoint.unit}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1">Multi-member centroid</div>
                </div>

                <div className="p-4 bg-[#071126] border border-[#122040] rounded-xl text-center">
                  <div className="text-[11px] text-slate-400 uppercase tracking-wider mb-1">Spread (Std Dev σ)</div>
                  <div className="text-2xl font-black text-[#00D9F5] font-mono">
                    ±{currentLeadPoint.ensemble_std} <span className="text-xs font-normal text-slate-400">{currentLeadPoint.unit}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1">Intra-ensemble dispersion</div>
                </div>

                <div className="p-4 bg-[#071126] border border-[#122040] rounded-xl text-center">
                  <div className="text-[11px] text-slate-400 uppercase tracking-wider mb-1">10th – 90th Percentile</div>
                  <div className="text-xl font-bold text-amber-400 font-mono">
                    {currentLeadPoint.quantiles.p10} – {currentLeadPoint.quantiles.p90}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1">80% confidence interval</div>
                </div>

                <div className="p-4 bg-[#071126] border border-[#122040] rounded-xl text-center">
                  <div className="text-[11px] text-slate-400 uppercase tracking-wider mb-1">Active Members</div>
                  <div className="text-2xl font-black text-purple-400 font-mono">
                    {currentLeadPoint.member_count} <span className="text-xs font-normal text-slate-400">/ 5</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1">
                    {currentLeadPoint.missing_member_fraction > 0 ? `${currentLeadPoint.missing_member_fraction * 100}% dropped` : 'Complete agreement'}
                  </div>
                </div>
              </div>
            )}

            {/* Timeline Sparkline / Horizon Table */}
            <div className="bg-[#071126] border border-[#122040] rounded-xl p-4 overflow-x-auto">
              <div className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
                10-Day Multi-Horizon Dispersion Table
              </div>
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#122040] text-slate-500 text-[10px]">
                    <th className="py-2 px-3">Horizon</th>
                    <th className="py-2 px-3">Lead Hours</th>
                    <th className="py-2 px-3">Mean</th>
                    <th className="py-2 px-3">Spread (±σ)</th>
                    <th className="py-2 px-3">P10</th>
                    <th className="py-2 px-3">P50</th>
                    <th className="py-2 px-3">P90</th>
                    <th className="py-2 px-3">Agreement</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#122040]/60">
                  {uncertaintySeries?.timeline?.map((pt) => (
                    <tr 
                      key={pt.lead_day}
                      onClick={() => setSelectedLeadDay(pt.lead_day)}
                      className={`cursor-pointer transition ${
                        selectedLeadDay === pt.lead_day ? 'bg-[#168BFF]/20 text-white' : 'hover:bg-[#122040]/30 text-slate-300'
                      }`}
                    >
                      <td className="py-2 px-3 font-bold text-white">Day {pt.lead_day}</td>
                      <td className="py-2 px-3 text-slate-400">+{pt.lead_time_hours}h</td>
                      <td className="py-2 px-3 font-semibold text-slate-200">{pt.ensemble_mean} {pt.unit}</td>
                      <td className="py-2 px-3 text-[#00D9F5]">±{pt.ensemble_std}</td>
                      <td className="py-2 px-3 text-slate-400">{pt.quantiles.p10}</td>
                      <td className="py-2 px-3 text-purple-300">{pt.quantiles.p50}</td>
                      <td className="py-2 px-3 text-slate-400">{pt.quantiles.p90}</td>
                      <td className="py-2 px-3 text-emerald-400">{pt.member_count} of 5</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
