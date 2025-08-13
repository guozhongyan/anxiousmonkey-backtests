
# NAMM-50 Free-Source Training Hotfix

This patch:
- removes hard dependency on `core/tools` imports in training
- uses **Alpha Vantage `TIME_SERIES_DAILY_ADJUSTED` (free)** for history
- consumes whatever factors are already available (NAAIM + FRED today)
- runs a quick **random weight search** to maximize daily Sharpe
- emits `docs/models/namm50.json` the UI expects (with bucketed weights)

## How to install
1. Unzip at repo root so paths are preserved.
2. Ensure repo secret **ALPHAVANTAGE_API_KEY** exists.
3. Run the workflow **train-models-lite** once from Actions.
4. Refresh your app; donut weights should no longer be 100% NAAM.
