"""
ml-service/models.py
--------------------
Unified Model Zoo for Time-Series Energy Consumption Forecasting.
Implements:
1. SeasonalNaiveForecaster (24-hour / daily seasonal baseline)
2. SARIMAForecaster (statsmodels SARIMAX with seasonal order (1, 1, 1) x (1, 0, 0, 24))
3. LSTMForecaster (PyTorch deep recurrent neural network with sequential windowing)
4. GradientBoostingForecaster (scikit-learn HistGradientBoosting with lag & calendar features)
5. ProphetForecaster (Graceful wrapper detecting runtime availability)
"""

import time
import math
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from pipeline import calculate_metrics

# Optional deep learning & statistical imports
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import MinMaxScaler

# ---------------------------------------------------------
# PyTorch LSTM Architecture
# ---------------------------------------------------------
if HAS_TORCH:
    class PyTorchLSTM(nn.Module):
        def __init__(self, input_dim: int = 1, hidden_dim: int = 32, num_layers: int = 1):
            super().__init__()
            self.lstm = nn.LSTM(
                input_size=input_dim,
                hidden_size=hidden_dim,
                num_layers=num_layers,
                batch_first=True
            )
            self.fc = nn.Linear(hidden_dim, 1)

        def forward(self, x):
            # x shape: [batch_size, seq_len, input_dim]
            out, _ = self.lstm(x)
            last_step = out[:, -1, :]
            pred = self.fc(last_step)
            return pred

# ---------------------------------------------------------
# Base Forecaster Interface
# ---------------------------------------------------------
class BaseForecaster:
    def __init__(self, name: str):
        self.name = name
        self.is_fitted = False
        self.training_time_sec = 0.0

    def fit(self, train_series: pd.Series, **kwargs):
        raise NotImplementedError

    def predict(self, steps: int, **kwargs) -> np.ndarray:
        raise NotImplementedError

    def evaluate(self, train_series: pd.Series, test_series: pd.Series) -> Dict[str, Any]:
        t0 = time.time()
        self.fit(train_series)
        self.training_time_sec = round(time.time() - t0, 3)

        preds = self.predict(steps=len(test_series))
        # Ensure non-negative consumption
        preds = np.clip(preds, a_min=0.0, a_max=None)
        metrics = calculate_metrics(test_series.values, preds)
        metrics["model_name"] = self.name
        metrics["training_time_sec"] = self.training_time_sec
        metrics["test_steps"] = len(test_series)
        return {
            "metrics": metrics,
            "predictions": preds.tolist(),
            "actuals": test_series.values.tolist()
        }

# ---------------------------------------------------------
# 1. Seasonal Naive Forecaster
# ---------------------------------------------------------
class SeasonalNaiveForecaster(BaseForecaster):
    def __init__(self, season_length: int = 24):
        super().__init__(name="Seasonal Naive (24h)")
        self.season_length = season_length
        self.history: Optional[np.ndarray] = None

    def fit(self, train_series: pd.Series, **kwargs):
        self.history = train_series.values
        self.is_fitted = True

    def predict(self, steps: int, **kwargs) -> np.ndarray:
        if not self.is_fitted or self.history is None or len(self.history) == 0:
            return np.zeros(steps)
        k = min(self.season_length, len(self.history))
        recent_cycle = self.history[-k:]
        reps = math.ceil(steps / k)
        tiled = np.tile(recent_cycle, reps)[:steps]
        return tiled

# ---------------------------------------------------------
# 2. SARIMA Forecaster
# ---------------------------------------------------------
class SARIMAForecaster(BaseForecaster):
    def __init__(self, order=(1, 1, 1), seasonal_order=(1, 0, 0, 24)):
        super().__init__(name="SARIMA")
        self.order = order
        self.seasonal_order = seasonal_order
        self.model_res = None
        self.last_value = 0.0

    def fit(self, train_series: pd.Series, **kwargs):
        if not HAS_STATSMODELS:
            raise RuntimeError("statsmodels is not installed.")
        # If series is very short, adapt order
        n = len(train_series)
        seas = self.seasonal_order
        if n < 60:
            seas = (0, 0, 0, 0)
        try:
            model = SARIMAX(
                train_series.values,
                order=self.order,
                seasonal_order=seas,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            self.model_res = model.fit(disp=False, maxiter=50)
            self.is_fitted = True
            self.last_value = float(train_series.iloc[-1])
        except Exception:
            # Fall back to simpler order
            try:
                model = SARIMAX(train_series.values, order=(1, 1, 0), enforce_stationarity=False)
                self.model_res = model.fit(disp=False, maxiter=30)
                self.is_fitted = True
            except Exception:
                self.is_fitted = False

    def predict(self, steps: int, **kwargs) -> np.ndarray:
        if self.is_fitted and self.model_res is not None:
            try:
                forecast = self.model_res.forecast(steps=steps)
                return np.asarray(forecast, dtype=float)
            except Exception:
                pass
        return np.full(steps, self.last_value)

# ---------------------------------------------------------
# 3. PyTorch LSTM Forecaster
# ---------------------------------------------------------
class LSTMForecaster(BaseForecaster):
    def __init__(self, seq_len: int = 24, epochs: int = 25, lr: float = 0.005):
        super().__init__(name="LSTM (Deep Recurrent)")
        self.seq_len = seq_len
        self.epochs = epochs
        self.lr = lr
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        self.history_tail: Optional[np.ndarray] = None

    def fit(self, train_series: pd.Series, **kwargs):
        if not HAS_TORCH:
            raise RuntimeError("PyTorch is not available for LSTM training.")

        values = train_series.values.reshape(-1, 1)
        # Scaler fit STRICTLY on training data
        scaled = self.scaler.fit_transform(values)
        self.history_tail = scaled[-self.seq_len:]

        X, y = [], []
        for i in range(len(scaled) - self.seq_len):
            X.append(scaled[i:i + self.seq_len])
            y.append(scaled[i + self.seq_len])

        if len(X) < 10:
            # Not enough data for LSTM
            self.is_fitted = False
            return

        X_t = torch.tensor(np.array(X), dtype=torch.float32)
        y_t = torch.tensor(np.array(y), dtype=torch.float32)

        dataset = TensorDataset(X_t, y_t)
        loader = DataLoader(dataset, batch_size=32, shuffle=True)

        torch.manual_seed(42)
        self.model = PyTorchLSTM(input_dim=1, hidden_dim=32, num_layers=1)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.lr)

        self.model.train()
        for epoch in range(self.epochs):
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                pred = self.model(batch_x)
                loss = criterion(pred, batch_y)
                loss.backward()
                optimizer.step()

        self.model.eval()
        self.is_fitted = True

    def predict(self, steps: int, **kwargs) -> np.ndarray:
        if not self.is_fitted or self.model is None or self.history_tail is None:
            # Fallback
            return np.full(steps, 15.0)

        preds = []
        curr_seq = torch.tensor(self.history_tail, dtype=torch.float32).unsqueeze(0) # [1, seq_len, 1]

        self.model.eval()
        with torch.no_grad():
            for _ in range(steps):
                p = self.model(curr_seq) # [1, 1]
                preds.append(float(p.squeeze().item()))
                # Update window recursively
                curr_seq = torch.cat([curr_seq[:, 1:, :], p.unsqueeze(-1)], dim=1)

        preds_arr = np.array(preds).reshape(-1, 1)
        unscaled = self.scaler.inverse_transform(preds_arr).flatten()
        return unscaled

