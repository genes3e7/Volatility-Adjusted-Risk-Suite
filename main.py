"""
Risk Suite Main Entry Point.

This script acts as the orchestrator. It imports modules from the 'src' package,
executes the analysis pipeline, and saves the final Excel report.
"""

import logging

import pandas as pd

from src.config_manager import RiskConfig
from src.data_loader import DataLoader
from src.risk_engine import RiskEngine


def setup_logging() -> None:
    """Configure console logging."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def main() -> None:
    """Execute the main analysis workflow."""
    setup_logging()
    logging.info("--- Starting Volatility-Adjusted Risk Suite ---")

    # 1. Initialize Modules
    try:
        config = RiskConfig()
        loader = DataLoader(config.settings)
        engine = RiskEngine(config)
    except Exception as e:
        logging.error("Initialization failed: %s", e)
        return

    current_results = []
    drift_results = []

    # 2. Process Assets
    for ticker in config.assets:
        logging.info("Processing %s...", ticker)

        data = loader.fetch_history(ticker)
        if data is None:
            continue

        prices = data["Close"]
        annual_days = engine.get_annual_days(ticker)
        vol_series = engine.calculate_volatility(prices, annual_days)

        # --- ANALYSIS A: Current Risk ---
        current_price = float(prices.iloc[-1])
        raw_vol = float(vol_series.iloc[-1])

        # Handle case where current volatility is still NaN (brand new listing)
        if pd.isna(raw_vol):
            logging.warning("  [WARN] Insufficient data for %s. Skipping.", ticker)
            continue

        floor = engine.calculate_dynamic_floor(vol_series, annual_days)

        effective_vol = max(raw_vol, floor)
        is_floored = effective_vol > raw_vol

        lookback = config.settings["lookback_days"]
        cycle_high = float(prices.tail(lookback).max())
        drawdown = (cycle_high - current_price) / cycle_high

        row_curr = {
            "Ticker": ticker,
            "Price": current_price,
            "Cycle High (1y)": cycle_high,
            "Drawdown": -drawdown,
            "Raw Vol": raw_vol,
            "Dynamic Floor": floor,
            "Floor Active?": "YES" if is_floored else "No",
        }

        # Add Safe Prices
        safe_prices = engine.compute_safe_prices(effective_vol, cycle_high)
        row_curr.update(safe_prices)
        current_results.append(row_curr)

        # --- ANALYSIS B: Leverage Drift ---
        drift_days = config.settings["drift_lookback_days"]
        window = prices.tail(drift_days)
        ath_date = window.idxmax()
        ath_price = float(window.max())

        try:
            ath_vol = float(vol_series.loc[ath_date])
        except KeyError:
            ath_vol = float(vol_series.asof(ath_date))

        # Calculate historical limits using ATH Vol
        hist_limits = engine.compute_safe_prices(ath_vol, ath_price)

        row_drift = {
            "Ticker": ticker,
            "ATH Date": str(ath_date.date()),
            "ATH Price": ath_price,
            "ATH Vol": ath_vol,
            "Current Price": current_price,
        }

        for k, v in hist_limits.items():
            row_drift[f"ATH {k}"] = v

        # Survival Check (Half Kelly)
        hk_price = hist_limits.get("Half Kelly Price")

        if hk_price is None or pd.isna(hk_price):
            row_drift["SURVIVAL CHECK"] = "⚠️ Insufficient History"
        elif current_price <= hk_price:
            row_drift["SURVIVAL CHECK"] = "❌ LIQUIDATED"
        else:
            margin = (current_price - hk_price) / current_price
            row_drift["SURVIVAL CHECK"] = f"SAFE (+{margin:.1%})"

        drift_results.append(row_drift)

    # 3. Generate Report
    if not current_results:
        logging.warning("No results generated.")
        return

    filename = "risk_analysis_report.xlsx"

    # Transpose for readability (Ticker as columns)
    df_curr = pd.DataFrame(current_results).set_index("Ticker").T
    df_drift = pd.DataFrame(drift_results).set_index("Ticker").T

    try:
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            df_curr.to_excel(writer, sheet_name="Current Risk")
            df_drift.to_excel(writer, sheet_name="Leverage Drift")
        logging.info("\n[SUCCESS] Report saved to %s", filename)
    except PermissionError:
        logging.error("\n[ERROR] Close %s and try again.", filename)


if __name__ == "__main__":
    main()
