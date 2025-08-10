# AM Full Factor IO Hotfix (2025‑08‑10)

一键替换以下文件/目录（解压到仓库根目录，选择“覆盖”）：

- `tools/utils.py`（新增网络抓取与 Wayback 兜底工具、CSV/JSON 安全写入）
- `fetchers/naaim.py`（多源 + Wayback + 占位）
- `fetchers/ndx_breadth.py`（Top‑N + 逐步降级 + 占位/沿用旧值）
- `fetchers/china_proxy_fxi.py`（YF 拉取 FXI，失败时占位/沿用旧值）
- `fetchers/fred_bundle.py`（优先 FRED API；无 KEY 时 FredGraph CSV 兜底；失败写占位）
- `fetchers/prices.py`（AlphaVantage 优先；无 KEY 切 YF；失败安全占位）
- `pipelines/compose_outputs.py`（容错合成，缺失即 `null`，不再报错）

> 解压后直接 push 到 `main`，再运行 **publish-factors** 与（可选）**publish-prices** 工作流。
