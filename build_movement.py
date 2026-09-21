"""Build movement.html — 'May -> Aug 2026: Where the world is moving'.
Self-contained (Chart.js CDN + embedded data). Reads movement_data.json."""
import json

D = json.load(open('movement_data.json'))
DATA_JSON = json.dumps(D, separators=(',', ':'))

HTML = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Where The World Is Moving</title>
<meta name="description" content="May to August 2026 movement across Quick-Commerce home categories: seasonal rotation, category, brand and product-type risers and fallers.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'%3E%3Crect x='350' y='18' width='112' height='476' rx='56' fill='%23f9ab00'/%3E%3Crect x='201' y='200' width='112' height='294' rx='56' fill='%23e37400'/%3E%3Ccircle cx='95' cy='438' r='56' fill='%23e37400'/%3E%3C/svg%3E">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{
  --bg:#faf6ef; --card:#ffffff; --bd:#ece4d6; --ink:#2a2724; --mut:#8a7f70;
  --acc:#e37400; --blue:#0071e3; --grn:#1a7f37; --red:#c0392b; --gold:#f9ab00;
  --grnbg:#e6f2e9; --redbg:#f7e6e3;
}
:root:not([data-theme="light"]){ }
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#1a1714; --card:#241f1a; --bd:#3a3229; --ink:#f2ece2; --mut:#a79b89;
  --grnbg:#1e3323; --redbg:#3a221f;
}}
:root[data-theme="dark"]{
  --bg:#1a1714; --card:#241f1a; --bd:#3a3229; --ink:#f2ece2; --mut:#a79b89;
  --grnbg:#1e3323; --redbg:#3a221f;
}
*{box-sizing:border-box} html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:28px 16px 80px}
h1{font-size:clamp(26px,5vw,40px);line-height:1.1;margin:0 0 6px;letter-spacing:-.02em}
h1 .em{color:var(--acc)}
.sub{color:var(--mut);font-size:15px;margin:0 0 24px}
.eyebrow{font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--acc);margin:0 0 10px}
h2{font-size:20px;margin:38px 0 4px;letter-spacing:-.01em}
.h2sub{color:var(--mut);font-size:13.5px;margin:0 0 16px}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:0 0 8px}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:16px 18px}
.kpi .lab{font-size:12px;color:var(--mut);font-weight:600;letter-spacing:.02em}
.kpi .val{font-size:clamp(22px,4vw,30px);font-weight:750;letter-spacing:-.02em;margin-top:4px}
.kpi .val small{font-size:14px;font-weight:600;color:var(--mut)}
.up{color:var(--grn)} .dn{color:var(--red)}
.banner{background:linear-gradient(135deg,#fff7ec,#fdeede);border:1px solid #f2d9b8;border-radius:16px;
  padding:18px 20px;margin:20px 0 4px;color:#5a3b12}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .banner{background:linear-gradient(135deg,#2c2114,#332415);border-color:#5a4326;color:#f0d9b6}}
:root[data-theme="dark"] .banner{background:linear-gradient(135deg,#2c2114,#332415);border-color:#5a4326;color:#f0d9b6}
.banner b{color:inherit}
.banner .t{font-weight:750;font-size:15px;margin-bottom:6px;letter-spacing:-.01em}
.banner ul{margin:6px 0 0;padding-left:18px} .banner li{margin:3px 0;font-size:14px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:16px;padding:18px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.cwrap{position:relative;width:100%}
.legend{display:flex;gap:16px;align-items:center;font-size:12.5px;color:var(--mut);margin:2px 0 12px}
.dot{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.eqrow{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.chip{background:var(--bg);border:1px solid var(--bd);border-radius:999px;padding:5px 12px;font-size:13px}
.chip b{color:var(--ink)} .chip .s{color:var(--mut)}
.note{font-size:12.5px;color:var(--mut);margin-top:10px}
.foot{color:var(--mut);font-size:12px;margin-top:40px;border-top:1px solid var(--bd);padding-top:16px}
@media(max-width:720px){.grid2,.eqrow{grid-template-columns:1fr}.kpis{grid-template-columns:1fr 1fr}}
</style></head>
<body><div class="wrap">
  <p class="eyebrow">Quick-Commerce · Home · May → Aug 2026</p>
  <h1>Where the world is <span class="em">moving</span></h1>
  <p class="sub" id="sub"></p>

  <div class="kpis" id="kpis"></div>

  <div class="banner">
    <div class="t">The shift in one line: summer cooling is out, monsoon &amp; festive are in.</div>
    <ul>
      <li><b>Cooling collapses</b> — Air Cooler −100%, Electric Fan −55%, Ice Trays −58% as summer ends.</li>
      <li><b>Monsoon &amp; comfort rise</b> — Umbrella +206%, Room Heater +539%, Water Heater +213%, Blankets &amp; Towels up sharply.</li>
      <li><b>Festive ramp</b> — Decorative Lights +75%, Pooja +65%, Festive & Party categories +47–93%; Desidiya alone adds ₹20 Cr.</li>
    </ul>
  </div>

  <h2>The four home Super Categories</h2>
  <p class="h2sub">Modelled gross (MRP) ₹ Cr — every home super grew, but the mix rotated.</p>
  <div class="card"><div class="cwrap" style="height:230px"><canvas id="cSuper"></canvas></div></div>

  <h2>Product types on the move</h2>
  <p class="h2sub">Growth vs May (%). The dashed line is the <b>+25% Q-Commerce average</b> — bars past it gained share, bars short of it lost ground. Min size ₹3 Cr.</p>
  <div class="legend"><span><span class="dot" style="background:var(--grn)"></span>Grew faster / up</span><span><span class="dot" style="background:var(--red)"></span>Declined</span></div>
  <div class="card"><div class="cwrap" id="wTypes"><canvas id="cTypes"></canvas></div></div>

  <div class="eqrow" style="margin-top:16px">
    <div>
      <h2 style="margin-top:8px">Categories on the move</h2>
      <p class="h2sub">Growth vs May (%). Min size ₹3 Cr.</p>
      <div class="card"><div class="cwrap" id="wCats"><canvas id="cCats"></canvas></div></div>
    </div>
    <div>
      <h2 style="margin-top:8px">Brands moving the most money</h2>
      <p class="h2sub">Change in gross ₹ Cr, May → Aug. Min size ₹2 Cr.</p>
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
    <div class="note">Entry/exit is almost entirely <b>long-tail</b>: no brand above ₹0.5 Cr appeared or disappeared. The real movement is in magnitude (above), not in who is present — the assortment is stable, demand rotated. Scope excludes the non-home "Others" super category.</div>
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

// ---- subtitle + KPIs ----
const t=D.totals, g=t.aug-t.may, gp=Math.round((t.aug/t.may-1)*100);
document.getElementById('sub').textContent=`Modelled gross (MRP) across Blinkit · Instamart · Zepto — the four home Super Categories, ${D.months[0]} vs ${D.months[1]}.`;
document.getElementById('kpis').innerHTML=[
  ['May 2026','₹'+fmt(t.may)+' <small>Cr</small>'],
  ['Aug 2026','₹'+fmt(t.aug)+' <small>Cr</small>'],
  ['Growth','<span class="up">+'+gp+'%</span> <small>(+₹'+fmt(g)+' Cr)</small>']
].map(k=>`<div class="kpi"><div class="lab">${k[0]}</div><div class="val">${k[1]}</div></div>`).join('');
document.getElementById('newCount').textContent='· '+D.newCount+' total';
document.getElementById('exitCount').textContent='· '+D.exitCount+' total';

// ---- helpers ----
function mergeMovers(dim,key,topN){
  const seen={},all=[];
  (dim.risers||[]).concat(dim.fallers||[]).forEach(r=>{if(!seen[r.name]){seen[r.name]=1;all.push(r);}});
  all.sort((a,b)=>b[key]-a[key]);
  if(all.length>topN*2){return all.slice(0,topN).concat(all.slice(-topN));}
  return all;
}
// dashed +25% market-average reference (only for growth-% charts, passed inline per chart)
const marketLine={id:'mkt',afterDatasetsDraw(ch){const sx=ch.scales.x;if(!sx)return;const x=sx.getPixelForValue(25);
  const ctx=ch.ctx,top=ch.chartArea.top,bot=ch.chartArea.bottom;
  ctx.save();ctx.strokeStyle=C.acc;ctx.setLineDash([5,4]);ctx.lineWidth=1.5;
  ctx.beginPath();ctx.moveTo(x,top);ctx.lineTo(x,bot);ctx.stroke();
  ctx.setLineDash([]);ctx.fillStyle=C.acc;ctx.font='600 10px '+Chart.defaults.font.family;
  ctx.fillText('+25% mkt',x+4,top+11);ctx.restore();}};
function divergingChart(canvasId,wrapId,items,key,fmtVal,plugins){
  const h=Math.max(150,items.length*26+40);
  document.getElementById(wrapId).style.height=h+'px';
  const labels=items.map(r=>r.name.length>26?r.name.slice(0,25)+'…':r.name);
  const vals=items.map(r=>r[key]);
  const colors=vals.map(v=>v>=0?C.grn:C.red);
  return new Chart(document.getElementById(canvasId),{
    type:'bar',
    data:{labels,datasets:[{data:vals,backgroundColor:colors,borderRadius:4,barPercentage:.82,categoryPercentage:.82}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      layout:{padding:{right:14,left:6}},
      plugins:{legend:{display:false},
        tooltip:{callbacks:{label:c=>{const r=items[c.dataIndex];
          return `May ₹${fmt(r.may,1)} Cr → Aug ₹${fmt(r.aug,1)} Cr  (${r.pct>=0?'+':''}${r.pct}% · ${r.delta>=0?'+':''}₹${fmt(r.delta,1)} Cr)`;}}}},
      scales:{
        x:{grid:{color:C.bd},ticks:{callback:v=>fmtVal(v)},title:{display:true,text:fmtVal.title,color:C.mut}},
        y:{grid:{display:false},ticks:{color:C.ink,font:{size:12}}}}},
    plugins:plugins||[]
  });
}
const pctFmt=v=>v+'%'; pctFmt.title='Growth vs May (%)';
const crFmt=v=>(v>0?'+':'')+v+' Cr'; crFmt.title='Δ gross ₹ Cr';

// ---- Super categories grouped bars ----
new Chart(document.getElementById('cSuper'),{
  type:'bar',
  data:{labels:D.supers.map(s=>s.name.replace('General Home Improvement / Decor','Home Improve / Decor')),
    datasets:[
      {label:'May',data:D.supers.map(s=>s.may),backgroundColor:C.blue+'99',borderRadius:5,barPercentage:.9,categoryPercentage:.72},
      {label:'Aug',data:D.supers.map(s=>s.aug),backgroundColor:C.acc,borderRadius:5,barPercentage:.9,categoryPercentage:.72}]},
  options:{responsive:true,maintainAspectRatio:false,
    plugins:{legend:{position:'top',labels:{boxWidth:12,boxHeight:12,usePointStyle:true,pointStyle:'rectRounded'}},
      tooltip:{callbacks:{label:c=>`${c.dataset.label}: ₹${fmt(c.parsed.y,1)} Cr`}}},
    scales:{x:{grid:{display:false},ticks:{color:C.ink,font:{size:11.5}}},
      y:{grid:{color:C.bd},ticks:{callback:v=>'₹'+v}}}}
});

// ---- movers ----
divergingChart('cTypes','wTypes',mergeMovers(D.types,'pct',8),'pct',pctFmt,[marketLine]);
divergingChart('cCats','wCats',mergeMovers(D.categories,'pct',7),'pct',pctFmt,[marketLine]);
divergingChart('cBrands','wBrands',mergeMovers(D.brands,'delta',8),'delta',crFmt);

// ---- new / gone chips ----
const chip=(name,val,unit)=>`<span class="chip"><b>${name}</b> <span class="s">${unit}${fmt(val,1)} Cr</span></span>`;
document.getElementById('newChips').innerHTML=(D.newBrands.length?D.newBrands:[{name:'—',aug:0}]).map(r=>chip(r.name,r.aug,'₹')).join('')||'—';
document.getElementById('exitChips').innerHTML=(D.exitBrands.length?D.exitBrands:[{name:'—',may:0}]).map(r=>chip(r.name,r.may,'was ₹')).join('')||'—';

document.getElementById('foot').innerHTML='Modelled ₹ = category MRP totals distributed by Est. Category Share SP, SP & MRP (net → units → gross). May uses May-period totals, Aug uses Aug-period totals, so movement reflects both category resizing and within-category share shifts. Growth % is each item vs its own May figure; the +25% line is the blended Q-Commerce home average. Non-home "Others" excluded.';
</script>
</body></html>"""

out = HTML.replace('__DATA__', DATA_JSON)
open('movement.html', 'w').write(out)
print(f'Wrote movement.html ({len(out)//1024} KB)')
