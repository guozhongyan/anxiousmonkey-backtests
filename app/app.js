const BASE = "https://guozhongyan.github.io/anxiousmonkey-backtests/";
const URLS = {
  factors: BASE + "factors_namm50.json",
  model:   BASE + "models/namm50.json",
  prices:  BASE + "prices.json"
};
const SPOT_LIST = ["SPY","QQQ","TQQQ","SOXL","FEZ","CURE"];

let donutChart = null;

function setLastUpdated() {
  const el = document.getElementById("lastUpdated");
  el.textContent = "Last updated " + new Date().toLocaleString("zh-CN",{hour12:false});
}
async function safeFetchJSON(url) {
  try {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) return null;
    return await r.json();
  } catch (e) {
    console.error("fetch failed:", url, e);
    return null;
  }
}
function lastFromSeries(series) {
  try {
    if (!Array.isArray(series) || !series.length) return null;
    const last = series[series.length - 1];
    if (Array.isArray(last)) {
      for (let i = last.length - 1; i >= 0; i--) {
        if (typeof last[i] === "number" && isFinite(last[i])) return last[i];
      }
      return null;
    }
    if (typeof last === "number" && isFinite(last)) return last;
    return null;
  } catch { return null; }
}
function liveBadge(el, ok) { el.textContent = ok ? "LIVE" : "—"; }
function setStatValue(id, v, suffix="") {
  const el = document.getElementById(id);
  el.textContent = (v==null || !isFinite(v)) ? "—" : `${(+v).toFixed(Math.abs(v)<10?2:1)}${suffix}`;
}
function pill(txt, ok) {
  const span = document.createElement("span");
  span.className = "pill " + (ok ? "live":"missing");
  span.textContent = txt + (ok ? " • LIVE" : " • MISSING");
  return span;
}
function renderFactorFlags(map) {
  const host = document.getElementById("factorFlags");
  host.innerHTML = "";
  Object.keys(map).forEach(k => host.appendChild(pill(k.toUpperCase(), !!map[k])));
}
function destroyChartIfAny() {
  try {
    if (donutChart) { donutChart.destroy(); donutChart = null; }
    else {
      const ex = Chart.getChart("weightsChart");
      if (ex) ex.destroy();
    }
    const c = document.getElementById("weightsChart");
    c.getContext("2d").clearRect(0,0,c.width,c.height);
  } catch {}
}
function renderWeights(weightsObj) {
  const labels = Object.keys(weightsObj || {});
  const values = labels.map(k => Number(weightsObj[k]||0));
  const total  = values.reduce((a,b)=>a+b,0);

  const empty  = document.getElementById("weightsEmpty");
  const legend = document.getElementById("weightsLegend");
  destroyChartIfAny();
  legend.innerHTML = "";

  if (!labels.length || total <= 0) { empty.hidden = false; return; }
  empty.hidden = true;

  const palette = [
    "#6ea3ff","#7dd3fc","#a78bfa","#f472b6","#fb7185",
    "#f59e0b","#84cc16","#34d399","#22d3ee","#60a5fa"
  ];
  const colors = labels.map((_,i)=>palette[i%palette.length]);

  const ctx = document.getElementById("weightsChart").getContext("2d");
  donutChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: colors, borderWidth: 0 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: "68%",
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c)=>`${c.label}: ${(c.parsed/total*100).toFixed(1)}%` } }
      }
    }
  });

  labels.forEach((label,i)=>{
    const el = document.createElement("span");
    el.className = "item";
    el.style.borderColor = colors[i] + "80";
    el.style.color = colors[i];
    el.textContent = `${label.toUpperCase()}: ${(values[i]/total*100).toFixed(1)}%`;
    legend.appendChild(el);
  });
}
function renderSpot(prices) {
  const host = document.getElementById("spotRow");
  host.innerHTML = "";
  SPOT_LIST.forEach(sym=>{
    const chip = document.createElement("span");
    chip.className = "chip";
    const v = prices && (prices[sym] ?? prices[sym?.toLowerCase?.()]);
    chip.textContent = v ? `${sym}: ${v}` : `${sym}: —`;
    host.appendChild(chip);
  });
}
function clamp(x,lo,hi){return Math.min(hi,Math.max(lo,x));}
function normFactor(name,v){
  if (v==null || !isFinite(v)) return 0;
  const n = name.toUpperCase();
  if (n.includes("NAAIM")) return clamp((v/100)*2-1,-1,1);
  if (n.includes("50") || n.includes("BREADTH")) return clamp((v/100)*2-1,-1,1);
  if (n.includes("VIX")) return -clamp((v-12)/20,0,1);
  if (n.includes("CHINA") || n.includes("FXI")) return clamp(v,-1,1);
  return clamp(v/10,-1,1);
}
function sigmoid(x){return 1/(1+Math.exp(-x));}
function heuristicPlaybook({live,vals}) {
  const msgs = [];
  const ok = Object.values(live).filter(Boolean).length;
  if (ok < 3) msgs.push("数据不全：部分因子仍为占位/空值。");

  if (vals.naaim != null) {
    if (vals.naaim > 75) msgs.push("机构仓位偏高 → 做多倾向，警惕回撤风险。");
    else if (vals.naaim < 25) msgs.push("机构仓位偏低 → 反弹可能提升，轻仓试探。");
    else msgs.push("机构仓位中性。");
  }
  if (vals.ndx50 != null) {
    if (vals.ndx50 > 60) msgs.push(">50DMA 面宽良好，短线风险偏好上升。");
    else if (vals.ndx50 < 40) msgs.push(">50DMA 面宽走弱，注意回撤风险。");
  }
  if (vals.fred != null) {
    if (vals.fred < 0) msgs.push("宏观景气偏弱 → 降杠杆，重视风险控制。");
    else msgs.push("宏观条件中性。");
  }
  if (vals.china != null) msgs.push("China proxy 已纳入监控，注意与风险资产联动。");

  if (!msgs.length) msgs.push("Neutral：仅在强信号共振时加减仓，保持中性敞口。");
  return "Playbook: " + msgs.join(" ");
}
function heuristicScore(weights, vals) {
  const keys = Object.keys(weights||{});
  if (!keys.length) return {score:null, prob:null, tilt:"—"};
  let agg = 0, wsum = 0;
  keys.forEach(k=>{
    const w = +weights[k] || 0; if (w<=0) return;
    const n = k.toLowerCase();
    let v = null;
    if (n.includes("naam") || n.includes("naaim")) v = vals.naaim;
    else if (n.includes("ndx") || n.includes("50")) v = vals.ndx50;
    else if (n.includes("china") || n.includes("fxi")) v = vals.china;
    else if (n.includes("fred")) v = vals.fred;
    agg += w * normFactor(k, v);
    wsum += w;
  });
  if (wsum<=0) return {score:null,prob:null,tilt:"—"};
  const score = agg/wsum;
  const prob  = sigmoid(score*1.8);
  const tilt  = score>0.2 ? "Bullish" : (score<-0.2 ? "Bearish" : "Neutral");
  return {score, prob, tilt};
}

