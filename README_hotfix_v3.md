# Anxious Monkey — Frontend Hotfix v3

替换 `app/` 目录的三个文件：

- `app/index.html`
- `app/styles.css`
- `app/app.js`

主要改动：
- 修复画布错误（destroy & clear；空数据不绘图）
- 缩小饼图占位（≤260px，移动端更小）
- Spot 增加 SOXL/FEZ/CURE，来自 `docs/prices.json`
- 顶部显示每个因子的 LIVE/MISSING
- 启发式 Playbook + Up Probability 兜底显示

前端仅读取：
- `docs/models/namm50.json`
- `docs/factors_namm50.json`
- `docs/prices.json`

提交到 Pages 分支后刷新即可。
