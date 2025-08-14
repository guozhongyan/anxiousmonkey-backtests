AnxiousMonkey CI/Core Hotfix — 2025-08-14 02:35:25Z

What this fixes
---------------
1) ModuleNotFoundError: 'core'
   - Adds a lightweight 'core' package with utils (ensure_dir, ts_now_iso, write_json, to_json_ready, zscore).
   - Keeps legacy imports working: `from core.utils import ...`

2) JSON writer signature mismatch
   - write_json now accepts 'indent=' and forwards kwargs safely.

3) GitHub Actions non-fast-forward push
   - Workflows pull --rebase before pushing.

4) Missing PYTHONPATH & ALPHAVANTAGE_API_KEY
   - Workflows export PYTHONPATH=.
   - Train workflows pass ALPHAVANTAGE_API_KEY from repository secrets.

How to apply
------------
1. Unzip these files at the ROOT of your repository (do not change paths).
2. Commit to main (or your default branch).
3. In GitHub > Actions, run these workflows in order:
   - publish-factors
   - train-models
   - train-models-lite

Prereqs
-------
- Settings > Secrets and variables > Actions:
  add repository secret:  ALPHAVANTAGE_API_KEY

Files included
--------------
- core/__init__.py
- core/utils.py
- .github/workflows/publish-factors.yml
- .github/workflows/train-models.yml
- .github/workflows/train-models-lite.yml
- README_hotfix.txt