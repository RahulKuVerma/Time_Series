# Demonstration Walkthrough Script & Presenter Checklist
**Duration:** 1 to 2 Minutes  
**Project:** Energy Consumption Forecasting Using Time-Series ML  
**Programme:** HCLTech Career Shaper Programme — III Year Industry Project (Project 33)  
**Presenter:** Rahul Kumar Verma  

---

## 1. Quick Video / Live Demo Script (90 Seconds)

### [00:00 – 00:15] Introduction & Problem Context
> *"Good morning mentors and evaluators. My name is Rahul Kumar Verma, presenting Project 33: 'Energy Consumption Forecasting Using Time-Series ML' under the HCLTech Career Shaper Programme.*  
> *Commercial facilities and grid operators face steep peak demand penalties due to sudden electrical load surges. Our objective is to deliver accurate multi-step forecasting across diverse facilities using statistical, deep learning, and ML models without data leakage."*

### [00:15 – 00:35] Data Ingestion & Quality Audit (Tab 1 & 2)
> *"Starting on our dashboard, the system monitors 5,000 canonical hourly records across five anonymized facilities: Office complexes, Data Centers, Warehouses, and Canteens.*  
> *Under the Data Explorer tab, users can upload new CSV or Excel files. Our validation pipeline automatically enforces the exact six canonical columns, clips impossible negative values, normalizes operating day types, and isolates 160 synthetic anomaly events into a dedicated audit file without polluting the core schema."*

### [00:35 – 00:55] Exploratory Analysis & Model Comparison (Tab 3 & 4)
> *"In the EDA tab, we observe distinct 24-hour diurnal patterns—data centers run high constant baselines around 50 kWh, while offices exhibit sharp daytime peaks dropping by 75% on weekends.*  
> *Under Model Comparison, we evaluated Seasonal Naive, SARIMA, PyTorch LSTM, and HistGradientBoosting on a strict 20% chronological holdout test window. Seasonal Naive achieved an MAE of 3.966 kWh, with SARIMA at 5.526 kWh and LSTM at 5.574 kWh."*

### [00:55 – 01:20] Live Forecast Execution & Uncertainty Bands (Tab 5)
> *"Now let's run a live forecast in our Forecast Studio. We select 'Office_A', choose our PyTorch Deep Recurrent LSTM architecture, and set a 7-day horizon of 168 hours.*  
> *With one click, the model fits the recent historical sequence and projects all 168 steps. Notice the seamless transition from historical actuals into the projected curve, accompanied by dynamic 95% confidence bounds that communicate uncertainty. We can immediately export these forecast records as a CSV."*

### [01:20 – 01:30] Conclusion & Ethical Compliance (Tab 6 & 7)
> *"All runs are persistently recorded in our relational database, and our system enforces strict DPDP Act 2023 compliance by anonymizing building identities. Thank you, and I look forward to your questions!"*

---

## 2. Presenter Demonstration Checklist

- [ ] **Environment Check:** FastAPI running on `http://localhost:8000` (terminal 1).
- [ ] **Frontend Check:** Vite dev server running on `http://localhost:5173` (terminal 2).
- [ ] **Browser Window:** Browser opened at `http://localhost:5173` in fullscreen mode.
- [ ] **Display Resolution:** 1920x1080 recommended for optimal dashboard presentation.
- [ ] **Tab Flow Sequence:**
  1. Open on **Dashboard** (highlight KPI cards, healthy service status pill).
  2. Navigate to **Data Explorer** (show data quality audit, anomaly rate 3.56%).
  3. Navigate to **EDA & Analytics** (show diurnal load bar profile).
  4. Navigate to **Model Comparison** (highlight MAE/RMSE/MAPE benchmark table).
  5. Navigate to **Forecast Studio** (select Office_A, LSTM, 168h horizon; click 'Generate Forecast'; hover over chart tooltip; click 'Export CSV').
  6. Navigate to **Run History** (verify newly generated forecast UUID listed).
  7. Conclude on **Documentation** (reiterate DPDP Act 2023 compliance).