async function main(){
  setLastUpdated();
  document.getElementById("btnRefresh").addEventListener("click",()=>location.reload());

  const [factors,model,prices] = await Promise.all([
    safeFetchJSON(URLS.factors),
    safeFetchJSON(URLS.model),
    safeFetchJSON(URLS.prices)
  ]);

  renderSpot(prices);

  const f = (factors && factors.factors) || factors || {};
  const naaimSeries = f.naaim_exposure?.series ?? f.naaim?.series ?? null;
  const ndxSeries   = f.ndx_breadth?.series ?? f.ndx50?.series ?? null;
  const chinaSeries = f.china_proxy?.series ?? f.china?.series ?? null;
  const fredSeries  = f.fred_macro?.series  ?? f.fred?.series  ?? null;

  const vals = {
    naaim: lastFromSeries(naaimSeries),
    ndx50: lastFromSeries(ndxSeries),
    china: lastFromSeries(chinaSeries),
    fred:  lastFromSeries(fredSeries)
  };

  setStatValue("v-naaim", vals.naaim);
  setStatValue("v-ndx50", vals.ndx50, "%");
  setStatValue("v-china", vals.china);
  setStatValue("v-fred",  vals.fred);

  const live = {
    naaim: Array.isArray(naaimSeries) && naaimSeries.length>0,
    ndx50: Array.isArray(ndxSeries)   && ndxSeries.length>0,
    china: Array.isArray(chinaSeries) && chinaSeries.length>0,
    fred:  Array.isArray(fredSeries)  && fredSeries.length>0
  };
  liveBadge(document.getElementById("live-naaim"), live.naaim);
  liveBadge(document.getElementById("live-ndx50"), live.ndx50);
  liveBadge(document.getElementById("live-china"), live.china);
  liveBadge(document.getElementById("live-fred"),  live.fred);
  renderFactorFlags(live);

  const weights = (model && (model.weights || model?.latest?.weights)) || {};
  renderWeights(weights);

  document.getElementById("playbook").textContent = heuristicPlaybook({live, vals});
  const {score, prob, tilt} = heuristicScore(weights, vals);
  document.getElementById("score").textContent  = (score==null)?"—":score.toFixed(2);
  document.getElementById("probUp").textContent = (prob==null) ?"—":(prob*100).toFixed(1)+"%";
  document.getElementById("tilt").textContent   = tilt;
}

document.addEventListener("DOMContentLoaded", main);
