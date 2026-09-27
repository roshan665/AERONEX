"""
Implementations of AeroNex Anomaly Models:
1. DeterministicBaselineModel (Operational Fallback)
2. IsolationForestAnomalyModel (Experimental ML Baseline)
3. SpatiotemporalResearchModelStub (Research Roadmap Extension Point)
"""

import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import numpy as np
import joblib

from sklearn.ensemble import IsolationForest

from app.ml.interfaces import AnomalyModel
from app.ml.schemas import ModelMetadata
from app.ml.features import FEATURE_COLUMNS, FEATURE_SCHEMA_VERSION


class DeterministicBaselineModel(AnomalyModel):
    """
    Deterministic rule-based baseline model implementing the AnomalyModel protocol.
    Applies physical thresholding and climatological Z-score criteria across normalized fields.
    """

    def __init__(
        self,
        z_threshold: float = 3.0,
        precip_threshold: float = 0.35,
        version: str = "1.0.0"
    ):
        self._z_threshold = z_threshold
        self._precip_threshold = precip_threshold
        self._version = version
        self._is_fitted = True

    @property
    def model_id(self) -> str:
        return "deterministic_baseline"

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "DeterministicBaselineModel":
        # Deterministic rules require no data-driven parameter estimation
        self._is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Evaluates physical criteria across feature columns:
        Col 0: temp_anomaly_z
        Col 1: wind_anomaly_z
        Col 2: mslp_anomaly_z
        Col 3: precip_rate_normalized
        """
        temp_z = np.abs(X[:, 0])
        wind_z = X[:, 1]
        mslp_deficit_z = -X[:, 2]  # Negative MSLP Z = low pressure
        precip = X[:, 3]

        is_anomaly = (
            (temp_z >= self._z_threshold) |
            (wind_z >= self._z_threshold) |
            (mslp_deficit_z >= self._z_threshold) |
            (precip >= self._precip_threshold)
        )
        return is_anomaly.astype(int)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """
        Continuous severity score computed as normalized maximum variable deviation.
        """
        temp_score = np.clip(np.abs(X[:, 0]) / 5.0, 0.0, 1.0)
        wind_score = np.clip(np.maximum(0.0, X[:, 1]) / 5.0, 0.0, 1.0)
        mslp_score = np.clip(np.maximum(0.0, -X[:, 2]) / 5.0, 0.0, 1.0)
        precip_score = np.clip(X[:, 3], 0.0, 1.0)

        # Max-pool across variables
        max_scores = np.maximum.reduce([temp_score, wind_score, mslp_score, precip_score])
        return max_scores

    def save(self, filepath: str) -> None:
        """Safely saves deterministic model configuration as JSON."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        config = {
            "model_id": self.model_id,
            "version": self._version,
            "z_threshold": self._z_threshold,
            "precip_threshold": self._precip_threshold,
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "DeterministicBaselineModel":
        with open(filepath, "r", encoding="utf-8") as f:
            config = json.load(f)
        return cls(
            z_threshold=config.get("z_threshold", 3.0),
            precip_threshold=config.get("precip_threshold", 0.35),
            version=config.get("version", "1.0.0")
        )

    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            model_id=self.model_id,
            model_name="Deterministic Physical Threshold Baseline",
            version=self._version,
            model_type="DETERMINISTIC_RULES",
            status="OPERATIONAL_BASELINE",
            feature_schema_version=FEATURE_SCHEMA_VERSION,
            training_dataset_id="NONE (EXPERT_RULES)",
            training_timestamp=None,
            random_seed=None,
            hyperparameters={
                "z_threshold": self._z_threshold,
                "precip_threshold": self._precip_threshold,
            },
            is_operational=True,
            description=(
                "Robust deterministic meteorological detector based on 3-sigma climatological departures "
                "and WMO synoptic threshold criteria. Operates as primary production baseline."
            ),
            limitations=[
                "Uses fixed physical thresholds that do not account for nonlinear multi-variable interactions.",
                "Subject to false positives in high-variance polar or coastal transition zones.",
            ]
        )


