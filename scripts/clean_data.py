"""
scripts/clean_data.py
---------------------
Data engineering and validation pipeline for Energy Consumption Forecasting.
Validates schemas, sanitizes types, checks boundary constraints, ensures chronological
ordering per building, produces audit logs, and writes canonical cleaned outputs.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CANONICAL_COLUMNS = [
    'timestamp',
    'building_id',
    'consumption_kWh',
    'temperature_C',
    'humidity_pct',
    'day_type'
]

VALID_DAY_TYPES = {'Weekday', 'Weekend', 'Holiday'}

def validate_and_clean_dataframe(df: pd.DataFrame, source_name: str = "dataset") -> tuple[pd.DataFrame, dict]:
    """
    Validates and cleans energy consumption DataFrame.
    Returns:
        (cleaned_df, quality_report)
    """
    initial_rows = len(df)
    report = {
        "source_name": source_name,
        "initial_rows": initial_rows,
        "actions_logged": [],
        "validation_errors": [],
        "missing_values_imputed": 0,
        "range_violations_corrected": 0,
        "duplicates_removed": 0
    }

    # 1. Check required columns
    missing_cols = [c for c in CANONICAL_COLUMNS if c not in df.columns]
    if missing_cols:
        err = f"Missing mandatory canonical columns: {missing_cols}"
        report["validation_errors"].append(err)
        raise ValueError(err)

    df_clean = df[CANONICAL_COLUMNS].copy()

    # 2. Check and parse timestamp
    try:
        df_clean['parsed_timestamp'] = pd.to_datetime(df_clean['timestamp'], errors='coerce')
        nat_count = df_clean['parsed_timestamp'].isna().sum()
        if nat_count > 0:
            report["actions_logged"].append(f"Dropped {nat_count} rows with invalid timestamps.")
            df_clean = df_clean.dropna(subset=['parsed_timestamp'])
    except Exception as e:
        report["validation_errors"].append(f"Timestamp parsing error: {e}")
        raise

    # 3. Coerce numeric types
    for col in ['consumption_kWh', 'temperature_C', 'humidity_pct']:
        non_numeric = pd.to_numeric(df_clean[col], errors='coerce')
        nan_num = non_numeric.isna().sum()
        if nan_num > 0:
            report["actions_logged"].append(f"Found {nan_num} non-numeric values in {col}; forward-filling.")
            report["missing_values_imputed"] += int(nan_num)
            # Use forward fill per building where possible
            non_numeric = non_numeric.ffill().bfill()
        df_clean[col] = non_numeric.astype(float)

    # 4. Check impossible values / range boundaries
    neg_consumption = (df_clean['consumption_kWh'] < 0).sum()
    if neg_consumption > 0:
        report["range_violations_corrected"] += int(neg_consumption)
        report["actions_logged"].append(f"Clipped {neg_consumption} negative consumption values to 0.0.")
        df_clean['consumption_kWh'] = df_clean['consumption_kWh'].clip(lower=0.0)

    hum_out_of_bounds = ((df_clean['humidity_pct'] < 0) | (df_clean['humidity_pct'] > 100)).sum()
    if hum_out_of_bounds > 0:
        report["range_violations_corrected"] += int(hum_out_of_bounds)
        report["actions_logged"].append(f"Clipped {hum_out_of_bounds} humidity values to [0.0, 100.0].")
        df_clean['humidity_pct'] = df_clean['humidity_pct'].clip(0.0, 100.0)

    temp_out_of_bounds = ((df_clean['temperature_C'] < -20.0) | (df_clean['temperature_C'] > 65.0)).sum()
    if temp_out_of_bounds > 0:
        report["range_violations_corrected"] += int(temp_out_of_bounds)
        report["actions_logged"].append(f"Flagged {temp_out_of_bounds} out-of-normal temperature values.")

    # 5. Normalize day_type
    df_clean['day_type'] = df_clean['day_type'].astype(str).str.strip().str.capitalize()
    invalid_days = ~df_clean['day_type'].isin(VALID_DAY_TYPES)
    if invalid_days.sum() > 0:
        report["actions_logged"].append(f"Corrected {invalid_days.sum()} invalid day_types to calendar-derived values.")
        # Infer day_type from parsed timestamp day of week
        is_wknd = df_clean.loc[invalid_days, 'parsed_timestamp'].dt.weekday >= 5
        df_clean.loc[invalid_days, 'day_type'] = np.where(is_wknd, 'Weekend', 'Weekday')

    # 6. Normalize building_id
    df_clean['building_id'] = df_clean['building_id'].astype(str).str.strip()

    # 7. Check duplicates
    before_dedup = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=['parsed_timestamp', 'building_id'])
    dups = before_dedup - len(df_clean)
    if dups > 0:
        report["duplicates_removed"] = dups
        report["actions_logged"].append(f"Removed {dups} duplicate (timestamp, building_id) entries.")

    # 8. Sort chronologically
    df_clean = df_clean.sort_values(by=['parsed_timestamp', 'building_id']).reset_index(drop=True)

    # 9. Format timestamp column strictly as YYYY-MM-DD HH:MM
    df_clean['timestamp'] = df_clean['parsed_timestamp'].dt.strftime('%Y-%m-%d %H:%M')
    df_clean = df_clean[CANONICAL_COLUMNS]

    final_rows = len(df_clean)
    report["final_rows"] = final_rows
    report["rows_retained_pct"] = round(final_rows / initial_rows * 100, 2) if initial_rows > 0 else 0
    report["date_range_start"] = df_clean['timestamp'].min()
    report["date_range_end"] = df_clean['timestamp'].max()
    report["unique_buildings"] = sorted(df_clean['building_id'].unique().tolist())
    report["mean_consumption_kWh"] = round(float(df_clean['consumption_kWh'].mean()), 2)
    report["peak_consumption_kWh"] = round(float(df_clean['consumption_kWh'].max()), 2)

    return df_clean, report

def run_pipeline(
    raw_csv_path: str = "dataset.csv",
    synthetic_csv_path: str = "data/processed/synthetic_data.csv",
    cleaned_output_path: str = "data/processed/dataset_cleaned.csv",
    augmented_output_path: str = "data/processed/dataset_augmented_5000.csv",
    report_output_path: str = "data/processed/cleaning_quality_report.json"
):
    logging.info(f"Loading raw seed dataset from {raw_csv_path}...")
    df_raw = pd.read_csv(raw_csv_path)
    df_cleaned, report_seed = validate_and_clean_dataframe(df_raw, source_name="original_supplied_seed")

    os.makedirs(os.path.dirname(cleaned_output_path), exist_ok=True)
    df_cleaned.to_csv(cleaned_output_path, index=False)
    logging.info(f"Saved canonical cleaned seed dataset ({len(df_cleaned)} rows) to {cleaned_output_path}")

    # Check if synthetic data exists and merge for augmented 5000 dataset
    if os.path.exists(synthetic_csv_path):
        logging.info(f"Found synthetic data at {synthetic_csv_path}. Creating combined 5,000 row canonical dataset...")
        df_synth = pd.read_csv(synthetic_csv_path)
        df_combined = pd.concat([df_cleaned, df_synth], ignore_index=True)
        df_augmented, report_aug = validate_and_clean_dataframe(df_combined, source_name="seed_plus_synthetic_5000")
        df_augmented.to_csv(augmented_output_path, index=False)
        logging.info(f"Saved augmented canonical dataset ({len(df_augmented)} rows) to {augmented_output_path}")

        metadata = {
            "provenance": {
                "original_supplied_rows": len(df_cleaned),
                "synthetic_generated_rows": len(df_synth),
                "total_rows": len(df_augmented),
                "note": "Canonical schema strictly preserved. Synthetic rows generated with calibrated building diurnal profiles."
            },
            "seed_quality": report_seed,
            "augmented_quality": report_aug
        }
    else:
        metadata = {
            "provenance": {
                "original_supplied_rows": len(df_cleaned),
                "synthetic_generated_rows": 0,
                "total_rows": len(df_cleaned)
            },
            "seed_quality": report_seed
        }

    with open(report_output_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logging.info(f"Saved data quality audit report to {report_output_path}")

if __name__ == "__main__":
    run_pipeline()
