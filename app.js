/* App bootstrap for GitHub Pages under /<user>.github.io/anxiousmonkey-backtests/app/ */

const ctx = {
  repoBase: "",
  urls: {},
  charts: {},
  $: sel => document.querySelector(sel),
  fmtPct: v => (v==null || isNaN(v) ? "—" : (Math.round(v*100)/100) + "%"),
  fmt: v => (v==null || isNaN(v) ? "—" : (Math.round(v*100)/100)),
};

function detectRepoBase(){
  // e.g. /anxiousmonkey-backtests/app/  -> /anxiousmonkey-backtests/
  const parts = location.pathname.split("/").filter(Boolean);
  // find repo name (assumed second segment for user pages)
  if (parts.length >= 2){
    ctx.repoBase = "/" + parts.slice(0, 1+ (parts[1]==='app' ? 1 : 1)).join("/") + "/";
  }else{
    ctx.repoBase = "/";
  }
  // Force to repository root (strip trailing 'app/')
  if (ctx.repoBase.endsWith("/app/")){
    ctx.repoBase = ctx.repoBase.replace(/app\/$/, "");
  }
}
detectRepoBase();

ctx.urls = {
  factors: ctx.repoBase + "factors_namm50.json",
  model:   ctx.repoBase + "models/namm50.json",
  prices:  ctx.repoBase + "prices.json"
};

// wire helpful anchors
ctx.$("#rawLink").href = ctx.urls.factors;
ctx.$("#repoLink").href = `https://github.com${ctx.repoBase.replace(/\/$/,"")}`;

// Safe fetch with timeout & graceful fail
async function getJSON(url, timeoutMs=15000){
  const ctrl = new AbortController();
  const t = setTimeout(()=>ctrl.abort(), timeoutMs);
  try{
    const r = await fetch(url, {signal: ctrl.signal, cache: "no-store"});
    if(!r.ok) throw new Error("HTTP "+r.status);
    return await r.json();
  }finally{
    clearTimeout(t);
  }
}

function lastValue(series, idx=1){
  if(!Array.isArray(series) || series.length===0) return null;
  const row = series[series.length-1];
  if(!row) return null;
  // Find first numeric from idx onward
  for(let i=idx;i<row.length;i++){
    if(typeof row[i]==="number") return row[i];
    const maybe = Number(row[i]);
    if(!isNaN(maybe)) return maybe;
  }
  return null;
}

function datesAnd(series){
  const xs=[], ys1=[], ys2=[];
  if(!Array.isArray(series)) return {xs, ys1, ys2};
  for(const r of series){
    if(!r || r.length<2) continue;
    const d = r[0];
    let t = (typeof d==="string") ? new Date(d) : new Date(d*1000);
    if(isNaN(t.getTime())){ // fallback if index is like "0","1"
      const i = Number(d);
      t = isNaN(i) ? new Date() : new Date(2000,0,1+i);
    }
    xs.push(t);
    // collect first/second numeric
    let v1=null, v2=null;
    for(let i=1;i<r.length;i++){
      const n = Number(r[i]);
      if(!isNaN(n) && v1===null){ v1=n; continue; }
      if(!isNaN(n) && v2===null){ v2=n; break; }
    }
    ys1.push(v1);
    ys2.push(v2);
  }
  return {xs, ys1, ys2};
}

function mkLine(el, labels, data, label, color){
  if(!el) return null;
  return new Chart(el.getContext("2d"), {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: label, data: data, borderColor: color, tension: 0.25, pointRadius: 0, borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {ticks:{color:"#91a1ba"}, grid:{color:"#1a2132"}, type: "time", time: {unit:"month"}},
        y: {ticks:{color:"#91a1ba"}, grid:{color:"#1a2132"}}
      },
      plugins:{
        legend:{labels:{color:"#c7d3ea"}},
        tooltip:{mode:"index", intersect:false}
      }
    }
  });
}

function mkTwo(el, labels, y1, y2, l1, l2, c1, c2){
  if(!el) return null;
  return new Chart(el.getContext("2d"), {
    type: "line",
    data: { labels,
      datasets: [
        {label:l1, data: y1, borderColor: c1, tension:.25, pointRadius:0, borderWidth:2},
        {label:l2, data: y2, borderColor: c2, tension:.25, pointRadius:0, borderWidth:2}
      ]},
    options: {
      responsive:true, maintainAspectRatio:false,
      scales:{ x:{ticks:{color:"#91a1ba"}, grid:{color:"#1a2132"}, type:"time", time:{unit:"month"}},
              y:{ticks:{color:"#91a1ba"}, grid:{color:"#1a2132"}}},
      plugins:{ legend:{labels:{color:"#c7d3ea"}}, tooltip:{mode:"index", intersect:false} }
    }
  });
}

