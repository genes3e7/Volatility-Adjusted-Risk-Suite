"""
Data Loader Module.

Handles fetching historical market data from external APIs (Yahoo Finance).
"""

import logging
from typing import Any, Dict, Optional

import pandas as pd
import yfinance as yf


class DataLoader:
    """Fetches and preprocesses financial data."""

    def __init__(self, settings: Dict[str, Any]):
        """
        Initialize the loader with configuration settings.

        Args:
            settings: The 'settings' dictionary from RiskConfig.
        """
        self.settings = settings

    def fetch_history(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Fetches historical data sufficient for both dynamic floors and drift.

        Args:
            ticker: The asset symbol (e.g., 'BTC-USD').

        Returns:
            pd.DataFrame or None: Historical price data.
        """
        drift_days = self.settings.get("drift_lookback_days", 1825)
        floor_cfg = self.settings.get("dynamic_floor", {})
        floor_years = floor_cfg.get("lookback_years", 5)

        # Calculate max lookback needed (max of drift or dynamic floor)
        floor_days = floor_years * 365
        max_days = max(drift_days, floor_days) + 365  # Add buffer

        # Convert to year string for yfinance (e.g., "7y")
        years_str = f"{int(max_days / 365) + 1}y"

        try:
            data = yf.download(ticker, period=years_str, interval="1d", progress=False)

            if data.empty:
                return None

            # Flatten MultiIndex columns if present (compatibility fix)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            return data

        except Exception as e:
            logging.error("Error fetching data for %s: %s", ticker, e)
            return None
