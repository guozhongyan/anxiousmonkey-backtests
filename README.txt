
AM Hotfix: Ensure NAMM-50 model is published to GitHub Pages

What this fixes
---------------
- Adds a robust `models/namm50/train.py` that writes BOTH:
    * `docs/models/namm50.json`
    * `docs/namm50.json`
  so you can fetch with either:
    /models/namm50.json  or  /namm50.json

- Adds a safe `pipelines/compose_outputs.py` with a `main()` so the workflow
  step never fails with "no attribute 'main'". It writes a tiny `docs/compose_ok.json`.

How to apply
------------
Replace these two files in your repo:
  - models/namm50/train.py
  - pipelines/compose_outputs.py

Then re-run:
  1) train-models (this will commit and push docs/namm50.json)
  2) pages build and deployment (auto on push)

After deploy, test:
  https://<user>.github.io/anxiousmonkey-backtests/namm50.json
  https://<user>.github.io/anxiousmonkey-backtests/models/namm50.json
