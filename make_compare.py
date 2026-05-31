"""Build compare.html — the cross-platform (All-Platform) comparison.

Platforms define CATEGORIES differently, so the only apples-to-apples axes are
PRODUCT TYPE and BRAND, both normalised across platforms (product type via
product_types.py; brand via lowercase key). This reads the three per-platform
data files and emits a self-contained page comparing each product type AND each
brand across Blinkit / Instamart / Zepto, with a click-to-expand attribute panel.
"""
import json

PLATS = [("Blinkit", "dashboard_data.json", "B"),
         ("Instamart", "instamart_dashboard_data.json", "I"),
         ("Zepto", "zepto_dashboard_data.json", "Z")]


def sales_per_sku(d):
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


def aggregate(sku, key_fn, sub_fn, disp_fn):
    """Generic per-entity aggregation. key_fn -> grouping key; sub_fn -> the
    'spread' dimension counted distinctly (brands for a type / types for a brand)."""
    m = {}
    for s in sku:
        k = key_fn(s)
        if k is None:
            continue
        a = m.setdefault(k, {"disp": disp_fn(s), "g": 0.0, "n": 0.0, "k": 0,
                             "spread": {}, "spS": 0.0, "spN": 0, "osaW": 0.0, "osaWN": 0.0})
        a["g"] += s["_g"]; a["n"] += s["_n"]; a["k"] += 1
        sd = sub_fn(s)
        a["spread"][sd] = a["spread"].get(sd, 0.0) + s["_g"]
        if s.get("sp"):
            a["spS"] += s["sp"]; a["spN"] += 1
        if s.get("osa") is not None:
            w = s["_g"] or 1e-6
            a["osaW"] += s["osa"]*w; a["osaWN"] += w
    out = {}
    for k, a in m.items():
        top = max(a["spread"].items(), key=lambda x: x[1])[0] if a["spread"] else ""
        out[k] = {"disp": a["disp"], "g": round(a["g"]), "n": round(a["n"]), "k": a["k"],
                  "b": len(a["spread"]),
                  "sp": round(a["spS"]/a["spN"]) if a["spN"] else 0,
                  "o": round(a["osaW"]/a["osaWN"], 1) if a["osaWN"] else 0,
                  "top": top}
    return out


type_aggs, brand_aggs, totals = {}, {}, {}
for name, f, key in PLATS:
    d = json.load(open(f))
    sku = sales_per_sku(d)
    type_aggs[key] = aggregate(sku, lambda s: s["pt"] if s["pt"] != "Other" else None,
                               lambda s: s["b"].lower(), lambda s: s["pt"])
    brand_aggs[key] = aggregate(sku, lambda s: s["b"].lower(),
                                lambda s: s["pt"], lambda s: s["b"])
    totals[key] = {"g": round(sum(d["meta"]["default_sales"].values()) * 1e7),
                   "k": d["kpis"]["skus"], "subs": len(d["subcats"]),
                   "types": len(type_aggs[key]), "brands": len(brand_aggs[key])}


def build_rows(aggs, use_disp):
    keys = set()
    for k in ("B", "I", "Z"):
        keys |= set(aggs[k])
    rows = []
    for kk in keys:
        # display label: prefer a non-empty disp from any platform
        label = kk
        for k in ("B", "I", "Z"):
            if kk in aggs[k]:
                label = aggs[k][kk]["disp"] if use_disp else kk
                break
        row = {"t": label}
        present = 0
        for k in ("B", "I", "Z"):
            v = aggs[k].get(kk)
            if v:
                present += 1
                row[k] = {"g": v["g"], "n": v["n"], "k": v["k"], "b": v["b"],
                          "sp": v["sp"], "o": v["o"], "top": v["top"]}
            else:
                row[k] = None
        row["p"] = present
        rows.append(row)
    rows.sort(key=lambda r: -sum((r[k]["g"] if r[k] else 0) for k in ("B", "I", "Z")))
    return rows


type_rows = build_rows(type_aggs, use_disp=False)
brand_rows = build_rows(brand_aggs, use_disp=True)

