am_naaim_404_hotfix (2025-08-10)

Usage
-----
1) Unzip at the ROOT of your repo (anxiousmonkey-backtests).
2) This will replace: fetchers/naaim.py
3) Commit to main, then re-run 'publish-factors'.

What changed
------------
- Multi-source fetch for NAAIM CSV (primary, www mirror, Wayback snapshot).
- If all fail: keep previous CSV if exists; else write an empty placeholder (date,value).
- Prevents workflow from failing on 404 while keeping downstream schema stable.
