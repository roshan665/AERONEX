"""
Pydantic Models for Dashboard Overview API
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class DashboardCard(BaseModel):
    id: str
    title: str
    value: str
    subtext: str
    trend: str
    icon: str
    color: str
    badge_color: str
    glow_color: str


class CriticalAlertItem(BaseModel):
    event_id: str
    name: str
    hazard_type: str
    severity: str
    region: str
    centroid: List[float] = Field(..., description="[Latitude, Longitude]")
    peak_intensity: str
    lead_time_days: str
    updated_ago: str


class OverviewSummary(BaseModel):
    active_anomaly_count: int
    critical_alerts_count: int
    regions_monitored_count: int
    forecast_horizon_days: int
    forecast_horizon_hours: int
    latest_model_run: str
    data_provenance: str
    is_simulated: bool = True
    disclaimer: str


class SeverityItem(BaseModel):
    name: str
    value: int
    percentage: float
    color: str


class OverviewResponse(BaseModel):
    summary: OverviewSummary
    dashboard_cards: List[DashboardCard]
    hazard_breakdown: Dict[str, int]
    severity_distribution: List[SeverityItem]
    critical_alerts: List[CriticalAlertItem]
