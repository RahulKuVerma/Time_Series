"""
tests/test_models.py
--------------------
Unit tests for forecasting models: Seasonal Naive, SARIMA, LSTM, Gradient Boosting.
"""

import sys
import os
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ml-service')))

from models import (
    SeasonalNaiveForecaster,
    SARIMAForecaster,
    LSTMForecaster,
    GradientBoostingForecaster,
    get_model_registry
)

@pytest.fixture
def sample_series():
    # 200 hours of synthetic sinusoidal curve
    np.random.seed(42)
    t = np.arange(200)
    cycle = 15.0 + 5.0 * np.sin(2 * np.pi * t / 24.0) + np.random.normal(0, 0.5, 200)
    return pd.Series(cycle)

def test_seasonal_naive_forecast(sample_series):
    model = SeasonalNaiveForecaster(season_length=24)
    model.fit(sample_series)
    preds = model.predict(steps=48)
    assert len(preds) == 48
    # Should repeat the last 24 values
    np.testing.assert_allclose(preds[:24], preds[24:])

def test_sarima_forecast(sample_series):
    model = SARIMAForecaster(order=(1, 1, 0), seasonal_order=(0, 0, 0, 0))
    model.fit(sample_series)
    preds = model.predict(steps=24)
    assert len(preds) == 24
    assert not np.isnan(preds).any()

def test_gradient_boosting_forecast(sample_series):
    model = GradientBoostingForecaster(lag_count=24)
    model.fit(sample_series)
    preds = model.predict(steps=24)
    assert len(preds) == 24
    assert (preds >= 0).all()

def test_lstm_forecast(sample_series):
    model = LSTMForecaster(seq_len=24, epochs=5, lr=0.01)
    model.fit(sample_series)
    preds = model.predict(steps=24)
    assert len(preds) == 24
    assert not np.isnan(preds).any()

def test_model_registry():
    registry = get_model_registry()
    assert "seasonal_naive" in registry
    assert "sarima" in registry
    assert "lstm" in registry
    assert "gradient_boosting" in registry
    assert "prophet" in registry
