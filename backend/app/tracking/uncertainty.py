"""
Forecast Uncertainty Service: Ensemble Spread & Deterministic Decay Fallback
"""

from typing import Optional, List, Dict, Any
from app.tracking.models import (
    UncertaintySummaryResponse,
    EventUncertaintyDetail,
    UncertaintyLeadTimeBand
)
from app.tracking.scenarios import (
    STANDARD_LEAD_TIME_DECAY,
    build_synthetic_ensemble_scenario
)


class UncertaintyService:
    """
    Computes forecast uncertainty metrics when ensemble data exists,
    and provides rigorous deterministic fallback guidelines when ensemble spread is unavailable.
    """

    @classmethod
    def get_summary(
        cls,
        dataset_id: Optional[str] = None,
        force_mode: Optional[str] = None
    ) -> UncertaintySummaryResponse:
        """
        Reports system-wide uncertainty capabilities and active mode.
        """
        is_ensemble = force_mode == "ensemble" or dataset_id == "synthetic_ensemble_demo"

        if is_ensemble:
            return UncertaintySummaryResponse(
                uncertainty_mode="ENSEMBLE_MEMBERS",
                is_available=True,
                ensemble_members_count=5,
                primary_provider="AeroNex Synthetic Multi-Member Generator",
                message=(
                    "Ensemble variance and spatial centroid dispersion available across 5 reproducible "
                    "perturbed forecast members."
                ),
                lead_time_decay=STANDARD_LEAD_TIME_DECAY,
                known_limitations=[
                    "Synthetic ensemble members are perturbed demonstrations; they do not represent operational GEFS 31-member runs.",
                    "Member agreement decays beyond Day 4 due to divergent track trajectories."
                ]
            )

        # Standard Deterministic Fallback (NOAA GFS operational & prototype default)
        return UncertaintySummaryResponse(
            uncertainty_mode="DETERMINISTIC_ONLY",
            is_available=False,
            ensemble_members_count=1,
            primary_provider="NOAA NCEP GFS 0.25° (Deterministic Operational Run)",
            message=(
                "Ensemble spread is unavailable for single-member deterministic NWP forecasts. "
                "Predictability inherently decays with forecast lead time; confidence is evaluated using "
                "standardized synoptic error growth bands rather than fabricated ensemble variance."
            ),
            lead_time_decay=STANDARD_LEAD_TIME_DECAY,
            known_limitations=[
                "Single-run deterministic forecasts produce an individual deterministic trajectory without ensemble variance.",
                "Fixed physical thresholds do not quantify probabilistic risk or climatological return periods.",
                "Atmospheric predictability decays rapidly beyond Day 5 (120h lead time) due to non-linear chaos."
            ]
        )

    @classmethod
    def get_event_uncertainty(cls, event_or_track_id: str) -> EventUncertaintyDetail:
        """
        Retrieves uncertainty profile for an individual event or track.
        """
        normalized_id = event_or_track_id.lower().replace("-", "_")

        # The Cyclone event has an associated reproducible 5-member synthetic demonstration
        if "evt_001" in normalized_id or "trk_cyc" in normalized_id or "cyclone" in normalized_id:
            return build_synthetic_ensemble_scenario()

        # Deterministic Fallback for all other events
        return EventUncertaintyDetail(
            event_id=event_or_track_id,
            track_id=event_or_track_id if event_or_track_id.startswith("TRK-") else None,
            uncertainty_mode="DETERMINISTIC_ONLY",
            is_available=False,
            ensemble_members_count=1,
            daily_spread=[],
            lead_time_decay=STANDARD_LEAD_TIME_DECAY,
            methodology_notes=(
                "DETERMINISTIC FORECAST: Ensemble spread is unavailable for this event. "
                "Confidence bounds are governed by lead-time skill decay guidelines."
            ),
            known_limitations=[
                "Deterministic model output cannot provide true probabilistic ensemble spread.",
                "Footprint boundaries reflect single-model threshold crossings, not ensemble probability envelopes."
            ]
        )
