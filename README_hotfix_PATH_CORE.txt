Hotfix pack (PATH+CORE) — 2025-08-13T20:43:01.891723Z

Fixes:
1) ModuleNotFoundError: 'core' in GitHub Actions
   - Provides 'core/' shim (core/__init__.py, core/utils.py).
   - Workflows now call Python with `-m`, ensuring repo root on sys.path.

2) Push rejects (non-fast-forward)
   - All commit steps now fetch & pull --rebase before push.

How to apply:
  • Upload the folders in this zip to the repo root (keep paths).
  • Commit to main (or upload to the main branch directly).
  • Re-run Actions (publish-factors / publish-prices / train-models).
