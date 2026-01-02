"""
Configuration Manager Module.

Handles loading, parsing, and providing typed access to settings from
the JSON configuration file.
"""

import json
import logging
from typing import Any, Dict, List


class RiskConfig:
    """
    Manages application settings and risk parameters.

    Attributes:
        path (str): Path to the configuration file.
        data (Dict): Raw loaded configuration data.
    """

    def __init__(self, config_path: str = "config.json"):
        """Initialize and load the configuration."""
        self.path = config_path
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load JSON data from file with error handling."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error("CRITICAL: Configuration file %s not found.", self.path)
            raise
        except json.JSONDecodeError:
            logging.error("CRITICAL: Failed to decode JSON from %s.", self.path)
            raise

    @property
    def assets(self) -> List[str]:
        """Return the list of asset tickers."""
        return self.data.get("assets", [])

    @property
    def settings(self) -> Dict[str, Any]:
        """Return the general settings dictionary."""
        return self.data.get("settings", {})

    @property
    def multipliers(self) -> Dict[str, float]:
        """Return the risk multiplier dictionary."""
        return self.data.get("risk_multipliers", {})
