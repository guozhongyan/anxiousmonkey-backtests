
// ---- Base path auto-detect for GitHub Pages Project Sites ----
// Works whether the page loads at /anxiousmonkey-backtests/ or /anxiousmonkey-backtests/app/
function getRepoBase() {
  const parts = window.location.pathname.split('/').filter(Boolean);
  // parts[0] = repo name when hosted at /<repo>/..., fall back to '/'
  return parts.length ? `/${parts[0]}/` : '/';
}
const BASE = getRepoBase();
const bust = () => `?v=${Date.now()}`; // cache-busting to avoid stale JSON

const URLS = {
  factors: `${BASE}factors_namm50.json${bust()}`,
  model:   `${BASE}models/namm50.json${bust()}`,
  prices:  `${BASE}prices.json${bust()}`
};

// Robust fetch with human-friendly error message
async function fetchJSON(url) {
  const r = await fetch(url, { cache: 'no-store' });
  if (!r.ok) throw new Error(`HTTP ${r.status} ${url}`);
  return r.json();
}

// 建议：数据加载处加 try/catch，失败时提示
async function loadAll() {
  try {
    const [factors, model, prices] = await Promise.all([
      fetchJSON(URLS.factors),
      fetchJSON(URLS.model),
      fetchJSON(URLS.prices),
    ]);
    return { factors, model, prices };
  } catch (e) {
    alert(`加载数据失败：${e.message}`);
    throw e;
  }
}

const fmtPct = x => (x==null? "—" : (x*100).toFixed(2)+'%');
const $ = sel => document.querySelector(sel);

function lastVal(series){
  if(!series || !series.length) return null;
  const last = series[series.length-1];
  // series shape: [ts, a, b] or [ts, v]
  return last[1]==null? last[2] ?? null : last[1];
}

function badge(name, w){
  const span = document.createElement('span');
  span.className = 'b';
  span.textContent = `${name}: ${(w*100).toFixed(1)}%`;
  return span;
}

function playbook(model, factors){
  const w = model.weights || {};
  const hints = [];
  const naaim = factors.naaim_exposure?.series;
  const ndx50 = factors.ndx_breadth?.series;
  const china = factors.china_proxy?.series;
  const fred  = factors.fred_macro?.series;

  const na = lastVal(naaim);
  const b50 = lastVal(ndx50);
  const fx  = lastVal(china);
  const fm  = lastVal(fred);

  // Very light rules
  if(na!=null){
    if(na > 80) hints.push('NAAIM 高位，适度降杠杆，等待回落信号。');
    else if(na < 30) hints.push('NAAIM 低位，关注反弹确认后加仓。');
    else hints.push('NAAIM 中性区，维持基准仓位。');
  }
  if(b50!=null){
    if(b50 > 60) hints.push('NDX >50DMA 覆盖面广，偏多。');
    else if(b50 < 40) hints.push('NDX >50DMA 覆盖面收缩，偏防守。');
  }
  if(fm!=null){
    const dgs10 = fm[fm.length-1]?.[1];
    const dff   = fm[fm.length-1]?.[2];
    if(dgs10!=null && dff!=null){
      const slope = dgs10 - dff;
      if(slope < 0.25) hints.push('利率曲线偏平/倒挂，保持谨慎。');
      else hints.push('利率曲线走陡，风险偏好改善。');
    }
  }
  if(fx!=null){
    if(fx < 0) hints.push('China proxy 走弱，对全球风险资产的拖累需跟踪。');
  }
  if(!hints.length) hints.push('数据更新中，维持基准仓位。');
  return hints.join('\n');
}

function renderSpark(ctxId, series, mapY){
  const ctx = document.getElementById(ctxId);
  if(!ctx || !series) return;
  const data = series.map(([ts, a, b]) => ({x: ts, y: mapY? mapY(a,b): (a ?? b)})).filter(d=>d.y!=null);
  if(!data.length) return;
  new Chart(ctx, {
    type:'line',
    data:{ datasets:[{data, borderWidth:1.5, pointRadius:0, tension:.2}]},
    options:{responsive:true, scales:{x:{type:'time',display:false},y:{display:false}}, plugins:{legend:{display:false}, tooltip:{mode:'index',intersect:false}}}
  });
}

function renderPrices(prices){
  const box = $('#prices'); box.innerHTML='';
  if(!prices || !prices.tickers) { box.textContent='—'; return; }
  for(const t of prices.tickers){
    const el = document.createElement('div'); el.className='t';
    const chg = t.change ?? 0; const sign = chg>=0?'up':'dn';
    el.innerHTML = `<span class="sym">${t.symbol}</span> <span>${t.price?.toFixed(2)??'—'}</span> <span class="chg ${sign}">${(chg*100).toFixed(2)}%</span>`;
    box.appendChild(el);
  }
}

async function main(){
  try{
    const {factors, model, prices} = await loadAll();
    $('#asOf').textContent = factors.as_of || '—';
    $('#version').textContent = model.version || '—';
    // weights
    const wd = $('#weights'); wd.innerHTML='';
    const W = model.weights || {};
    Object.entries(W).forEach(([k,v])=> wd.appendChild(badge(k, v)));

    // KPIs
    $('#k-naaim').textContent = fmtPct(lastVal(factors.naaim_exposure?.series));
    $('#k-ndx50').textContent = fmtPct((lastVal(factors.ndx_breadth?.series)||0)/100);
    $('#k-china').textContent = (lastVal(factors.china_proxy?.series)?.toFixed(2)) ?? '—';
    $('#k-fred').textContent = '✓';

    // Charts
    renderSpark('chart-naaim', factors.naaim_exposure?.series, (v)=>v);
    renderSpark('chart-ndx50', factors.ndx_breadth?.series, (v)=>v);
    renderSpark('chart-china', factors.china_proxy?.series, (v)=>v);
    renderSpark('chart-fred', factors.fred_macro?.series, (a,b)=>a); // use DGS10

    // Playbook
    $('#playbookText').textContent = playbook(model, factors);

    // Prices (optional if present)
    if(prices) renderPrices(prices);
    else $('#prices').textContent = '—';

  }catch(e){
    console.error(e);
  }
}
document.addEventListener('DOMContentLoaded', main);
