"""
Unit Tests for AI/ML Feature Pipeline, Model Interfaces, Registry, and Serialization
"""

import os
import tempfile
import pytest
import numpy as np

from app.ml.features import (
    FeatureExtractor,
    FEATURE_COLUMNS,
    FEATURE_SCHEMA_VERSION,
)
from app.ml.models import (
    DeterministicBaselineModel,
    IsolationForestAnomalyModel,
    SpatiotemporalResearchModelStub,
)
from app.ml.registry import ModelRegistry, model_registry
from app.engine.synthetic_generator import SyntheticWeatherGenerator
from app.engine.preprocessor import GridPreprocessor


def test_feature_extractor_schema_and_column_order():
    schema = FeatureExtractor.get_feature_schema()
    assert schema.version == FEATURE_SCHEMA_VERSION
    assert schema.feature_names == FEATURE_COLUMNS
    assert len(schema.features_metadata) == len(FEATURE_COLUMNS)

    # Validate that absolute geographic coordinates are not in primary feature columns
    assert "lat" not in schema.feature_names
    assert "latitude" not in schema.feature_names
    assert "lon" not in schema.feature_names
    assert "longitude" not in schema.feature_names


def test_feature_tensor_extraction():
    dataset, _ = SyntheticWeatherGenerator.generate_dataset(lead_time_hours=24, seed=42)
    grid = GridPreprocessor.preprocess(dataset)

    tensor = FeatureExtractor.extract_grid_feature_tensor(grid)
    assert tensor.shape == (grid.shape[0], grid.shape[1], len(FEATURE_COLUMNS))
    assert not np.any(np.isnan(tensor))

    X, coords = FeatureExtractor.extract_tabular_features(grid)
    assert X.shape[1] == len(FEATURE_COLUMNS)
    assert len(coords) == X.shape[0]


def test_deterministic_baseline_model():
    model = DeterministicBaselineModel()
    assert model.model_id == "deterministic_baseline"
    
    meta = model.metadata()
    assert meta.model_type == "DETERMINISTIC_RULES"
    assert meta.is_operational is True
    assert meta.status == "OPERATIONAL_BASELINE"

    # Test synthetic features: 2 samples, one normal, one extreme anomaly
    X = np.zeros((2, len(FEATURE_COLUMNS)), dtype=np.float32)
    X[1, 0] = 4.5  # Extreme temperature anomaly
    X[1, 1] = 4.2  # Extreme wind anomaly

    preds = model.predict(X)
    assert preds[0] == 0
    assert preds[1] == 1

    scores = model.score_samples(X)
    assert 0.0 <= scores[0] < 0.1
    assert scores[1] > 0.8

    # Save & reload
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        model.save(tmp_path)
        reloaded = DeterministicBaselineModel.load(tmp_path)
        assert reloaded.model_id == model.model_id
        np.testing.assert_array_equal(reloaded.predict(X), preds)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_isolation_forest_model_pipeline():
    # Generate small training matrix
    rng = np.random.RandomState(42)
    X_train = rng.normal(0, 1, size=(200, len(FEATURE_COLUMNS))).astype(np.float32)
    # Inject a few outliers
    X_train[-5:, 0] = 5.0
    X_train[-5:, 1] = 6.0

    model = IsolationForestAnomalyModel(n_estimators=30, contamination=0.05, random_state=42)
    assert model.model_id == "isolation_forest_v1"
    
    # Must fail predict before fit
    with pytest.raises(RuntimeError):
        model.predict(X_train[:10])

    model.fit(X_train)
    preds = model.predict(X_train)
    assert len(preds) == len(X_train)
    assert set(preds).issubset({0, 1})

    scores = model.score_samples(X_train)
    assert len(scores) == len(X_train)
    assert np.all((scores >= 0.0) & (scores <= 1.0))

    meta = model.metadata()
    assert meta.model_type == "ISOLATION_FOREST"
    assert meta.status == "EXPERIMENTAL_SYNTHETIC_BENCHMARK"
    assert meta.is_operational is False  # Explicitly labeled experimental!

    # Save and reload
    with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        model.save(tmp_path)
        reloaded = IsolationForestAnomalyModel.load(tmp_path)
        assert reloaded.model_id == model.model_id
        np.testing.assert_array_equal(reloaded.predict(X_train[:20]), preds[:20])
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if os.path.exists(tmp_path + ".meta.json"):
            os.remove(tmp_path + ".meta.json")


def test_spatiotemporal_research_stub():
    stub = SpatiotemporalResearchModelStub()
    assert stub.model_id == "spatiotemporal_research_stub"
    meta = stub.metadata()
    assert meta.status == "RESEARCH_ROADMAP"
    assert meta.is_operational is False

    with pytest.raises(NotImplementedError):
        stub.predict(np.zeros((5, len(FEATURE_COLUMNS))))


def test_model_registry_lifecycle():
    registry = ModelRegistry()
    list_res = registry.list_models()
    assert len(list_res.models) >= 3
    assert list_res.active_model_id == "deterministic_baseline"

    # Switch to isolation forest
    updated_meta = registry.set_active_model("isolation_forest_v1")
    assert updated_meta.model_id == "isolation_forest_v1"
    assert registry.get_active_model().model_id == "isolation_forest_v1"

    # Attempt switching to research stub must raise ValueError
    with pytest.raises(ValueError):
        registry.set_active_model("spatiotemporal_research_stub")

    # Attempt switching to nonexistent model must raise KeyError
    with pytest.raises(KeyError):
        registry.set_active_model("nonexistent_deep_net")

    # Revert back to operational baseline
    registry.set_active_model("deterministic_baseline")
    assert registry.get_active_model().model_id == "deterministic_baseline"
