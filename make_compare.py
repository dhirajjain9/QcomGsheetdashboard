"""Build compare.html — the cross-platform (All-Platform) comparison.

Insight-first flow (not a raw matrix):
  1) Price & Availability — pick a product type -> per-platform avg SP & OSA with
     auto insight, plus ranked "biggest price gaps" and "underserved demand" lists.
  2) Brand head-to-head — pick a brand -> where it wins/loses across platforms with
     auto insight (incl. share of each platform), plus ranked "expansion gap" list.

Product type & brand are the only axes comparable across platforms (categories
differ), normalised by product_types.py / lowercase brand key.
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
        label = kk
        for k in ("B", "I", "Z"):
            if kk in aggs[k]:
                label = aggs[k][kk]["disp"] if use_disp else kk
                break
        row = {"t": label, "p": 0}
        for k in ("B", "I", "Z"):
            v = aggs[k].get(kk)
            if v:
                row["p"] += 1
                row[k] = {"g": v["g"], "n": v["n"], "k": v["k"], "b": v["b"],
                          "sp": v["sp"], "o": v["o"], "top": v["top"]}
            else:
                row[k] = None
        rows.append(row)
    rows.sort(key=lambda r: -sum((r[k]["g"] if r[k] else 0) for k in ("B", "I", "Z")))
    return rows


DATA = {"totals": totals,
        "typeRows": build_rows(type_aggs, use_disp=False),
        "brandRows": build_rows(brand_aggs, use_disp=True)}

HTML = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>QcomDashboard-EverydayEssentials</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#f7f4fb;--panel:#fff;--panel2:#f4efe4;--line:#e7dfd1;--txt:#1f2630;--mut:#6b7280;--acc:#2563eb;
 --grn:#16a34a;--red:#dc2626;--B:#ea9e0b;--I:#ea580c;--Z:#7c3aed;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;font-size:14px;line-height:1.5}
.wrap{max-width:1120px;margin:0 auto;padding:22px 18px 60px}
header{display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:12px;margin-bottom:6px}
h1{font-size:25px;font-weight:700;letter-spacing:-.3px;margin:0}
h1 span{color:var(--acc)}
.sub{color:var(--mut);font-size:13px;margin:2px 0 18px}
a.back{font-size:12.5px;color:var(--mut);text-decoration:none;border:1px solid var(--line);padding:6px 12px;border-radius:8px;background:var(--panel)}
a.back:hover{color:var(--txt);border-color:var(--acc)}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 15px;border-top:4px solid var(--line)}
.kpi.B{border-top-color:var(--B)} .kpi.I{border-top-color:var(--I)} .kpi.Z{border-top-color:var(--Z)}
.kpi .n{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.4px}
.kpi.B .n{color:var(--B)} .kpi.I .n{color:var(--I)} .kpi.Z .n{color:var(--Z)}
.kpi .v{font-size:20px;font-weight:700;margin-top:2px}
.kpi .l{font-size:11px;color:var(--mut)}
.tabs{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;margin-bottom:16px}
.tabs button{border:0;background:var(--panel);color:var(--mut);padding:9px 18px;font-size:13.5px;cursor:pointer;font-weight:600}
.tabs button.on{background:#111827;color:#fff}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:18px}
.card h3{margin:0 0 2px;font-size:15px}
.h3sub{color:var(--mut);font-size:12px;margin-bottom:12px}
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:14px}
select{border:1px solid var(--line);border-radius:9px;padding:8px 12px;font-size:14px;font-weight:600;min-width:240px;background:var(--panel);color:var(--txt)}
.tag{font-size:11px;color:var(--mut);background:var(--panel2);border:1px solid var(--line);padding:3px 9px;border-radius:6px}
.spot{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
@media(max-width:720px){.spot{grid-template-columns:1fr}.grid2{grid-template-columns:1fr!important}.kpis{grid-template-columns:1fr}}
.pcard{border:1px solid var(--line);border-radius:11px;padding:13px 14px;border-top:4px solid var(--line)}
.pcard.B{border-top-color:var(--B)} .pcard.I{border-top-color:var(--I)} .pcard.Z{border-top-color:var(--Z)}
.pcard.absent{opacity:.55;background:repeating-linear-gradient(45deg,#fafafa,#fafafa 6px,#f3f3f3 6px,#f3f3f3 12px)}
.pcard .pn{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.3px}
.pcard.B .pn{color:var(--B)} .pcard.I .pn{color:var(--I)} .pcard.Z .pn{color:var(--Z)}
.pcard .big{font-size:23px;font-weight:700;margin:4px 0 1px}
.pcard .biglbl{font-size:10.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.3px}
.pcard .row{display:flex;justify-content:space-between;font-size:12.5px;margin-top:6px;border-top:1px dashed var(--line);padding-top:5px}
.pcard .row .k{color:var(--mut)}
.badge{display:inline-block;font-size:10px;font-weight:700;padding:2px 7px;border-radius:5px;margin-left:6px;vertical-align:middle}
.bg-grn{background:#dcfce7;color:#166534}.bg-red{background:#fee2e2;color:#991b1b}.bg-amb{background:#fef3c7;color:#92400e}
.insight{background:#eef5ff;border:1px solid #d3e3fb;border-radius:11px;padding:13px 15px;margin-top:14px;font-size:13.5px;line-height:1.6}
.insight b{color:#0b3d91}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
thead th{position:sticky;top:0;background:var(--panel);z-index:2;text-align:right;padding:7px 9px;border-bottom:2px solid var(--line);white-space:nowrap}
thead th:first-child,tbody td:first-child{text-align:left}
tbody td{padding:6px 9px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
tbody tr{cursor:pointer}tbody tr:hover{background:var(--panel2)}
.tableScroll{max-height:430px;overflow:auto}
.dotc{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px;vertical-align:middle}
.miss{color:#c7c0b3}
</style></head>
<body><div class="wrap">
<header>
 <div><h1>Cross-Platform <span>Comparison</span></h1>
  <div class="sub">Blinkit · Instamart · Zepto compared on the only common axes — <b>product type</b> &amp; <b>brand</b> (categories differ per platform) · Apr 2026</div></div>
 <a class="back" href="platforms.html">← All platforms</a>
</header>
<div class="kpis" id="kpis"></div>

<div class="tabs" id="tabs">
 <button data-t="price" class="on">💰 Price &amp; Availability</button>
 <button data-t="brand">🏷️ Brand head-to-head</button>
</div>

<!-- ============ PRICE & AVAILABILITY ============ -->
<div id="priceTab">
 <div class="card">
  <div class="controls"><span class="tag">Product type</span><select id="typeSel"></select>
   <span class="tag" id="typeNote"></span></div>
  <div class="spot" id="priceSpot"></div>
  <div class="insight" id="priceInsight"></div>
 </div>
 <div class="grid2">
  <div class="card"><h3>💸 Biggest price gaps</h3><div class="h3sub">Same product type, widest avg-SP spread across platforms — positioning / arbitrage. Click to inspect.</div><div class="tableScroll"><table id="gapTbl"></table></div></div>
  <div class="card"><h3>📉 Underserved demand</h3><div class="h3sub">Real sales but low availability (OSA &lt; 40%) on a platform = unmet demand. Click to inspect.</div><div class="tableScroll"><table id="underTbl"></table></div></div>
 </div>
</div>

<!-- ============ BRAND HEAD-TO-HEAD ============ -->
<div id="brandTab" style="display:none">
 <div class="card">
  <div class="controls"><span class="tag">Brand</span><select id="brandSel"></select>
   <span class="tag" id="brandNote"></span></div>
  <div class="spot" id="brandSpot"></div>
  <div class="insight" id="brandInsight"></div>
 </div>
 <div class="card"><h3>🚀 Biggest expansion gaps</h3><div class="h3sub">Brands strong on one platform but <b>absent / thin</b> on another — where they could grow. Click to inspect.</div><div class="tableScroll"><table id="brandGapTbl"></table></div></div>
</div>

<script>
const DATA=__DATA__;
const PK=[['B','Blinkit'],['I','Instamart'],['Z','Zepto']];
const NAME={B:'Blinkit',I:'Instamart',Z:'Zepto'},COL={B:'#ea9e0b',I:'#ea580c',Z:'#7c3aed'};
const money=v=>v==null?'–':v>=1e7?'₹'+(v/1e7).toFixed(2)+'Cr':v>=1e5?'₹'+(v/1e5).toFixed(1)+'L':v>=1e3?'₹'+(v/1e3).toFixed(1)+'K':'₹'+Math.round(v);
const pres=r=>['B','I','Z'].filter(k=>r[k]);
const absent=r=>['B','I','Z'].filter(k=>!r[k]);
const byId=(rows)=>{const m={};rows.forEach(r=>m[r.t]=r);return m;};
const TYPES=DATA.typeRows, BRANDS=DATA.brandRows;
const TMAP=byId(TYPES), BMAP=byId(BRANDS);

document.getElementById('kpis').innerHTML=PK.map(([k,n])=>{const t=DATA.totals[k];
 return `<div class="kpi ${k}"><div class="n">${n}</div><div class="v">${money(t.g)}</div><div class="l">${t.k.toLocaleString()} SKUs · ${t.subs} categories · ${t.brands} brands</div></div>`;}).join('');

// ---------- shared mini-card ----------
function pcard(k,r,opts){ // opts: bigKey,bigLbl,fmtBig,badges{k:html},rows[[lbl,val]]
 if(!r){return `<div class="pcard ${k} absent"><div class="pn">${NAME[k]}</div><div class="big" style="font-size:15px;color:#a99">— not tracked —</div><div class="biglbl">absent on this platform</div></div>`;}
 const badge=opts.badges&&opts.badges[k]?opts.badges[k]:'';
 return `<div class="pcard ${k}"><div class="pn">${NAME[k]}</div>
  <div class="big">${opts.fmtBig(r[opts.bigKey])}${badge}</div><div class="biglbl">${opts.bigLbl}</div>
  ${opts.rows.map(([l,v])=>`<div class="row"><span class="k">${l}</span><span>${v(r)}</span></div>`).join('')}</div>`;
}

// ---------- PRICE & AVAILABILITY ----------
function fillTypeSel(){
 document.getElementById('typeSel').innerHTML=TYPES.filter(r=>r.p>=1).map(r=>`<option value="${r.t}">${r.t}</option>`).join('');
}
function renderPrice(t){
 const r=TMAP[t]; if(!r)return;
 const pr=pres(r);
 const wsp=pr.filter(k=>r[k].sp>0), wo=pr.filter(k=>r[k].o!=null);
 const loSP=wsp.length?wsp.reduce((a,k)=>r[k].sp<r[a].sp?k:a):null;
 const hiSP=wsp.length?wsp.reduce((a,k)=>r[k].sp>r[a].sp?k:a):null;
 const loO=wo.length?wo.reduce((a,k)=>r[k].o<r[a].o?k:a):null;
 const badges={};
 if(loSP&&hiSP&&loSP!==hiSP){badges[loSP]='<span class="badge bg-grn">cheapest</span>';badges[hiSP]='<span class="badge bg-red">priciest</span>';}
 if(loO&&r[loO].o<40)badges[loO]=(badges[loO]||'')+'<span class="badge bg-amb">low OSA</span>';
 document.getElementById('typeNote').textContent=`on ${r.p} of 3 platforms`;
 document.getElementById('priceSpot').innerHTML=PK.map(([k])=>pcard(k,r[k],{
   bigKey:'sp',bigLbl:'avg selling price',fmtBig:v=>'₹'+v,badges,
   rows:[['OSA',x=>`<b style="color:${x.o<40?'var(--red)':'var(--grn)'}">${x.o}%</b>`],
         ['Gross',x=>money(x.g)],['SKUs',x=>x.k],['Brands',x=>x.b],['Top brand',x=>x.top||'–']]})).join('');
 // insight
 let s='';
 if(wsp.length>=2){const spread=Math.round((r[hiSP].sp-r[loSP].sp)/r[loSP].sp*100);
   s+=`Avg SP runs <b>₹${r[loSP].sp} on ${NAME[loSP]}</b> → <b>₹${r[hiSP].sp} on ${NAME[hiSP]}</b> — a <b>${spread}% spread</b>. `;}
 else if(wsp.length===1)s+=`Priced ₹${r[wsp[0]].sp} on ${NAME[wsp[0]]} (only platform with price data). `;
 if(loO&&r[loO].o<40)s+=`Availability is weakest on <b>${NAME[loO]}</b> (OSA ${r[loO].o}%)${r[loO].g>2e6?` despite <b>${money(r[loO].g)}</b> of sales there → <b>underserved demand</b>`:''}. `;
 const ab=absent(r); if(ab.length)s+=`Not tracked on ${ab.map(k=>NAME[k]).join(' & ')}.`;
 document.getElementById('priceInsight').innerHTML='💡 '+(s||'Limited data for this type.');
}
function priceGaps(){ // types on >=2 platforms with sp, ranked by spread%
 const rows=TYPES.filter(r=>['B','I','Z'].filter(k=>r[k]&&r[k].sp>0).length>=2).map(r=>{
   const ks=['B','I','Z'].filter(k=>r[k]&&r[k].sp>0);
   const lo=ks.reduce((a,k)=>r[k].sp<r[a].sp?k:a),hi=ks.reduce((a,k)=>r[k].sp>r[a].sp?k:a);
   return {t:r.t,spread:(r[hi].sp-r[lo].sp)/r[lo].sp,lo,hi,r};}).filter(x=>x.spread>0)
   .sort((a,b)=>b.spread-a.spread).slice(0,25);
 document.getElementById('gapTbl').innerHTML=`<thead><tr><th>Product Type</th><th>Blinkit</th><th>Instamart</th><th>Zepto</th><th>Spread</th></tr></thead><tbody>`+
  rows.map(x=>`<tr data-t="${x.t}"><td>${x.t}</td>`+['B','I','Z'].map(k=>{const v=x.r[k];if(!v||!v.sp)return '<td class="miss">–</td>';
    const c=k===x.lo?'color:var(--grn);font-weight:700':k===x.hi?'color:var(--red);font-weight:700':'';return `<td style="${c}">₹${v.sp}</td>`;}).join('')+
    `<td><b>${Math.round(x.spread*100)}%</b></td></tr>`).join('')+`</tbody>`;
}
function underserved(){ // (type,platform) with gross>0.2Cr and OSA<40, by gross
 const rows=[];
 TYPES.forEach(r=>['B','I','Z'].forEach(k=>{if(r[k]&&r[k].g>2e6&&r[k].o!=null&&r[k].o<40)rows.push({t:r.t,k,g:r[k].g,o:r[k].o});}));
 rows.sort((a,b)=>b.g-a.g);
 document.getElementById('underTbl').innerHTML=`<thead><tr><th>Product Type</th><th>Platform</th><th>Sales</th><th>OSA</th></tr></thead><tbody>`+
  rows.slice(0,25).map(x=>`<tr data-t="${x.t}"><td>${x.t}</td><td style="text-align:right"><span class="dotc" style="background:${COL[x.k]}"></span>${NAME[x.k]}</td><td>${money(x.g)}</td><td style="color:var(--red);font-weight:700">${x.o}%</td></tr>`).join('')+`</tbody>`;
}

// ---------- BRAND HEAD-TO-HEAD ----------
function fillBrandSel(){
 document.getElementById('brandSel').innerHTML=BRANDS.filter(r=>r.p>=1).slice(0,400).map(r=>`<option value="${r.t}">${r.t}</option>`).join('');
}
const shareOf=(k,g)=>DATA.totals[k].g?(g/DATA.totals[k].g*100):0;
function renderBrand(t){
 const r=BMAP[t]; if(!r)return;
 const pr=pres(r);
 const strong=pr.reduce((a,k)=>r[k].g>r[a].g?k:a);
 const weak=pr.length>1?pr.reduce((a,k)=>r[k].g<r[a].g?k:a):null;
 const badges={[strong]:'<span class="badge bg-grn">strongest</span>'};
 if(weak&&weak!==strong)badges[weak]='<span class="badge bg-amb">weakest</span>';
 document.getElementById('brandNote').textContent=`present on ${r.p} of 3 platforms`;
 document.getElementById('brandSpot').innerHTML=PK.map(([k])=>pcard(k,r[k],{
   bigKey:'g',bigLbl:'gross sales',fmtBig:v=>money(v),badges,
   rows:[['% of platform',x=>`<b>${shareOf(k,x.g).toFixed(2)}%</b>`],
         ['SKUs',x=>x.k],['Product types',x=>x.b],['Avg SP',x=>'₹'+x.sp],
         ['OSA',x=>`${x.o}%`],['Top type',x=>x.top||'–']]})).join('');
 // insight
 let s=`Strongest on <b>${NAME[strong]}</b> — ${money(r[strong].g)} (<b>${shareOf(strong,r[strong].g).toFixed(1)}%</b> of ${NAME[strong]}'s gross), led by <b>${r[strong].top}</b>. `;
 const ab=absent(r);
 if(ab.length)s+=`<b>Absent on ${ab.map(k=>NAME[k]).join(' & ')}</b> → clear expansion gap. `;
 else if(weak&&weak!==strong)s+=`Thinnest on ${NAME[weak]} (${money(r[weak].g)}). `;
 // thin range note
 const thin=pr.filter(k=>r[k].k>=25).map(k=>({k,rps:r[k].g/r[k].k})).sort((a,b)=>a.rps-b.rps)[0];
 if(thin&&pr.length>1){const richest=pr.map(k=>({k,rps:r[k].g/r[k].k})).sort((a,b)=>b.rps-a.rps)[0];
   if(richest.rps>thin.rps*1.8)s+=`Range is widest-but-thinnest on ${NAME[thin.k]} (${r[thin.k].k} SKUs at ${money(Math.round(thin.rps))}/SKU vs ${money(Math.round(richest.rps))}/SKU on ${NAME[richest.k]}). `;}
 document.getElementById('brandInsight').innerHTML='💡 '+s;
}
function brandGaps(){ // brands strong somewhere (>=0.5Cr) but absent on >=1 platform
 const rows=BRANDS.filter(r=>r.p>=1&&r.p<3).map(r=>{const mx=Math.max(...pres(r).map(k=>r[k].g));return {r,mx};})
   .filter(x=>x.mx>=5e6).sort((a,b)=>b.mx-a.mx).slice(0,25);
 document.getElementById('brandGapTbl').innerHTML=`<thead><tr><th>Brand</th><th>Blinkit</th><th>Instamart</th><th>Zepto</th><th>Missing on</th></tr></thead><tbody>`+
  rows.map(({r})=>`<tr data-t="${r.t}"><td>${r.t}</td>`+['B','I','Z'].map(k=>r[k]?`<td>${money(r[k].g)}</td>`:'<td class="miss">–</td>').join('')+
   `<td style="color:var(--red);font-weight:600">${absent(r).map(k=>NAME[k]).join(', ')}</td></tr>`).join('')+`</tbody>`;
}

// ---------- wiring ----------
function showTab(t){
 document.getElementById('priceTab').style.display=t==='price'?'':'none';
 document.getElementById('brandTab').style.display=t==='brand'?'':'none';
}
document.querySelectorAll('#tabs button').forEach(b=>b.onclick=()=>{
 document.querySelectorAll('#tabs button').forEach(x=>x.classList.remove('on'));b.classList.add('on');showTab(b.dataset.t);});
document.getElementById('typeSel').addEventListener('change',e=>renderPrice(e.target.value));
document.getElementById('brandSel').addEventListener('change',e=>renderBrand(e.target.value));
document.getElementById('gapTbl').addEventListener('click',e=>{const tr=e.target.closest('tr[data-t]');if(tr){document.getElementById('typeSel').value=tr.dataset.t;renderPrice(tr.dataset.t);window.scrollTo({top:0,behavior:'smooth'});}});
document.getElementById('underTbl').addEventListener('click',e=>{const tr=e.target.closest('tr[data-t]');if(tr){document.getElementById('typeSel').value=tr.dataset.t;renderPrice(tr.dataset.t);window.scrollTo({top:0,behavior:'smooth'});}});
document.getElementById('brandGapTbl').addEventListener('click',e=>{const tr=e.target.closest('tr[data-t]');if(tr){document.getElementById('brandSel').value=tr.dataset.t;renderBrand(tr.dataset.t);window.scrollTo({top:0,behavior:'smooth'});}});

fillTypeSel(); fillBrandSel();
renderPrice(TYPES[0].t); priceGaps(); underserved();
renderBrand(BRANDS[0].t); brandGaps();
</script>
</div></body></html>
"""

out = HTML.replace("__DATA__", json.dumps(DATA, separators=(",", ":")))
open("compare.html", "w").write(out)
print(f"Wrote compare.html ({len(out)//1024} KB) — Price&Availability + Brand head-to-head flows")
