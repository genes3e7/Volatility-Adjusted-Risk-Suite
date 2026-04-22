"""
Risk Engine Module.

Contains the core mathematical logic for volatility calculation,
dynamic floor determination, and safe price projection.
"""

from typing import Dict

import numpy as np
import pandas as pd

from src.config_manager import RiskConfig


class RiskEngine:
    """Performs mathematical risk calculations"""

    def __init__(self, config: RiskConfig):
        """Initialize the engine with the configuration object."""
        self.config = config
        self.settings = config.settings

    def get_annual_days(self, ticker: str) -> int:
        """Determine trading days based on asset class."""
        if "-" in ticker:
            return self.settings.get("crypto_trading_days", 365)
        return self.settings.get("stock_trading_days", 252)

    def calculate_volatility(self, prices: pd.Series, annual_days: int) -> pd.Series:
        """
        Calculate annualized rolling volatility.

        Updated to use min_periods=5 to handle new listings (IPOs)
        that haven't been trading for the full window (30 days) yet.
        """
        window = self.settings.get("volatility_window", 30)
        log_ret = np.log(prices / prices.shift(1))

        # Fix: Allow calculation if we have at least 5 days of data
        rolling_vol = log_ret.rolling(window=window, min_periods=5).std() * np.sqrt(annual_days)
        return rolling_vol

    def calculate_dynamic_floor(self, rolling_vol: pd.Series, annual_days: int) -> float:
        """Calculate the 25th percentile floor from historical volatility."""
        cfg = self.settings.get("dynamic_floor", {})
        years = cfg.get("lookback_years", 5)
        percentile = cfg.get("percentile", 0.25)

        window_size = int(years * annual_days)

        if len(rolling_vol) < window_size:
            return 0.50  # Safe fallback if insufficient history

        history = rolling_vol.tail(window_size)
        return float(history.quantile(percentile))

    def compute_safe_prices(self, vol: float, cycle_high: float) -> Dict[str, float]:
        """Generate the dictionary of safe prices based on multipliers."""
        res = {}

        # Guard clause: If volatility is NaN, return None for prices
        if pd.isna(vol):
            for name in self.config.multipliers.keys():
                res[f"{name} Price"] = None
            return res

        max_cap = self.settings.get("max_crash_cap", 0.85)

        for name, mult in self.config.multipliers.items():
            crash = vol * mult
            if crash > max_cap:
                crash = max_cap
            res[f"{name} Price"] = cycle_high * (1 - crash)

        return res