# ---------------------------------------------------------
# 4. Gradient Boosting Forecaster (HistGradientBoosting)
# ---------------------------------------------------------
class GradientBoostingForecaster(BaseForecaster):
    def __init__(self, lag_count: int = 24):
        super().__init__(name="Gradient Boosting (ML Baseline)")
        self.lag_count = lag_count
        self.model = HistGradientBoostingRegressor(random_state=42, max_iter=60)
        self.last_window: Optional[np.ndarray] = None

    def _create_features(self, series: pd.Series):
        df_feat = pd.DataFrame({'y': series.values})
        for i in range(1, self.lag_count + 1):
            df_feat[f'lag_{i}'] = df_feat['y'].shift(i)
        df_feat['rolling_mean_6'] = df_feat['y'].shift(1).rolling(6).mean()
        df_feat['rolling_mean_24'] = df_feat['y'].shift(1).rolling(24).mean()
        return df_feat.dropna()

    def fit(self, train_series: pd.Series, **kwargs):
        feat = self._create_features(train_series)
        if len(feat) < 20:
            self.is_fitted = False
            return
        X = feat.drop(columns=['y'])
        y = feat['y']
        self.model.fit(X, y)
        self.last_window = train_series.values[-self.lag_count:].copy()
        self.is_fitted = True

    def predict(self, steps: int, **kwargs) -> np.ndarray:
        if not self.is_fitted or self.last_window is None:
            return np.full(steps, 15.0)

        preds = []
        buf = list(self.last_window)
        for _ in range(steps):
            row = {}
            for i in range(1, self.lag_count + 1):
                row[f'lag_{i}'] = buf[-i]
            row['rolling_mean_6'] = np.mean(buf[-6:])
            row['rolling_mean_24'] = np.mean(buf[-24:]) if len(buf) >= 24 else np.mean(buf)
            X_step = pd.DataFrame([row])
            p = float(self.model.predict(X_step)[0])
            preds.append(p)
            buf.append(p)

        return np.array(preds)

# ---------------------------------------------------------
# 5. Prophet Forecaster Wrapper
# ---------------------------------------------------------
class ProphetForecaster(BaseForecaster):
    def __init__(self):
        super().__init__(name="Prophet")
        self.prophet_model = None

    def fit(self, train_series: pd.Series, timestamps: Optional[pd.Series] = None, **kwargs):
        if not HAS_PROPHET:
            self.is_fitted = False
            return
        # If prophet installed, fit
        try:
            df_p = pd.DataFrame({
                'ds': pd.to_datetime(timestamps if timestamps is not None else pd.date_range("2024-01-01", periods=len(train_series), freq='h')),
                'y': train_series.values
            })
            self.prophet_model = Prophet(daily_seasonality=True, weekly_seasonality=True)
            self.prophet_model.fit(df_p)
            self.is_fitted = True
        except Exception:
            self.is_fitted = False

    def predict(self, steps: int, **kwargs) -> np.ndarray:
        if not self.is_fitted or self.prophet_model is None:
            raise RuntimeError("Prophet is not installed or available on this system.")
        future = self.prophet_model.make_future_dataframe(periods=steps, freq='h', include_history=False)
        forecast = self.prophet_model.predict(future)
        return forecast['yhat'].values

def get_model_registry() -> Dict[str, BaseForecaster]:
    """Returns factory registry of supported forecasters."""
    return {
        "seasonal_naive": SeasonalNaiveForecaster(season_length=24),
        "sarima": SARIMAForecaster(order=(1, 1, 1), seasonal_order=(1, 0, 0, 24)),
        "lstm": LSTMForecaster(seq_len=24, epochs=20),
        "gradient_boosting": GradientBoostingForecaster(lag_count=24),
        "prophet": ProphetForecaster()
    }
