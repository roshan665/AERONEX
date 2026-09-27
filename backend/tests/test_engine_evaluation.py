"""
Scientific Evaluation & Validation of Anomaly Detection Pipeline Against Injected Ground-Truth
"""

import time
import pytest
import numpy as np
from app.engine.config import EngineConfig
from app.engine.pipeline import AnomalyDetectionPipeline
from app.engine.preprocessor import GridPreprocessor
from app.engine.synthetic_generator import SyntheticWeatherGenerator


def test_scientific_evaluation_metrics_against_ground_truth():
    """
    Evaluates detector precision, recall, F1 score, and spatial IoU against
    known injected synthetic anomalies.
    
    NOTE: These metrics are calculated on DEMONSTRATION SYNTHETIC GRIDS with known
    mathematical ground-truth masks. They do NOT represent validation on operational
    real-world NWP observational forecasts.
    """
    # 1. Generate deterministic synthetic grid + ground truth
    dataset, ground_truth = SyntheticWeatherGenerator.generate_dataset(lead_time_hours=24, seed=42)

    config = EngineConfig()
    pipeline = AnomalyDetectionPipeline(config=config)

    # Measure exact execution duration
    t0 = time.perf_counter()
    result = pipeline.run(dataset)
    t1 = time.perf_counter()
    pipeline_duration_ms = (t1 - t0) * 1000.0

    assert pipeline_duration_ms < 1000.0  # Must be fast (< 1 second)
    assert result.total_anomalies_detected >= 3
    assert result.total_footprints_extracted >= 3

    # 2. Extract detection masks directly from detectors
    normalized_grid = GridPreprocessor.preprocess(dataset)
    temp_detections = pipeline.temp_detector.detect(normalized_grid)
    wind_detections = pipeline.wind_detector.detect(normalized_grid)
    pressure_detections = pipeline.pressure_detector.detect(normalized_grid)
    precip_detections = pipeline.precip_detector.detect(normalized_grid)

    heat_det = next(d for d in temp_detections if d.category == "heat_wave")
    cold_det = next(d for d in temp_detections if d.category == "cold_wave")
    wind_det = next(d for d in wind_detections if d.category == "wind_anomaly")
    press_det = next(d for d in pressure_detections if d.category == "pressure_anomaly")
    precip_det = next(d for d in precip_detections if d.category == "precipitation_anomaly")

    evaluation_pairs = [
        ("Heat Dome Anomaly", heat_det.mask, ground_truth["heat_dome"]),
        ("Cold Wave Anomaly", cold_det.mask, ground_truth["cold_wave"]),
        ("Cyclone Pressure Anomaly", press_det.mask, ground_truth["cyclone_pressure"]),
        ("Extreme Monsoon Rainfall", precip_det.mask, ground_truth["heavy_rain"]),
    ]

    print("\n" + "="*80)
    print("AERONEX PHASE 4: EMPIRICAL SCIENTIFIC EVALUATION REPORT (SYNTHETIC GROUND TRUTH)")
    print(f"Dataset Dimensions: {dataset.lats.shape[0]} lats x {dataset.lons.shape[0]} lons")
    print(f"End-to-End Execution Time: {pipeline_duration_ms:.2f} ms")
    print("="*80)
    print(f"{'Anomaly Target':<28} | {'Precision':<9} | {'Recall':<8} | {'F1 Score':<8} | {'IoU Overlap':<11}")
    print("-" * 80)

    for name, pred_mask, gt_mask in evaluation_pairs:
        tp = int(np.logical_and(pred_mask, gt_mask).sum())
        fp = int(np.logical_and(pred_mask, ~gt_mask).sum())
        fn = int(np.logical_and(~pred_mask, gt_mask).sum())

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        iou = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0

        print(f"{name:<28} | {precision:.3f}     | {recall:.3f}    | {f1:.3f}    | {iou:.3f}")

        # Scientific baseline quality guarantees
        assert precision >= 0.70, f"{name} precision {precision:.3f} below 0.70"
        assert recall >= 0.75, f"{name} recall {recall:.3f} below 0.75"
        assert f1 >= 0.75, f"{name} F1 score {f1:.3f} below 0.75"
        assert iou >= 0.60, f"{name} IoU {iou:.3f} below 0.60"

    print("="*80 + "\n")
