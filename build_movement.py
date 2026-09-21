"""Build movement.html — 'May -> Aug 2026: Where the world is moving'.
Self-contained (Chart.js CDN + embedded data). Reads movement_data.json.
Platform toggle (All / Blinkit / Instamart / Zepto) re-renders every view."""
import json

D = json.load(open('movement_data.json'))
DATA_JSON = json.dumps(D, separators=(',', ':'))

HTML = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Where The World Is Moving</title>
<meta name="description" content="May to August 2026 movement across Quick-Commerce home categories: platform-wise and platform-category growth and de-growth, brand and product-type risers and fallers.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'%3E%3Crect x='350' y='18' width='112' height='476' rx='56' fill='%23f9ab00'/%3E%3Crect x='201' y='200' width='112' height='294' rx='56' fill='%23e37400'/%3E%3Ccircle cx='95' cy='438' r='56' fill='%23e37400'/%3E%3C/svg%3E">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{
  --bg:#faf6ef; --card:#ffffff; --bd:#ece4d6; --ink:#2a2724; --mut:#8a7f70;
  --acc:#e37400; --blue:#0071e3; --grn:#1a7f37; --red:#c0392b; --gold:#f9ab00;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#1a1714; --card:#241f1a; --bd:#3a3229; --ink:#f2ece2; --mut:#a79b89;
}}
:root[data-theme="dark"]{--bg:#1a1714; --card:#241f1a; --bd:#3a3229; --ink:#f2ece2; --mut:#a79b89;}
*{box-sizing:border-box} html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:28px 16px 80px}
h1{font-size:clamp(26px,5vw,40px);line-height:1.1;margin:0 0 6px;letter-spacing:-.02em}
h1 .em{color:var(--acc)}
.sub{color:var(--mut);font-size:15px;margin:0 0 22px}
.eyebrow{font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--acc);margin:0 0 10px}
h2{font-size:20px;margin:38px 0 4px;letter-spacing:-.01em}
.h2sub{color:var(--mut);font-size:13.5px;margin:0 0 16px}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:0 0 8px}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:16px 18px}
.kpi .lab{font-size:12px;color:var(--mut);font-weight:600}
.kpi .val{font-size:clamp(22px,4vw,30px);font-weight:750;letter-spacing:-.02em;margin-top:4px}
.kpi .val small{font-size:14px;font-weight:600;color:var(--mut)}
.up{color:var(--grn)} .dn{color:var(--red)}
.seg{display:inline-flex;flex-wrap:wrap;gap:4px;background:var(--card);border:1px solid var(--bd);
  border-radius:12px;padding:4px;margin:0 0 20px}
.seg button{border:0;background:transparent;color:var(--mut);font:inherit;font-size:13.5px;font-weight:600;
  padding:8px 16px;border-radius:9px;cursor:pointer;transition:.12s}
