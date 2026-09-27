"""
Model Registry & Lifecycle Manager for AeroNex AI/ML Models
"""

import os
from typing import Dict, List, Optional
from datetime import datetime, timezone

from app.core.logging import logger
from app.ml.interfaces import AnomalyModel
from app.ml.models import (
    DeterministicBaselineModel,
    IsolationForestAnomalyModel,
    SpatiotemporalResearchModelStub
)
from app.ml.schemas import ModelMetadata, ModelListResponse
from app.ml.features import FeatureExtractor
from app.engine.synthetic_generator import SyntheticWeatherGenerator
from app.engine.preprocessor import GridPreprocessor


class ModelRegistry:
    """
    Central repository for model lifecycle management, configuration-based selection,
    and safe artifact loading.
    """

    _instance: Optional["ModelRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelRegistry, cls).__new__(cls)
            cls._instance._models: Dict[str, AnomalyModel] = {}
            cls._instance._active_model_id: str = "deterministic_baseline"
            cls._instance._artifacts_dir: str = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data",
                "models"
            )
            cls._instance._initialize_registry()
        return cls._instance

    def _initialize_registry(self) -> None:
        """Initializes default models and ensures experimental baseline is trained."""
        os.makedirs(self._artifacts_dir, exist_ok=True)

        # 1. Deterministic Baseline (Operational Fallback)
        deterministic = DeterministicBaselineModel()
        det_path = os.path.join(self._artifacts_dir, "deterministic_baseline.json")
        deterministic.save(det_path)
        self._models[deterministic.model_id] = deterministic

        # 2. Experimental Isolation Forest Baseline
        if_path = os.path.join(self._artifacts_dir, "isolation_forest_v1.joblib")
        if os.path.exists(if_path) and os.path.exists(if_path + ".meta.json"):
            try:
                iso_forest = IsolationForestAnomalyModel.load(if_path)
                self._models[iso_forest.model_id] = iso_forest
                logger.info("Loaded pre-trained Isolation Forest artifact from registry storage.")
            except Exception as e:
                logger.warning(f"Failed loading cached model: {e}. Re-training experimental baseline.")
                iso_forest = self._train_experimental_baseline(if_path)
                self._models[iso_forest.model_id] = iso_forest
        else:
            iso_forest = self._train_experimental_baseline(if_path)
            self._models[iso_forest.model_id] = iso_forest

        # 3. Spatiotemporal Research Extension Point Stub
        research_stub = SpatiotemporalResearchModelStub()
        self._models[research_stub.model_id] = research_stub

    def _train_experimental_baseline(self, save_path: str) -> IsolationForestAnomalyModel:
        """
        Trains Isolation Forest on synthetic demonstration grids.
        Strictly labeled as an experimental demonstration baseline.
        """
        logger.info("Training Isolation Forest on synthetic benchmark perturbation fields...")
        dataset, _ = SyntheticWeatherGenerator.generate_dataset(lead_time_hours=24, seed=42)
        grid = GridPreprocessor.preprocess(dataset)
        X, _ = FeatureExtractor.extract_tabular_features(grid)

        model = IsolationForestAnomalyModel(
            n_estimators=100,
            contamination=0.06,
            random_state=42,
            training_dataset_id="SYNTHETIC_NWP_BENCHMARK_2025"
        )
        model.fit(X)
        model.save(save_path)
        logger.info(f"Trained and saved Isolation Forest baseline ({X.shape[0]} samples) to {save_path}")
        return model

    def list_models(self) -> ModelListResponse:
        """Returns metadata for all registered models."""
        models_meta = [m.metadata() for m in self._models.values()]
        return ModelListResponse(
            models=models_meta,
            active_model_id=self._active_model_id,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def get_model(self, model_id: str) -> Optional[AnomalyModel]:
        return self._models.get(model_id)

    def get_active_model(self) -> AnomalyModel:
        return self._models[self._active_model_id]

    def set_active_model(self, model_id: str) -> ModelMetadata:
        if model_id not in self._models:
            raise KeyError(f"Model ID '{model_id}' not found in registry. Available: {list(self._models.keys())}")
        
        target = self._models[model_id]
        if target.metadata().status == "RESEARCH_ROADMAP":
            raise ValueError(
                f"Model '{model_id}' is a research roadmap extension point and cannot be selected for operational inference."
            )
        
        self._active_model_id = model_id
        logger.info(f"Active anomaly model switched to: {model_id}")
        return target.metadata()


model_registry = ModelRegistry()