function mkBars(el, labels, data){
  if(!el) return null;
  return new Chart(el.getContext("2d"),{
    type: "bar",
    data: { labels, datasets:[{ label:"Weight", data, backgroundColor:"#6ea8fe" }]},
    options: {
      responsive:true, maintainAspectRatio:false,
      scales:{ x:{ticks:{color:"#91a1ba"}, grid:{display:false}}, y:{ticks:{color:"#91a1ba"}, grid:{color:"#1a2132"}}},
      plugins:{ legend:{display:false} }
    }
  });
}

function labelFromScore(x, on=0.5, off=-0.5){
  if(x==null || isNaN(x)) return "Neutral";
  if(x>=on) return "Risk-On";
  if(x<=off) return "Risk-Off";
  return "Neutral";
}

function setKPI(id, text, tone="muted"){
  const el = ctx.$(id+" .value");
  if(!el) return;
  el.textContent = text;
  el.style.color = tone==="good" ? "#54d1a9" : tone==="bad" ? "#f97583" : "#e9eef6";
}

function playbookText(latest){
  const lines = [];
  const mood = labelFromScore(latest.naaim_z ?? 0);
  const fred = latest.real_rate ?? null;
  lines.push(`Regime: ${mood}`);
  if(fred!=null) lines.push(`Real-rate: ${fred.toFixed(2)}%`);
  lines.push(`Tactical: 3D Neutral | 12D Neutral | 1M Neutral`);
  lines.push(`Sizing: Balanced beta (no leverage).`);
  return lines.join("\n");
}

async function main(){
  try{
    const [factors, model] = await Promise.all([
      getJSON(ctx.urls.factors),
      getJSON(ctx.urls.model).catch(()=>({weights:{NAAM:1, FRED:0, NDX50:0, CHINA:0}}))
    ]);

    ctx.$("#asof").textContent = `as of ${factors?.as_of || "—"}`;

    // KPIs + charts
    const fx = factors?.factors || {};

    // NAAIM
    if(fx.naaim_exposure?.series){
      const s = fx.naaim_exposure.series;
      const {xs, ys1} = datesAnd(s);
      ctx.charts.naaim = mkLine(document.getElementById("naaimChart"), xs, ys1, "NAAIM", "#6ea8fe");
      const last = lastValue(s);
      setKPI("#kpi-naaim", last!=null ? last.toFixed(2) : "—", last>75 ? "good" : last<25 ? "bad" : "muted");
    }

    // NDX breadth
    if(fx.ndx_breadth?.series){
      const s = fx.ndx_breadth.series;
      const {xs, ys1} = datesAnd(s);
      ctx.charts.ndx = mkLine(document.getElementById("ndxChart"), xs, ys1, ">50DMA", "#ffd166");
      const last = lastValue(s);
      setKPI("#kpi-ndx50", last!=null ? (last*100).toFixed(0)+"%" : "—", last>0.6 ? "good" : last<0.4 ? "bad" : "muted");
    }

    // China proxy
    if(fx.china_proxy?.series){
      const s = fx.china_proxy.series;
      const {xs, ys1} = datesAnd(s);
      ctx.charts.china = mkLine(document.getElementById("chinaChart"), xs, ys1, "FXI", "#a0e7e5");
      const last = lastValue(s);
      setKPI("#kpi-china", last!=null ? last.toFixed(2) : "—", "muted");
    }

    // FRED Macro (two series)
    if(fx.fred_macro?.series){
      const s = fx.fred_macro.series;
      const {xs, ys1, ys2} = datesAnd(s);
      ctx.charts.fred = mkTwo(document.getElementById("fredChart"), xs, ys1, ys2, "DGS10", "DFF", "#6ea8fe", "#ff7d7d");
      const last10 = lastValue(s,1); const lastFF = lastValue(s,2);
      setKPI("#kpi-fred", (last10!=null && lastFF!=null) ? `${last10.toFixed(2)} / ${lastFF.toFixed(2)}` : "—", "muted");
    }

    // Weights (from model)
    let labels=[], data=[];
    if(model?.weights){
      labels = Object.keys(model.weights);
      data = labels.map(k=>Number(model.weights[k]||0));
      ctx.charts.weights = mkBars(document.getElementById("weightsChart"), labels, data);
    }

    // Playbook
    const latest = {
      naaim_z: 0,
      real_rate: null
    };
    ctx.$("#playbook").textContent = playbookText(latest);
  }catch(e){
    console.error(e);
    alert("加载失败: " + e.message + "\\nURL: " + (e?.url || ""));
  }
}

main();
