# Energy Consumption Forecasting Using Time-Series ML
### HCLTech Career Shaper Programme — III Year Industry Project
**Project No.:** 33 | **Domain:** Digital-Data-AI / AIML | **Duration:** 4 Weeks | **Format:** Individual Project  
**Author / Learner:** Rahul Kumar Verma  
**Academic Year:** 2025–26 | **Mentor:** Gaur Shaily (`gaur-shaily@hcltech.com`)  

[![Unit Tests](https://img.shields.io/badge/Unit%20Tests-15%2F15%20Passing-brightgreen)](#testing--verification)
[![Python](https://img.shields.io/badge/Python-3.14%20%7C%20FastAPI-blue)](https://fastapi.tiangolo.com)
[![Java](https://img.shields.io/badge/Java-21%20LTS%20%7C%20Spring%20Boot%203-red)](https://spring.io)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%7C%20Vite-61dafb)](https://vitejs.dev)
[![License](https://img.shields.io/badge/License-Apache%202.0-yellow)](LICENSE)
[![Compliance](https://img.shields.io/badge/DPDP%20Act%202023-Compliant-emerald)](docs/ethical_compliance_declaration.md)

---

## 1. Executive Summary & Project Purpose

Electrical energy consumption forecasting across commercial and industrial facilities is essential for dynamic peak tariff avoidance, HVAC chiller pre-cooling, battery storage optimization, and electrical grid decarbonization. 

This repository delivers an end-to-end, full-stack, production-grade time-series forecasting web application. The platform validates and cleans multi-facility metering data, extracts diurnal load signatures, benchmarks multiple time-series machine learning models (**PyTorch LSTM**, **Statsmodels SARIMA**, **HistGradientBoosting**, and **Seasonal Naive** baselines) under a strict **zero-lookahead chronological holdout protocol**, and delivers multi-step forecasts up to **7 days (168 hours)** with **95% confidence intervals**.

---

## 2. System Architecture & High-Level Design

The application is structured into decoupled, enterprise-grade tiers:

```
                      +-------------------------------------------------+
                      |       Frontend Dashboard (React 18 + Vite)      |
                      |   • KPI Cards     • Data Explorer & Ingestion   |
                      |   • EDA Visuals   • Multi-Model Comparison      |
                      |   • Forecast Tab  • Run History & CSV Download  |
                      +-----------------------+-------------------------+
                                              |
                                              | HTTP / JSON (Proxy)
                                              v
                      +-------------------------------------------------+
                      |     Enterprise Gateway (Java 21 + Spring Boot)  |
                      |   • CORS Security   • OpenAPI 3 / Swagger Docs  |
                      |   • Validation      • H2 / PostgreSQL JPA Store |
                      +-----------------------+-------------------------+
                                              |
                                              | Reactive WebClient
                                              v
                      +-------------------------------------------------+
                      |   Time-Series ML Service (Python 3.14 + FastAPI)|
                      |   • Resampling Pipeline • PyTorch Deep LSTM     |
                      |   • Statsmodels SARIMA  • Gradient Boosting     |
                      |   • MAE/RMSE/MAPE Calc  • Uncertainty Ribbons   |
                      +-----------------------+-------------------------+
                                              |
                                              | SQLite / PostgreSQL
                                              v
                      +-------------------------------------------------+
                      |                 Database Layer                  |
                      |   • datasets_meta     • training_runs           |
                      |   • forecast_runs     • forecast_records        |
                      +-------------------------------------------------+
```

- **Detailed Diagrams:** See [`docs/architecture.md`](docs/architecture.md) for the full architectural block diagram and Data Flow Diagram (DFD Level 0) in Mermaid.

---

## 3. Repository Structure & Deliverables Mapping

| Directory / File | Description | Deliverable Check |
|---|---|---|
| `dataset.csv` | Canonical 6-column dataset (500 seed rows, hourly cadence) | **Source of Truth** |
| `data_dictionary.csv` | Completed schema dictionary with data types, units, and descriptions | **Week 4 Core** |
| `Project_Brief.docx` | Original mentor requirements specification | **Reference** |
| `Project_Synopsis_Rahul_Kumar_Verma.docx` | Completed formal Word synopsis matching template structure | **Week 4 Core** |
| `frontend/` | React 18 + Vite dashboard with responsive glassmorphism UI | **Working Prototype** |
| `backend/` | Java 21 + Spring Boot 3 enterprise REST gateway & persistence | **Enterprise Layer** |
| `ml-service/` | Python 3.14 + FastAPI service with PyTorch LSTM & SARIMA | **ML Engine** |
| `data/processed/` | Cleaned canonical seed and 5,000-row augmented datasets | **Cleaned Data** |
| `data/anomaly_labels.csv` | 160 isolated synthetic anomaly events (3.56% rate) | **Quality Audit** |
| `reports/figures/` | Publication-quality EDA diagnostic visualizations (4 figures) | **3+ Visualizations** |
| `reports/project_report.md` | Comprehensive 18-section academic/industry report (8+ pages) | **Min 8 Pages** |
| `notebooks/eda_energy_consumption.ipynb` | Executable Jupyter Notebook demonstrating exploratory analysis | **EDA Notebook** |
| `scripts/` | Data generation, cleaning, EDA, benchmark, and smoke test scripts | **Reproducibility** |
| `tests/` | PyTest automated test suite (15 unit tests covering pipeline and APIs) | **Automated QA** |
| `docs/` | Architecture, demo walkthrough script, and signed ethical declaration | **Governance** |

---

## 4. Dataset Provenance & Cadence Resolution

1. **Exact 6 Canonical Columns:** Both `dataset.csv` and generated datasets strictly preserve these six columns in exact order without unauthorized additions:
   ```csv
   timestamp,building_id,consumption_kWh,temperature_C,humidity_pct,day_type
   ```
2. **Cadence Consistency:** Seed records were verified to be **hourly** timestamps (e.g., `2024-01-01 01:00`) interleaved across five facilities: `DataCenter`, `Office_A`, `Office_B`, `Warehouse`, and `Canteen`. The pipeline normalizes each facility onto a consistent 24-step daily grid ($m=24$).
3. **Synthetic Augmentation:** To meet the mentor's 5,000-row target, `scripts/generate_synthetic_data.py` generated 4,500 physically calibrated synthetic hourly records (`data/processed/dataset_augmented_5000.csv`) with distinct facility base loads, diurnal cycles, and thermal sensitivities.
4. **Isolated Anomaly Tracking:** 160 realistic fault events (spikes, drops, HVAC runaways at 3.56%) were stored in `data/anomaly_labels.csv` rather than polluting canonical columns.

---

## 5. Model Zoo & Empirical Benchmark Results

Evaluated on a **strict 20% chronological holdout test window (1,000 hours)** for facility `Office_A` without data leakage:

| Model Architecture | MAE (kWh) | RMSE (kWh) | Safe MAPE (%) | sMAPE (%) | Training Latency | Operational Status |
|---|---|---|---|---|---|---|
| **Seasonal Naive (24h)** | **3.966** | **6.375** | **57.40%** | **44.82%** | **0.001s** | Production Ready |
| **SARIMA (1,1,1)x(1,0,0)24** | 5.526 | 6.568 | 91.11% | 61.20% | 1.707s | Production Ready |
| **LSTM (Deep Recurrent)** | 5.574 | 6.628 | 91.64% | 61.85% | 15.947s | Production Ready |
| **HistGradientBoosting** | 5.666 | 6.699 | 96.07% | 63.40% | 0.294s | Production Ready |
| **Prophet** | — | — | — | — | — | Runtime Fallback Logged |

- **Evaluation Metric Note:** Safe MAPE is calculated using an $\epsilon = 0.1\text{ kWh}$ threshold to protect against division-by-zero during low night baselines. Symmetric MAPE (sMAPE) is reported as a supplemental robust metric.

---

## 6. Quickstart Guide (Local Execution)

### Step 1: Clone & Inspect Workspace
```powershell
# Open Windows PowerShell in project root
cd "c:\Users\Rahul Kumar Verma\OneDrive\Desktop\4_week_project"
```

### Step 2: Data Pipeline & EDA Generation
Execute data sanitization and generate diagnostic figures:
```powershell
# 1. Validate & clean canonical dataset + create 5,000 augmented rows
python scripts/clean_data.py

# 2. Generate publication-quality figures under reports/figures/
python scripts/eda_analysis.py

# 3. Benchmark all forecasting models and record metrics
python scripts/train_and_evaluate.py
```

### Step 3: Run Automated Test Suite
```powershell
# Run all 15 unit tests across pipeline, models, and FastAPI routes
python -m pytest tests/ -v

# Run the end-to-end integration smoke test
python scripts/smoke_test.py
```

### Step 4: Launch Backend & ML Service
Open **Terminal 1** to start the Python ML Service:
```powershell
cd ml-service
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger UI: `http://localhost:8000/docs`
- Service Health: `http://localhost:8000/health`

### Step 5: Launch Frontend Dashboard
Open **Terminal 2** to start the React + Vite dashboard:
```powershell
cd frontend
npm run dev
```
- Open browser at `http://localhost:5173`

*(Optional)* **Enterprise Spring Boot Gateway:**
If running Java Spring Boot alongside:
```powershell
cd backend
mvn spring-boot:run
```
- Gateway Swagger UI: `http://localhost:8080/swagger-ui.html`

---

## 7. Multi-Container Docker Deployment

To launch PostgreSQL, FastAPI, Spring Boot, and Nginx Frontend simultaneously via Docker:
```bash
docker compose up --build
```
- Frontend: `http://localhost:5173`
- Spring Boot Gateway: `http://localhost:8080`
- FastAPI ML Engine: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

---

## 8. API Contract & Endpoint Reference

| HTTP Method | Route | Description |
|---|---|---|
| `GET` | `/health` | System health status, database connection, and framework availability |
| `GET` | `/api/datasets/summary` | Row counts, date ranges, mean/peak consumption, and facility names |
| `POST` | `/api/datasets/upload` | Multipart file upload (.csv, .xlsx) with strict canonical schema validation |
| `GET` | `/api/datasets/quality` | Data completeness percentage, negative value check, and anomaly counts |
| `GET` | `/api/eda/summary` | Diurnal 24-hour load profiles, day type distributions, and correlations |
| `POST` | `/api/models/train` | Triggers model training on selected facility with chronological split |
| `GET` | `/api/models/metrics` | Returns benchmark comparison table (MAE, RMSE, MAPE, latency) |
| `POST` | `/api/forecast` | Generates 1-to-168 hour forecast with 95% uncertainty intervals |
| `GET` | `/api/forecast/history` | Lists previous forecast executions stored in the database |
| `GET` | `/api/forecast/{uuid}/download` | Streams generated forecast run as a downloadable CSV |
| `GET` | `/api/datasets/download/cleaned` | Streams canonical cleaned `dataset.csv` |

#### Sample Forecast Request (`POST /api/forecast`):
```json
{
  "building_id": "Office_A",
  "model_name": "lstm",
  "horizon_hours": 168
}
```

---

## 9. Ethical Compliance & Privacy Safeguards

- **Anonymization:** All facility identifiers are anonymized to generic classifications (`Office_A`, `DataCenter`, `Warehouse`, `Canteen`).
- **Occupancy Privacy:** Energy load signatures can reveal operating hours and presence. In strict adherence to the **Digital Personal Data Protection (DPDP) Act 2023**, no attempt is made to infer individual tenant presence or personal domestic routines.
- **Signed Declaration:** See [`docs/ethical_compliance_declaration.md`](docs/ethical_compliance_declaration.md) for the complete declaration.

---

## 10. Demonstration Script & Video Plan

A complete 90-second presenter talk track and pre-flight verification checklist for mentor evaluation is documented in [`docs/demo_script.md`](docs/demo_script.md).

---

## 11. Troubleshooting

1. **Port 8000 or 5173 already in use:**
   ```powershell
   Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
   ```
2. **Prophet C++ toolchain missing on Windows:**
   Prophet requires PyStan/CmdStanPy C++ compilers. The system automatically logs Prophet's status as unavailable and falls back to PyTorch LSTM, SARIMA, or HistGradientBoosting without failing.
3. **Windows Charset Encoding in Scripts:**
   All scripts explicitly reconfigure standard output to UTF-8 (`sys.stdout.reconfigure(encoding='utf-8')`) to prevent `charmap` console errors on Windows PowerShell.
