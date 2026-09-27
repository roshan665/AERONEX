"""
NOAA GFS Data Provider: Live Subregion GRIB2 Retrieval via NCEP NOMADS Filter API
"""

import os
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx

from app.ingestion.providers.base import BaseNWPProvider
from app.ingestion.parser import NWPFileParser
from app.engine.schemas import WeatherGridDataset
from app.core.logging import logger


class NOAAGFSProvider(BaseNWPProvider):
    """
    Live NOAA NCEP GFS 0.25° operational forecast provider.
    Uses the official NOMADS GRIB Filter service to request exact variable
    and geographic spatial subsets over HTTP without transferring full global volumes.
    """

    NOMADS_FILTER_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"
    NOMADS_PROD_DIR = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/"

    def __init__(self, cache_dir: str):
        super().__init__(
            provider_id="noaa_gfs",
            provider_name="NOAA NCEP Global Forecast System (GFS 0.25°)",
            cache_dir=cache_dir
        )
        os.makedirs(self.cache_dir, exist_ok=True)

    def discover_available_cycles(self) -> List[str]:
        """Discovers active model run directories on NOMADS."""
        try:
            r = httpx.get(self.NOMADS_PROD_DIR, timeout=8.0)
            if r.status_code != 200:
                logger.warning(f"NOMADS directory probe returned HTTP {r.status_code}")
                return []

            dates = []
            for line in r.text.split("\n"):
                if 'href="gfs.' in line:
                    date_part = line.split('href="gfs.')[1].split('/"')[0].strip()
                    if date_part.isdigit() and len(date_part) == 8:
                        dates.append(date_part)

            cycles = []
            for d in sorted(dates, reverse=True)[:3]:
                for h in ["00", "06", "12", "18"]:
                    cycles.append(f"{d}_{h}Z")
            return cycles
        except Exception as e:
            logger.warning(f"Unable to discover live NOMADS GFS cycles: {str(e)}")
            return []

    def fetch_dataset(
        self,
        cycle_date: str,
        cycle_hour: str,
        lead_time_hours: int = 24,
        geographic_bounds: Optional[List[float]] = None,
        variables: Optional[List[str]] = None,
    ) -> str:
        """
        Subsets and downloads target variables and bounding box from NOMADS GRIB Filter.
        """
        # Default to South Asia domain if no bounds specified
        # Bounds format: [min_lat, max_lat, min_lon, max_lon]
        if geographic_bounds and len(geographic_bounds) == 4:
            min_lat, max_lat, min_lon, max_lon = geographic_bounds
        else:
            min_lat, max_lat, min_lon, max_lon = 8.0, 38.0, 65.0, 95.0

        # Build cache file name based on query signature
        lead_str = f"f{lead_time_hours:03d}"
        cache_key = f"gfs_{cycle_date}_{cycle_hour}_{lead_str}_{min_lat}_{max_lat}_{min_lon}_{max_lon}"
        cache_filename = f"{cache_key}.grib2"
        cached_path = os.path.join(self.cache_dir, cache_filename)

        if os.path.exists(cached_path) and os.path.getsize(cached_path) > 100:
            logger.info(f"Reusing cached GFS dataset from: {cached_path}")
            return cached_path

        # Construct official NOMADS GRIB Filter parameters
        file_name = f"gfs.t{cycle_hour}z.pgrb2.0p25.{lead_str}"
        dir_param = f"/gfs.{cycle_date}/{cycle_hour}/atmos"

        params: Dict[str, str] = {
            "file": file_name,
            "dir": dir_param,
            "subregion": "on",
            "bottomlat": str(int(min_lat)),
            "toplat": str(int(max_lat)),
            "leftlon": str(int(min_lon)),
            "rightlon": str(int(max_lon)),
        }

        # Request standard core surface variables
        params["var_TMP"] = "on"
        params["lev_2_m_above_ground"] = "on"
        params["var_UGRD"] = "on"
        params["var_VGRD"] = "on"
        params["lev_10_m_above_ground"] = "on"
        params["var_PRMSL"] = "on"
        params["lev_mean_sea_level"] = "on"

        logger.info(f"Submitting query to NOAA NOMADS GRIB Filter for {file_name}...")

        try:
            with httpx.Client(timeout=25.0) as client:
                response = client.get(self.NOMADS_FILTER_URL, params=params)

            if response.status_code != 200:
                raise RuntimeError(
                    f"NOMADS server returned HTTP {response.status_code}: {response.text[:200]}"
                )

            content = response.content
            if len(content) < 16 or content[:4] != b"GRIB":
                raise ValueError(
                    f"NOMADS response did not contain a valid GRIB2 header. Received: {response.text[:300]}"
                )

            with open(cached_path, "wb") as f:
                f.write(content)

            logger.info(
                f"Successfully downloaded and cached NOAA GFS subset: {len(content)} bytes to {cached_path}"
            )
            return cached_path

        except Exception as e:
            logger.error(f"Failed to fetch live dataset from NOAA NOMADS: {str(e)}")
            raise

    def parse_dataset(
        self,
        file_path: str,
        lead_time_hours: Optional[int] = None,
        dataset_id: Optional[str] = None
    ) -> WeatherGridDataset:
        return NWPFileParser.parse_file(file_path, lead_time_hours, dataset_id or "noaa_gfs_live")
