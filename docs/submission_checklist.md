# Mentor Deliverables Submission Checklist

**Project Title:** Energy Consumption Forecasting Using Time-Series ML  
**Programme:** HCLTech Career Shaper Programme — III Year Industry Project (Project No. 33)  
**Learner:** Rahul Kumar Verma | **Mentor:** Gaur Shaily  

---

| Deliverable (Mentor Specification) | Expected Location / Format | Actual Repository Filepath | Verification Status | Notes / Execution Proof |
|---|---|---|---|---|
| **1. Completed Working Prototype** | Full-stack runnable web app | `frontend/`, `backend/`, `ml-service/` | **VERIFIED & OPERATIONAL** | React + Vite UI tested via `npm run build`; FastAPI tested via PyTest (15/15 passed). |
| **2. Comprehensive Project Report** | Min 8 pages equivalent | `reports/project_report.md` | **VERIFIED & COMPLETE** | 18 full sections with empirical benchmark metrics, architecture, and references. |
| **3. Project Synopsis Document** | Filled DOCX matching template | `Project_Synopsis_Rahul_Kumar_Verma.docx` | **VERIFIED & GENERATED** | Fully populated Word DOCX preserving mentor table order and metrics. |
| **4. EDA Analysis & Visualizations** | 3+ meaningful plots + script | `scripts/eda_analysis.py`, `reports/figures/` | **VERIFIED (4 FIGURES)** | `fig1_consumption_over_time.png`, `fig2_consumption_distribution.png`, `fig3_diurnal_and_weekly_patterns.png`, `fig4_weather_correlation_matrix.png`. |
| **5. Reproducible EDA Notebook** | Jupyter Notebook with plots | `notebooks/eda_energy_consumption.ipynb` | **VERIFIED & READY** | Runnable notebook detailing data schema, diurnal curves, and modeling insights. |
| **6. Cleaned & Preprocessed Dataset** | `dataset.csv` (exact 6 columns) | `data/processed/dataset_cleaned.csv`, `dataset.csv` | **VERIFIED & IMMUTABLE** | Exact columns: `['timestamp', 'building_id', 'consumption_kWh', 'temperature_C', 'humidity_pct', 'day_type']`. |
| **7. Completed Data Dictionary** | Fully completed data dictionary | `data_dictionary.csv`, `data/data_dictionary.csv` | **VERIFIED & COMPLETE** | All 6 columns populated with types, sample values, units, and privacy notes. |
| **8. Synthetic Generation Script** | Reproducible CLI script | `scripts/generate_synthetic_data.py` | **VERIFIED & EXECUTED** | Generated 4,500 realistic rows (5,000 total); 160 anomalies (3.56%) isolated in `data/anomaly_labels.csv`. |
| **9. Forecasting Models Implemented** | Seasonal Naive, SARIMA, LSTM | `ml-service/models.py` | **VERIFIED (4 MODELS)** | Seasonal Naive, SARIMA, PyTorch LSTM, HistGradientBoosting implemented with unified interface. |
| **10. Zero-Leakage Evaluation** | Holdout split, MAE/RMSE/MAPE | `ml-service/pipeline.py`, `scripts/train_and_evaluate.py` | **VERIFIED (20% HOLDOUT)** | Real empirical metrics recorded: Naive MAE=3.966, SARIMA MAE=5.526, LSTM MAE=5.574. |
| **11. Demo Walkthrough Script** | 1–2 minute video/live plan | `docs/demo_script.md` | **VERIFIED & STRUCTURED** | 90-second timestamped talk track and presenter verification checklist. |
| **12. Ethical Compliance Declaration** | Signed compliance document | `docs/ethical_compliance_declaration.md` | **VERIFIED & SIGNED** | Form filled affirming DPDP Act 2023, building anonymization, and AI tool disclosure. |
| **13. System Architecture Documentation** | Architecture & DFD Level 0 | `docs/architecture.md` | **VERIFIED & DIAGRAMMED** | Full system block diagram, Level 0 DFD, and relational database schema in Mermaid. |
| **14. Automated Unit & Smoke Tests** | Test suite with pytest | `tests/`, `scripts/smoke_test.py` | **VERIFIED (100% PASS)** | 15/15 PyTest unit tests passed; end-to-end smoke test passed. |
