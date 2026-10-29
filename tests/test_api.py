"""
tests/test_api.py
-----------------
Integration unit tests for FastAPI endpoints using TestClient.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ml-service')))

from app import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "UP"
    assert "frameworks" in data

def test_dataset_summary_endpoint():
    res = client.get("/api/datasets/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_rows" in data
    assert "buildings" in data
    assert data["total_rows"] > 0

def test_dataset_quality_endpoint():
    res = client.get("/api/datasets/quality")
    assert res.status_code == 200
    data = res.json()
    assert "data_completeness_pct" in data
    assert "labeled_anomalies_count" in data

def test_eda_summary_endpoint():
    res = client.get("/api/eda/summary")
    assert res.status_code == 200
    data = res.json()
    assert "diurnal_profile" in data
    assert "correlations" in data

def test_models_metrics_endpoint():
    res = client.get("/api/models/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "models" in data or "recent_runs" in data

def test_forecast_endpoint_and_history():
    payload = {
        "building_id": "Office_A",
        "model_name": "seasonal_naive",
        "horizon_hours": 24
    }
    res = client.post("/api/forecast", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["horizon_hours"] == 24
    assert len(data["forecast"]) == 24
    uuid_str = data["forecast_uuid"]

    # Test history endpoint
    h_res = client.get("/api/forecast/history")
    assert h_res.status_code == 200
    history = h_res.json()
    assert any(item["forecast_uuid"] == uuid_str for item in history)

    # Test CSV download endpoint
    dl_res = client.get(f"/api/forecast/{uuid_str}/download")
    assert dl_res.status_code == 200
    assert "predicted_kWh" in dl_res.text
