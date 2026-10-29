"""
ml-service/database.py
----------------------
SQLite persistence layer for Energy Consumption Forecasting.
Stores dataset metadata, training runs, model metrics, and forecast records.
Lightweight local fallback for PostgreSQL/Docker with identical relational schema.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "energy_forecast.db"))

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Dataset metadata table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datasets_meta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        row_count INTEGER NOT NULL,
        building_count INTEGER NOT NULL,
        start_date TEXT,
        end_date TEXT,
        created_at TEXT NOT NULL,
        is_active INTEGER DEFAULT 1
    )
    """)

    # 2. Training runs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS training_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_uuid TEXT UNIQUE NOT NULL,
        model_name TEXT NOT NULL,
        building_id TEXT NOT NULL,
        train_steps INTEGER NOT NULL,
        test_steps INTEGER NOT NULL,
        mae REAL,
        rmse REAL,
        mape REAL,
        smape REAL,
        training_time_sec REAL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 3. Forecast runs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS forecast_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        forecast_uuid TEXT UNIQUE NOT NULL,
        model_name TEXT NOT NULL,
        building_id TEXT NOT NULL,
        horizon_hours INTEGER NOT NULL,
        start_timestamp TEXT NOT NULL,
        end_timestamp TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 4. Forecast records table (individual step points)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS forecast_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        forecast_uuid TEXT NOT NULL,
        step_number INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        predicted_kWh REAL NOT NULL,
        lower_bound_kWh REAL,
        upper_bound_kWh REAL,
        FOREIGN KEY (forecast_uuid) REFERENCES forecast_runs(forecast_uuid) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()

def log_training_run(run_data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO training_runs (
        run_uuid, model_name, building_id, train_steps, test_steps,
        mae, rmse, mape, smape, training_time_sec, status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_data["run_uuid"],
        run_data["model_name"],
        run_data["building_id"],
        run_data.get("train_steps", 0),
        run_data.get("test_steps", 0),
        run_data.get("mae"),
        run_data.get("rmse"),
        run_data.get("mape"),
        run_data.get("smape"),
        run_data.get("training_time_sec", 0.0),
        run_data.get("status", "SUCCESS"),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def log_forecast_run(
    forecast_uuid: str,
    model_name: str,
    building_id: str,
    horizon_hours: int,
    start_ts: str,
    end_ts: str,
    records: List[Dict[str, Any]]
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO forecast_runs (
        forecast_uuid, model_name, building_id, horizon_hours,
        start_timestamp, end_timestamp, status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        forecast_uuid,
        model_name,
        building_id,
        horizon_hours,
        start_ts,
        end_ts,
        "COMPLETED",
        datetime.now().isoformat()
    ))

    # Insert individual predicted steps
    for r in records:
        cursor.execute("""
        INSERT INTO forecast_records (
            forecast_uuid, step_number, timestamp, predicted_kWh, lower_bound_kWh, upper_bound_kWh
        ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            forecast_uuid,
            r["step"],
            r["timestamp"],
            r["predicted_kWh"],
            r.get("lower_bound_kWh"),
            r.get("upper_bound_kWh")
        ))

    conn.commit()
    conn.close()

def get_recent_training_runs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM training_runs ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_forecast_history(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM forecast_runs ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_forecast_by_uuid(forecast_uuid: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM forecast_runs WHERE forecast_uuid = ?", (forecast_uuid,))
    run_row = cursor.fetchone()
    if not run_row:
        conn.close()
        return None
    res = dict(run_row)
    cursor.execute("SELECT step_number, timestamp, predicted_kWh, lower_bound_kWh, upper_bound_kWh FROM forecast_records WHERE forecast_uuid = ? ORDER BY step_number ASC", (forecast_uuid,))
    res["records"] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return res

# Initialize on import
init_db()
