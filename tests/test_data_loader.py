"""
Tests for DataLoader.
"""

import pandas as pd
import pytest

from src.data_loader import DataLoader


@pytest.fixture
def mock_settings():
    return {"drift_lookback_days": 100, "dynamic_floor": {"lookback_years": 1}}


def test_fetch_history_success(mocker, mock_settings):
    """Test successful data fetch."""
    loader = DataLoader(mock_settings)

    # Mock yfinance response
    mock_data = pd.DataFrame({"Close": [100, 101, 102]})
    mocker.patch("yfinance.download", return_value=mock_data)

    df = loader.fetch_history("BTC-USD")
    assert df is not None
    assert len(df) == 3
    assert "Close" in df.columns


def test_fetch_history_empty(mocker, mock_settings):
    """Test handling of empty dataframe (ticker not found)."""
    loader = DataLoader(mock_settings)
    mocker.patch("yfinance.download", return_value=pd.DataFrame())

    df = loader.fetch_history("INVALID-TICKER")
    assert df is None


def test_fetch_history_flatten_multiindex(mocker, mock_settings):
    """Test that MultiIndex columns (yfinance quirk) are flattened."""
    loader = DataLoader(mock_settings)

    # Create MultiIndex DataFrame (e.g., Price -> Close -> Ticker)
    arrays = [["Close"], ["BTC-USD"]]
    tuples = list(zip(*arrays))
    index = pd.MultiIndex.from_tuples(tuples, names=["Price", "Ticker"])
    mock_data = pd.DataFrame([100], columns=index)

    mocker.patch("yfinance.download", return_value=mock_data)

    df = loader.fetch_history("BTC-USD")
    assert isinstance(df.columns, pd.Index)
    assert not isinstance(df.columns, pd.MultiIndex)
    assert "Close" in df.columns
