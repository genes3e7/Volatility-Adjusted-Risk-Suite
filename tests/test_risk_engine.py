"""
Tests for RiskEngine.
Stresses Math, NaN handling, and Edge Cases.
"""

import numpy as np
import pandas as pd
import pytest

from src.config_manager import RiskConfig
from src.risk_engine import RiskEngine


@pytest.fixture
def mock_config(mocker):
    """Mock configuration with standard settings."""
    config = mocker.Mock(spec=RiskConfig)
    config.settings = {
        "volatility_window": 30,
        "crypto_trading_days": 365,
        "stock_trading_days": 252,
        "max_crash_cap": 0.85,
        "dynamic_floor": {"lookback_years": 5, "percentile": 0.25},
    }
    config.multipliers = {"Half Kelly": 1.5}
    return config


def test_volatility_calculation_standard(mock_config):
    """Test normal volatility calculation."""
    engine = RiskEngine(mock_config)
    # Create a predictable price series (1% daily growth)
    prices = pd.Series([100 * (1.01) ** i for i in range(100)])

    vol = engine.calculate_volatility(prices, 365)
    # Volatility should be roughly calculated, not NaN
    assert not vol.isna().all()
    assert vol.iloc[-1] > 0


def test_volatility_short_history_bmnr_case(mock_config):
    """
    Test the 'BMNR' Edge Case: Asset exists but history < 30 days.
    The engine should NOT return all NaNs if min_periods is set correctly.
    """
    engine = RiskEngine(mock_config)
    # Only 10 days of data
    prices = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109])

    vol = engine.calculate_volatility(prices, 365)

    # Should have values at the end, despite short history
    assert not pd.isna(vol.iloc[-1])


def test_dynamic_floor_insufficient_history(mock_config):
    """Test fallback when history is shorter than the 5-year lookback."""
    engine = RiskEngine(mock_config)
    # Short volatility history
    short_vol = pd.Series([0.5, 0.6, 0.4])

    floor = engine.calculate_dynamic_floor(short_vol, 365)

    # Should fallback to default safe 0.50
    assert floor == 0.50


def test_compute_safe_prices_nan_volatility(mock_config):
    """
    Test safe price calculation when volatility is NaN.
    Should handle gracefully without crashing.
    """
    engine = RiskEngine(mock_config)

    # Pass NaN as volatility
    result = engine.compute_safe_prices(np.nan, cycle_high=100.0)

    assert result["Half Kelly Price"] is None


def test_compute_safe_prices_hard_cap(mock_config):
    """Ensure crashes are capped at 85% (Max Crash Cap)."""
    engine = RiskEngine(mock_config)

    # Insane volatility (1000%)
    result = engine.compute_safe_prices(vol=10.0, cycle_high=100.0)

    # 1.5 multiplier * 10.0 vol = 1500% crash -> Should cap at 85%
    # Price = 100 * (1 - 0.85) = 15.0
    expected_price = 100.0 * (1 - 0.85)
    assert result["Half Kelly Price"] == pytest.approx(expected_price)
