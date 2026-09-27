"""
Overview Service for Dashboard Situation Analysis
"""

from typing import Dict, Any, List
from app.data.demo_data import (
    SYSTEM_METADATA, 
    REGIONS_CATALOG, 
    ANOMALIES_CATALOG
)
from app.models.overview import (
    OverviewResponse, 
    OverviewSummary, 
    DashboardCard, 
    SeverityItem, 
    CriticalAlertItem
)


class OverviewService:
    @staticmethod
    def get_overview(region_id: str = None) -> OverviewResponse:
        anomalies = ANOMALIES_CATALOG
        if region_id:
            anomalies = [a for a in anomalies if a["region"].lower().replace(" ", "_") == region_id.lower()]

        active_count = len(anomalies)
        critical_count = sum(1 for a in anomalies if a["severity"] == "High")
        regions_count = len(REGIONS_CATALOG)

        # Hazard breakdown
        hazard_breakdown = {
            "cyclones": sum(1 for a in anomalies if a["category_key"] == "cyclone"),
            "heat_domes": sum(1 for a in anomalies if a["category_key"] == "heat_wave"),
            "cold_waves": sum(1 for a in anomalies if a["category_key"] == "cold_wave"),
            "wind_anomalies": sum(1 for a in anomalies if a["category_key"] == "wind_anomaly"),
            "pressure_anomalies": sum(1 for a in anomalies if a["category_key"] == "pressure_anomaly"),
        }

        # Severity distribution
        high_cnt = sum(1 for a in anomalies if a["severity"] == "High")
        med_cnt = sum(1 for a in anomalies if a["severity"] == "Medium")
        low_cnt = sum(1 for a in anomalies if a["severity"] == "Low")
        total = max(1, active_count)

        severity_distribution = [
            SeverityItem(name="High", value=high_cnt, percentage=round((high_cnt / total) * 100, 1), color="#ef4444"),
            SeverityItem(name="Medium", value=med_cnt, percentage=round((med_cnt / total) * 100, 1), color="#f59e0b"),
            SeverityItem(name="Low", value=low_cnt, percentage=round((low_cnt / total) * 100, 1), color="#3b82f6"),
        ]

        # Dashboard cards matching frontend format
        dashboard_cards = [
            DashboardCard(
                id="active-anomalies",
                title="Active Anomalies",
                value=str(active_count),
                subtext="2 from last 24h",
                trend="up",
                icon="AlertTriangle",
                color="red",
                badge_color="bg-red-500/10 text-red-400 border-red-500/20",
                glow_color="rgba(239, 68, 68, 0.15)",
            ),
            DashboardCard(
                id="regions-monitored",
                title="Regions Monitored",
                value=str(regions_count),
                subtext="Global Coverage",
                trend="neutral",
                icon="MapPin",
                color="blue",
                badge_color="bg-blue-500/10 text-blue-400 border-blue-500/20",
                glow_color="rgba(59, 130, 246, 0.15)",
            ),
            DashboardCard(
                id="forecast-horizon",
                title="Forecast Horizon",
                value=f"{SYSTEM_METADATA['forecast_range_days']} Days",
                subtext="Day 1 – Day 10",
                trend="neutral",
                icon="Calendar",
                color="green",
                badge_color="bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
                glow_color="rgba(16, 185, 129, 0.15)",
            ),
            DashboardCard(
                id="latest-data",
                title="Latest Data",
                value="Apr 26, 2025 14:00 UTC",
                subtext=SYSTEM_METADATA["data_source_label"],
                trend="neutral",
                icon="Clock",
                color="purple",
                badge_color="bg-purple-500/10 text-purple-400 border-purple-500/20",
                glow_color="rgba(168, 85, 247, 0.15)",
            ),
        ]

        # Critical alerts summary
        critical_alerts = [
            CriticalAlertItem(
                event_id=a["id"],
                name=a["name"],
                hazard_type=a["type"],
                severity=a["severity"],
                region=a["region"],
                centroid=[a["lat"], a["lon"]],
                peak_intensity=a["max_wind"] if "Cyclone" in a["type"] or "Wind" in a["type"] else a["central_pressure"],
                lead_time_days=a["forecast_window"],
                updated_ago=a["updated_ago"],
            )
            for a in anomalies[:5]
        ]

        summary = OverviewSummary(
            active_anomaly_count=active_count,
            critical_alerts_count=critical_count,
            regions_monitored_count=regions_count,
            forecast_horizon_days=SYSTEM_METADATA["forecast_range_days"],
            forecast_horizon_hours=SYSTEM_METADATA["forecast_range_hours"],
            latest_model_run=SYSTEM_METADATA["latest_data_timestamp"],
            data_provenance=SYSTEM_METADATA["data_provenance"],
            is_simulated=True,
            disclaimer=SYSTEM_METADATA["disclaimer"],
        )

        return OverviewResponse(
            summary=summary,
            dashboard_cards=dashboard_cards,
            hazard_breakdown=hazard_breakdown,
            severity_distribution=severity_distribution,
            critical_alerts=critical_alerts,
        )
