"""
scripts/generate_synthetic_data.py
----------------------------------
Generates realistic, physically plausible synthetic time-series energy consumption data.
Designed for Project No. 33: "Energy Consumption Forecasting Using Time-Series ML".

Features:
- Building-specific baseline and diurnal profiles (DataCenter, Office_A, Office_B, Warehouse, Canteen)
- Exogenous temperature and humidity physical correlations
- Day-type impacts (Weekday, Weekend, Holiday)
- 2-5% configurable anomaly injection (spikes, dropouts, HVAC faults)
- Preserves exact 6 canonical columns:
  ['timestamp', 'building_id', 'consumption_kWh', 'temperature_C', 'humidity_pct', 'day_type']
- Saves anomaly labels separately into `data/anomaly_labels.csv` without polluting the canonical schema.
"""

import argparse
import os
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

BUILDING_PROFILES = {
    'DataCenter': {
        'base_load': 45.0,
        'peak_load': 72.0,
        'noise_std': 2.5,
        'temp_sensitivity': 0.8,
        'weekend_factor': 0.95,
        'holiday_factor': 0.93,
        'peak_hours': [11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    },
    'Office_A': {
        'base_load': 4.0,
        'peak_load': 17.5,
        'noise_std': 1.0,
        'temp_sensitivity': 0.4,
        'weekend_factor': 0.25,
        'holiday_factor': 0.20,
        'peak_hours': [9, 10, 11, 12, 13, 14, 15, 16, 17]
    },
    'Office_B': {
        'base_load': 4.5,
        'peak_load': 18.0,
        'noise_std': 1.1,
        'temp_sensitivity': 0.45,
        'weekend_factor': 0.28,
        'holiday_factor': 0.22,
        'peak_hours': [9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    },
    'Warehouse': {
        'base_load': 7.0,
        'peak_load': 16.5,
        'noise_std': 1.2,
        'temp_sensitivity': 0.3,
        'weekend_factor': 0.50,
        'holiday_factor': 0.40,
        'peak_hours': [6, 7, 8, 9, 10, 14, 15, 16]
    },
    'Canteen': {
        'base_load': 3.5,
        'peak_load': 15.0,
        'noise_std': 0.9,
        'temp_sensitivity': 0.35,
        'weekend_factor': 0.30,
        'holiday_factor': 0.15,
        'peak_hours': [7, 8, 9, 12, 13, 14, 17, 18, 19]
    }
}

CANONICAL_COLUMNS = [
    'timestamp',
    'building_id',
    'consumption_kWh',
    'temperature_C',
    'humidity_pct',
    'day_type'
]

def is_holiday(dt: datetime) -> bool:
    # Sample holidays in Jan-March 2024 (e.g. Republic Day 2024-01-26, etc.)
    holiday_dates = {
        (1, 1),   # New Year
        (1, 15),  # Pongal/Makar Sankranti
        (1, 26),  # Republic Day
        (3, 8),   # Maha Shivratri
        (3, 25),  # Holi
    }
    return (dt.month, dt.day) in holiday_dates

def generate_synthetic_data(
    num_rows: int = 4500,
    start_date_str: str = "2024-01-21 21:00",
    seed: int = 42,
    anomaly_rate: float = 0.035,
    output_path: str = "data/processed/synthetic_data.csv",
    anomaly_output_path: str = "data/anomaly_labels.csv"
):
    np.random.seed(seed)
    start_dt = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")
    buildings = list(BUILDING_PROFILES.keys())

    records = []
    anomalies = []

    # Sequence of timestamps and building assignments matching interleaved hourly format
    curr_dt = start_dt
    for i in range(num_rows):
        b_id = buildings[i % len(buildings)]
        prof = BUILDING_PROFILES[b_id]

        hour = curr_dt.hour
        is_wknd = curr_dt.weekday() >= 5
        is_hol = is_holiday(curr_dt)

        if is_hol:
            day_type = 'Holiday'
            occ_multiplier = prof['holiday_factor']
        elif is_wknd:
            day_type = 'Weekend'
            occ_multiplier = prof['weekend_factor']
        else:
            day_type = 'Weekday'
            occ_multiplier = 1.0

        # Ambient temperature simulation: daily curve + seasonal drift + noise
        day_of_year = curr_dt.timetuple().tm_yday
        seasonal_temp = 27.0 + 3.0 * math.sin(2 * math.pi * (day_of_year - 15) / 365.0)
        daily_temp_cycle = 4.5 * math.sin(2 * math.pi * (hour - 9) / 24.0)
        temp_c = round(float(seasonal_temp + daily_temp_cycle + np.random.normal(0, 0.7)), 1)
        temp_c = max(18.0, min(42.0, temp_c))

        # Relative humidity anti-correlated with temperature
        base_humidity = 58.0 - 0.7 * (temp_c - 27.0)
        humidity_pct = round(float(base_humidity + np.random.normal(0, 1.8)), 1)
        humidity_pct = max(20.0, min(95.0, humidity_pct))

        # Energy consumption calculation
        if hour in prof['peak_hours']:
            diurnal_shape = 0.7 + 0.3 * math.sin(math.pi * (hour - min(prof['peak_hours'])) / (max(prof['peak_hours']) - min(prof['peak_hours']) + 1))
            load_target = prof['base_load'] + (prof['peak_load'] - prof['base_load']) * diurnal_shape * occ_multiplier
        else:
            load_target = prof['base_load'] * (0.85 + 0.15 * occ_multiplier)

        # Thermal cooling load dependency
        cooling_addition = max(0.0, (temp_c - 26.0) * prof['temp_sensitivity'])
        consumption = load_target + cooling_addition + np.random.normal(0, prof['noise_std'])

        # Anomaly injection (2-5% rate)
        is_anomaly = False
        anomaly_type = "None"
        severity = 0.0

        if np.random.rand() < anomaly_rate:
            is_anomaly = True
            roll = np.random.rand()
            if roll < 0.45:
                # Spike anomaly (surge, equipment fault, unexpected override)
                factor = np.random.uniform(1.4, 2.1)
                consumption *= factor
                anomaly_type = "High Consumption Surge"
                severity = round(factor, 2)
            elif roll < 0.80:
                # Sudden drop / sensor dropout
                factor = np.random.uniform(0.15, 0.45)
                consumption *= factor
                anomaly_type = "Power Drop / Sensor Undervoltage"
                severity = round(factor, 2)
            else:
                # HVAC chiller lockup during heat peak
                consumption += 18.5
                anomaly_type = "HVAC Continuous Runaway"
                severity = 18.5

        consumption = round(max(0.5, float(consumption)), 2)

        ts_str = curr_dt.strftime("%Y-%m-%d %H:%M")
        records.append({
            'timestamp': ts_str,
            'building_id': b_id,
            'consumption_kWh': consumption,
            'temperature_C': temp_c,
            'humidity_pct': humidity_pct,
            'day_type': day_type
        })

        if is_anomaly:
            anomalies.append({
                'timestamp': ts_str,
                'building_id': b_id,
                'anomaly_type': anomaly_type,
                'severity_factor': severity,
                'consumption_kWh': consumption,
                'provenance': 'synthetic'
            })

        # Advance timestamp every step (hourly)
        curr_dt += timedelta(hours=1)

    df_synth = pd.DataFrame(records)[CANONICAL_COLUMNS]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_synth.to_csv(output_path, index=False)
    print(f"Saved {len(df_synth)} synthetic rows to {output_path}")

    if anomalies:
        os.makedirs(os.path.dirname(anomaly_output_path), exist_ok=True)
        df_anom = pd.DataFrame(anomalies)
        df_anom.to_csv(anomaly_output_path, index=False)
        print(f"Saved {len(df_anom)} anomaly labels ({len(df_anom)/num_rows*100:.2f}%) to {anomaly_output_path}")

    return df_synth

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic energy consumption time-series data.")
    parser.add_argument("--rows", type=int, default=4500, help="Number of rows to generate (default: 4500)")
    parser.add_argument("--start", type=str, default="2024-01-21 21:00", help="Start timestamp YYYY-MM-DD HH:MM")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--anomaly-rate", type=float, default=0.035, help="Anomaly fraction between 0.02 and 0.05")
    parser.add_argument("--output", type=str, default="data/processed/synthetic_data.csv", help="Output file path")
    parser.add_argument("--anomaly-output", type=str, default="data/anomaly_labels.csv", help="Anomaly labels path")

    args = parser.parse_args()
    generate_synthetic_data(
        num_rows=args.rows,
        start_date_str=args.start,
        seed=args.seed,
        anomaly_rate=args.anomaly_rate,
        output_path=args.output,
        anomaly_output_path=args.anomaly_output
    )
