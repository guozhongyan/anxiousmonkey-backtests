# Hotfix: Switch Spot prices to Alpha Vantage GLOBAL_QUOTE

This hotfix replaces `fetchers/prices.py` so the app shows near‑real‑time quotes
(GLOBAL_QUOTE, ~15 min delay), with a fallback to EOD `TIME_SERIES_DAILY`.

## Files
- `fetchers/prices.py` — main fetcher (symbols: SPY, QQQ, TQQQ, SOXL, FEZ, CURE)
- `.github/workflows/publish-prices.yml` — optional workflow (use it if yours is broken)

## How to apply
1. In GitHub → Settings → Secrets → Actions, set `ALPHAVANTAGE_API_KEY`.
2. Upload/replace the files above in your repo.
3. Run the workflow **publish-prices** (or wait for the cron).

Output is written to `docs/prices.json`. The app reads it automatically.
