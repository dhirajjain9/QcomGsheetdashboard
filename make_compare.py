"""Build compare.html — the cross-platform (All-Platform) comparison.

Platforms define CATEGORIES differently, so the only apples-to-apples axis is
PRODUCT TYPE (+ brand), normalised by product_types.py across all platforms.
This reads the three per-platform data files and emits a self-contained page
comparing each product type across Blinkit / Instamart / Zepto.
"""
import json
from collections import defaultdict

PLATS = [("Blinkit", "dashboard_data.json", "B"),
         ("Instamart", "instamart_dashboard_data.json", "I"),
         ("Zepto", "zepto_dashboard_data.json", "Z")]


def sales_per_sku(d):
    """Replicate the dashboard sales model -> per-SKU gross & net (₹)."""
    sku = d["sku_level"]; DS = d["meta"]["default_sales"]
    for s in sku:
        s["_g"] = 0.0; s["_n"] = 0.0
    for sub in d["subcats"]:
        T = DS.get(sub, 0) * 1e7
        rows = [s for s in sku if s["s"] == sub and (s.get("csp") or 0) > 0
                and (s.get("sp") or 0) > 0 and (s.get("mrp") or 0) > 0]
        ss = sum(s["csp"] for s in rows)
        if T <= 0 or not ss:
            continue
        den = sum((s["csp"]/ss)*(s["mrp"]/s["sp"]) for s in rows)
        if not den:
            continue
        Tsp = T/den
        for s in rows:
            net = (s["csp"]/ss)*Tsp
            s["_n"] = net; s["_g"] = (net/s["sp"])*s["mrp"]
    return sku


def agg(d):
    """Per product-type metrics for one platform."""
    sku = sales_per_sku(d)
    m = {}
    for s in sku:
        t = s["pt"]
        if t == "Other":
            continue
        a = m.setdefault(t, {"g": 0.0, "n": 0.0, "k": 0, "brands": {},
                             "spS": 0.0, "spN": 0, "osaW": 0.0, "osaWN": 0.0})
        a["g"] += s["_g"]; a["n"] += s["_n"]; a["k"] += 1
        bk = s["b"].lower()
        a["brands"][bk] = a["brands"].get(bk, 0.0) + s["_g"]
        if s.get("sp"):
            a["spS"] += s["sp"]; a["spN"] += 1
        if s.get("osa") is not None:
            w = s["_g"] or 1e-6
            a["osaW"] += s["osa"]*w; a["osaWN"] += w
    out = {}
    for t, a in m.items():
        top = max(a["brands"].items(), key=lambda x: x[1])[0] if a["brands"] else ""
        out[t] = {"g": round(a["g"]), "n": round(a["n"]), "k": a["k"],
                  "b": len(a["brands"]),
                  "sp": round(a["spS"]/a["spN"]) if a["spN"] else 0,
                  "o": round(a["osaW"]/a["osaWN"], 1) if a["osaWN"] else 0,
                  "tb": top}
    return out


plataggs = {}
totals = {}
for name, f, key in PLATS:
    d = json.load(open(f))
    plataggs[key] = agg(d)
    # headline gross = the platform's entered MRP total (matches its dashboard; incl. Other)
    full_gross = round(sum(d["meta"]["default_sales"].values()) * 1e7)
    totals[key] = {"g": full_gross,
                   "k": d["kpis"]["skus"], "subs": len(d["subcats"]),
                   "types": len(plataggs[key])}

alltypes = set()
for key in ("B", "I", "Z"):
    alltypes |= set(plataggs[key])

rows = []
for t in alltypes:
    row = {"t": t}
    present = 0
    for key in ("B", "I", "Z"):
        v = plataggs[key].get(t)
        if v:
            present += 1
            row[key] = v
        else:
            row[key] = None
    row["p"] = present
    rows.append(row)
# default order: by combined gross
rows.sort(key=lambda r: -sum((r[k]["g"] if r[k] else 0) for k in ("B", "I", "Z")))

DATA = {"plats": [{"name": n, "key": k} for n, f, k in PLATS],
        "totals": totals, "rows": rows,
        "shared": sum(1 for r in rows if r["p"] == 3),
        "ntypes": len(rows)}

HTML = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>QcomDashboard-EverydayEssentials</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#f7f4fb;--panel:#fff;--panel2:#f4efe4;--line:#e7dfd1;--txt:#1f2630;--mut:#6b7280;--acc:#2563eb;
 --B:#ea9e0b;--Bc:#fef3c7;--Bt:#b45309;--I:#ea580c;--Ic:#ffe6cc;--It:#c2410c;--Z:#7c3aed;--Zc:#ece2fb;--Zt:#6d28d9;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;font-size:14px;line-height:1.5}
