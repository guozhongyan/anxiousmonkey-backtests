
const BASE = 'https://guozhongyan.github.io/anxiousmonkey-backtests';
const FACTORS_URL = `${BASE}/factors_namm50.json`;
const MODEL_URL   = `${BASE}/models/namm50.json`;
const PRICES_URL  = `${BASE}/prices.json`;

function fmtNum(v, digits=2) {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  const n = Number(v);
  if (!Number.isFinite(n)) return '—';
  return n.toLocaleString(undefined, {maximumFractionDigits: digits});
}
async function fetchJson(url) {
  const u = `${url}?t=${Date.now()}`;
  const res = await fetch(u, {cache:'no-store'});
  if (!res.ok) throw new Error(`HTTP ${res.status} @ ${u}`);
  return res.json();
}
function parseSeries(arr) {
  const xs=[], ys=[];
  if (!Array.isArray(arr)) return {xs,ys};
  for (const item of arr) {
    if (!Array.isArray(item) || item.length < 2) continue;
    let d, v;
    if (item.length>=3) { d=item[0]; v=item[2]; }
    else { d=item[0]; v=item[1]; }
    const y = Number(v);
    if (!Number.isFinite(y)) continue;
    xs.push(d); ys.push(y);
  }
  return {xs,ys};
}
function ensureChart(ctx, type, data, opts){
  if (!ctx) return null;
  if (ctx._amChart) { ctx._amChart.destroy(); }
  ctx._amChart = new Chart(ctx, { type, data, options: opts || {responsive:true,maintainAspectRatio:false,
    plugins:{legend:{display:false}}, scales:{x:{display:false},y:{display:true,grid:{color:'rgba(255,255,255,.05)'}} } } });
  return ctx._amChart;
}
function renderWeights(model){
  const weights = (model && model.weights) || {};
  const labels = Object.keys(weights);
  const vals   = labels.map(k=>Number(weights[k]||0));
  const colors = ['#7aa2ff','#8bd2fd','#7de3c1','#ffd47e','#f8a0d4','#c6b6ff','#a8ffbf','#ffb4b4'];
  const ds = { labels, datasets:[{ data:vals, backgroundColor:labels.map((_,i)=>colors[i%colors.length]), borderWidth:0 }] };
  const ctx = document.getElementById('wChart').getContext('2d');
  ensureChart(ctx,'doughnut', ds, {plugins:{legend:{display:false}}});
  const legend = document.getElementById('weight-legend');
  legend.innerHTML = labels.map((l,i)=>`<span class="badge">${l}: ${fmtNum(vals[i]*100,2)}%</span>`).join(' ');
}
function renderPlaybook(model){
  const note = (model && model.latest && model.latest.note) || 'Playbook: Neutral · 观察为主；仅在强信号共振时加减仓，保持中性敞口。';
  document.getElementById('playbook').textContent = note;
}
function renderKPI(series, id){
  const ys = parseSeries(series).ys;
  const last = ys.length ? ys[ys.length-1] : null;
  document.getElementById(id).textContent = fmtNum(last, 2);
}
function renderLine(canvasId, series){
  const el = document.getElementById(canvasId);
  if (!el) return;
  const {xs, ys} = parseSeries(series);
  ensureChart(el.getContext('2d'),'line', {
    labels: xs,
    datasets:[{data:ys, borderWidth:1.5, pointRadius:0, tension:.2}]
  });
}
function renderFactors(j){
  const f = (j && j.factors) || {};
  const asof = (j && j.as_of) ? new Date(j.as_of) : null;
  if (asof) document.getElementById('asof').textContent = `Last updated ${asof.toLocaleString()}`;
  if (f.naaim_exposure?.series){ renderKPI(f.naaim_exposure.series, 'kpi-naaim'); renderLine('naaimChart', f.naaim_exposure.series); }
  if (f.ndx_breadth?.series){ renderKPI(f.ndx_breadth.series, 'kpi-ndx50'); renderLine('ndxChart', f.ndx_breadth.series); }
  if (f.china_proxy?.series){ renderKPI(f.china_proxy.series, 'kpi-china'); renderLine('chinaChart', f.china_proxy.series); }
  if (f.fred_macro?.series){ renderKPI(f.fred_macro.series, 'kpi-fred'); renderLine('fredChart', f.fred_macro.series); }
}
function renderModel(j){ renderWeights(j||{}); renderPlaybook(j||{}); }
function renderSpot(prices){
  const box = document.getElementById('spot');
  const arr = (prices && prices.quotes) || [];
  if (!arr.length) { box.textContent = '—'; return; }
  box.innerHTML = arr.map(q => `<span class="badge">${q.symbol}: ${fmtNum(q.price, 2)}</span>`).join('');
}
function renderSpotEmpty(){ document.getElementById('spot').textContent = '—'; }

async function loadAll(){
  try{
    const [factors, model, prices] = await Promise.all([
      fetchJson(FACTORS_URL),
      fetchJson(MODEL_URL),
      fetchJson(PRICES_URL).catch(()=>null)
    ]);
    renderFactors(factors);
    renderModel(model);
    if (prices) renderSpot(prices); else renderSpotEmpty();
  }catch(e){ alert(`加载失败: ${e.message}`); console.error(e); }
}
document.getElementById('btnRefresh').addEventListener('click', loadAll);
document.addEventListener('DOMContentLoaded', loadAll);
