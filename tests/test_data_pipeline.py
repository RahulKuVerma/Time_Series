"""
tests/test_data_pipeline.py
---------------------------
Unit tests for data validation, schema enforcement, chronological split, and metric calculation.
"""

import sys
import os
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ml-service')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from pipeline import calculate_metrics, chronological_split, prepare_building_series, CANONICAL_COLUMNS
from clean_data import validate_and_clean_dataframe

def test_canonical_schema():
    expected = ['timestamp', 'building_id', 'consumption_kWh', 'temperature_C', 'humidity_pct', 'day_type']
    assert CANONICAL_COLUMNS == expected

def test_calculate_metrics():
    y_true = np.array([10.0, 20.0, 30.0, 40.0])
    y_pred = np.array([12.0, 18.0, 33.0, 38.0])

    res = calculate_metrics(y_true, y_pred)
    assert "mae" in res
    assert "rmse" in res
    assert "mape" in res
    assert "smape" in res

    # MAE should be (2+2+3+2)/4 = 2.25
    assert res["mae"] == 2.25
    assert res["rmse"] > 0
    assert res["mape"] > 0

def test_chronological_split_no_leakage():
    dates = pd.date_range("2024-01-01", periods=100, freq='h')
    df = pd.DataFrame({
        'timestamp': dates.strftime('%Y-%m-%d %H:%M'),
        'consumption_kWh': np.random.uniform(5, 50, 100)
    })

    train_df, test_df = chronological_split(df, test_ratio=0.20)
    assert len(train_df) == 80
    assert len(test_df) == 20

    # Ensure train timestamps strictly precede test timestamps
    train_max_ts = pd.to_datetime(train_df['timestamp'].iloc[-1])
    test_min_ts = pd.to_datetime(test_df['timestamp'].iloc[0])
    assert train_max_ts < test_min_ts

def test_validate_and_clean_dataframe():
    raw_data = {
        'timestamp': ['2024-01-01 01:00', '2024-01-01 02:00', 'invalid_time', '2024-01-01 03:00'],
        'building_id': ['Office_A', 'Office_A', 'Office_A', 'Office_A'],
        'consumption_kWh': [10.5, -5.0, 20.0, 15.2], # negative consumption
        'temperature_C': [25.0, 26.5, 30.0, 28.0],
        'humidity_pct': [45.0, 120.0, 50.0, 48.0], # humidity > 100
        'day_type': ['weekday', 'WEEKEND', 'holiday', 'invalid_type']
    }
    df = pd.DataFrame(raw_data)
    clean_df, report = validate_and_clean_dataframe(df)

    # 1 invalid timestamp should be dropped
    assert len(clean_df) == 3
    # negative consumption should be clipped to 0
    assert (clean_df['consumption_kWh'] >= 0).all()
    # humidity clipped to 100
    assert (clean_df['humidity_pct'] <= 100).all()
    # day types normalized
    assert set(clean_df['day_type']).issubset({'Weekday', 'Weekend', 'Holiday'})
