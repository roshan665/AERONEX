"""
Common Anomaly Model Interface Protocol for AeroNex AI/ML Models
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
import numpy as np

from app.ml.schemas import ModelMetadata


class AnomalyModel(ABC):
    """
    Abstract interface protocol unifying deterministic baselines, unsupervised ML models,
    and future spatiotemporal neural architectures under a single contract.
    """

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Unique model identifier, e.g. 'deterministic_baseline' or 'isolation_forest_v1'."""
        pass

    @abstractmethod
    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "AnomalyModel":
        """
        Fits or initializes the model.
        X: Feature matrix of shape (N_samples, N_features).
        y: Optional reference labels for supervised evaluation (None for unsupervised).
        """
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predicts binary anomaly indicators.
        Returns: 1D boolean/int array of length N_samples (1 = anomalous, 0 = normal).
        """
        pass

    @abstractmethod
    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """
        Computes continuous anomaly severity scores on [0.0, 1.0].
        Higher values indicate stronger anomaly deviation.
        """
        pass

    @abstractmethod
    def save(self, filepath: str) -> None:
        """Serializes model weights / parameters to a secure file path."""
        pass

    @classmethod
    @abstractmethod
    def load(cls, filepath: str) -> "AnomalyModel":
        """Deserializes a validated model artifact from a secure file path."""
        pass

    @abstractmethod
    def metadata(self) -> ModelMetadata:
        """Returns structured metadata including version, feature schema, hyperparameters, and caveats."""
        pass
