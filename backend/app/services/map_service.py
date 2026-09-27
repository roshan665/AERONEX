"""
Map Service for Rendering GeoJSON (RFC 7946) Vectors & Leaflet Layer Descriptors
"""

from typing import Dict, Any, List
from app.data.demo_data import MAP_LAYERS, ANOMALIES_CATALOG, SYSTEM_METADATA
from app.models.map import (
    MapLayersResponse, 
    MapLayerDescriptor, 
    GeoJsonFeatureCollection, 
    GeoJsonFeature, 
    GeoJsonGeometry
)


class MapService:
    @staticmethod
    def get_map_layers() -> MapLayersResponse:
        layers = [MapLayerDescriptor(**l) for l in MAP_LAYERS]

        # 1. Anomaly Footprints FeatureCollection (Polygon)
        # Note: GeoJSON requires [Longitude, Latitude] ordering!
        anomaly_features: List[GeoJsonFeature] = []
        for a in ANOMALIES_CATALOG:
            # Convert [Lat, Lon] pairs from data to GeoJSON [Lon, Lat]
            geojson_ring = [[coord[1], coord[0]] for coord in a["footprint_polygon"]]
            
            # Ensure closed ring
            if geojson_ring[0] != geojson_ring[-1]:
                geojson_ring.append(geojson_ring[0])

            feature = GeoJsonFeature(
                type="Feature",
                id=a["id"],
                geometry=GeoJsonGeometry(
                    type="Polygon",
                    coordinates=[geojson_ring]
                ),
                properties={
                    "event_id": a["id"],
                    "name": a["name"],
                    "hazard_type": a["type"],
                    "category_key": a["category_key"],
                    "severity": a["severity"],
                    "severity_level": a["severity_level"],
                    "color": a["color"],
                    "region": a["region"],
                    "estimated_area": a["estimated_area"],
                    "estimated_area_km2": a["estimated_area_km2"],
                    "max_wind": a["max_wind"],
                    "central_pressure": a["central_pressure"],
                    "anomaly_score": a["anomaly_score"],
                    "centroid": [a["lon"], a["lat"]],  # [Lon, Lat]
                    "forecast_window": a["forecast_window"],
                    "is_simulated": True,
                }
            )
            anomaly_features.append(feature)

        anomalies_fc = GeoJsonFeatureCollection(
            type="FeatureCollection",
            metadata={
                "dataset": SYSTEM_METADATA["data_provenance"],
                "total_features": len(anomaly_features),
                "crs": "EPSG:4326",
                "valid_time": SYSTEM_METADATA["latest_data_timestamp"],
                "is_simulated": True,
            },
            features=anomaly_features
        )

        # 2. Forecast Trajectory Tracks FeatureCollection (LineString)
        track_features: List[GeoJsonFeature] = []
        for a in ANOMALIES_CATALOG:
            if a.get("forecast_track"):
                track_coords = [[coord[1], coord[0]] for coord in a["forecast_track"]]
                track_feature = GeoJsonFeature(
                    type="Feature",
                    id=f"{a['id']}-track",
                    geometry=GeoJsonGeometry(
                        type="LineString",
                        coordinates=track_coords
                    ),
                    properties={
                        "event_id": a["id"],
                        "name": f"{a['name']} Forecast Track",
                        "color": a["color"],
                        "severity": a["severity"],
                        "forecast_window": a["forecast_window"],
                        "is_simulated": True,
                    }
                )
                track_features.append(track_feature)

        tracks_fc = GeoJsonFeatureCollection(
            type="FeatureCollection",
            metadata={
                "dataset": SYSTEM_METADATA["data_provenance"],
                "total_tracks": len(track_features),
                "crs": "EPSG:4326",
                "is_simulated": True,
            },
            features=track_features
        )

        return MapLayersResponse(
            available_layers=layers,
            anomalies_geojson=anomalies_fc,
            tracks_geojson=tracks_fc,
            geojson=anomalies_fc,
            data_provenance=SYSTEM_METADATA["data_provenance"],
            is_simulated=True,
        )
