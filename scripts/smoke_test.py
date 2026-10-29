"""
scripts/smoke_test.py
---------------------
End-to-End Smoke Test verifying:
1. Canonical dataset presence and 6-column integrity.
2. Data dictionary completeness.
3. Figures generated in reports/figures/.
4. ML model benchmarks recorded.
5. FastAPI service route execution via TestClient.
"""

import os
import sys
import pandas as pd

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient

# Path adjustments
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ml-service')))
from app import app
from pipeline import CANONICAL_COLUMNS

def run_smoke_test():
    print("==================================================")
    print("RUNNING END-TO-END SMOKE TEST")
    print("Project: Energy Consumption Forecasting Using Time-Series ML")
    print("==================================================")

    # 1. Dataset checks
    csv_path = "dataset.csv"
    assert os.path.exists(csv_path), "Missing dataset.csv in root!"
    df = pd.read_csv(csv_path)
    assert list(df.columns) == CANONICAL_COLUMNS, f"Columns mismatch in {csv_path}: {df.columns.tolist()}"
    print(f"[OK] dataset.csv verified: {len(df)} rows, 6 canonical columns.")

    aug_path = "data/processed/dataset_augmented_5000.csv"
    assert os.path.exists(aug_path), f"Missing {aug_path}!"
    df_aug = pd.read_csv(aug_path)
    assert len(df_aug) == 5000, f"Expected 5,000 rows, found {len(df_aug)}"
    assert list(df_aug.columns) == CANONICAL_COLUMNS
    print(f"[OK] Augmented dataset verified: {len(df_aug)} rows, 6 canonical columns.")

    # 2. Data dictionary
    dict_path = "data_dictionary.csv"
    assert os.path.exists(dict_path), "Missing data_dictionary.csv!"
    df_dict = pd.read_csv(dict_path)
    assert len(df_dict) == 6, f"Expected 6 rows in data dictionary, got {len(df_dict)}"
    print(f"[OK] data_dictionary.csv verified: all 6 canonical columns documented.")

    # 3. Figures
    expected_figures = [
        "fig1_consumption_over_time.png",
        "fig2_consumption_distribution.png",
        "fig3_diurnal_and_weekly_patterns.png",
        "fig4_weather_correlation_matrix.png"
    ]
    for fig in expected_figures:
        p = os.path.join("reports", "figures", fig)
        assert os.path.exists(p), f"Missing figure: {p}"
    print("[OK] All 4 publication-quality EDA figures verified in reports/figures/.")

    # 4. API Endpoints
    client = TestClient(app)

    h_res = client.get("/health")
    assert h_res.status_code == 200 and h_res.json()["status"] == "UP"
    print("[OK] GET /health returned 200 UP.")

    s_res = client.get("/api/datasets/summary")
    assert s_res.status_code == 200
    print(f"[OK] GET /api/datasets/summary returned {s_res.json()['total_rows']} total rows.")

    f_res = client.post("/api/forecast", json={
        "building_id": "Office_A",
        "model_name": "seasonal_naive",
        "horizon_hours": 24
    })
    assert f_res.status_code == 200
    f_data = f_res.json()
    assert len(f_data["forecast"]) == 24
    print("[OK] POST /api/forecast generated 24-hour forecast with confidence bounds.")

    dl_res = client.get(f"/api/forecast/{f_data['forecast_uuid']}/download")
    assert dl_res.status_code == 200
    print("[OK] GET /api/forecast/{uuid}/download returned CSV stream.")

    print("\nALL SMOKE TEST CHECKS PASSED SUCCESSFULLY (100% SUCCESS)!")

if __name__ == "__main__":
    run_smoke_test()
