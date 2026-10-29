"""
scripts/train_and_evaluate.py
-----------------------------
Benchmarks all forecasting models on the canonical energy consumption dataset.
- Evaluates on chronological test split (20% holdout).
- Computes MAE, RMSE, MAPE, and sMAPE.
- Compares Seasonal Naive, SARIMA, LSTM, and Gradient Boosting.
- Saves results to `reports/model_benchmark_results.json`.
"""

import os
import sys
import json
import logging
import pandas as pd

# Add ml-service to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ml-service')))

from pipeline import prepare_building_series, chronological_split
from models import (
    SeasonalNaiveForecaster,
    SARIMAForecaster,
    LSTMForecaster,
    GradientBoostingForecaster,
    HAS_PROPHET
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def benchmark_models(
    csv_path: str = "data/processed/dataset_augmented_5000.csv",
    output_report_path: str = "reports/model_benchmark_results.json",
    target_building: str = "Office_A"
):
    if not os.path.exists(csv_path):
        csv_path = "dataset.csv"

    logging.info(f"Loading data from {csv_path} for building {target_building}...")
    df = pd.read_csv(csv_path)

    # Condition regular hourly series
    b_df = prepare_building_series(df, building_id=target_building, resample_freq='h')
    train_df, test_df = chronological_split(b_df, test_ratio=0.20)

    train_series = train_df['consumption_kWh']
    test_series = test_df['consumption_kWh']

    logging.info(f"Chronological split -> Train steps: {len(train_series)}, Test steps: {len(test_series)}")

    models = [
        SeasonalNaiveForecaster(season_length=24),
        SARIMAForecaster(order=(1, 1, 1), seasonal_order=(1, 0, 0, 24)),
        GradientBoostingForecaster(lag_count=24),
        LSTMForecaster(seq_len=24, epochs=25, lr=0.005)
    ]

    results = []

    for model in models:
        logging.info(f"Evaluating {model.name}...")
        try:
            eval_res = model.evaluate(train_series, test_series)
            m = eval_res["metrics"]
            m["status"] = "SUCCESS"
            results.append(m)
            logging.info(f"-> {model.name}: MAE={m['mae']}, RMSE={m['rmse']}, MAPE={m['mape']}%, Time={m['training_time_sec']}s")
        except Exception as e:
            logging.error(f"Error evaluating {model.name}: {e}")
            results.append({
                "model_name": model.name,
                "status": f"FAILED: {str(e)}"
            })

    # Prophet status documentation
    results.append({
        "model_name": "Prophet",
        "status": "UNAVAILABLE" if not HAS_PROPHET else "AVAILABLE",
        "reason": "Prophet C++ toolchain (CmdStanPy) not installed on this environment; Gradient Boosting / SARIMA / LSTM utilized."
    })

    benchmark_summary = {
        "dataset_path": csv_path,
        "building_id": target_building,
        "total_series_steps": len(b_df),
        "train_steps": len(train_series),
        "test_steps": len(test_series),
        "split_method": "Chronological 80/20 Holdout (No Lookahead Leakage)",
        "models": results
    }

    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
    with open(output_report_path, "w") as f:
        json.dump(benchmark_summary, f, indent=2)

    logging.info(f"Model benchmark results saved to {output_report_path}")
    return benchmark_summary

if __name__ == "__main__":
    benchmark_models()
