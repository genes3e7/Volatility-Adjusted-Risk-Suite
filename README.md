# Volatility-Adjusted Risk Suite

![Python Support](https://img.shields.io/badge/python-3.11_to_3.14-blue)

A modular, professional-grade Python toolset for calculating safe leverage in volatile markets.

It combines **Current Risk Analysis** (for new positions) and **Leverage Drift Analysis** (for existing positions) into a single execution workflow with a multi-tab Excel output.

## 📂 Project Structure

The project follows a standard `src` layout for cleanliness and modularity.

```text
risk_suite/
├── config.json             # Central configuration (Assets & Settings)
├── main.py                 # ENTRY POINT (Run this script)
├── requirements.txt        # Production dependencies (Locked)
├── requirements-dev.txt    # Development dependencies (Locked)
├── README.md               # This file
└── src/                    # Internal logic modules
    ├── __init__.py
    ├── config_manager.py   # JSON loading logic
    ├── data_loader.py      # Yahoo Finance API handler
    └── risk_engine.py      # Core Mathematics (Volatility/Kelly)
```

## 🚀 Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Settings
Edit `config.json` to add your assets or adjust your risk tolerance.
* **Assets:** List of tickers (e.g., `BTC-USD`, `NVDA`).
* **Multipliers:** Safety factors (e.g., Death Floor = 2.5x Volatility).

### 3. Run the Suite
```bash
python main.py
```

### 4. View Results
Open **`risk_analysis_report.xlsx`**.

* **Tab 1: Current Risk**
    * Shows safe prices for entering **today**.
    * Uses **Dynamic Floors** to ignore fake calm periods (e.g., if BTC volatility drops below its 5-year 25th percentile).
* **Tab 2: Leverage Drift**
    * Shows the health of positions held from the **Cycle High (ATH)**.
    * Checks if your historical "Safe" position has drifted into mathematical liquidation.

## 🧪 Code Standards
* **PEP 8 Compliance:** Strictly followed for variable naming and layout.
* **Modular Design:** Logic separated into dedicated classes for maintainability.
* **Type Hinting:** Full Python typing support.
* **Error Handling:** Robust handling of missing data or API errors.
