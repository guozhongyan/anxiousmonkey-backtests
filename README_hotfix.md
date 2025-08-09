# AM Workflow Hotfix v2 (2025-08-09)

This hotfix fixes `ModuleNotFoundError: No module named 'tools'` by:
- Running Python in **package mode** via `runpy.run_module(...)`.
- Setting `PYTHONPATH` to the repo root.
- Ensuring `__init__.py` files exist for all package folders.
- Making `requirements.txt` optional.

## Replace steps
1. Upload all files in this zip keeping the folder structure (overwrite existing).
2. Commit to `main`.
3. In **Actions**, run `publish-factors`, then `train-models`.
