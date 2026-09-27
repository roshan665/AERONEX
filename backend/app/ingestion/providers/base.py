"""
Abstract Base Provider for Numerical Weather Prediction (NWP) Data Sources
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.engine.schemas import WeatherGridDataset


class BaseNWPProvider(ABC):
    """
    Abstract interface separating discovery, retrieval, caching, and parsing.
    """

    def __init__(self, provider_id: str, provider_name: str, cache_dir: str):
        self.provider_id = provider_id
        self.provider_name = provider_name
        self.cache_dir = cache_dir

    @abstractmethod
    def discover_available_cycles(self) -> List[str]:
        """Discovers available model initialization cycles (e.g. ['20260926_00', '20260926_06'])."""
        pass

    @abstractmethod
    def fetch_dataset(
        self,
        cycle_date: str,
        cycle_hour: str,
        lead_time_hours: int,
        geographic_bounds: Optional[List[float]] = None,
        variables: Optional[List[str]] = None,
    ) -> str:
        """Retrieves or locates the requested dataset, saving to local cache, returning file path."""
        pass

    @abstractmethod
    def parse_dataset(
        self,
        file_path: str,
        lead_time_hours: Optional[int] = None,
        dataset_id: Optional[str] = None
    ) -> WeatherGridDataset:
        """Parses the downloaded/cached file into standardized WeatherGridDataset."""
        pass
