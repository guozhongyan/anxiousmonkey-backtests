/* Anxious Monkey – Live Alpha (vanilla) */

const FACTORS_URL = './factors_namm50.json';
const MODEL_URL   = './models/namm50.json';
const PRICES_URL  = './prices.json';

const el = sel => document.querySelector(sel);
const fmtPct = v => (v == null || Number.isNaN(v)) ? '—' : `${(v*1).toFixed(2)}%`;
const fmtNum = v => (v == null || Number.isNaN(v)) ? '—' : (Math.abs(v)>=100 ? v.toFixed(0) : v.toFixed(2));
const toast = (msg) => {
  const t = el('#toast'); t.textContent = msg; t.classList.remove('hidden');
  clearTimeout(toast._t); toast._t = setTimeout(()=>t.classList.add('hidden'), 3800);
};

function last(series){
  if (!Array.isArray(series) || !series.length) return null;
  const item = series[series.length-1];
  // support [ts, value] or [ts, v1, v2]
  const val = Array.isArray(item) ? item[item.length-1] : null;
  return (val==null||isNaN(val)) ? null : +val;
}

function toLine(series, idx=1){ // series:[[ts, v],[...]] or mixed
  if(!Array.isArray(series)) return {labels:[],data:[]};
  const labels=[], data=[];
  for(const row of series){
    if(!Array.isArray(row)) continue;
    const ts = row[0];
    const v  = row[idx] ?? row[row.length-1];
    if(ts && v!=null && !Number.isNaN(+v)){ labels.push(ts); data.push(+v); }
  }
  return {labels,data};
}

function computeFredSpread(fred){ // prefer 10Y-FF
  // fred.series columns may be ["DGS10","DFF"] or triplets with name at [0]
  if(!fred || !Array.isArray(fred.series)) return null;
  const rows = fred.series;
  const out = rows.map(r=>{
    if(Array.isArray(r)){
      const ts = r[0];
      // try two-col: [ts, DGS10, DFF]
      const y10 = r[1]; const ff = r[2];
      if(ts!=null && y10!=null && ff!=null) return [ts, (+y10) - (+ff)];
    }
    return null;
  }).filter(Boolean);
  return out;
}

function makeLine(ctx, labels, data, label){
  return new Chart(ctx, {
    type:'line',
    data:{ labels, datasets:[{
      label, data, tension:.24, borderWidth:2, pointRadius:0,
    }]},
    options:{
      responsive:true,
      maintainAspectRatio:false,
      scales:{
        x:{ type:'timeseries', ticks:{ color:'#a7b0c0' }, grid:{ color:'#253047' } },
        y:{ ticks:{ color:'#a7b0c0' }, grid:{ color:'#253047' } }
      },
      plugins:{
        legend:{ display:false },
        tooltip:{ intersect:false, mode:'index' }
      }
    }
  });
}

function makeDoughnut(ctx, labels, data){
  const palette = ['#6ea8fe','#8eecf5','#6be585','#ffcc66'];
  return new Chart(ctx,{
    type:'doughnut',
    data:{ labels, datasets:[{ data, backgroundColor:palette, borderWidth:0 }]},
    options:{
      cutout:'62%',
      plugins:{ legend:{ display:false } }
    }
  });
}

