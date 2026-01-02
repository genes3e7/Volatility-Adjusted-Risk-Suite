"""
Tests for ConfigManager.
"""

import json

import pytest

from src.config_manager import RiskConfig

# Mock config data
MOCK_CONFIG = {
    "assets": ["BTC-USD"],
    "risk_multipliers": {"Half Kelly": 1.5},
    "settings": {
        "lookback_days": 365,
        "crypto_trading_days": 365,
        "stock_trading_days": 252,
        "dynamic_floor": {"lookback_years": 5, "percentile": 0.25},
    },
}


def test_load_valid_config(tmp_path):
    """Ensure valid JSON loads correctly."""
    p = tmp_path / "config.json"
    p.write_text(json.dumps(MOCK_CONFIG), encoding="utf-8")

    config = RiskConfig(str(p))
    assert config.assets == ["BTC-USD"]
    assert config.multipliers["Half Kelly"] == 1.5


def test_missing_config_file():
    """Ensure missing file raises FileNotFoundError (or handles gracefully)."""
    with pytest.raises(FileNotFoundError):
        RiskConfig("non_existent.json")


def test_malformed_json(tmp_path):
    """Ensure broken JSON raises an error."""
    p = tmp_path / "bad.json"
    p.write_text("{broken_json: ", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        RiskConfig(str(p))


def test_missing_keys(tmp_path):
    """Ensure missing keys return default empty values, not crashes."""
    p = tmp_path / "empty.json"
    p.write_text("{}", encoding="utf-8")

    config = RiskConfig(str(p))
    assert config.assets == []
    assert config.settings == {}
