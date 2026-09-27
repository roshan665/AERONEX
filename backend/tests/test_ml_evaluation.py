"""
Unit Tests for Scientific Model Evaluation Framework
"""

import pytest
from app.ml.evaluation import ModelEvaluationService
from app.ml.schemas import ModelEvaluationBenchmark


def test_model_evaluation_against_synthetic_ground_truth():
    benchmark = ModelEvaluationService.evaluate_all_models(lead_time_hours=24, seed=100)

    assert isinstance(benchmark, ModelEvaluationBenchmark)
    assert benchmark.is_synthetic_evaluation is True
    assert benchmark.evaluation_provenance == "SYNTHETIC_BENCHMARK_LABELS"
    assert "deterministic_baseline" in benchmark.models
    assert "isolation_forest_v1" in benchmark.models

    det_metrics = benchmark.models["deterministic_baseline"]
    assert 0.0 <= det_metrics.precision <= 1.0
    assert 0.0 <= det_metrics.recall <= 1.0
    assert 0.0 <= det_metrics.f1_score <= 1.0
    assert 0.0 <= det_metrics.footprint_iou <= 1.0
    assert det_metrics.mean_inference_latency_ms >= 0.0

    cm = det_metrics.confusion_matrix
    total_cells = cm.true_positives + cm.false_positives + cm.false_negatives + cm.true_negatives
    assert total_cells == det_metrics.total_samples

    # Isolation Forest metrics
    ml_metrics = benchmark.models["isolation_forest_v1"]
    assert 0.0 <= ml_metrics.precision <= 1.0
    assert 0.0 <= ml_metrics.recall <= 1.0
    assert 0.0 <= ml_metrics.f1_score <= 1.0

    # Summary table
    assert len(benchmark.summary_table) == 2
    assert len(benchmark.scientific_caveats) >= 3
    assert "BENCHMARK PROVENANCE" in benchmark.scientific_caveats[0]
