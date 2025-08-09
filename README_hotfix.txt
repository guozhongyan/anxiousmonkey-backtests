
# AM Full Factor IO Hotfix (2025-08-09)

Contents:
- fetchers/naaim.py                (NAAIM CSV with URL fallbacks + keep-previous)
- fetchers/ndx_breadth_topn.py     (NDX >50DMA top-20 breadth, YF fallback)
- fetchers/china_proxy_fxi.py      (FXI close series)
- fetchers/fred_bundle.py          (FRED DGS10 & DFF daily)
- pipelines/compose_outputs.py     (writes docs/factors_namm50.json with 4 factors)
- models/namm50/train.py           (defines main(); writes docs/models/namm50.json)
- tools/utils.py                   (ensure_dir, ts_now_iso, zscore, rolling_sharpe, to_json_ready)

How to apply (web UI):
1) Download this zip and unzip locally.
2) In GitHub -> Code -> Add file -> Upload files, drag the extracted files/folders to the repo root so paths match.
3) Commit to main.
4) Run Actions:
   - publish-factors (or wait for push trigger)
   - train-models
After both succeed, you should have:
   - docs/factors_namm50.json      (NAAIM, FRED Macro, >50DMA, China Proxy)
   - docs/models/namm50.json       (NAMM-50 model summary with latest score & Sharpe)