async function fetchJSON(u){
  const r = await fetch(u, {cache:'no-store'});
  if(!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

function setKpi(id, v){ el(id).textContent = (typeof v === 'string') ? v : fmtPct(v); }

function playbookText({naaim,lastNdx50,fredSpread}){
  // 极简规则：NAAIM>60 & NDX50>50 & spread>0 => Risk-On；反之 Risk-Off；否则 Neutral
  if(naaim!=null && naaim>60 && lastNdx50!=null && lastNdx50>50 && fredSpread!=null && fredSpread>0){
    return "Playbook: Risk-On ↗︎  • 提高 beta，顺势持有；若次日回撤<1.2% 继续持有。";
  }
  if(naaim!=null && naaim<30 && lastNdx50!=null && lastNdx50<40 && fredSpread!=null && fredSpread<=0){
    return "Playbook: Risk-Off ↘︎  • 降低仓位，必要时对冲；关注利率与流动性收紧信号。";
  }
  return "Playbook: Neutral  • 观望为主；仅在强信号共振时加减仓，保持中性敞口。";
}

async function main(){
  const nowStr = new Date().toLocaleString();
  el('#lastUpdated').textContent = nowStr;

  let factors=null, model=null, prices=null;
  try{ factors = await fetchJSON(FACTORS_URL); }catch(e){ toast(`加载 factors 失败：${e.message}`); }
  try{ model   = await fetchJSON(MODEL_URL);   }catch(e){ toast(`加载 model 失败：${e.message}`); }
  try{ prices  = await fetchJSON(PRICES_URL);  }catch(e){ /* 价格可能未部署，不提示 */ }

  // KPI & charts
  // ----- weights
  if(model && model.weights){
    const labels = Object.keys(model.weights);
    const data   = labels.map(k=>+model.weights[k] || 0);
    const wctx = el('#weightsChart').getContext('2d');
    makeDoughnut(wctx, labels, data);
    el('#weightsLegend').innerHTML = labels.map((k,i)=>(
      `<span class="item"><span class="sw" style="background:var(--c${i})"></span>${k}: ${fmtPct(data[i]*100)}</span>`
    )).join('');
  }

  // ----- factors
  let naaimSeries, ndxSeries, chinaSeries, fredSeries;
  if(factors && factors.factors){
    naaimSeries = factors.factors.naaim_exposure?.series || null;
    ndxSeries   = factors.factors.ndx_breadth?.series   || null;
    chinaSeries = factors.factors.china_proxy?.series   || null;
    fredSeries  = factors.factors.fred_macro?.series    || null;

    // KPIs
    setKpi('#kpiNaaim', last(naaimSeries));
    setKpi('#kpiNdx50', last(ndxSeries));
    setKpi('#kpiChina', last(chinaSeries));
    const fredSpreadSeries = computeFredSpread({series: fredSeries});
    setKpi('#kpiFred', last(fredSpreadSeries));

    // charts
    if(naaimSeries){
      const {labels,data} = toLine(naaimSeries);
      makeLine(el('#naaimChart'), labels, data, 'NAAIM');
    }
    if(ndxSeries){
      const {labels,data} = toLine(ndxSeries);
      makeLine(el('#ndxChart'), labels, data, '>50DMA');
    }
    if(chinaSeries){
      const {labels,data} = toLine(chinaSeries);
      makeLine(el('#chinaChart'), labels, data, 'FXI Proxy');
    }
    if(fredSpreadSeries){
      const {labels,data} = toLine(fredSpreadSeries);
      makeLine(el('#fredChart'), labels, data, '10Y − FF');
    }

    // Playbook
    const pb = playbookText({
      naaim: last(naaimSeries),
      lastNdx50: last(ndxSeries),
      fredSpread: last(computeFredSpread({series: fredSeries}))
    });
    el('#playbook').innerHTML = `<p>${pb}</p>`;
  } else {
    el('#playbook').innerHTML = `<p>数据暂不可用。请稍后刷新或检查发布工作流。</p>`;
  }

  // ----- Spot price (QQQ / SPY)
  if(prices && prices.prices){
    const sym = prices.prices.QQQ ? 'QQQ' : (prices.prices.SPY ? 'SPY' : null);
    if(sym){
      const {labels,data} = toLine(prices.prices[sym]);
      makeLine(el('#spotChart'), labels, data, sym);
    }
  }

  // updated time from any文件
  const asOf = factors?.as_of || model?.as_of || prices?.as_of;
  if(asOf) el('#lastUpdated').textContent = new Date(asOf).toLocaleString();
}

el('#refreshBtn').addEventListener('click', ()=>{
  el('#toast').classList.add('hidden');
  main().catch(e=>toast(e.message));
});

// 首次
main().catch(e=>toast(e.message));
