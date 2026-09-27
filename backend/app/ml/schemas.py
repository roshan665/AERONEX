"""
Pydantic Schemas for AI/ML Baseline, Anomaly Scoring, Model Registry, and Scientific Evaluation
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class ScoringWeightsConfig(BaseModel):
    """
    Configurable weighting parameters for multi-component anomaly scoring.
    All weights must be non-negative and sum to 1.0 (within numerical tolerance).
    """
    w_temp: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight for temperature anomaly magnitude")
    w_wind: float = Field(default=0.20, ge=0.0, le=1.0, description="Weight for wind anomaly magnitude")
    w_pressure: float = Field(default=0.20, ge=0.0, le=1.0, description="Weight for pressure deficit magnitude")
    w_spatial: float = Field(default=0.15, ge=0.0, le=1.0, description="Weight for spatial extent / footprint area")
    w_persistence: float = Field(default=0.10, ge=0.0, le=1.0, description="Weight for multi-horizon temporal persistence")
    w_quality: float = Field(default=0.10, ge=0.0, le=1.0, description="Weight for data quality and observational integrity")

    @field_validator("w_quality")
    @classmethod
    def validate_sum(cls, v: float, info) -> float:
        data = info.data
        if "w_temp" in data and "w_wind" in data and "w_pressure" in data and "w_spatial" in data and "w_persistence" in data:
            total = data["w_temp"] + data["w_wind"] + data["w_pressure"] + data["w_spatial"] + data["w_persistence"] + v
            if not (0.98 <= total <= 1.02):
                raise ValueError(f"Scoring weights must sum to 1.0 (+/- 0.02 tolerance). Total sum is {total:.4f}")
        return v


class ComponentAnomalyScore(BaseModel):
    """Granular diagnostic metric for a single normalized anomaly component."""
    component_name: str = Field(..., description="Machine-readable component key, e.g. thermal_deviation")
    display_name: str = Field(..., description="Human-readable label")
    raw_value: Optional[float] = Field(None, description="Observed raw physical measurement")
    raw_unit: Optional[str] = Field(None, description="Physical unit (°C, hPa, km/h, km², etc.)")
    reference_normal: Optional[float] = Field(None, description="Climatological or baseline normal reference")
    normalized_score: float = Field(..., ge=0.0, le=1.0, description="Normalized dimensionless deviation on [0.0, 1.0]")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight applied in composite aggregation")
    weighted_contribution: float = Field(..., description="Contribution score: normalized_score * weight")
    contribution_percent: float = Field(..., description="Relative percentage contribution to composite score")
    interpretation: str = Field(..., description="Meteorological interpretation of this component")


class CompositeAnomalyScore(BaseModel):
    """
    Consolidated scientific anomaly score synthesized across physical components.
    
    CRITICAL SCIENTIFIC PRINCIPLE:
    This score is an empirical index of multidimensional deviation on [0.0, 1.0] or [0.0, 100.0].
    It is NOT a calibrated probability and MUST NOT be represented as a statistical likelihood of future catastrophe.
    """
    event_id: str
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Normalized dimensionless continuous score [0.0, 1.0]")
    overall_score_100: float = Field(..., ge=0.0, le=100.0, description="Scaled score [0.0, 100.0] for dashboard gauge display")
    severity_tier: str = Field(..., description="Discrete classification: Low, Medium, High, Extreme")
    is_probability: bool = Field(default=False, description="Strictly False. Uncalibrated multi-criteria index.")
    primary_contributing_variables: List[str] = Field(..., description="Ordered list of variables driving the score")
    components: Dict[str, ComponentAnomalyScore] = Field(..., description="Dictionary of all component scores")
    detection_method: str = Field(..., description="Scoring methodology identifier")
    data_quality_warnings: List[str] = Field(default_factory=list, description="Data caveats, missing value penalties")
    score_interpretation: str = Field(..., description="Plain-language meteorological synopsis of score drivers")
    score_limitations: List[str] = Field(..., description="Explicit scientific caveats and methodological bounds")


class FeatureMetadata(BaseModel):
    name: str
    unit: str
    description: str
    preprocessing: str


class FeatureSchema(BaseModel):
    version: str
    feature_names: List[str]
    features_metadata: Dict[str, FeatureMetadata]
    created_at: str


class ModelMetadata(BaseModel):
    model_id: str
    model_name: str
    version: str
    model_type: str = Field(..., description="'DETERMINISTIC_RULES', 'ISOLATION_FOREST', 'SPATIOTEMPORAL_RESEARCH'")
    status: str = Field(..., description="'OPERATIONAL_BASELINE', 'EXPERIMENTAL_SYNTHETIC_BENCHMARK', 'RESEARCH_ROADMAP'")
    feature_schema_version: str
    training_dataset_id: Optional[str] = None
    training_timestamp: Optional[str] = None
    random_seed: Optional[int] = None
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    is_operational: bool
    description: str
    limitations: List[str]


class ModelListResponse(BaseModel):
    models: List[ModelMetadata]
    active_model_id: str
    timestamp: str


class ModelSelectionRequest(BaseModel):
    model_id: str = Field(..., description="ID of the model to activate: 'deterministic_baseline' or 'isolation_forest_v1'")


class ConfusionMatrix(BaseModel):
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int


class EvaluationMetricSummary(BaseModel):
    model_id: str
    model_name: str
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    detection_rate: float
    footprint_iou: float
    confusion_matrix: ConfusionMatrix
    total_samples: int
    mean_inference_latency_ms: float
    evaluation_status: str


class ModelEvaluationBenchmark(BaseModel):
    evaluation_id: str
    evaluated_at: str
    evaluation_dataset: str
    evaluation_provenance: str = Field(
        default="SYNTHETIC_BENCHMARK_LABELS",
        description="Dataset provenance: 'SYNTHETIC_BENCHMARK_LABELS' or 'HISTORICAL_REANALYSIS_VERIFIED'"
    )
    is_synthetic_evaluation: bool = True
    models: Dict[str, EvaluationMetricSummary]
    summary_table: List[Dict[str, Any]]
    comparative_analysis: str
    scientific_caveats: List[str]


class EnsembleQuantiles(BaseModel):
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float


class LeadTimeUncertaintyPoint(BaseModel):
    lead_day: int
    lead_time_hours: int
    valid_time: str
    ensemble_mean: float
    ensemble_std: float
    quantiles: EnsembleQuantiles
    member_count: int
    missing_member_fraction: float
    unit: str


class ForecastUncertaintySeries(BaseModel):
    variable: str
    variable_name: str
    unit: str
    horizon_days: int
    is_available: bool
    uncertainty_mode: str = Field(..., description="'ENSEMBLE_MEMBERS', 'DETERMINISTIC_ONLY', 'UNAVAILABLE'")
    member_count: int
    timeline: List[LeadTimeUncertaintyPoint]
    caveats: List[str]
    empty_state_explanation: Optional[str] = None
    data_provenance: str = "SYNTHETIC_ENSEMBLE_DEMO"
    is_simulated: bool = True