DATA = {"plats": [{"name": n, "key": k} for n, f, k in PLATS],
        "totals": totals,
        "typeRows": type_rows, "brandRows": brand_rows,
        "sharedTypes": sum(1 for r in type_rows if r["p"] == 3),
        "sharedBrands": sum(1 for r in brand_rows if r["p"] == 3),
        "nTypes": len(type_rows), "nBrands": len(brand_rows)}

HTML = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>QcomDashboard-EverydayEssentials</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#f7f4fb;--panel:#fff;--panel2:#f4efe4;--line:#e7dfd1;--txt:#1f2630;--mut:#6b7280;--acc:#2563eb;
 --B:#ea9e0b;--I:#ea580c;--Z:#7c3aed;}
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
.kpi.B .n{color:var(--B)} .kpi.I .n{color:var(--I)} .kpi.Z .n{color:var(--Z)}
.kpi .v{font-size:21px;font-weight:700;margin-top:3px}
.kpi .l{font-size:11px;color:var(--mut)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:18px}
.card h3{margin:0 0 2px;font-size:15px}
.h3sub{color:var(--mut);font-size:12px;margin-bottom:12px}
.controls{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:14px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:9px;overflow:hidden}
.seg button{border:0;background:var(--panel);color:var(--mut);padding:7px 13px;font-size:12.5px;cursor:pointer;font-weight:500}
.seg button.on{background:var(--acc);color:#fff;font-weight:600}
.seg.mode button.on{background:#111827}
input#q{border:1px solid var(--line);border-radius:9px;padding:7px 12px;font-size:13px;min-width:200px}
label.chk{font-size:12.5px;color:var(--mut);display:inline-flex;align-items:center;gap:5px;cursor:pointer}
.cwrap{position:relative;height:430px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
thead th{position:sticky;top:0;background:var(--panel);z-index:2;text-align:right;padding:8px 9px;border-bottom:2px solid var(--line);cursor:pointer;white-space:nowrap}
thead th:first-child,tbody td:first-child{text-align:left}
tbody td{padding:7px 9px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
tbody tr{cursor:pointer}
tbody tr:hover{background:var(--panel2)}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-left:3px}
.lead{font-weight:700}
.bB{color:var(--B)} .bI{color:var(--I)} .bZ{color:var(--Z)}
.miss{color:#c7c0b3}
.tableScroll{max-height:560px;overflow:auto}
.tag{font-size:11px;color:var(--mut);background:var(--panel2);border:1px solid var(--line);padding:2px 8px;border-radius:6px}
#detail{display:none}
#detail table{font-size:12.5px}
#detail .pill{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:middle}
.closeX{float:right;cursor:pointer;color:var(--mut);font-size:18px;line-height:1}
.detName{font-size:17px;font-weight:700}
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
  <span class="tag">View</span>
  <div class="seg mode" id="mode">
   <button data-x="t" class="on">By Product Type</button>
   <button data-x="b">By Brand</button>
  </div>
  <span class="tag" style="margin-left:8px">Metric</span>
  <div class="seg" id="metric">
   <button data-m="g" class="on">Gross ₹</button>
   <button data-m="n">Net ₹</button>
   <button data-m="k">SKUs</button>
   <button data-m="b" id="bBtn"># Brands</button>
   <button data-m="sp">Avg SP</button>
   <button data-m="o">OSA %</button>
  </div>
  <label class="chk"><input type="checkbox" id="only3"> On all 3</label>
  <input id="q" placeholder="filter…">
 </div>
 <h3 id="chartTitle">Top product types <span class="tag" id="chartNote"></span></h3>
 <div class="h3sub">Bars = the selected metric per platform. Product type &amp; brand are the only axes comparable across platforms — categories are not.</div>
 <div class="cwrap"><canvas id="chart"></canvas></div>
</div>

<div class="card" id="detail">
 <span class="closeX" onclick="closeDetail()">✕</span>
 <div class="detName" id="detName"></div>
 <div class="h3sub" id="detSub"></div>
 <div style="overflow:auto"><table id="detTbl"></table></div>
</div>

<div class="card">
 <h3 id="matTitle">Full matrix</h3>
 <div class="h3sub">Click a <b>row</b> to see all its attributes across platforms. Click a column header to sort. <b>Bold</b> = leading platform on the current metric; dots show presence.</div>
 <div class="tableScroll"><table id="tbl"><thead></thead><tbody></tbody></table></div>
</div>

<script>
const DATA=__DATA__;
const PK=[['B','Blinkit'],['I','Instamart'],['Z','Zepto']];
const COL={B:'#ea9e0b',I:'#ea580c',Z:'#7c3aed'};
let mode='t', metric='g', only3=false, q='', sortKey='g', sortDir=-1;
const ADD={g:1,n:1,k:1,b:1};
const money=v=>v>=1e7?'₹'+(v/1e7).toFixed(2)+'Cr':v>=1e5?'₹'+(v/1e5).toFixed(1)+'L':v>=1e3?'₹'+(v/1e3).toFixed(1)+'K':'₹'+Math.round(v);
function fmt(v,m){if(v==null)return '–';if(m==='g'||m==='n')return money(v);if(m==='sp')return '₹'+v;if(m==='o')return v+'%';return v;}
const rowsAll=()=>mode==='t'?DATA.typeRows:DATA.brandRows;
const entityWord=()=>mode==='t'?'product type':'brand';
const spreadWord=()=>mode==='t'?'brands':'product types';
const val=(r,k)=>r[k]?r[k][metric]:null;

document.getElementById('sub').textContent=`Compare across Blinkit · Instamart · Zepto on the only common axes — product type & brand · Apr 2026`;
document.getElementById('kpis').innerHTML=PK.map(([k,n])=>{const t=DATA.totals[k];
 return `<div class="kpi ${k}"><div class="n">${n}</div><div class="v">${money(t.g)}</div><div class="l">${t.k.toLocaleString()} SKUs · ${t.subs} categories · ${t.types} types · ${t.brands} brands</div></div>`;}).join('');

function syncLabels(){
 document.getElementById('bBtn').textContent=mode==='t'?'# Brands':'# Types';
 document.getElementById('chartTitle').firstChild.textContent=mode==='t'?'Top product types ':'Top brands ';
 document.getElementById('matTitle').textContent=mode==='t'?'Product-type matrix':'Brand matrix';
 document.querySelector('#sub').textContent=`${rowsAll().length} ${entityWord()}s across 3 platforms · ${mode==='t'?DATA.sharedTypes:DATA.sharedBrands} on all three · Apr 2026`;
}
function filtered(){let rs=rowsAll().filter(r=>!only3||r.p===3);if(q)rs=rs.filter(r=>r.t.toLowerCase().includes(q));return rs;}
let chart;
function rankRows(){const by=ADD[metric]?metric:'g';
 return [...filtered()].sort((a,b)=>{const s=r=>['B','I','Z'].reduce((x,k)=>x+(r[k]?r[k][by]:0),0);return s(b)-s(a);}).slice(0,18);}
function draw(){
 const rs=rankRows();
 document.getElementById('chartNote').textContent=ADD[metric]?'':'(ranked by gross size)';
 const ds=PK.map(([k,n])=>({label:n,data:rs.map(r=>val(r,k)||0),backgroundColor:COL[k],borderRadius:4,categoryPercentage:.72,barPercentage:.92}));
 if(chart)chart.destroy();
 chart=new Chart(document.getElementById('chart'),{type:'bar',data:{labels:rs.map(r=>r.t),datasets:ds},
  options:{maintainAspectRatio:false,indexAxis:'y',plugins:{legend:{position:'top'},
    tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${fmt(c.raw,metric)}`}}},
   scales:{x:{grid:{color:'#eee'},ticks:{callback:v=>(metric==='g'||metric==='n')?money(v):metric==='sp'?'₹'+v:v}},
           y:{grid:{display:false},ticks:{font:{size:11},autoSkip:false}}}}});
}
const leadKey=r=>{let best=null,bv=-Infinity;for(const k of['B','I','Z']){const v=val(r,k);if(v!=null&&v>bv){bv=v;best=k;}}return best;};
function drawTable(){
 document.querySelector('#tbl thead').innerHTML='<tr>'+
  [[mode==='t'?'Product Type':'Brand','t'],['Blinkit','B'],['Instamart','I'],['Zepto','Z'],['On','p']]
   .map(([h,k])=>`<th data-k="${k}">${h}</th>`).join('')+'</tr>';
 const rs=[...filtered()].sort((a,b)=>{const av=val(a,sortKey)??-1,bv=val(b,sortKey)??-1;return sortDir*(av-bv);});
 document.querySelector('#tbl tbody').innerHTML=rs.map((r,idx)=>{
   const lk=leadKey(r);
   const cell=k=>{const v=val(r,k);if(v==null)return '<td class="miss">–</td>';
     return `<td class="${k===lk?'lead b'+k:''}" title="top ${spreadWord().slice(0,-1)}: ${r[k].top||'–'}">${fmt(v,metric)}</td>`;};
   const dots=['B','I','Z'].map(k=>r[k]?`<span class="dot" style="background:${COL[k]}"></span>`:'').join('');
   return `<tr data-i="${idx}"><td>${r.t}</td>${cell('B')}${cell('I')}${cell('Z')}<td>${dots}</td></tr>`;}).join('');
 // attach current sorted list for click lookup
 window._cur=rs;
}
const METS=[['g','Gross ₹'],['n','Net ₹'],['k','SKUs'],['b',mode==='t'?'# Brands':'# Types'],['sp','Avg SP'],['o','OSA %']];
function showDetail(r){
 document.getElementById('detName').textContent=r.t;
 document.getElementById('detSub').textContent=`${entityWord()} · present on ${r.p} of 3 platforms`;
 const mets=[['g','Gross ₹'],['n','Net ₹'],['k','SKUs'],['b',mode==='t'?'# Brands':'# Types'],['sp','Avg SP'],['o','OSA %'],['top',mode==='t'?'Top brand':'Top type']];
 let h='<thead><tr><th style="text-align:left">Platform</th>'+mets.map(m=>`<th>${m[1]}</th>`).join('')+'</tr></thead><tbody>';
 for(const [k,n] of PK){const v=r[k];
   h+=`<tr><td style="text-align:left"><span class="pill" style="background:${COL[k]}"></span>${n}</td>`;
   if(!v){h+=`<td class="miss" colspan="7" style="text-align:center">not present / not tracked</td></tr>`;continue;}
   h+=mets.map(m=>m[0]==='top'?`<td style="text-align:left">${v.top||'–'}</td>`:`<td>${fmt(v[m[0]],m[0])}</td>`).join('')+'</tr>';}
 h+='</tbody>';
 document.getElementById('detTbl').innerHTML=h;
 const d=document.getElementById('detail');d.style.display='block';d.scrollIntoView({behavior:'smooth',block:'nearest'});
}
function closeDetail(){document.getElementById('detail').style.display='none';}
function redraw(){syncLabels();draw();drawTable();}
// events
document.querySelectorAll('#mode button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('#mode button').forEach(x=>x.classList.remove('on'));b.classList.add('on');
  mode=b.dataset.x; closeDetail(); if(!ADD[metric]&&metric!=='sp'&&metric!=='o')metric='g'; sortKey=ADD[metric]?metric:'g'; sortDir=-1; redraw();});
document.querySelectorAll('#metric button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('#metric button').forEach(x=>x.classList.remove('on'));b.classList.add('on');
  metric=b.dataset.m; sortKey=ADD[metric]?metric:'B'; sortDir=-1; redraw();});
document.getElementById('only3').onchange=e=>{only3=e.target.checked;redraw();};
document.getElementById('q').oninput=e=>{q=e.target.value.toLowerCase().trim();redraw();};
document.querySelector('#tbl thead').addEventListener('click',e=>{const th=e.target.closest('th');if(!th)return;const k=th.dataset.k;if(k==='t'||k==='p')return;if(sortKey===k)sortDir*=-1;else{sortKey=k;sortDir=-1;}drawTable();});
document.querySelector('#tbl tbody').addEventListener('click',e=>{const tr=e.target.closest('tr');if(!tr)return;const r=window._cur[+tr.dataset.i];if(r)showDetail(r);});
redraw();
</script>
</div></body></html>
"""

out = HTML.replace("__DATA__", json.dumps(DATA, separators=(",", ":")))
open("compare.html", "w").write(out)
print(f"Wrote compare.html ({len(out)//1024} KB)")
print(f"  product types: {DATA['nTypes']} ({DATA['sharedTypes']} on all 3)")
print(f"  brands:        {DATA['nBrands']} ({DATA['sharedBrands']} on all 3)")
