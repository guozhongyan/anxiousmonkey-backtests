# AM Hotfix: PYTHONPATH + Packages (2025-08-09)

Fixes `ModuleNotFoundError: No module named 'tools'` on GitHub Actions by:
- Exporting `PYTHONPATH=${{ github.workspace }}` in workflows.
- Adding `__init__.py` files to `fetchers/`, `models/`, `models/namm50/`, `tools/`, `pipelines/`.
- Optional `bootstrap.py` for local runs (`import bootstrap`).

Upload to the repo root (keep paths).
