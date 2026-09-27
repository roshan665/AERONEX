"""
End-to-End Meteorological Anomaly Detection & Footprint Pipeline Orchestrator
"""

import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.engine.config import EngineConfig, engine_config
from app.engine.schemas import WeatherGridDataset, FootprintEntity
from app.engine.preprocessor import GridPreprocessor
from app.engine.detectors.temperature_detector import TemperatureAnomalyDetector
from app.engine.detectors.wind_detector import WindAnomalyDetector
from app.engine.detectors.pressure_detector import PressureAnomalyDetector
from app.engine.detectors.precipitation_detector import PrecipitationAnomalyDetector
from app.engine.footprints import FootprintExtractor
from app.engine.aggregation import EventAggregator
from app.engine.tracker import TemporalEventTracker
from app.models.anomaly import AnomalyEvent


class PipelineExecutionResult(BaseModel):
    execution_time_ms: float
    lead_time_hours: int
    valid_time: str
    grid_shape: List[int]
    total_anomalies_detected: int
    total_footprints_extracted: int
    events: List[AnomalyEvent]
    footprints: List[FootprintEntity]
    temporal_associations: List[Dict[str, Any]] = Field(default_factory=list)
    preprocessing_warnings: List[str] = Field(default_factory=list)
    data_provenance: str = "DEMO_SYNTHETIC_DATASET"
    is_simulated: bool = True


class AnomalyDetectionPipeline:
    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or engine_config
        self.temp_detector = TemperatureAnomalyDetector(self.config.thresholds)
        self.wind_detector = WindAnomalyDetector(self.config.thresholds)
        self.pressure_detector = PressureAnomalyDetector(self.config.thresholds)
        self.precip_detector = PrecipitationAnomalyDetector(self.config.thresholds)

    def run(
        self,
        dataset: WeatherGridDataset,
        previous_footprints: Optional[List[FootprintEntity]] = None,
    ) -> PipelineExecutionResult:
        start_time = time.perf_counter()

        # 1. Preprocess & Normalize
        normalized_grid = GridPreprocessor.preprocess(dataset)

        # 2. Run Detectors
        raw_detections = []
        raw_detections.extend(self.temp_detector.detect(normalized_grid))
        raw_detections.extend(self.wind_detector.detect(normalized_grid))
        raw_detections.extend(self.pressure_detector.detect(normalized_grid))
        raw_detections.extend(self.precip_detector.detect(normalized_grid))

        # 3. Extract Footprints & Polygons
        extracted_footprints: List[FootprintEntity] = []
        for det in raw_detections:
            fps = FootprintExtractor.extract_footprints(
                detection=det,
                lats=normalized_grid.lats,
                lons=normalized_grid.lons,
                config=self.config.footprint,
                thresholds=self.config.thresholds,
            )
            extracted_footprints.extend(fps)

        # 4. Aggregate & Physically Cross-Correlate Events
        aggregated_events = EventAggregator.aggregate_events(
            footprints=extracted_footprints,
            grid=normalized_grid,
        )

        # 5. Temporal Association (if previous timestep provided)
        associations = []
        if previous_footprints:
            associations = TemporalEventTracker.track_footprints(
                current_footprints=extracted_footprints,
                previous_footprints=previous_footprints,
                config=self.config.tracking,
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return PipelineExecutionResult(
            execution_time_ms=round(elapsed_ms, 2),
            lead_time_hours=normalized_grid.lead_time_hours,
            valid_time=normalized_grid.valid_time,
            grid_shape=list(normalized_grid.shape),
            total_anomalies_detected=len(aggregated_events),
            total_footprints_extracted=len(extracted_footprints),
            events=aggregated_events,
            footprints=extracted_footprints,
            temporal_associations=associations,
            preprocessing_warnings=normalized_grid.preprocessing_warnings,
            data_provenance=dataset.data_source,
            is_simulated=True,
        )
