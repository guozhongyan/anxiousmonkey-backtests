
AnxiousMonkey Pages Hotfix — 2025-08-13 19:56:21Z

What this zip fixes:
1) Adds a working GitHub Pages workflow (.github/workflows/deploy-pages.yml) — with required environment.name=github-pages.
2) Ensures publish-factors / train-models / publish-prices jobs run with PYTHONPATH and do not crash on 'core'/'tools' imports.
3) Provides core/utils.py and a tools/utils.py shim to keep old imports working.
4) Minimal compose_outputs.py (with main()) to write docs/factors_namm50.json.
5) Minimal NAMM-50 train.py to write docs/models/namm50.json.
6) Free AlphaVantage prices fetcher (TIME_SERIES_DAILY) writing docs/prices.json.
7) docs/index.html convenience landing (links to /app/).

How to apply:
- Drop these files/folders at the repo root, keep existing app/ code.
- Commit to main. Ensure repo Settings → Pages → Source = GitHub Actions.
- Run 'publish-factors' and 'train-models' workflows, then 'Deploy Pages' triggers on push to main.

Secrets:
- ALPHAVANTAGE_API_KEY (required by publish-prices).
