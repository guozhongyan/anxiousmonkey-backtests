const ROOT = location.pathname.includes('/anxiousmonkey-backtests/') ? '/anxiousmonkey-backtests/' : '/';
const FACTORS_URL = ROOT + 'factors_namm50.json';
const MODELS_URL = ROOT + 'models/namm50.json';
const PRICES_URL = ROOT + 'prices.json';

async function fetchJson(url, retries=3){
  for(let i=0;i<retries;i++){
    try{
      const res = await fetch(url);
      if(!res.ok) throw new Error(res.status);
      return await res.json();
    }catch(e){
      if(i===retries-1) return null;
      await new Promise(r=>setTimeout(r,500));
    }
  }
}

function getLatest(series){
  if(!series || !series.length) return null;
  const last = series[series.length-1];
  for(let i=last.length-1;i>=0;i--){
    const v = Number(last[i]);
    if(!isNaN(v)) return v;
  }
  return null;
}

function updateKpi(id,val){
  document.getElementById(id).textContent = val!=null ? val.toFixed(1) : '—';
}

function renderWeights(weights){
  const map = {NAAM:'NAAIM',NAAIM:'NAAIM',NAMM:'NAAIM',FRED:'FRED',NDX50:'NDX50',CHINA:'CHINA'};
  const container = document.getElementById('weights');
  container.innerHTML='';
  Object.entries(weights||{}).forEach(([k,v])=>{
    if(!(k in map)) return;
    const pct = (v*100).toFixed(0);
    const row = document.createElement('div');
    row.className='weight-row';
    row.innerHTML = `<span class="w-label">${map[k]}</span>`+
      `<div class="w-bar"><div class="w-fill" style="width:${pct}%"></div></div>`+
      `<span class="w-val">${pct}%</span>`;
    container.appendChild(row);
  });
}

function renderPlaybook(stats){
  const pb = document.getElementById('playbook');
  let text='Neutral';
  if(stats.naaim>75 && stats.ndx50>50) text='Risk-On';
  else if(stats.naaim<25 && stats.ndx50<50) text='Risk-Off';
  pb.textContent=text;
}

function toSeries(arr){
  if(!arr) return [];
  return arr.map(pt=>{
    const [d,...vals]=pt;
    const value = Number(vals.reverse().find(v=>!isNaN(v)));
    return {time:d, value};
  });
}

function renderChart(id,series){
  if(!series || !series.length) return;
  const el = document.getElementById(id);
  const chart = LightweightCharts.createChart(el,{height:240,layout:{textColor:'#e9eef6',background:{type:'solid',color:'transparent'}},grid:{vertLines:{color:'#2a3142'},horzLines:{color:'#2a3142'}},rightPriceScale:{borderColor:'#2a3142'},timeScale:{borderColor:'#2a3142'}});
  const line = chart.addLineSeries({color:'#6ea8fe'});
  line.setData(toSeries(series));
}

function renderSpot(prices){
  const el = document.getElementById('spot');
  if(!prices || !prices.prices){el.textContent='—';return;}
  const tickers=['SPY','QQQ','TQQQ'];
  el.textContent = tickers.map(t=>`${t}: ${prices.prices[t]??'—'}`).join(' | ');
}

async function load(){
  const [factors, models, prices] = await Promise.all([
    fetchJson(FACTORS_URL),
    fetchJson(MODELS_URL),
    fetchJson(PRICES_URL)
  ]);

  if(factors && factors.as_of){
    document.getElementById('lastUpdated').textContent = new Date(factors.as_of).toLocaleString();
  }

  const stats = {
    naaim: getLatest(factors?.factors?.NAAM || factors?.factors?.NAMM || factors?.factors?.NAAIM),
    ndx50: getLatest(factors?.factors?.NDX50),
    china: getLatest(factors?.factors?.CHINA),
    fred: getLatest(factors?.factors?.FRED)
  };

  updateKpi('kpiNaaim', stats.naaim);
  updateKpi('kpiNdx50', stats.ndx50);
  updateKpi('kpiChina', stats.china);
  updateKpi('kpiFred', stats.fred);

  if(models && models.weights) renderWeights(models.weights);
  renderPlaybook(stats);
  renderChart('naaimChart', factors?.factors?.NAAM || factors?.factors?.NAMM || factors?.factors?.NAAIM);
  renderChart('ndxChart', factors?.factors?.NDX50);
  renderChart('chinaChart', factors?.factors?.CHINA);
  renderChart('fredChart', factors?.factors?.FRED);
  renderSpot(prices);
}

document.getElementById('refreshBtn').addEventListener('click', load);
load();
