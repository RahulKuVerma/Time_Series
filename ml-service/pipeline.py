"""
ml-service/pipeline.py
----------------------
Core data loading, validation, time-series splitting, and evaluation metrics.
Ensures zero data leakage: scalers and preprocessing fit ONLY on training sets.
Chronological splits preserve temporal ordering.
"""

import math
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, List

CANONICAL_COLUMNS = [
    'timestamp',
    'building_id',
    'consumption_kWh',
    'temperature_C',
    'humidity_pct',
    'day_type'
]

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Computes MAE, RMSE, MAPE, and sMAPE.
    Safe handling for near-zero denominators.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    # MAE
    mae = float(np.mean(np.abs(y_true - y_pred)))

    # RMSE
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    # Safe MAPE with epsilon threshold (0.1 kWh) to avoid division by zero
    epsilon = 0.1
    safe_actuals = np.where(np.abs(y_true) < epsilon, epsilon, np.abs(y_true))
    mape = float(np.mean(np.abs(y_true - y_pred) / safe_actuals) * 100.0)

    # Symmetric MAPE (sMAPE) as robust supplemental metric
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    safe_denom = np.where(denom < epsilon, epsilon, denom)
    smape = float(np.mean(np.abs(y_true - y_pred) / safe_denom) * 100.0)

    return {
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "mape": round(mape, 2),
        "smape": round(smape, 2)
    }

def prepare_building_series(
    df: pd.DataFrame,
    building_id: str,
    resample_freq: str = 'h'
) -> pd.DataFrame:
    """
    Filters data for a specific building, ensures regular hourly grid,
    and forward-fills gaps with time-series safe interpolation.
    """
    sub = df[df['building_id'] == building_id].copy()
    sub['dt'] = pd.to_datetime(sub['timestamp'])
    sub = sub.sort_values('dt').drop_duplicates(subset=['dt']).set_index('dt')

    # Resample to ensure strictly regular hourly grid without missing time steps
    regular = sub.resample(resample_freq).agg({
        'consumption_kWh': 'mean',
        'temperature_C': 'mean',
        'humidity_pct': 'mean',
        'day_type': 'first',
        'building_id': 'first'
    })

    # Forward fill then backward fill for regular series
    regular['building_id'] = building_id
    regular['consumption_kWh'] = regular['consumption_kWh'].ffill().bfill()
    regular['temperature_C'] = regular['temperature_C'].ffill().bfill()
    regular['humidity_pct'] = regular['humidity_pct'].ffill().bfill()

    # Reconstruct day_type if missing
    if regular['day_type'].isna().any():
        is_wknd = regular.index.weekday >= 5
        regular['day_type'] = np.where(is_wknd, 'Weekend', 'Weekday')

    regular = regular.reset_index()
    regular['timestamp'] = regular['dt'].dt.strftime('%Y-%m-%d %H:%M')
    return regular

def chronological_split(
    df: pd.DataFrame,
    test_ratio: float = 0.20
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits DataFrame strictly chronologically into train and test partitions.
    Guarantees no future lookahead or shuffling leakage.
    """
    n = len(df)
    split_idx = int(n * (1.0 - test_ratio))
    train_df = df.iloc[:split_idx].copy().reset_index(drop=True)
    test_df = df.iloc[split_idx:].copy().reset_index(drop=True)
    return train_df, test_df
