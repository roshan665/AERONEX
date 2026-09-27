"""
FastAPI Routes for Scientific Model Evaluation and Forecast Uncertainty Series
"""

from typing import Optional
from fastapi import APIRouter, Query

from app.ml.schemas import (
    ModelEvaluationBenchmark,
    ForecastUncertaintySeries,
)
from app.ml.evaluation import ModelEvaluationService
from app.ml.uncertainty import ForecastUncertaintyService

router = APIRouter(tags=["AI/ML Evaluation & Uncertainty"])


@router.get(
    "/evaluation",
    response_model=ModelEvaluationBenchmark,
    summary="Scientific Benchmark Evaluation Results",
    description="Returns empirical precision, recall, F1, IoU, and confusion matrix comparing deterministic and ML baselines on synthetic ground-truth masks."
)
def get_model_evaluation(
    lead_time_hours: int = Query(default=24, ge=0, le=240, description="Lead time horizon to evaluate"),
    seed: int = Query(default=100, description="Evaluation dataset random seed")
) -> ModelEvaluationBenchmark:
    return ModelEvaluationService.evaluate_all_models(
        lead_time_hours=lead_time_hours,
        seed=seed
    )


@router.get(
    "/uncertainty/series",
    response_model=ForecastUncertaintySeries,
    summary="Multi-Lead-Time Forecast Uncertainty Series",
    description="Returns ensemble spread, standard deviation, and quantiles (p10-p90) across 10-day forecast horizon. Explicitly reports unavailable state when deterministic mode is selected."
)
@router.get(
    "/uncertainty-series",
    response_model=ForecastUncertaintySeries,
    include_in_schema=False
)
def get_uncertainty_series(
    variable: str = Query(default="temperature", description="Target meteorological variable: temperature, wind, pressure"),
    mode: str = Query(default="ensemble", description="Mode: 'ensemble' (5-member demonstration) or 'deterministic' (unavailable empty state)")
) -> ForecastUncertaintySeries:
    return ForecastUncertaintyService.get_variable_uncertainty(
        variable=variable,
        mode=mode
    )
