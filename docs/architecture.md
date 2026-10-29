# System Architecture & Data Flow Specification

**Project Title:** Energy Consumption Forecasting Using Time-Series ML  
**Programme:** HCLTech Career Shaper Programme — III Year Industry Project (Project No. 33)  
**Learner:** Rahul Kumar Verma  

---

## 1. High-Level System Architecture

```mermaid
graph TD
    subgraph Client_Layer ["Client & Presentation Layer"]
        UI["React 18 + Vite Dashboard<br/>(Port 5173)"]
        SVG["Interactive SVG Chart Engine<br/>(Confidence Bands, Tooltips)"]
        UI --- SVG
    end

    subgraph Gateway_Layer ["Enterprise API Gateway"]
        GW["Java 21 + Spring Boot 3<br/>(Port 8080)"]
        CORS["CORS Filter & Security Policy"]
        SWAGGER["OpenAPI 3 / Swagger UI<br/>(/swagger-ui.html)"]
        WC["Reactive WebClient Proxy"]
        GW --- CORS
        GW --- SWAGGER
        GW --- WC
    end

    subgraph ML_Service_Layer ["Time-Series Machine Learning Engine"]
        API["FastAPI Python 3.14<br/>(Port 8000)"]
        PIPE["Data Conditioning & Resampling Pipeline"]
        REG["Model Registry Interface"]
        
        SNAIVE["Seasonal Naive Forecaster<br/>(24h Cycle Baseline)"]
        SARIMA["SARIMAX Forecaster<br/>(statsmodels (1,1,1)x(1,0,0)24)"]
        LSTM["Deep Recurrent LSTM<br/>(PyTorch 2.13 Sequential Window)"]
        GB["HistGradientBoosting<br/>(scikit-learn Lag Features)"]
        
        API --> PIPE
        PIPE --> REG
        REG --> SNAIVE
        REG --> SARIMA
        REG --> LSTM
        REG --> GB
    end

    subgraph Persistence_Layer ["Relational Database Storage"]
        DB[("SQLite Local / PostgreSQL<br/>(data/energy_forecast.db)")]
        T_DATA["datasets_meta"]
        T_RUNS["training_runs"]
        T_FC["forecast_runs & forecast_records"]
        DB --- T_DATA
        DB --- T_RUNS
        DB --- T_FC
    end

    UI -->|"HTTP / REST (Proxy)"| GW
    UI -->|"Direct Dev API"| API
    WC -->|"Async HTTP"| API
    API -->|"SQLAlchemy / SQLite"| DB
    GW -->|"JPA / Hibernate"| DB
```

---

## 2. Data Flow Diagram (DFD Level 0)

```mermaid
flowchart LR
    User(["Facility Manager / Learner"])

    subgraph Energy_Forecasting_System ["Energy Forecasting System (Project 33)"]
        P1["1.0 Ingest & Sanitize Data<br/>(Validate 6 Columns, Boundaries)"]
        P2["2.0 Exploratory Analysis<br/>(Diurnal Curves, Correlations)"]
        P3["3.0 Model Training & Evaluation<br/>(Chronological 80/20 Holdout)"]
        P4["4.0 Multi-Step Forecasting<br/>(Recursive Horizon up to 168h)"]
    end

    D1[("Canonical Dataset Storage<br/>(dataset.csv & 5,000 Augmented)")]
    D2[("Model Benchmarks & Forecast Records<br/>(energy_forecast.db)")]
    D3[("Isolated Anomaly Labels<br/>(data/anomaly_labels.csv)")]

    User -->|"Uploads CSV/Excel Energy Data"| P1
    P1 -->|"Cleaned 6-column records"| D1
    P1 -->|"Logged Anomaly Events (3.56%)"| D3
    D1 -->|"Time-series records"| P2
    P2 -->|"Visual Aggregations & Stats"| User
    D1 -->|"Historical Series"| P3
    P3 -->|"MAE, RMSE, MAPE Metrics"| D2
    D2 -->|"Model Comparison Table"| User
    P4 -->|"Projects 24h-168h with 95% Band"| User
    P4 -->|"Stores Forecast Steps"| D2
```

---

## 3. Database Relational Schema

### `datasets_meta`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `filename` TEXT NOT NULL
- `row_count` INTEGER NOT NULL
- `building_count` INTEGER NOT NULL
- `start_date` TEXT
- `end_date` TEXT
- `created_at` TEXT NOT NULL

### `training_runs`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `run_uuid` TEXT UNIQUE NOT NULL
- `model_name` TEXT NOT NULL
- `building_id` TEXT NOT NULL
- `train_steps` INTEGER NOT NULL
- `test_steps` INTEGER NOT NULL
- `mae` REAL
- `rmse` REAL
- `mape` REAL
- `smape` REAL
- `training_time_sec` REAL
- `status` TEXT NOT NULL
- `created_at` TEXT NOT NULL

### `forecast_runs`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `forecast_uuid` TEXT UNIQUE NOT NULL
- `model_name` TEXT NOT NULL
- `building_id` TEXT NOT NULL
- `horizon_hours` INTEGER NOT NULL
- `start_timestamp` TEXT NOT NULL
- `end_timestamp` TEXT NOT NULL
- `status` TEXT NOT NULL
- `created_at` TEXT NOT NULL

### `forecast_records`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `forecast_uuid` TEXT NOT NULL (Foreign Key)
- `step_number` INTEGER NOT NULL
- `timestamp` TEXT NOT NULL
- `predicted_kWh` REAL NOT NULL
- `lower_bound_kWh` REAL
- `upper_bound_kWh` REAL