.wrap{max-width:1180px;margin:0 auto;padding:22px 18px 60px}
header{display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:12px;margin-bottom:6px}
h1{font-size:25px;font-weight:700;letter-spacing:-.3px;margin:0}
h1 span{color:var(--acc)}
.sub{color:var(--mut);font-size:13px;margin:2px 0 18px}
a.back{font-size:12.5px;color:var(--mut);text-decoration:none;border:1px solid var(--line);padding:6px 12px;border-radius:8px;background:var(--panel)}
a.back:hover{color:var(--txt);border-color:var(--acc)}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:18px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;border-top:4px solid var(--line)}
.kpi.B{border-top-color:var(--B)} .kpi.I{border-top-color:var(--I)} .kpi.Z{border-top-color:var(--Z)}
.kpi .n{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.4px}
.kpi.B .n{color:var(--Bt)} .kpi.I .n{color:var(--It)} .kpi.Z .n{color:var(--Zt)}
.kpi .v{font-size:21px;font-weight:700;margin-top:3px}
.kpi .l{font-size:11px;color:var(--mut)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:18px}
.card h3{margin:0 0 2px;font-size:15px}
.h3sub{color:var(--mut);font-size:12px;margin-bottom:12px}
.controls{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:14px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:9px;overflow:hidden}
.seg button{border:0;background:var(--panel);color:var(--mut);padding:7px 13px;font-size:12.5px;cursor:pointer;font-weight:500}
.seg button.on{background:var(--acc);color:#fff;font-weight:600}
input#q{border:1px solid var(--line);border-radius:9px;padding:7px 12px;font-size:13px;min-width:180px}
label.chk{font-size:12.5px;color:var(--mut);display:inline-flex;align-items:center;gap:5px;cursor:pointer}
.cwrap{position:relative;height:420px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
thead th{position:sticky;top:0;background:var(--panel);z-index:2;text-align:right;padding:8px 9px;border-bottom:2px solid var(--line);cursor:pointer;white-space:nowrap}
thead th:first-child,tbody td:first-child{text-align:left}
tbody td{padding:7px 9px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
tbody tr:hover{background:var(--panel2)}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-left:3px}
.lead{font-weight:700}
.bB{color:var(--Bt)} .bI{color:var(--It)} .bZ{color:var(--Zt)}
.miss{color:#c7c0b3}
.tableScroll{max-height:560px;overflow:auto}
.tag{font-size:11px;color:var(--mut);background:var(--panel2);border:1px solid var(--line);padding:2px 8px;border-radius:6px}
</style></head>
<body><div class="wrap">
<header>
 <div>
  <h1>Cross-Platform <span>Comparison</span></h1>
  <div class="sub" id="sub"></div>
 </div>
 <a class="back" href="platforms.html">← All platforms</a>
</header>

<div class="kpis" id="kpis"></div>

<div class="card">
 <div class="controls">
  <span class="tag">Metric</span>
  <div class="seg" id="metric">
   <button data-m="g" class="on">Gross ₹</button>
   <button data-m="n">Net ₹</button>
   <button data-m="k">SKUs</button>
   <button data-m="b"># Brands</button>
   <button data-m="sp">Avg SP</button>
   <button data-m="o">OSA %</button>
  </div>
  <label class="chk"><input type="checkbox" id="only3"> Only types on all 3</label>
  <input id="q" placeholder="filter product type…">
 </div>
 <h3>Top product types <span class="tag" id="chartNote"></span></h3>
 <div class="h3sub">Bars = the selected metric per platform. Product type is the common denominator — categories are not comparable across platforms.</div>
 <div class="cwrap"><canvas id="chart"></canvas></div>
</div>

<div class="card">
 <h3>Full matrix</h3>
 <div class="h3sub">Click a column header to sort. <b>Bold</b> = the leading platform for that type on the current metric. Dots show where the type is present.</div>
 <div class="tableScroll"><table id="tbl"><thead></thead><tbody></tbody></table></div>
</div>

<script>
const DATA=__DATA__;
const PK=[['B','Blinkit'],['I','Instamart'],['Z','Zepto']];
const COL={B:getCSS('--B'),I:getCSS('--I'),Z:getCSS('--Z')};
function getCSS(v){return getComputedStyle(document.documentElement).getPropertyValue(v).trim();}
let metric='g', only3=false, q='', sortKey='g', sortDir=-1;
const ADD={g:1,n:1,k:1,b:1};            // additive metrics (else average)
const money=v=>v>=1e7?'₹'+(v/1e7).toFixed(2)+'Cr':v>=1e5?'₹'+(v/1e5).toFixed(1)+'L':v>=1e3?'₹'+(v/1e3).toFixed(1)+'K':'₹'+Math.round(v);
function fmt(v,m){if(v==null)return '–';if(m==='g'||m==='n')return money(v);if(m==='sp')return '₹'+v;if(m==='o')return v+'%';return v;}
function val(r,k){return r[k]?r[k][metric]:null;}

document.getElementById('sub').textContent=`${DATA.ntypes} product types across 3 platforms · ${DATA.shared} present on all three · Apr 2026`;
// KPIs
document.getElementById('kpis').innerHTML=PK.map(([k,n])=>{const t=DATA.totals[k];
 return `<div class="kpi ${k}"><div class="n">${n}</div><div class="v">${money(t.g)}</div><div class="l">${t.k.toLocaleString()} SKUs · ${t.subs} categories · ${t.types} product types</div></div>`;}).join('');

function rowsView(){
 let rs=DATA.rows.filter(r=>!only3||r.p===3);
 if(q)rs=rs.filter(r=>r.t.toLowerCase().includes(q));
 const add=ADD[metric];
 rs=[...rs].sort((a,b)=>{
   const av=val(a,sortKey)??-1, bv=val(b,sortKey)??-1; return sortDir*(av-bv);});
 return rs;
}
let chart;
function rankRows(){ // for the chart: additive -> by selected metric sum; average -> by gross size
 let rs=DATA.rows.filter(r=>!only3||r.p===3); if(q)rs=rs.filter(r=>r.t.toLowerCase().includes(q));
 const by=ADD[metric]?metric:'g';
 return [...rs].sort((a,b)=>{const s=r=>('B I Z'.split(' ').reduce((x,k)=>x+(r[k]?r[k][by]:0),0));return s(b)-s(a);}).slice(0,18);
}
function draw(){
 const rs=rankRows();
 document.getElementById('chartNote').textContent=ADD[metric]?'ranked by total '+metric:'(ranked by gross size)';
 const ds=PK.map(([k,n])=>({label:n,data:rs.map(r=>val(r,k)||0),backgroundColor:COL[k],borderRadius:4,
   borderWidth:0,categoryPercentage:.7,barPercentage:.92}));
 if(chart)chart.destroy();
 chart=new Chart(document.getElementById('chart'),{type:'bar',data:{labels:rs.map(r=>r.t),datasets:ds},
  options:{maintainAspectRatio:false,indexAxis:'y',plugins:{legend:{position:'top'},
    tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${fmt(c.raw,metric)}`}}},
   scales:{x:{grid:{color:'#eee'},ticks:{callback:v=>metric==='g'||metric==='n'?money(v):metric==='sp'?'₹'+v:v}},
           y:{grid:{display:false},ticks:{font:{size:11},autoSkip:false}}}}});
}
function leadKey(r){let best=null,bv=-Infinity;for(const k of['B','I','Z']){const v=val(r,k);if(v!=null&&v>bv){bv=v;best=k;}}return best;}
function drawTable(){
 const heads=['Product Type','Blinkit','Instamart','Zepto','On'];
 const keys=['t','B','I','Z','p'];
 document.querySelector('#tbl thead').innerHTML='<tr>'+heads.map((h,i)=>{
   const k=keys[i]; const arrow=(sortKey===k||(k==='B'&&sortKey==='B'))?'':'';
   return `<th data-k="${k}">${h}</th>`;}).join('')+'</tr>';
 const rs=rowsView(); const lead=metric;
 document.querySelector('#tbl tbody').innerHTML=rs.map(r=>{
   const lk=leadKey(r);
   const cell=k=>{const v=val(r,k);if(v==null)return '<td class="miss">–</td>';
     const cls=(k===lk?'lead b'+k:'');return `<td class="${cls}" title="${r[k].tb||''}">${fmt(v,metric)}</td>`;};
   const dots=['B','I','Z'].map(k=>r[k]?`<span class="dot" style="background:${COL[k]}"></span>`:'').join('');
   return `<tr><td>${r.t}</td>${cell('B')}${cell('I')}${cell('Z')}<td>${dots}</td></tr>`;}).join('');
}
function redraw(){draw();drawTable();}
// events
document.querySelectorAll('#metric button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('#metric button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); metric=b.dataset.m; sortKey=(metric in {sp:1,o:1})?'B':metric; if(!(metric in {sp:1,o:1}))sortKey=metric; sortDir=-1; redraw();});
document.getElementById('only3').onchange=e=>{only3=e.target.checked;redraw();};
document.getElementById('q').oninput=e=>{q=e.target.value.toLowerCase().trim();redraw();};
document.querySelector('#tbl thead').addEventListener('click',e=>{const th=e.target.closest('th');if(!th)return;
  const k=th.dataset.k; if(k==='t'||k==='p')return; if(sortKey===k)sortDir*=-1;else{sortKey=k;sortDir=-1;} drawTable();});
redraw();
</script>
</div></body></html>
"""

out = HTML.replace("__DATA__", json.dumps(DATA, separators=(",", ":")))
open("compare.html", "w").write(out)
print(f"Wrote compare.html ({len(out)//1024} KB) · {DATA['ntypes']} types, {DATA['shared']} on all 3")
print("Platform gross totals:", {k: round(v["g"]/1e7, 1) for k, v in totals.items()})
