# AM Workflow Hotfix Package

This package fixes `ModuleNotFoundError: No module named 'tools'` by running Python in **package mode** and ensuring
required package init files exist.

## What files are included
- `.github/workflows/publish-factors.yml`
- `.github/workflows/train-models.yml`
- Empty package initializers: `fetchers/__init__.py`, `pipelines/__init__.py`, `tools/__init__.py`,
  `models/__init__.py`, `namm50/__init__.py`, `signals/__init__.py`

## How to use
1. Drag-and-drop the `fetchers/`, `pipelines/`, `tools/`, `models/`, `namm50/`, `signals/` folders from this zip
   into the repo root so that **each** directory contains an empty `__init__.py`. (If the folder already exists, keep your files—only add `__init__.py`.)
2. Replace your existing workflow files with ones from `.github/workflows/` in this package.
3. Go to **Actions** and run:
   - `publish-factors`
   - `train-models`

No Python source files need to be edited.
Generated on 2025-08-09T14:28:49.445093Z.
