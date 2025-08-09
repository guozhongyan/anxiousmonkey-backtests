Hotfix: resilient NAAIM fetcher

Replace your repository file:
  fetchers/naaim.py  ->  (this package) fetchers_naaim.py (rename to naaim.py)

What it does:
- Tries multiple historical CSV URLs from naaim.org
- If 404, parses the NAAIM Exposure Index web page table
- If still not available, writes an empty CSV placeholder so workflow continues
- No API keys required (free sources only)
