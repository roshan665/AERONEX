"""
Local File NWP Provider: Offline Loading of Bundled NetCDF4 and GRIB2 Fixtures
"""

import os
from typing import List, Dict, Any, Optional
from app.ingestion.providers.base import BaseNWPProvider
from app.ingestion.parser import NWPFileParser
from app.engine.schemas import WeatherGridDataset


class LocalFileProvider(BaseNWPProvider):
    """
    Offline data provider that loads NetCDF and GRIB files directly from disk
    without requiring external internet access.
    """

    def __init__(self, data_dir: str):
        super().__init__(
            provider_id="local_file",
            provider_name="Local Offline NWP Storage",
            cache_dir=data_dir
        )
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def discover_available_cycles(self) -> List[str]:
        cycles = []
        if not os.path.exists(self.data_dir):
            return cycles

        for f in os.listdir(self.data_dir):
            if f.endswith((".nc", ".nc4", ".grib2", ".grb2")):
                name = os.path.splitext(f)[0]
                cycles.append(name)
        return sorted(cycles)

    def fetch_dataset(
        self,
        cycle_date: str,
        cycle_hour: str,
        lead_time_hours: int,
        geographic_bounds: Optional[List[float]] = None,
        variables: Optional[List[str]] = None,
    ) -> str:
        # Search for matching file in local data dir
        if not os.path.exists(self.data_dir):
            raise FileNotFoundError(f"Local data directory does not exist: {self.data_dir}")

        files = os.listdir(self.data_dir)
        target_files = [f for f in files if f.endswith((".nc", ".nc4", ".grib2", ".grb2"))]

        if not target_files:
            raise FileNotFoundError(f"No NetCDF or GRIB2 files found in local storage: {self.data_dir}")

        # Prefer South Asia GFS sample if present
        for f in target_files:
            if "south_asia" in f or "gfs" in f:
                return os.path.join(self.data_dir, f)

        return os.path.join(self.data_dir, target_files[0])

    def parse_dataset(
        self,
        file_path: str,
        lead_time_hours: Optional[int] = None,
        dataset_id: Optional[str] = None
    ) -> WeatherGridDataset:
        return NWPFileParser.parse_file(file_path, lead_time_hours, dataset_id)
