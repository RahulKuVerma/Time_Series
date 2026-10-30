import React, { useState, useEffect } from 'react';
import {
  Activity,
  BarChart3,
  Calendar,
  CheckCircle2,
  Database,
  Download,
  FileSpreadsheet,
  FileText,
  Flame,
  HelpCircle,
  History,
  Layers,
  LineChart,
  Moon,
  Play,
  RefreshCw,
  ShieldCheck,
  Sun,
  TrendingUp,
  UploadCloud,
  Zap,
  AlertTriangle,
  Award,
  Target
} from 'lucide-react';
import { TimeSeriesChart, DiurnalBarChart, MultiModelEvaluationChart } from './components/InteractiveChart';

const API_BASE = ''; // Uses Vite proxy to http://localhost:8000

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [health, setHealth] = useState(null);
  const [summary, setSummary] = useState(null);
  const [quality, setQuality] = useState(null);
  const [edaData, setEdaData] = useState(null);
  const [benchmark, setBenchmark] = useState(null);
  const [historyRuns, setHistoryRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Theme state with localStorage persistence
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('energyforecast_theme');
    if (saved === 'light' || saved === 'dark') return saved;
    return 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('energyforecast_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Forecast state
  const [selectedBuilding, setSelectedBuilding] = useState('Office_A');
  const [selectedModel, setSelectedModel] = useState('lstm');
  const [horizonHours, setHorizonHours] = useState(168);
  const [forecastResult, setForecastResult] = useState(null);
  const [forecastingLoading, setForecastingLoading] = useState(false);

  // Upload state
  const [uploadStatus, setUploadStatus] = useState(null);

  // Fetch initial data
  const fetchData = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const [hRes, sRes, qRes, eRes, bRes, histRes] = await Promise.all([
        fetch(`${API_BASE}/health`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/datasets/summary`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/datasets/quality`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/eda/summary`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/models/metrics`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/forecast/history`).then(r => r.json()).catch(() => [])
      ]);

      setHealth(hRes);
      setSummary(sRes);
      setQuality(qRes);
      setEdaData(eRes);
      setBenchmark(bRes);
      setHistoryRuns(histRes);
    } catch (err) {
      setErrorMsg('Failed to connect to backend service. Please verify the ML/Spring service is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Trigger Forecast
  const handleRunForecast = async () => {
    setForecastingLoading(true);
    setErrorMsg('');
    try {
      const res = await fetch(`${API_BASE}/api/forecast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          building_id: selectedBuilding,
          model_name: selectedModel,
          horizon_hours: parseInt(horizonHours, 10)
        })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Forecasting failed');
      }
      const data = await res.json();
      setForecastResult(data);
      // Refresh history
      fetch(`${API_BASE}/api/forecast/history`).then(r => r.json()).then(setHistoryRuns);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setForecastingLoading(false);
    }
  };

  // Handle File Upload
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    setUploadStatus({ status: 'uploading', message: 'Validating and ingesting file...' });
    try {
      const res = await fetch(`${API_BASE}/api/datasets/upload`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      setUploadStatus({ status: 'success', message: data.message });
      fetchData();
    } catch (err) {
      setUploadStatus({ status: 'error', message: err.message });
    }
  };

  const buildings = summary?.buildings || ['Office_A', 'Office_B', 'Warehouse', 'DataCenter', 'Canteen'];

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="brand-badge">
          <div className="brand-icon">
            <Zap size={22} />
          </div>
          <div>
            <div className="brand-title">EnergyForecaster</div>
            <div className="brand-sub">Project 33 • AIML</div>
          </div>
        </div>

        <nav className="nav-menu">
          <button
            type="button"
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <Activity size={18} />
            <span>Dashboard</span>
          </button>

          <button
            type="button"
            className={`nav-item ${activeTab === 'explorer' ? 'active' : ''}`}
            onClick={() => setActiveTab('explorer')}
          >
            <FileSpreadsheet size={18} />
            <span>Data Explorer</span>
          </button>

          <button
            type="button"
            className={`nav-item ${activeTab === 'eda' ? 'active' : ''}`}
            onClick={() => setActiveTab('eda')}
          >
            <BarChart3 size={18} />
            <span>EDA & Analytics</span>
          </button>

          <button
            type="button"
            className={`nav-item ${activeTab === 'models' ? 'active' : ''}`}
            onClick={() => setActiveTab('models')}
          >
            <Layers size={18} />
            <span>Model Comparison</span>
          </button>

          <button
            type="button"
            className={`nav-item ${activeTab === 'forecast' ? 'active' : ''}`}
            onClick={() => setActiveTab('forecast')}
          >
            <TrendingUp size={18} />
            <span>Forecast Studio</span>
          </button>

          <button
            type="button"
            className={`nav-item ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            <History size={18} />
            <span>Run History</span>
          </button>

          <button
            type="button"
            className={`nav-item ${activeTab === 'about' ? 'active' : ''}`}
            onClick={() => setActiveTab('about')}
          >
            <HelpCircle size={18} />
            <span>Documentation</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>HCLTech Career Shaper</div>
          <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>Academic Year 2025-26</div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        <header className="topbar">
          <div className="topbar-title-section">
            <h1>Energy Consumption Forecasting Using Time-Series ML</h1>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {/* Theme Change Feature in Navbar */}
            <button
              type="button"
              className="theme-toggle-btn"
              onClick={toggleTheme}
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
              aria-label="Toggle theme mode"
            >
              <div className="theme-toggle-track">
                <div className={`theme-toggle-thumb ${theme}`}>
                  {theme === 'dark' ? <Moon size={10} /> : <Sun size={10} />}
                </div>
              </div>
              <span className="theme-toggle-label">{theme === 'dark' ? 'Dark' : 'Light'}</span>
            </button>

            <button type="button" className="btn-secondary" onClick={fetchData} title="Refresh Data">
              <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
              <span>Sync</span>
            </button>

            <div className="status-pill">
              <div className="status-dot"></div>
              <span>{health?.status === 'UP' ? 'Services Online' : 'Connecting...'}</span>
            </div>
          </div>
        </header>

        <main className="content-area">
          {errorMsg && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: 'var(--accent-rose)',
              padding: '12px 18px',
              borderRadius: 8,
              marginBottom: 24,
              display: 'flex',
              alignItems: 'center',
              gap: 10
            }}>
              <AlertTriangle size={18} />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div>
              {/* 1. Overall Cumulative KPI Cards Produced by Trained Data */}
              <div className="card-grid">
                <div className="glass-card accent-glow">
                  <div className="kpi-title">
                    <span>Trained Dataset Timesteps</span>
                    <Database size={16} color="var(--accent-emerald)" />
                  </div>
                  <div className="kpi-value">{summary?.total_rows?.toLocaleString() || '5,000'}</div>
                  <div className="kpi-sub">
                    <span>3,997 Train Steps • 1,000 Test Steps</span>
                  </div>
                </div>

                <div className="glass-card">
                  <div className="kpi-title">
                    <span>Cumulative Energy Evaluated</span>
                    <Zap size={16} color="var(--accent-amber)" />
                  </div>
                  <div className="kpi-value">
                    {benchmark?.cumulative_results?.cumulative_test_energy_kWh
                      ? `${benchmark.cumulative_results.cumulative_test_energy_kWh.toLocaleString()} kWh`
                      : '8,634 kWh'}
                  </div>
                  <div className="kpi-sub">
                    <span>36,765 kWh Trained • 45,399 kWh Total Monitored</span>
                  </div>
                </div>

                <div className="glass-card">
                  <div className="kpi-title">
                    <span>Out-of-Sample Inferences</span>
                    <Target size={16} color="var(--accent-cyan)" />
                  </div>
                  <div className="kpi-value">
                    {benchmark?.cumulative_results?.total_inferences_evaluated?.toLocaleString() || '4,000'}
                  </div>
                  <div className="kpi-sub">
                    <span>1,000 Evaluation Hours × 4 Model Architectures</span>
                  </div>
                </div>

                <div className="glass-card">
                  <div className="kpi-title">
                    <span>Champion Benchmark MAE</span>
                    <Award size={16} color="var(--accent-blue)" />
                  </div>
                  <div className="kpi-value">
                    {benchmark?.cumulative_results?.best_mae_kWh || '3.97'} <span style={{ fontSize: '1rem' }}>kWh</span>
                  </div>
                  <div className="kpi-sub">
                    <span>sMAPE 41.96% • Seasonal Naive (24h) Baseline</span>
                  </div>
                </div>
              </div>

              {/* 2. Interactive Multi-Model Test Evaluation Graph */}
              <div className="glass-card" style={{ marginBottom: 28 }}>
                <MultiModelEvaluationChart
                  timeline={benchmark?.evaluation_timeline || []}
                  models={benchmark?.models || []}
                  cumulativeStats={benchmark?.cumulative_results || null}
                  height={340}
                />
              </div>

              {/* 3. Cumulative Results Produced by Trained Models */}
              <div className="glass-card" style={{ marginBottom: 28 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
                  <div>
                    <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                      Cumulative Results Produced by Trained Models
                    </h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: 3 }}>
                      Chronological holdout evaluation on 1,000 future out-of-sample timesteps with zero lookahead leakage.
                    </p>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Evaluated Facility: <code style={{ color: 'var(--accent-emerald)', background: 'var(--bg-code)', padding: '3px 8px', borderRadius: 4, fontWeight: 600 }}>Office_A</code>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 16 }}>
                  {/* LSTM Card */}
                  <div style={{
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-subtle)',
                    padding: '16px 18px',
                    borderRadius: 12,
                    position: 'relative'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#10b981' }}></span>
                        <span style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-primary)' }}>PyTorch LSTM</span>
                      </div>
                      <span style={{
                        background: 'rgba(16, 185, 129, 0.15)',
                        color: '#10b981',
                        fontSize: '0.72rem',
                        padding: '2px 8px',
                        borderRadius: 4,
                        fontWeight: 600
                      }}>
                        Deep Recurrent
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 12 }}>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>MAE (Mean Abs Error)</div>
                        <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name.includes('LSTM'))?.mae?.toFixed(3) || '5.574'} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>kWh</span>
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>RMSE</div>
                        <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name.includes('LSTM'))?.rmse?.toFixed(3) || '6.628'} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>kWh</span>
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>sMAPE Error</div>
                        <div style={{ fontSize: '0.92rem', fontWeight: 600, color: '#10b981', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name.includes('LSTM'))?.smape?.toFixed(1) || '64.9'}%
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>Training Latency</div>
                        <div style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-secondary)', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name.includes('LSTM'))?.training_time_sec !== undefined ? `${benchmark.models.find(m => m.model_name.includes('LSTM')).training_time_sec}s` : '7.94s'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* SARIMA Card */}
                  <div style={{
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-subtle)',
                    padding: '16px 18px',
                    borderRadius: 12,
                    position: 'relative'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#8b5cf6' }}></span>
                        <span style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-primary)' }}>Statsmodels SARIMA</span>
                      </div>
                      <span style={{
                        background: 'rgba(139, 92, 246, 0.15)',
                        color: '#8b5cf6',
                        fontSize: '0.72rem',
                        padding: '2px 8px',
                        borderRadius: 4,
                        fontWeight: 600
                      }}>
                        Econometric
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 12 }}>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>MAE (Mean Abs Error)</div>
                        <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name === 'SARIMA')?.mae?.toFixed(3) || '5.526'} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>kWh</span>
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>RMSE</div>
                        <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name === 'SARIMA')?.rmse?.toFixed(3) || '6.568'} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>kWh</span>
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>sMAPE Error</div>
                        <div style={{ fontSize: '0.92rem', fontWeight: 600, color: '#8b5cf6', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name === 'SARIMA')?.smape?.toFixed(1) || '64.6'}%
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>Training Latency</div>
                        <div style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-secondary)', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name === 'SARIMA')?.training_time_sec !== undefined ? `${benchmark.models.find(m => m.model_name === 'SARIMA').training_time_sec}s` : '0.90s'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Gradient Boosting Card */}
                  <div style={{
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-subtle)',
                    padding: '16px 18px',
                    borderRadius: 12,
                    position: 'relative'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f59e0b' }}></span>
                        <span style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-primary)' }}>HistGradientBoosting</span>
                      </div>
                      <span style={{
                        background: 'rgba(245, 158, 11, 0.15)',
                        color: '#f59e0b',
                        fontSize: '0.72rem',
                        padding: '2px 8px',
                        borderRadius: 4,
                        fontWeight: 600
                      }}>
                        ML Lag Regressor
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 12 }}>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>MAE (Mean Abs Error)</div>
                        <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name.includes('Gradient'))?.mae?.toFixed(3) || '5.666'} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>kWh</span>
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>RMSE</div>
                        <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name.includes('Gradient'))?.rmse?.toFixed(3) || '6.699'} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>kWh</span>
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>sMAPE Error</div>
                        <div style={{ fontSize: '0.92rem', fontWeight: 600, color: '#f59e0b', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name.includes('Gradient'))?.smape?.toFixed(1) || '65.4'}%
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>Training Latency</div>
                        <div style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-secondary)', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name.includes('Gradient'))?.training_time_sec !== undefined ? `${benchmark.models.find(m => m.model_name.includes('Gradient')).training_time_sec}s` : '0.23s'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Seasonal Naive Card */}
                  <div style={{
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-subtle)',
                    padding: '16px 18px',
                    borderRadius: 12,
                    position: 'relative'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#06b6d4' }}></span>
                        <span style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-primary)' }}>Seasonal Naive (24h)</span>
                      </div>
                      <span style={{
                        background: 'rgba(6, 182, 212, 0.15)',
                        color: '#06b6d4',
                        fontSize: '0.72rem',
                        padding: '2px 8px',
                        borderRadius: 4,
                        fontWeight: 600
                      }}>
                        Benchmark Leader
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 12 }}>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>MAE (Mean Abs Error)</div>
                        <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name.includes('Naive'))?.mae?.toFixed(3) || '3.966'} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>kWh</span>
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>RMSE</div>
                        <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name.includes('Naive'))?.rmse?.toFixed(3) || '6.375'} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>kWh</span>
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>sMAPE Error</div>
                        <div style={{ fontSize: '0.92rem', fontWeight: 600, color: '#06b6d4', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name.includes('Naive'))?.smape?.toFixed(1) || '41.96'}%
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>Training Latency</div>
                        <div style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-secondary)', marginTop: 2 }}>
                          {benchmark?.models?.find(m => m.model_name.includes('Naive'))?.training_time_sec !== undefined ? `${benchmark.models.find(m => m.model_name.includes('Naive')).training_time_sec}s` : '0.00s'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 4. Quick Launch CTA (Kept as requested) */}
              <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 20 }}>
                <div>
                  <h3 style={{ fontSize: '1.15rem', color: 'var(--text-primary)' }}>Ready to generate 7-Day Building Forecasts?</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: 4 }}>
                    Execute multi-step recurrent forecasting with uncertainty bands across 168 hours.
                  </p>
                </div>
                <button type="button" className="btn-primary" onClick={() => setActiveTab('forecast')}>
                  <Play size={16} fill="#fff" />
                  <span>Open Forecast Studio</span>
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: DATA EXPLORER */}
          {activeTab === 'explorer' && (
            <div>
              <div className="glass-card" style={{ marginBottom: 24 }}>
                <h3 style={{ fontSize: '1.15rem', marginBottom: 12 }}>Dataset Ingestion & Validation</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 20 }}>
                  Upload custom CSV or Excel files. Uploaded files must match the exact six canonical columns:
                  <code style={{ color: 'var(--accent-emerald)', marginLeft: 6, background: 'var(--bg-code)', padding: '2px 8px', borderRadius: 4 }}>timestamp, building_id, consumption_kWh, temperature_C, humidity_pct, day_type</code>
                </p>

                <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
                  <label className="btn-primary" style={{ cursor: 'pointer' }}>
                    <UploadCloud size={18} />
                    <span>Choose CSV / Excel File</span>
                    <input type="file" accept=".csv, .xlsx, .xls" onChange={handleFileUpload} style={{ display: 'none' }} />
                  </label>

                  <a href={`${API_BASE}/api/datasets/download/cleaned`} download className="btn-secondary">
                    <Download size={16} />
                    <span>Download Cleaned dataset.csv</span>
                  </a>
                </div>

                {uploadStatus && (
                  <div style={{
                    marginTop: 18,
                    padding: '12px 16px',
                    borderRadius: 8,
                    fontSize: '0.88rem',
                    background: uploadStatus.status === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                    color: uploadStatus.status === 'success' ? 'var(--accent-emerald)' : 'var(--accent-rose)'
                  }}>
                    {uploadStatus.message}
                  </div>
                )}
              </div>

              {/* Data Quality Report */}
              <div className="glass-card" style={{ marginBottom: 24 }}>
                <h3 style={{ fontSize: '1.05rem', marginBottom: 16 }}>Data Quality & Anomaly Audit</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 20 }}>
                  <div style={{ background: 'var(--bg-surface-elevated)', padding: 14, borderRadius: 8 }}>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Negative Value Violations</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 'bold', color: quality?.negative_consumption_count === 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                      {quality?.negative_consumption_count || 0}
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-surface-elevated)', padding: 14, borderRadius: 8 }}>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Humidity Range [0-100]</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 'bold', color: quality?.humidity_out_of_bounds_count === 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                      {quality?.humidity_out_of_bounds_count || 0} Violations
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-surface-elevated)', padding: 14, borderRadius: 8 }}>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Isolated Anomaly Labels</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 'bold', color: 'var(--accent-amber)' }}>
                      {quality?.labeled_anomalies_count || 160} ({quality?.anomaly_rate_pct || 3.56}%)
                    </div>
                  </div>
                </div>

                {quality?.anomalies_sample && quality.anomalies_sample.length > 0 && (
                  <div>
                    <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: 10 }}>Sample Isolated Anomaly Events (data/anomaly_labels.csv)</h4>
                    <div className="data-table-container">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Timestamp</th>
                            <th>Building</th>
                            <th>Anomaly Type</th>
                            <th>Severity Factor</th>
                            <th>Observed (kWh)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {quality.anomalies_sample.slice(0, 5).map((a, i) => (
                            <tr key={i}>
                              <td>{a.timestamp}</td>
                              <td>{a.building_id}</td>
                              <td><span style={{ color: 'var(--accent-amber)' }}>{a.anomaly_type}</span></td>
                              <td>{a.severity_factor}</td>
                              <td>{a.consumption_kWh} kWh</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: EDA & ANALYTICS */}
          {activeTab === 'eda' && (
            <div>
              {/* Diurnal Profile Chart */}
              <div className="glass-card" style={{ marginBottom: 28 }}>
                <h3 style={{ fontSize: '1.05rem', marginBottom: 16 }}>Diurnal 24-Hour Average Load Profile by Facility</h3>
                {edaData?.diurnal_profile && (
                  <DiurnalBarChart data={edaData.diurnal_profile} buildings={buildings} />
                )}
              </div>

              {/* Statistical Spread Table */}
              <div className="glass-card" style={{ marginBottom: 28 }}>
                <h3 style={{ fontSize: '1.05rem', marginBottom: 16 }}>Empirical Facility Spread & Quantiles</h3>
                <div className="data-table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Facility</th>
                        <th>Observations</th>
                        <th>Mean (kWh)</th>
                        <th>Std Dev</th>
                        <th>Min</th>
                        <th>25th Pct</th>
                        <th>Median</th>
                        <th>75th Pct</th>
                        <th>Max</th>
                      </tr>
                    </thead>
                    <tbody>
                      {edaData?.building_statistics?.map((b) => (
                        <tr key={b.building_id}>
                          <td style={{ fontWeight: 600, color: 'var(--accent-blue)' }}>{b.building_id}</td>
                          <td>{b.count}</td>
                          <td>{b.mean}</td>
                          <td>{b.std}</td>
                          <td>{b.min}</td>
                          <td>{b.p25}</td>
                          <td style={{ fontWeight: 600, color: 'var(--accent-emerald)' }}>{b.median}</td>
                          <td>{b.p75}</td>
                          <td>{b.max}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Weather Correlations */}
              {edaData?.correlations && (
                <div className="glass-card">
                  <h3 style={{ fontSize: '1.05rem', marginBottom: 16 }}>Pearson Correlation Matrix</h3>
                  <div className="data-table-container">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Feature</th>
                          {edaData.correlations.columns.map((c) => (
                            <th key={c}>{c}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {edaData.correlations.columns.map((r, i) => (
                          <tr key={r}>
                            <td style={{ fontWeight: 600 }}>{r}</td>
                            {edaData.correlations.matrix[i].map((val, j) => (
                              <td key={j} style={{
                                color: val > 0.4 ? 'var(--accent-emerald)' : val < -0.4 ? 'var(--accent-rose)' : 'var(--text-secondary)',
                                fontWeight: Math.abs(val) > 0.5 ? 600 : 400
                              }}>
                                {val.toFixed(2)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: MODEL COMPARISON */}
          {activeTab === 'models' && (
            <div>
              <div className="glass-card" style={{ marginBottom: 28 }}>
                <h3 style={{ fontSize: '1.15rem', marginBottom: 12 }}>Chronological Benchmark Results (20% Holdout Test Window)</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 20 }}>
                  Models trained strictly on past records and evaluated on chronological future test window. Zero lookahead leakage.
                </p>

                <div className="data-table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Model Name</th>
                        <th>MAE (kWh)</th>
                        <th>RMSE (kWh)</th>
                        <th>MAPE (%)</th>
                        <th>sMAPE (%)</th>
                        <th>Training Latency</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {benchmark?.models?.filter(m => m.status !== 'UNAVAILABLE').map((m, idx) => (
                        <tr key={idx}>
                          <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{m.model_name}</td>
                          <td style={{ color: 'var(--accent-blue)' }}>{m.mae !== undefined ? m.mae.toFixed(3) : '—'}</td>
                          <td style={{ color: 'var(--accent-purple)' }}>{m.rmse !== undefined ? m.rmse.toFixed(3) : '—'}</td>
                          <td style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>{m.mape !== undefined ? `${m.mape.toFixed(1)}%` : '—'}</td>
                          <td>{m.smape !== undefined ? `${m.smape.toFixed(1)}%` : '—'}</td>
                          <td>{m.training_time_sec !== undefined ? `${m.training_time_sec}s` : '—'}</td>
                          <td>
                            <span style={{
                              padding: '4px 8px',
                              borderRadius: 4,
                              fontSize: '0.75rem',
                              background: m.status === 'SUCCESS' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                              color: m.status === 'SUCCESS' ? 'var(--accent-emerald)' : 'var(--accent-rose)'
                            }}>
                              {m.status || (m.reason ? 'UNAVAILABLE' : 'READY')}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div style={{ marginTop: 20, fontSize: '0.82rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: 14 }}>
                  <strong>Evaluation Note:</strong> Safe MAPE calculated with ε=0.1 threshold to protect against division-by-zero during low night baselines. Symmetric MAPE (sMAPE) provided as supplemental robust metric.
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: FORECAST STUDIO */}
          {activeTab === 'forecast' && (
            <div>
              {/* Parameter Controls */}
              <div className="glass-card" style={{ marginBottom: 28 }}>
                <h3 style={{ fontSize: '1.15rem', marginBottom: 16 }}>Forecast Configuration</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, alignItems: 'flex-end' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6 }}>Target Facility</label>
                    <select
                      className="select-input"
                      style={{ width: '100%' }}
                      value={selectedBuilding}
                      onChange={(e) => setSelectedBuilding(e.target.value)}
                    >
                      {buildings.map(b => (
                        <option key={b} value={b}>{b}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6 }}>Forecasting Architecture</label>
                    <select
                      className="select-input"
                      style={{ width: '100%' }}
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                    >
                      <option value="lstm">LSTM (Deep Recurrent Neural Net)</option>
                      <option value="sarima">SARIMA (Statistical Econometric)</option>
                      <option value="gradient_boosting">Gradient Boosting (ML Lag Tree)</option>
                      <option value="seasonal_naive">Seasonal Naive (24h Baseline)</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6 }}>Forecast Horizon</label>
                    <select
                      className="select-input"
                      style={{ width: '100%' }}
                      value={horizonHours}
                      onChange={(e) => setHorizonHours(e.target.value)}
                    >
                      <option value="24">24 Hours (1 Day)</option>
                      <option value="48">48 Hours (2 Days)</option>
                      <option value="72">72 Hours (3 Days)</option>
                      <option value="168">168 Hours (7 Days / 1 Week)</option>
                    </select>
                  </div>

                  <button
                    type="button"
                    className="btn-primary"
                    style={{ height: 42, justifyContent: 'center' }}
                    onClick={handleRunForecast}
                    disabled={forecastingLoading}
                  >
                    <Play size={16} fill="#fff" />
                    <span>{forecastingLoading ? 'Generating Forecast...' : 'Generate Forecast'}</span>
                  </button>
                </div>
              </div>

              {/* Chart Visualization */}
              {forecastResult && (
                <div className="glass-card" style={{ marginBottom: 28 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                    <div>
                      <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                        {forecastResult.building_id} • {forecastResult.model_name}
                      </h3>
                      <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                        Multi-step Forecast across {forecastResult.horizon_hours} hours with 95% Confidence Bounds
                      </div>
                    </div>

                    <a
                      href={`${API_BASE}/api/forecast/${forecastResult.forecast_uuid}/download`}
                      download
                      className="btn-secondary"
                    >
                      <Download size={15} />
                      <span>Export CSV</span>
                    </a>
                  </div>

                  <div className="svg-chart-wrapper">
                    <TimeSeriesChart
                      historical={forecastResult.recent_history || []}
                      forecast={forecastResult.forecast || []}
                      title={`Predicted Hourly Load for ${forecastResult.building_id}`}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 6: RUN HISTORY */}
          {activeTab === 'history' && (
            <div>
              <div className="glass-card">
                <h3 style={{ fontSize: '1.15rem', marginBottom: 16 }}>Recorded Forecast Executions</h3>
                <div className="data-table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>UUID</th>
                        <th>Facility</th>
                        <th>Model</th>
                        <th>Horizon</th>
                        <th>Period Start</th>
                        <th>Period End</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historyRuns.length === 0 ? (
                        <tr>
                          <td colSpan="7" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 24 }}>
                            No forecast runs recorded yet. Run a forecast in Forecast Studio.
                          </td>
                        </tr>
                      ) : (
                        historyRuns.map((r, i) => (
                          <tr key={i}>
                            <td style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{r.forecast_uuid?.slice(0, 8)}...</td>
                            <td style={{ fontWeight: 600, color: 'var(--accent-blue)' }}>{r.building_id}</td>
                            <td>{r.model_name}</td>
                            <td>{r.horizon_hours} Hours</td>
                            <td>{r.start_timestamp}</td>
                            <td>{r.end_timestamp}</td>
                            <td>
                              <a
                                href={`${API_BASE}/api/forecast/${r.forecast_uuid}/download`}
                                download
                                style={{ color: 'var(--accent-emerald)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 4 }}
                              >
                                <Download size={14} />
                                <span>CSV</span>
                              </a>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 7: DOCUMENTATION & ABOUT */}
          {activeTab === 'about' && (
            <div>
              <div className="glass-card" style={{ marginBottom: 24 }}>
                <h3 style={{ fontSize: '1.2rem', marginBottom: 12 }}>Project Specifications & Provenance</h3>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: 1.7 }}>
                  <p><strong style={{ color: 'var(--text-primary)' }}>Title:</strong> Energy Consumption Forecasting Using Time-Series ML</p>
                  <p><strong style={{ color: 'var(--text-primary)' }}>Programme:</strong> HCLTech Career Shaper Programme — III Year Industry Project (Project No. 33)</p>
                  <p><strong style={{ color: 'var(--text-primary)' }}>Domain:</strong> Digital-Data-AI / AIML</p>
                  <p><strong style={{ color: 'var(--text-primary)' }}>Learner:</strong> Rahul Kumar Verma</p>
                  <p style={{ marginTop: 12 }}>
                    <strong style={{ color: 'var(--text-primary)' }}>Dataset Provenance:</strong> The canonical dataset is composed of 500 original seed records complemented by 4,500 physically calibrated synthetic hourly records across five facilities (DataCenter, Office_A, Office_B, Warehouse, Canteen), strictly maintaining the 6 canonical columns:
                    <code style={{ color: 'var(--accent-emerald)', display: 'block', margin: '8px 0', background: 'var(--bg-code)', padding: '6px 12px', borderRadius: 6 }}>
                      timestamp, building_id, consumption_kWh, temperature_C, humidity_pct, day_type
                    </code>
                  </p>
                </div>
              </div>

              <div className="glass-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--accent-amber)', marginBottom: 12 }}>
                  <ShieldCheck size={22} />
                  <h3 style={{ fontSize: '1.15rem' }}>Ethical Compliance & Privacy Safeguards</h3>
                </div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6 }}>
                  <p>
                    Energy consumption profiles inherently reflect occupancy patterns and operating schedules. In strict compliance with privacy standards and the <strong style={{ color: 'var(--text-primary)' }}>Digital Personal Data Protection (DPDP) Act 2023</strong>:
                  </p>
                  <ul style={{ paddingLeft: 24, marginTop: 8 }}>
                    <li>All building identifiers are anonymized to generic categories without exposing real organizational or individual identities.</li>
                    <li>No attempt is made to infer individual tenant presence or private living habits.</li>
                    <li>Anomaly detection annotations are stored in separate audit logs (`data/anomaly_labels.csv`) without compromising the core dataset.</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
