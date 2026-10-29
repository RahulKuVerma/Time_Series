"""
ml-service/app.py
-----------------
Production-ready FastAPI Service for Energy Consumption Forecasting.
Exposes REST endpoints, validates inputs, performs time-series forecasting,
calculates evaluation metrics, serves EDA statistics, and handles persistence.
"""

import os
import io
import math
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from pipeline import (
    CANONICAL_COLUMNS,
    prepare_building_series,
    chronological_split,
    calculate_metrics
)
from models import (
    get_model_registry,
    HAS_TORCH,
    HAS_STATSMODELS,
    HAS_PROPHET
)
from database import (
    init_db,
    log_training_run,
    log_forecast_run,
    get_recent_training_runs,
    get_forecast_history,
    get_forecast_by_uuid
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Ensure DB is created
init_db()

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
ACTIVE_DATASET_PATH = os.path.join(DATA_DIR, "processed", "dataset_augmented_5000.csv")
if not os.path.exists(ACTIVE_DATASET_PATH):
    ACTIVE_DATASET_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset.csv"))

app = FastAPI(
    title="Energy Consumption Forecasting ML API",
    description="Time-series forecasting REST API using LSTM, SARIMA, Seasonal Naive, and Gradient Boosting. Project No. 33.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_dataset() -> pd.DataFrame:
    global ACTIVE_DATASET_PATH
    if not os.path.exists(ACTIVE_DATASET_PATH):
        root_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset.csv"))
        if os.path.exists(root_csv):
            ACTIVE_DATASET_PATH = root_csv
        else:
            raise HTTPException(status_code=500, detail="No active dataset.csv found.")
    return pd.read_csv(ACTIVE_DATASET_PATH)

# ---------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------
class TrainRequest(BaseModel):
    building_id: str = Field(default="Office_A", description="Building facility identifier")
    model_name: str = Field(default="lstm", description="seasonal_naive, sarima, lstm, gradient_boosting, or prophet")
    test_split_ratio: float = Field(default=0.20, ge=0.05, le=0.40)

class ForecastRequest(BaseModel):
    building_id: str = Field(default="Office_A", description="Target building")
    model_name: str = Field(default="lstm", description="Selected forecaster")
    horizon_hours: int = Field(default=168, ge=1, le=168, description="Forecast horizon up to 7 days (168h)")

# ---------------------------------------------------------
# 1. Health Check
# ---------------------------------------------------------
@app.get("/health", tags=["System"])
def get_health():
    """Health check endpoint indicating service, model framework, and database availability."""
    return {
        "status": "UP",
        "service": "Energy Consumption Forecasting ML Service",
        "timestamp": datetime.now().isoformat(),
        "database": "SQLite (Active)",
        "frameworks": {
            "pytorch_lstm": "AVAILABLE" if HAS_TORCH else "UNAVAILABLE",
            "statsmodels_sarima": "AVAILABLE" if HAS_STATSMODELS else "UNAVAILABLE",
            "prophet": "AVAILABLE" if HAS_PROPHET else "UNAVAILABLE (Fallback to GradientBoosting)"
        },
        "active_dataset": os.path.basename(ACTIVE_DATASET_PATH)
    }

# ---------------------------------------------------------
# 2. Dataset Summary
# ---------------------------------------------------------
@app.get("/api/datasets/summary", tags=["Datasets"])
def get_dataset_summary():
    """Returns overview statistics of current active energy dataset."""
    df = get_current_dataset()
    df['parsed_dt'] = pd.to_datetime(df['timestamp'], errors='coerce')

    return {
        "filename": os.path.basename(ACTIVE_DATASET_PATH),
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": df.columns.tolist(),
        "buildings": sorted(df['building_id'].unique().tolist()),
        "building_count": df['building_id'].nunique(),
        "start_timestamp": str(df['parsed_dt'].min()),
        "end_timestamp": str(df['parsed_dt'].max()),
        "mean_consumption_kWh": round(float(df['consumption_kWh'].mean()), 2),
        "peak_consumption_kWh": round(float(df['consumption_kWh'].max()), 2),
        "min_consumption_kWh": round(float(df['consumption_kWh'].min()), 2),
        "avg_temperature_C": round(float(df['temperature_C'].mean()), 2),
        "avg_humidity_pct": round(float(df['humidity_pct'].mean()), 2)
    }

# ---------------------------------------------------------
# 3. Dataset Upload & Validation
# ---------------------------------------------------------
@app.post("/api/datasets/upload", tags=["Datasets"])
async def upload_dataset(file: UploadFile = File(...)):
    """Uploads CSV or Excel energy file, checks canonical schema, and updates active dataset."""
    global ACTIVE_DATASET_PATH
    filename = file.filename or "uploaded_data.csv"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ['.csv', '.xlsx', '.xls']:
        raise HTTPException(status_code=400, detail="Only CSV and Excel (.xlsx, .xls) files are supported.")

    contents = await file.read()
    try:
        if ext == '.csv':
            df_up = pd.read_csv(io.BytesIO(contents))
        else:
            df_up = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse uploaded file: {str(e)}")

    # Validate mandatory canonical columns
    missing = [c for c in CANONICAL_COLUMNS if c not in df_up.columns]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Schema violation: missing mandatory canonical columns: {missing}. Expected exactly: {CANONICAL_COLUMNS}"
        )

    # Save to data/processed
    dest_path = os.path.join(DATA_DIR, "processed", f"upload_{uuid.uuid4().hex[:8]}_{filename}")
    df_up[CANONICAL_COLUMNS].to_csv(dest_path, index=False)
    ACTIVE_DATASET_PATH = dest_path

    return {
        "status": "SUCCESS",
        "message": f"Dataset {filename} validated and activated successfully.",
        "rows_ingested": len(df_up),
        "columns": df_up.columns.tolist()
    }

# ---------------------------------------------------------
# 4. Data Quality Audit
# ---------------------------------------------------------
@app.get("/api/datasets/quality", tags=["Datasets"])
def get_dataset_quality():
    """Audits data quality: missing values, bounds violations, duplicate timestamps, anomaly counts."""
    df = get_current_dataset()
    total = len(df)

    null_counts = {col: int(df[col].isna().sum()) for col in df.columns}
    neg_consumption = int((df['consumption_kWh'] < 0).sum())
    hum_out_of_bounds = int(((df['humidity_pct'] < 0) | (df['humidity_pct'] > 100)).sum())

    # Check for anomaly labels file
    anomaly_file = os.path.join(DATA_DIR, "anomaly_labels.csv")
    anomaly_count = 0
    anomalies_sample = []
    if os.path.exists(anomaly_file):
        df_anom = pd.read_csv(anomaly_file)
        anomaly_count = len(df_anom)
        anomalies_sample = df_anom.head(10).to_dict(orient="records")

    return {
        "total_rows": total,
        "null_counts": null_counts,
        "negative_consumption_count": neg_consumption,
        "humidity_out_of_bounds_count": hum_out_of_bounds,
        "data_completeness_pct": round((1.0 - sum(null_counts.values()) / (total * len(df.columns))) * 100, 2),
        "labeled_anomalies_count": anomaly_count,
        "anomaly_rate_pct": round((anomaly_count / total) * 100, 2) if total > 0 else 0.0,
        "anomalies_sample": anomalies_sample
    }

# ---------------------------------------------------------
# 5. Exploratory Data Analysis (EDA) Summary
# ---------------------------------------------------------
@app.get("/api/eda/summary", tags=["EDA"])
def get_eda_summary():
    """Provides structured aggregations for dynamic EDA charts: diurnal profiles, correlations, distributions."""
    df = get_current_dataset()
    df['parsed_dt'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['hour'] = df['parsed_dt'].dt.hour

    # 1. Diurnal profile per building
    diurnal = df.groupby(['hour', 'building_id'])['consumption_kWh'].mean().unstack().fillna(0).to_dict()

    # 2. Consumption by day_type
    day_type_summary = df.groupby(['day_type', 'building_id'])['consumption_kWh'].mean().unstack().fillna(0).to_dict()

    # 3. Overall building statistics
    building_stats = []
    for b in df['building_id'].unique():
        sub = df[df['building_id'] == b]['consumption_kWh']
        building_stats.append({
            "building_id": b,
            "count": int(len(sub)),
            "mean": round(float(sub.mean()), 2),
            "std": round(float(sub.std()), 2),
            "min": round(float(sub.min()), 2),
            "p25": round(float(sub.quantile(0.25)), 2),
            "median": round(float(sub.median()), 2),
            "p75": round(float(sub.quantile(0.75)), 2),
            "max": round(float(sub.max()), 2)
        })

    # 4. Correlation matrix
    num_cols = ['consumption_kWh', 'temperature_C', 'humidity_pct', 'hour']
    corr_df = df[num_cols].corr().round(3)
    corr_matrix = {
        "columns": num_cols,
        "matrix": corr_df.values.tolist()
    }

    return {
        "diurnal_profile": diurnal,
        "day_type_summary": day_type_summary,
        "building_statistics": building_stats,
        "correlations": corr_matrix
    }

# ---------------------------------------------------------
# 6. Model Training & Validation
# ---------------------------------------------------------
@app.post("/api/models/train", tags=["Models"])
def train_model(req: TrainRequest):
    """Trains selected forecasting model on building data using chronological holdout split."""
    df = get_current_dataset()
    registry = get_model_registry()

    model_key = req.model_name.lower().strip()
    if model_key not in registry:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{req.model_name}'. Supported: {list(registry.keys())}"
        )

    model = registry[model_key]

    b_df = prepare_building_series(df, building_id=req.building_id, resample_freq='h')
    train_df, test_df = chronological_split(b_df, test_ratio=req.test_split_ratio)

    train_series = train_df['consumption_kWh']
    test_series = test_df['consumption_kWh']

    try:
        eval_res = model.evaluate(train_series, test_series)
        metrics = eval_res["metrics"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")

    run_uuid = uuid.uuid4().hex
    run_record = {
        "run_uuid": run_uuid,
        "model_name": model.name,
        "building_id": req.building_id,
        "train_steps": len(train_series),
        "test_steps": len(test_series),
        "mae": metrics["mae"],
        "rmse": metrics["rmse"],
        "mape": metrics["mape"],
        "smape": metrics["smape"],
        "training_time_sec": metrics["training_time_sec"],
        "status": "SUCCESS"
    }
    log_training_run(run_record)

    # Return test predictions for evaluation chart
    sample_points = []
    test_ts = test_df['timestamp'].tolist()
    for i in range(min(168, len(test_series))):
        sample_points.append({
            "timestamp": test_ts[i],
            "actual_kWh": round(float(test_series.iloc[i]), 2),
            "predicted_kWh": round(float(eval_res["predictions"][i]), 2)
        })

    return {
        "run_uuid": run_uuid,
        "metrics": metrics,
        "building_id": req.building_id,
        "evaluation_sample": sample_points
    }

# ---------------------------------------------------------
# 7. Model Metrics & Comparison
# ---------------------------------------------------------
@app.get("/api/models/metrics", tags=["Models"])
def get_model_metrics():
    """Returns latest benchmark comparisons across all models."""
    benchmark_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports", "model_benchmark_results.json"))
    if os.path.exists(benchmark_file):
        with open(benchmark_file, "r") as f:
            return json.load(f)

    # Fallback to recent runs from database
    runs = get_recent_training_runs(limit=20)
    return {"recent_runs": runs}

# ---------------------------------------------------------
# 8. Forecast Generation
# ---------------------------------------------------------
@app.post("/api/forecast", tags=["Forecasting"])
def generate_forecast(req: ForecastRequest):
    """Generates future consumption forecast up to 7 days (168h) with uncertainty intervals."""
    df = get_current_dataset()
    registry = get_model_registry()

    model_key = req.model_name.lower().strip()
    if model_key not in registry:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{req.model_name}'. Choose from: {list(registry.keys())}"
        )

    model = registry[model_key]
    b_df = prepare_building_series(df, building_id=req.building_id, resample_freq='h')
    series = b_df['consumption_kWh']

    # Fit on all available historical data for this building
    try:
        model.fit(series)
        preds = model.predict(steps=req.horizon_hours)
        preds = np.clip(preds, a_min=0.0, a_max=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting execution failed: {str(e)}")

    # Calculate residual uncertainty band (empirical std)
    residual_std = float(series.diff().std()) if len(series) > 1 else 2.0
    if np.isnan(residual_std) or residual_std <= 0:
        residual_std = 2.0

    last_dt = pd.to_datetime(b_df['timestamp'].iloc[-1])
    forecast_points = []
    db_records = []

    for step_idx in range(req.horizon_hours):
        step_dt = last_dt + timedelta(hours=step_idx + 1)
        ts_str = step_dt.strftime('%Y-%m-%d %H:%M')
        pred_val = round(float(preds[step_idx]), 2)

        # Expanding confidence interval over horizon
        uncertainty = 1.96 * residual_std * math.sqrt(1 + step_idx * 0.015)
        lower_b = round(max(0.0, pred_val - uncertainty), 2)
        upper_b = round(pred_val + uncertainty, 2)

        record = {
            "step": step_idx + 1,
            "timestamp": ts_str,
            "predicted_kWh": pred_val,
            "lower_bound_kWh": lower_b,
            "upper_bound_kWh": upper_b
        }
        forecast_points.append(record)
        db_records.append(record)

    forecast_uuid = uuid.uuid4().hex
    log_forecast_run(
        forecast_uuid=forecast_uuid,
        model_name=model.name,
        building_id=req.building_id,
        horizon_hours=req.horizon_hours,
        start_ts=forecast_points[0]["timestamp"],
        end_ts=forecast_points[-1]["timestamp"],
        records=db_records
    )

    # Include recent 48 hours of historical actuals for continuous visualization
    recent_history = []
    tail_sub = b_df.tail(48)
    for _, row in tail_sub.iterrows():
        recent_history.append({
            "timestamp": row['timestamp'],
            "actual_kWh": round(float(row['consumption_kWh']), 2)
        })

    return {
        "forecast_uuid": forecast_uuid,
        "model_name": model.name,
        "building_id": req.building_id,
        "horizon_hours": req.horizon_hours,
        "recent_history": recent_history,
        "forecast": forecast_points
    }

# ---------------------------------------------------------
# 9. Forecast History
# ---------------------------------------------------------
@app.get("/api/forecast/history", tags=["Forecasting"])
def get_all_forecast_history():
    """Lists previous forecast runs with timestamps, parameters, and status."""
    return get_forecast_history(limit=50)

# ---------------------------------------------------------
# 10. Forecast Download CSV
# ---------------------------------------------------------
@app.get("/api/forecast/{forecast_uuid}/download", tags=["Forecasting"])
def download_forecast_csv(forecast_uuid: str):
    """Downloads generated forecast run as a CSV file."""
    f_data = get_forecast_by_uuid(forecast_uuid)
    if not f_data or "records" not in f_data:
        raise HTTPException(status_code=404, detail="Forecast ID not found.")

    df_out = pd.DataFrame(f_data["records"])
    stream = io.StringIO()
    df_out.to_csv(stream, index=False)

    return Response(
        content=stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=forecast_{forecast_uuid[:8]}.csv"}
    )

# ---------------------------------------------------------
# 11. Download Cleaned Dataset
# ---------------------------------------------------------
@app.get("/api/datasets/download/cleaned", tags=["Datasets"])
def download_cleaned_dataset():
    """Downloads canonical cleaned dataset CSV."""
    cleaned_path = os.path.abspath(os.path.join(DATA_DIR, "processed", "dataset_cleaned.csv"))
    if not os.path.exists(cleaned_path):
        cleaned_path = ACTIVE_DATASET_PATH

    return FileResponse(
        cleaned_path,
        media_type="text/csv",
        filename="dataset_cleaned.csv"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