class IsolationForestAnomalyModel(AnomalyModel):
    """
    Experimental Machine Learning Baseline using Scikit-Learn IsolationForest.
    Trained on multidimensional meteorological feature vectors.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        contamination: float = 0.05,
        random_state: int = 42,
        version: str = "1.0.0",
        training_dataset_id: Optional[str] = "SYNTHETIC_NWP_BENCHMARK_2025"
    ):
        self._n_estimators = n_estimators
        self._contamination = contamination
        self._random_state = random_state
        self._version = version
        self._training_dataset_id = training_dataset_id
        self._training_timestamp: Optional[str] = None
        self._model = IsolationForest(
            n_estimators=self._n_estimators,
            contamination=self._contamination,
            random_state=self._random_state,
            n_jobs=-1
        )
        self._is_fitted = False

    @property
    def model_id(self) -> str:
        return "isolation_forest_v1"

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "IsolationForestAnomalyModel":
        """
        Trains Isolation Forest on feature matrix X.
        Enforces feature dimension validation.
        """
        if X.ndim != 2 or X.shape[1] != len(FEATURE_COLUMNS):
            raise ValueError(
                f"Feature matrix dimension mismatch: expected (*, {len(FEATURE_COLUMNS)}), got {X.shape}"
            )
        
        self._model.fit(X)
        self._is_fitted = True
        self._training_timestamp = datetime.now(timezone.utc).isoformat()
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Returns binary anomaly labels: 1 for anomaly (outlier), 0 for normal inlier.
        """
        if not self._is_fitted:
            raise RuntimeError("IsolationForestAnomalyModel must be fitted before predict.")
        
        # Scikit-learn returns -1 for outlier, 1 for inlier
        raw_preds = self._model.predict(X)
        return np.where(raw_preds == -1, 1, 0)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """
        Computes continuous anomaly scores normalized to [0.0, 1.0].
        Lower decision_function values = more anomalous.
        """
        if not self._is_fitted:
            raise RuntimeError("IsolationForestAnomalyModel must be fitted before score_samples.")
        
        # decision_function: positive = normal, negative = anomaly
        df = self._model.decision_function(X)
        
        # Map decision function to [0.0, 1.0] using sigmoid-like scaling
        # Typical range of df is roughly [-0.4, 0.4]
        scores = 1.0 / (1.0 + np.exp(df * 8.0))
        return np.clip(scores, 0.0, 1.0)

    def save(self, filepath: str) -> None:
        """Saves model artifact and sidecar metadata JSON securely."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self._model, filepath)

        sidecar_path = filepath + ".meta.json"
        meta = {
            "model_id": self.model_id,
            "version": self._version,
            "n_estimators": self._n_estimators,
            "contamination": self._contamination,
            "random_state": self._random_state,
            "training_dataset_id": self._training_dataset_id,
            "training_timestamp": self._training_timestamp,
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "feature_columns": FEATURE_COLUMNS,
            "is_fitted": self._is_fitted,
        }
        with open(sidecar_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "IsolationForestAnomalyModel":
        """Safely loads model artifact and validates sidecar schema."""
        sidecar_path = filepath + ".meta.json"
        if not os.path.exists(sidecar_path):
            raise FileNotFoundError(f"Model sidecar metadata file not found at {sidecar_path}")
        
        with open(sidecar_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        if meta.get("feature_schema_version") != FEATURE_SCHEMA_VERSION:
            raise ValueError(
                f"Feature schema version mismatch: artifact has {meta.get('feature_schema_version')}, "
                f"system expects {FEATURE_SCHEMA_VERSION}"
            )

        instance = cls(
            n_estimators=meta.get("n_estimators", 100),
            contamination=meta.get("contamination", 0.05),
            random_state=meta.get("random_state", 42),
            version=meta.get("version", "1.0.0"),
            training_dataset_id=meta.get("training_dataset_id"),
        )
        instance._model = joblib.load(filepath)
        instance._is_fitted = meta.get("is_fitted", True)
        instance._training_timestamp = meta.get("training_timestamp")
        return instance

    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            model_id=self.model_id,
            model_name="Experimental Isolation Forest Baseline",
            version=self._version,
            model_type="ISOLATION_FOREST",
            status="EXPERIMENTAL_SYNTHETIC_BENCHMARK",
            feature_schema_version=FEATURE_SCHEMA_VERSION,
            training_dataset_id=self._training_dataset_id,
            training_timestamp=self._training_timestamp or "2026-09-27T00:00:00Z",
            random_seed=self._random_state,
            hyperparameters={
                "n_estimators": self._n_estimators,
                "contamination": self._contamination,
                "max_samples": "auto",
                "random_state": self._random_state,
            },
            is_operational=False,
            description=(
                "Unsupervised tree-based anomaly detector partitioning high-dimensional meteorological "
                "feature space. Trained on synthetic multi-variable perturbation grids."
            ),
            limitations=[
                "EXPERIMENTAL: Trained exclusively on controlled synthetic perturbation grids to validate ML pipeline integrity.",
                "DOES NOT PREDICT CYCLONES OR FUTURE DISASTERS. Produces diagnostic spatial anomaly flags only.",
                "Performance on synthetic data CANNOT be used as proof of operational skill on real NWP models.",
            ]
        )


class SpatiotemporalResearchModelStub(AnomalyModel):
    """
    Documented Architectural Extension Point for Future Spatiotemporal Deep Learning Models
    (e.g., ConvLSTM or 3D U-Net Spatial Segmentation).
    
    CRITICAL TRANSPARENCY RULE:
    Untrained neural networks are NOT used as operational detectors. This class documents
    input/output contracts, research roadmaps, and requirements for future phases.
    """

    @property
    def model_id(self) -> str:
        return "spatiotemporal_research_stub"

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "SpatiotemporalResearchModelStub":
        # Research extension point - fit is intentionally a documented no-op stub
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError(
            "Spatiotemporal deep learning model is a documented research extension point. "
            "Operational inference requires training on multi-year verified reanalysis grids (ERA5/IMD)."
        )

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError(
            "Spatiotemporal deep learning model is a documented research extension point."
        )

    def save(self, filepath: str) -> None:
        pass

    @classmethod
    def load(cls, filepath: str) -> "SpatiotemporalResearchModelStub":
        return cls()

    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            model_id=self.model_id,
            model_name="Spatiotemporal ConvLSTM / U-Net (Research Roadmap)",
            version="0.1.0-research",
            model_type="SPATIOTEMPORAL_RESEARCH",
            status="RESEARCH_ROADMAP",
            feature_schema_version=FEATURE_SCHEMA_VERSION,
            training_dataset_id="PENDING_ERA5_BENCHMARK",
            training_timestamp=None,
            random_seed=42,
            hyperparameters={
                "target_architecture": "Recurrent-Convolutional U-Net (ConvLSTM)",
                "input_tensor_contract": "(batch, timesteps=10, channels=4, height=96, width=161)",
                "output_tensor_contract": "(batch, timesteps=10, num_classes=5, height=96, width=161)",
                "loss_function": "Focal Tversky Loss (for extreme class imbalance)",
            },
            is_operational=False,
            description=(
                "Documented extension point and input/output contract for planned spatiotemporal "
                "segmentation models. Outlines requirements for multi-timestep spatial attention."
            ),
            limitations=[
                "NOT IMPLEMENTED AS AN OPERATIONAL DETECTOR in current phase.",
                "Requires verified multi-decade reanalysis labels (e.g. IMD Cyclone e-Atlas, ERA5 extremes).",
                "Significant GPU memory footprint (>16GB VRAM) required for full 4D spatiotemporal batch training.",
            ]
        )