.seg button:hover{color:var(--ink)}
.seg button.on{background:var(--acc);color:#fff}
.banner{background:linear-gradient(135deg,#fff7ec,#fdeede);border:1px solid #f2d9b8;border-radius:16px;
  padding:16px 20px;margin:18px 0 4px;color:#5a3b12}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .banner{background:linear-gradient(135deg,#2c2114,#332415);border-color:#5a4326;color:#f0d9b6}}
:root[data-theme="dark"] .banner{background:linear-gradient(135deg,#2c2114,#332415);border-color:#5a4326;color:#f0d9b6}
.banner .t{font-weight:750;font-size:15px;margin-bottom:4px;letter-spacing:-.01em}
.banner .x{font-size:14px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:16px;padding:18px}
.cwrap{position:relative;width:100%}
.legend{display:flex;gap:16px;align-items:center;font-size:12.5px;color:var(--mut);margin:2px 0 12px}
.dot{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.eqrow{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.chip{background:var(--bg);border:1px solid var(--bd);border-radius:999px;padding:5px 12px;font-size:13px}
.chip b{color:var(--ink)} .chip .s{color:var(--mut)}
.note{font-size:12.5px;color:var(--mut);margin-top:10px}
.foot{color:var(--mut);font-size:12px;margin-top:40px;border-top:1px solid var(--bd);padding-top:16px}
.topnav{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:0 0 22px}
.topnav .lbl{color:var(--mut);font-size:11px;margin-right:2px}
.topnav a{font-size:12.5px;font-weight:600;padding:6px 13px;border-radius:8px;border:1px solid var(--bd);
  text-decoration:none;color:var(--mut);background:var(--card)}
.topnav a:hover{color:var(--ink);border-color:var(--acc)}
.topnav a.cmp{color:var(--acc);border-color:var(--acc)}
.topnav .active{font-size:12.5px;font-weight:600;padding:6px 13px;border-radius:8px;border:1px solid var(--acc);
  background:var(--acc);color:#fff}
.topnav .sep{color:var(--bd);margin:0 2px}
@media(max-width:720px){.eqrow{grid-template-columns:1fr}.kpis{grid-template-columns:1fr 1fr}}
</style></head>
<body><div class="wrap">
  <div class="topnav">
    <span class="lbl">Platform:</span>
    <a href="index.html">Blinkit</a><a href="instamart.html">Instamart</a><a href="zepto.html">Zepto</a>
    <span class="sep">|</span>
    <a class="cmp" href="compare.html" title="Cross-platform comparison">⇄ Cross Platform</a>
    <span class="active">📈 Movement</span>
    <a href="platforms.html" title="All platforms">All ↗</a>
  </div>
  <p class="eyebrow">Quick-Commerce · Home · May → Aug 2026</p>
  <h1>Where the world is <span class="em">moving</span></h1>
  <p class="sub" id="sub"></p>

  <div class="seg" id="seg"></div>

  <div class="kpis" id="kpis"></div>

  <h2>Platform-wise growth</h2>
  <p class="h2sub">Modelled gross (MRP) ₹ Cr, May → Aug — how each platform's home business moved. Selected platform is highlighted.</p>
  <div class="card"><div class="cwrap" style="height:200px"><canvas id="cPlat"></canvas></div></div>

  <div class="banner" id="banner"></div>

  <h2>The four home Super Categories</h2>
  <p class="h2sub" id="superSub"></p>
  <div class="card"><div class="cwrap" style="height:230px"><canvas id="cSuper"></canvas></div></div>

  <h2 id="typeH">Product types on the move</h2>
  <p class="h2sub">Growth vs May (%). The dashed line is that scope's <b>overall average</b> — bars past it gained share, bars short of it lost ground.</p>
  <div class="legend"><span><span class="dot" style="background:var(--grn)"></span>Grew faster / up</span><span><span class="dot" style="background:var(--red)"></span>Declined</span></div>
  <div class="card"><div class="cwrap" id="wTypes"><canvas id="cTypes"></canvas></div></div>

  <div class="eqrow" style="margin-top:16px">
    <div>
      <h2 style="margin-top:8px" id="catH">Categories on the move</h2>
      <p class="h2sub">Growth vs May (%).</p>
      <div class="card"><div class="cwrap" id="wCats"><canvas id="cCats"></canvas></div></div>
    </div>
    <div>
      <h2 style="margin-top:8px">Brands moving the most money</h2>
      <p class="h2sub">Change in gross ₹ Cr, May → Aug.</p>
      <div class="card"><div class="cwrap" id="wBrands"><canvas id="cBrands"></canvas></div></div>
    </div>
  </div>

  <h2>New vs gone</h2>
  <p class="h2sub">Brand-level entry &amp; exit across the two snapshots.</p>
  <div class="card">
    <div class="eqrow">
      <div>
        <div style="font-weight:700;color:var(--grn);margin-bottom:2px">＋ New brands in Aug <span style="color:var(--mut);font-weight:500" id="newCount"></span></div>
        <div class="chips" id="newChips"></div>
      </div>
      <div>
        <div style="font-weight:700;color:var(--red);margin-bottom:2px">－ Gone since May <span style="color:var(--mut);font-weight:500" id="exitCount"></span></div>
        <div class="chips" id="exitChips"></div>
      </div>
    </div>
    <div class="note" id="churnNote"></div>
  </div>

  <div class="foot" id="foot"></div>
</div>

<script>
const D=__DATA__;
const css=k=>getComputedStyle(document.documentElement).getPropertyValue(k).trim();
const C={ink:css('--ink'),mut:css('--mut'),grn:css('--grn'),red:css('--red'),bd:css('--bd'),acc:css('--acc'),blue:css('--blue')};
Chart.defaults.font.family=getComputedStyle(document.body).fontFamily;
Chart.defaults.color=C.mut;
const fmt=(x,n=0)=>Number(x).toLocaleString('en-IN',{minimumFractionDigits:n,maximumFractionDigits:n});
let scope='all'; const CH={};
function kill(id){if(CH[id]){CH[id].destroy();delete CH[id];}}

// ---- market reference line (per growth-% chart) ----
function mktLine(avg){return {id:'mkt',afterDatasetsDraw(ch){const sx=ch.scales.x;if(!sx)return;const x=sx.getPixelForValue(avg);
  const ctx=ch.ctx,top=ch.chartArea.top,bot=ch.chartArea.bottom;
  ctx.save();ctx.strokeStyle=C.acc;ctx.setLineDash([5,4]);ctx.lineWidth=1.5;
  ctx.beginPath();ctx.moveTo(x,top);ctx.lineTo(x,bot);ctx.stroke();
  ctx.setLineDash([]);ctx.fillStyle=C.acc;ctx.font='600 10px '+Chart.defaults.font.family;
  ctx.fillText('+'+avg+'% avg',x+4,top+11);ctx.restore();}};}

function mergeMovers(dim,key,topN){
  const seen={},all=[];
  (dim.risers||[]).concat(dim.fallers||[]).forEach(r=>{if(!seen[r.name]){seen[r.name]=1;all.push(r);}});
  all.sort((a,b)=>b[key]-a[key]);
  return all.length>topN*2?all.slice(0,topN).concat(all.slice(-topN)):all;
}
function diverging(canvasId,wrapId,items,key,fmtVal,plugins){
  kill(canvasId);
  const h=Math.max(140,items.length*26+40);
  document.getElementById(wrapId).style.height=h+'px';
  const labels=items.map(r=>r.name.length>26?r.name.slice(0,25)+'…':r.name);
  const vals=items.map(r=>r[key]);
  CH[canvasId]=new Chart(document.getElementById(canvasId),{
    type:'bar',
    data:{labels,datasets:[{data:vals,backgroundColor:vals.map(v=>v>=0?C.grn:C.red),borderRadius:4,barPercentage:.82,categoryPercentage:.82}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,animation:{duration:300},
      layout:{padding:{right:14,left:6}},
      plugins:{legend:{display:false},
        tooltip:{callbacks:{label:c=>{const r=items[c.dataIndex];
          return `May ₹${fmt(r.may,1)} Cr → Aug ₹${fmt(r.aug,1)} Cr  (${r.pct>=0?'+':''}${r.pct}% · ${r.delta>=0?'+':''}₹${fmt(r.delta,1)} Cr)`;}}}},
      scales:{x:{grid:{color:C.bd},ticks:{callback:v=>fmtVal(v)},title:{display:true,text:fmtVal.title,color:C.mut}},
        y:{grid:{display:false},ticks:{color:C.ink,font:{size:12}}}}},
    plugins:plugins||[]
  });
}
const pctFmt=v=>v+'%'; pctFmt.title='Growth vs May (%)';
const crFmt=v=>(v>0?'+':'')+v+' Cr'; crFmt.title='Δ gross ₹ Cr';

// ---- platform-wise growth (static; highlights the selected scope) ----
function drawPlatforms(){
  kill('cPlat');
  const g=D.platformGrowth, labels=g.map(p=>p.label), pcts=g.map(p=>Math.round((p.aug/p.may-1)*100));
  const sel=scope;
  CH['cPlat']=new Chart(document.getElementById('cPlat'),{
    type:'bar',
    data:{labels,datasets:[{data:pcts,
      backgroundColor:g.map(p=>p.key===sel?C.acc:(pcts[g.indexOf(p)]>=0?C.grn:C.red)),
      borderRadius:5,barPercentage:.6}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,animation:{duration:300},
      plugins:{legend:{display:false},
        tooltip:{callbacks:{label:c=>{const p=g[c.dataIndex];return `May ₹${fmt(p.may)} Cr → Aug ₹${fmt(p.aug)} Cr  (+${Math.round((p.aug/p.may-1)*100)}%)`;}}}},
      scales:{x:{grid:{color:C.bd},ticks:{callback:v=>v+'%'},title:{display:true,text:'Home gross growth May → Aug (%)',color:C.mut}},
        y:{grid:{display:false},ticks:{color:C.ink,font:{size:13,weight:'600'}}}}}
  });
}

// ---- super categories grouped bars ----
function drawSuper(S){
  kill('cSuper');
  CH['cSuper']=new Chart(document.getElementById('cSuper'),{
    type:'bar',
    data:{labels:S.supers.map(s=>s.name.replace('General Home Improvement / Decor','Home Improve / Decor')),
      datasets:[
        {label:'May',data:S.supers.map(s=>s.may),backgroundColor:C.blue+'99',borderRadius:5,barPercentage:.9,categoryPercentage:.72},
        {label:'Aug',data:S.supers.map(s=>s.aug),backgroundColor:C.acc,borderRadius:5,barPercentage:.9,categoryPercentage:.72}]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:300},
      plugins:{legend:{position:'top',labels:{boxWidth:12,boxHeight:12,usePointStyle:true,pointStyle:'rectRounded'}},
        tooltip:{callbacks:{label:c=>`${c.dataset.label}: ₹${fmt(c.parsed.y,1)} Cr`}}},
      scales:{x:{grid:{display:false},ticks:{color:C.ink,font:{size:11.5}}},
        y:{grid:{color:C.bd},ticks:{callback:v=>'₹'+v}}}}
  });
}

const chip=(name,val,unit)=>`<span class="chip"><b>${name}</b> <span class="s">${unit}${fmt(val,1)} Cr</span></span>`;

function render(){
  const S=D.scopes[scope];
  const t=S.totals, g=t.aug-t.may, gp=Math.round((t.aug/t.may-1)*100), avg=gp;
  const plabel=D.platforms.find(p=>p.key===scope).label;
  document.getElementById('sub').textContent=`Modelled gross (MRP) — ${scope==='all'?'Blinkit · Instamart · Zepto combined':plabel}, home categories, ${D.months[0]} vs ${D.months[1]}.`;
  document.getElementById('kpis').innerHTML=[
    ['May 2026','₹'+fmt(t.may)+' <small>Cr</small>'],
    ['Aug 2026','₹'+fmt(t.aug)+' <small>Cr</small>'],
    ['Growth','<span class="'+(gp>=0?'up':'dn')+'">'+(gp>=0?'+':'')+gp+'%</span> <small>('+(g>=0?'+':'')+'₹'+fmt(g)+' Cr)</small>']
  ].map(k=>`<div class="kpi"><div class="lab">${k[0]}</div><div class="val">${k[1]}</div></div>`).join('');

  // dynamic insight banner from this scope's type movers
  const tr=(S.types.risers||[]).slice(0,3).map(r=>`${r.name} +${r.pct}%`);
  const fa=(S.types.fallers||[]).filter(r=>r.pct<0).slice(0,3).map(r=>`${r.name} ${r.pct}%`);
  document.getElementById('banner').innerHTML=
    `<div class="t">${plabel}: home gross ${gp>=0?'grew':'fell'} ${gp>=0?'+':''}${gp}% (₹${fmt(t.may)}→₹${fmt(t.aug)} Cr) — summer cooling out, monsoon &amp; festive in.</div>`+
    `<div class="x"><b style="color:var(--grn)">▲</b> ${tr.join(' · ')||'—'}<br><b style="color:var(--red)">▼</b> ${fa.join(' · ')||'no material decliners'}</div>`;

  document.getElementById('superSub').textContent=`Modelled gross (MRP) ₹ Cr — ${scope==='all'?'every home super grew, but the mix rotated':plabel+' home super categories'}.`;
  document.getElementById('typeH').textContent=`Product types on the move${scope==='all'?'':' · '+plabel}`;
  document.getElementById('catH').textContent=`Categories on the move${scope==='all'?'':' · '+plabel}`;

  drawPlatforms();
  drawSuper(S);
  diverging('cTypes','wTypes',mergeMovers(S.types,'pct',8),'pct',pctFmt,[mktLine(avg)]);
  diverging('cCats','wCats',mergeMovers(S.categories,'pct',7),'pct',pctFmt,[mktLine(avg)]);
  diverging('cBrands','wBrands',mergeMovers(S.brands,'delta',8),'delta',crFmt);

  document.getElementById('newCount').textContent='· '+S.newCount+' total';
  document.getElementById('exitCount').textContent='· '+S.exitCount+' total';
  document.getElementById('newChips').innerHTML=(S.newBrands.length?S.newBrands:[{name:'—',aug:0}]).map(r=>chip(r.name,r.aug,'₹')).join('');
  document.getElementById('exitChips').innerHTML=(S.exitBrands.length?S.exitBrands:[{name:'—',may:0}]).map(r=>chip(r.name,r.may,'was ₹')).join('');
  document.getElementById('churnNote').innerHTML=`Entry/exit is almost entirely <b>long-tail</b> — the real movement is in magnitude, not in who is present (assortment is stable, demand rotated). Scope excludes the non-home "Others" super category.`;
}

// ---- platform toggle ----
const seg=document.getElementById('seg');
seg.innerHTML=D.platforms.map(p=>`<button data-k="${p.key}"${p.key===scope?' class="on"':''}>${p.label}</button>`).join('');
seg.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;
  scope=b.dataset.k;[...seg.children].forEach(x=>x.classList.toggle('on',x.dataset.k===scope));render();});

document.getElementById('foot').innerHTML='Modelled ₹ = category MRP totals distributed by Est. Category Share SP, SP & MRP (net → units → gross). May uses May-period totals, Aug uses Aug-period totals, so movement reflects both category resizing and within-category share shifts. Growth % is each item vs its own May figure; the dashed line is the scope\'s blended average. Non-home "Others" excluded. Minimum size floors applied so tiny bases don\'t dominate.';
render();
</script>
</body></html>"""

out = HTML.replace('__DATA__', DATA_JSON)
open('movement.html', 'w').write(out)
print(f'Wrote movement.html ({len(out)//1024} KB)')
