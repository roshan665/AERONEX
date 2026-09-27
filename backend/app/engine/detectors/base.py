"""
Base Detector Protocol for Weather Anomaly Identification
"""

from abc import ABC, abstractmethod
from typing import List
import numpy as np
from app.engine.schemas import NormalizedWeatherGrid, DetectionResult
from app.engine.config import DetectorThresholds


class BaseAnomalyDetector(ABC):
    def __init__(self, thresholds: DetectorThresholds):
        self.thresholds = thresholds

    @abstractmethod
    def detect(self, grid: NormalizedWeatherGrid) -> List[DetectionResult]:
        """
        Evaluate normalized meteorological arrays and return a list of detection results.
        """
        pass

    @staticmethod
    def compute_zscore(observed: np.ndarray, mean: np.ndarray, std: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
        """
        Computes standardized score: Z = (X - μ) / max(σ, ε)
        Safely handles near-zero standard deviation and NaN values.
        """
        safe_std = np.where(std < epsilon, epsilon, std)
        z = (observed - mean) / safe_std
        # Zero out where std was negligible to avoid spurious extreme z-scores
        z = np.where(std < epsilon, 0.0, z)
        return z
