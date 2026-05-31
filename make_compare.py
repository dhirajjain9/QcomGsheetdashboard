"""Build compare.html — Cross Platform Analysis.

Context-first layout:
  • Q-Commerce TOTAL banner (gross, net, discount, brands, product types, OSA, SP)
  • 3 platform banners (same metrics each)
  • PRODUCT section: top-40 product types (gross/net/SP) + search -> Product ReportCard
    (① total size ② platform spread ③ leaders ④ attributes ⑤ SP value-tier verdict)
  • BRAND section: top-40 brands + search -> Brand ReportCard
    (① total ② attributes incl Net/Discount/SOV ③ root-cause gap diagnosis)

Product type & brand are the only axes comparable across platforms (categories
differ), normalised via product_types.py / lowercase brand key.
"""
import json
from collections import defaultdict

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
        a = m.setdefault(k, {"disp": disp_fn(s), "g": 0.0, "n": 0.0, "k": 0, "sov": 0.0,
                             "spread": {}, "spS": 0.0, "spN": 0, "osaW": 0.0, "osaWN": 0.0})
        a["g"] += s["_g"]; a["n"] += s["_n"]; a["k"] += 1; a["sov"] += (s.get("sov") or 0)
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
                  "b": len(a["spread"]), "keys": set(a["spread"].keys()), "sovsum": a["sov"],
                  "sp": round(a["spS"]/a["spN"]) if a["spN"] else 0,
                  "o": round(a["osaW"]/a["osaWN"], 1) if a["osaWN"] else 0, "top": top}
    return out


type_aggs, brand_aggs, totals = {}, {}, {}
BRAND_DISP = {}
TYPE_BRAND = defaultdict(lambda: defaultdict(float))
TYPE_SP = defaultdict(lambda: {"B": [], "I": [], "Z": []})

for name, f, key in PLATS:
    d = json.load(open(f))
    sku = sales_per_sku(d)
    for s in sku:
        bk = s["b"].lower(); BRAND_DISP.setdefault(bk, s["b"])
        if s["pt"] != "Other":
            TYPE_BRAND[s["pt"]][bk] += s["_g"]
            if s.get("sp") and s["sp"] > 0:
                TYPE_SP[s["pt"]][key].append((s["sp"], s["_g"]))
    type_aggs[key] = aggregate(sku, lambda s: s["pt"] if s["pt"] != "Other" else None,
                               lambda s: s["b"].lower(), lambda s: s["pt"])
    brand_aggs[key] = aggregate(sku, lambda s: s["b"].lower(),
                                lambda s: s["pt"], lambda s: s["b"])
    totals[key] = {"g": round(sum(d["meta"]["default_sales"].values()) * 1e7),
                   "k": d["kpis"]["skus"], "subs": len(d["subcats"]),
                   "types": len(type_aggs[key]), "brands": len(brand_aggs[key]),
                   "sov": sum((s.get("sov") or 0) for s in sku),
                   "n": round(sum(s["_n"] for s in sku)),
                   "osa": round(sum(s["osa"]*(s["_g"] or 0) for s in sku if s.get("osa") is not None)
                                / (sum((s["_g"] or 0) for s in sku if s.get("osa") is not None) or 1), 1),
                   "sp": round(sum(s["sp"] for s in sku if s.get("sp"))
                               / (sum(1 for s in sku if s.get("sp")) or 1))}


def quantile_edges(vals, n=5):
    vs = sorted(vals)
    if len(vs) < n * 2:
        return None
    edges = [vs[0]]
    for i in range(1, n):
        edges.append(vs[int(i/n*(len(vs)-1))])
    edges.append(vs[-1])

    def rnd(x):
        return int(round(x, -1)) if x >= 50 else int(round(x))
    edges = sorted(set(rnd(e) for e in edges))
    return edges if len(edges) >= 3 else None


def sp_tiers(type_):
    sp_all = []
    for k in ("B", "I", "Z"):
        sp_all += [sp for sp, g in TYPE_SP[type_][k]]
    edges = quantile_edges(sp_all, 5)
    if not edges:
        return None
    nb = len(edges) - 1
    gross = {k: [0.0]*nb for k in ("B", "I", "Z")}
    for k in ("B", "I", "Z"):
        for sp, g in TYPE_SP[type_][k]:
            idx = nb - 1
            for i in range(nb):
                if sp <= edges[i+1]:
                    idx = i; break
            gross[k][idx] += g
    return {"edges": edges, "g": {k: [round(x) for x in gross[k]] for k in ("B", "I", "Z")}}


def build_rows(aggs, use_disp, with_extras=False):
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
        union, tg, tn, tk, oW, oWN, spS, spN = set(), 0, 0, 0, 0.0, 0.0, 0, 0
        for k in ("B", "I", "Z"):
            v = aggs[k].get(kk)
            if v:
                row["p"] += 1
                row[k] = {"g": v["g"], "n": v["n"], "k": v["k"], "b": v["b"], "sp": v["sp"],
                          "o": v["o"], "top": v["top"], "sov": round(v["sovsum"]/(totals[k]["sov"] or 1)*100, 2)}
                union |= v["keys"]; tg += v["g"]; tn += v["n"]; tk += v["k"]
                if v["g"] > 0 and v["o"] is not None:
                    oW += v["o"]*v["g"]; oWN += v["g"]
                if v["sp"] > 0:
                    spS += v["sp"]*v["k"]; spN += v["k"]
            else:
                row[k] = None
        row["tot"] = {"g": tg, "n": tn, "k": tk, "b": len(union),
                      "sp": round(spS/spN) if spN else 0, "o": round(oW/oWN, 1) if oWN else 0}
        if with_extras:
            lead = sorted(TYPE_BRAND[kk].items(), key=lambda x: -x[1])[:4]
            row["lead"] = [[BRAND_DISP.get(bk, bk), round(g)] for bk, g in lead]
            row["tiers"] = sp_tiers(kk)
        rows.append(row)
    rows.sort(key=lambda r: -r["tot"]["g"])
    return rows


type_rows = build_rows(type_aggs, use_disp=False, with_extras=True)
brand_rows = build_rows(brand_aggs, use_disp=True)
allb = set()
for k in ("B", "I", "Z"):
    allb |= set(brand_aggs[k])
tg = sum(totals[k]["g"] for k in ("B", "I", "Z"))
tn = sum(totals[k]["n"] for k in ("B", "I", "Z"))
tk = sum(totals[k]["k"] for k in ("B", "I", "Z"))
qcom = {"g": tg, "n": tn, "k": tk, "brands": len(allb), "types": len(type_rows),
        "osa": round(sum(totals[k]["osa"]*totals[k]["g"] for k in ("B", "I", "Z"))/(tg or 1), 1),
        "sp": round(sum(totals[k]["sp"]*totals[k]["k"] for k in ("B", "I", "Z"))/(tk or 1))}
DATA = {"totals": totals, "qcom": qcom, "typeRows": type_rows, "brandRows": brand_rows}

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
h1{font-size:25px;font-weight:700;letter-spacing:-.3px;margin:0}h1 span{color:var(--acc)}
.sub{color:var(--mut);font-size:13px;margin:2px 0 16px}
a.back{font-size:12.5px;color:var(--mut);text-decoration:none;border:1px solid var(--line);padding:6px 12px;border-radius:8px;background:var(--panel)}
a.back:hover{color:var(--txt);border-color:var(--acc)}
.qtot{background:linear-gradient(100deg,#111827,#1f2937);color:#fff;border-radius:13px;padding:16px 20px;margin:0 0 12px;display:flex;flex-wrap:wrap;align-items:center;gap:10px 26px}
.qtot.sm{background:linear-gradient(100deg,#1f2937,#374151)}
.qtot .lead{font-size:11px;font-weight:700;color:#cbd5e1;text-transform:uppercase;letter-spacing:.6px;width:100%}
.qtot .big{font-size:27px;font-weight:800;letter-spacing:-.5px}
.qtot .met b{color:#fff;font-size:15px}.qtot .met{font-size:12px;color:#9aa6b6}
.platrow{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:22px}
@media(max-width:760px){.platrow{grid-template-columns:1fr}.spot{grid-template-columns:1fr!important}}
.pban{border-radius:12px;padding:13px 16px;color:#fff}
.pban.B{background:linear-gradient(100deg,#b45309,#ea9e0b)}.pban.I{background:linear-gradient(100deg,#9a3412,#ea580c)}.pban.Z{background:linear-gradient(100deg,#5b21b6,#7c3aed)}
.pban .pn{font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.5px;opacity:.95}
.pban .big{font-size:21px;font-weight:800;margin:2px 0}
.pban .mets{display:flex;flex-wrap:wrap;gap:3px 16px;font-size:11.5px;opacity:.95;margin-top:4px}
.pban .mets b{font-weight:700}
.sec{font-size:19px;font-weight:700;margin:26px 0 4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:14px}
.card h3{margin:0 0 2px;font-size:14px}
.step{font-size:11px;font-weight:700;color:var(--acc);text-transform:uppercase;letter-spacing:.5px}
.h3sub{color:var(--mut);font-size:12px;margin-bottom:12px}
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
input.search{border:1px solid var(--line);border-radius:9px;padding:9px 13px;font-size:14px;min-width:280px;background:var(--panel);color:var(--txt)}
.tag{font-size:11px;color:var(--mut);background:var(--panel2);border:1px solid var(--line);padding:3px 9px;border-radius:6px}
.qtot.detail{margin:14px 0}
.spot{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.pcard{border:1px solid var(--line);border-radius:11px;padding:13px 14px;border-top:4px solid var(--line)}
.pcard.B{border-top-color:var(--B)}.pcard.I{border-top-color:var(--I)}.pcard.Z{border-top-color:var(--Z)}
.pcard.absent{opacity:.55;background:repeating-linear-gradient(45deg,#fafafa,#fafafa 6px,#f3f3f3 6px,#f3f3f3 12px)}
.pcard .pn{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.3px}
.pcard.B .pn{color:var(--B)}.pcard.I .pn{color:var(--I)}.pcard.Z .pn{color:var(--Z)}
.pcard .big{font-size:22px;font-weight:700;margin:3px 0 1px}
.pcard .biglbl{font-size:10.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.3px}
.pcard .row{display:flex;justify-content:space-between;font-size:12.5px;margin-top:6px;border-top:1px dashed var(--line);padding-top:5px}
.pcard .row .k{color:var(--mut)}
.badge{display:inline-block;font-size:10px;font-weight:700;padding:2px 7px;border-radius:5px;margin-left:6px;vertical-align:middle}
.bg-grn{background:#dcfce7;color:#166534}.bg-amb{background:#fef3c7;color:#92400e}
.insight{background:#eef5ff;border:1px solid #d3e3fb;border-radius:11px;padding:13px 15px;margin-top:12px;font-size:13.5px;line-height:1.6}.insight b{color:#0b3d91}
.diagrow{border-left:5px solid var(--line);padding:10px 14px;border-radius:0 9px 9px 0;background:var(--panel2);margin-bottom:9px;font-size:13px;line-height:1.55}
.diagrow .pt{font-weight:700}.diagrow.good{background:#f0fdf4}.diagrow.warn{background:#fff7ed}.diagrow.bad{background:#fef2f2}
.cause{display:inline-block;background:#fff;border:1px solid var(--line);border-radius:6px;padding:1px 8px;font-size:12px;margin:2px 4px 0 0}
.verdict{border-radius:11px;padding:13px 15px;margin-top:12px;font-size:13.5px;line-height:1.6}
.verdict.uniform{background:#ecfdf5;border:1px solid #b9e8d0}.verdict.uniform b{color:#166534}
.verdict.vary{background:#fff7ed;border:1px solid #fed7aa}.verdict.vary b{color:#9a3412}
.spread-bar{display:flex;height:34px;border-radius:9px;overflow:hidden;border:1px solid var(--line);margin:4px 0 8px}
.spread-seg{display:flex;align-items:center;justify-content:center;color:#fff;font-size:12px;font-weight:700;min-width:2px}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--mut)}
.dotc{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle}
.leadrow{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.leadchip{font-size:12.5px;border:1px solid var(--line);border-radius:8px;padding:5px 10px;background:var(--panel2)}.leadchip b{color:var(--txt)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:720px){.grid2{grid-template-columns:1fr}}
table{border-collapse:collapse;width:100%;font-size:12.5px}
thead th{position:sticky;top:0;background:var(--panel);z-index:2;text-align:right;padding:7px 9px;border-bottom:2px solid var(--line);white-space:nowrap;cursor:pointer}
thead th:first-child,tbody td:first-child{text-align:left}
tbody td{padding:6px 9px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
tbody tr{cursor:pointer}tbody tr:hover{background:var(--panel2)}tbody tr.sel{background:#eef5ff}
.tableScroll{max-height:340px;overflow:auto}
.cwrap{position:relative;height:300px}
.miss{color:#c7c0b3}
</style></head>
<body><div class="wrap">
<header>
 <div><h1>Cross Platform <span>Analysis</span></h1>
  <div class="sub">Whole-of-Q-Commerce context, then drill into any <b>product type</b> or <b>brand</b> (the only axes comparable across platforms) · Apr 2026</div></div>
 <a class="back" href="platforms.html">← All platforms</a>
</header>

<!-- ===== CONTEXT ===== -->
<div class="qtot" id="qcomBanner"></div>
<div class="platrow" id="platBanners"></div>

<!-- ===== PRODUCT ===== -->
<div class="sec">📦 Product ReportCard</div>
<div class="card">
 <div class="controls"><input class="search" id="typeSearch" placeholder="search any product type…"><span class="tag" id="typeNote"></span></div>
 <div class="tableScroll"><table id="typeTbl"></table></div>
</div>
<div id="prodDetail">
 <div class="qtot detail" id="qtot"></div>
 <div class="grid2">
  <div class="card"><div class="step">② Platform-wise spread</div><h3>Where the demand sits</h3><div class="h3sub">Share of this product's total Q-Commerce gross by platform.</div><div class="spread-bar" id="spreadBar"></div><div class="legend" id="spreadLeg"></div></div>
  <div class="card"><div class="step">③ Who leads</div><h3>Top brands</h3><div class="h3sub">Across Q-Commerce (combined) and each platform's #1.</div><div id="leadQcom" style="margin-bottom:10px"></div><div id="leadPlat" class="leadrow"></div></div>
 </div>
 <div class="card"><div class="step">④ All attributes across platforms</div><h3>Platform scorecard</h3><div class="h3sub">Gross, net, discount, share, assortment, price & availability.</div><div class="spot" id="prodSpot"></div></div>
 <div class="card"><div class="step">⑤ SP distribution across value tiers</div><h3>Pricing — one strategy or platform-by-platform?</h3><div class="h3sub">Where each platform's gross sits across shared ₹ tiers. Same peak → one SP strategy; divergent → tailor by platform.</div><div class="cwrap"><canvas id="tierChart"></canvas></div><div class="verdict" id="tierVerdict"></div></div>
</div>

<!-- ===== BRAND ===== -->
<div class="sec">🏷️ Brand ReportCard</div>
<div class="card">
 <div class="controls"><input class="search" id="brandSearch" placeholder="search any brand…"><span class="tag" id="brandNote2"></span></div>
 <div class="tableScroll"><table id="brandTbl"></table></div>
</div>
<div id="brandDetail">
 <div class="qtot detail" id="bqtot"></div>
 <div class="card"><div class="step">② Attributes — total & platform-wise</div><h3>Scorecard</h3><div class="h3sub">Sales, realisation, assortment, price, availability & visibility per platform.</div><div class="spot" id="brandSpot"></div><div class="insight" id="brandInsight"></div></div>
 <div class="card"><div class="step">③ Why it isn't scaling — gap diagnosis</div><h3>What's holding it back, platform by platform</h3><div class="h3sub">Benchmarked to the brand's strongest platform. Root cause = distribution, assortment (SKUs), availability (OSA), visibility (SOV) or competition.</div><div id="brandDiag"></div></div>
</div>

<script>
const DATA=__DATA__;
const PK=[['B','Blinkit'],['I','Instamart'],['Z','Zepto']];
const NAME={B:'Blinkit',I:'Instamart',Z:'Zepto'},COL={B:'#ea9e0b',I:'#ea580c',Z:'#7c3aed'};
const money=v=>v==null?'–':v>=1e7?'₹'+(v/1e7).toFixed(2)+'Cr':v>=1e5?'₹'+(v/1e5).toFixed(1)+'L':v>=1e3?'₹'+(v/1e3).toFixed(1)+'K':'₹'+Math.round(v);
const disc=(g,n)=>(g>0&&n!=null)?Math.round((1-n/g)*100)+'%':'–';
const pres=r=>['B','I','Z'].filter(k=>r[k]);const absent=r=>['B','I','Z'].filter(k=>!r[k]);
const tc=s=>String(s).replace(/\b\w/g,c=>c.toUpperCase());
const TYPES=DATA.typeRows,BRANDS=DATA.brandRows;
const TMAP={},BMAP={};TYPES.forEach(r=>TMAP[r.t]=r);BRANDS.forEach(r=>BMAP[r.t]=r);
const shareOf=(k,g)=>DATA.totals[k].g?(g/DATA.totals[k].g*100):0;

// ===== CONTEXT BANNERS =====
const q=DATA.qcom;
document.getElementById('qcomBanner').innerHTML=
 `<div class="lead">Q-Commerce — all platforms</div>
  <div class="big">${money(q.g)}</div><div class="met" style="align-self:flex-end">gross&nbsp;MRP</div>
  <div class="met"><b>${money(q.n)}</b><br>net (SP)</div>
  <div class="met"><b>${disc(q.g,q.n)}</b><br>discount</div>
  <div class="met"><b>${q.brands.toLocaleString()}</b><br>brands</div>
  <div class="met"><b>${q.types}</b><br>product types</div>
  <div class="met"><b>${q.osa}%</b><br>avg OSA</div>
  <div class="met"><b>₹${q.sp}</b><br>avg SP</div>`;
document.getElementById('platBanners').innerHTML=PK.map(([k,n])=>{const t=DATA.totals[k];
 return `<div class="pban ${k}"><div class="pn">${n}</div><div class="big">${money(t.g)} <span style="font-size:12px;font-weight:600;opacity:.9">gross</span></div>
  <div class="mets"><span><b>${money(t.n)}</b> net</span><span><b>${disc(t.g,t.n)}</b> disc</span><span><b>${t.brands}</b> brands</span><span><b>${t.types}</b> types</span><span><b>${t.osa}%</b> OSA</span><span><b>₹${t.sp}</b> SP</span></div></div>`;}).join('');

// ===== shared card =====
function pcard(k,r,opts){
 if(!r)return `<div class="pcard ${k} absent"><div class="pn">${NAME[k]}</div><div class="big" style="font-size:15px;color:#a99">— not tracked —</div><div class="biglbl">absent on this platform</div></div>`;
 const badge=opts.badges&&opts.badges[k]?opts.badges[k]:'';
 return `<div class="pcard ${k}"><div class="pn">${NAME[k]}</div><div class="big">${opts.fmtBig(r[opts.bigKey])}${badge}</div><div class="biglbl">${opts.bigLbl}</div>
  ${opts.rows.map(([l,v])=>`<div class="row"><span class="k">${l}</span><span>${v(r)}</span></div>`).join('')}</div>`;
}

// ===== PRODUCT TABLE + DETAIL =====
function fillTypeTbl(qstr){
 let rs=TYPES.filter(r=>r.p>=1);
 if(qstr)rs=rs.filter(r=>r.t.toLowerCase().includes(qstr)); else rs=rs.slice(0,40);
 document.getElementById('typeNote').textContent=qstr?`${rs.length} match`:`top 40 of ${TYPES.length} product types`;
 document.getElementById('typeTbl').innerHTML=`<thead><tr><th>Product Type</th><th>Gross</th><th>Net</th><th>Discount</th><th>Avg SP</th><th>OSA</th><th>On</th></tr></thead><tbody>`+
  rs.map(r=>`<tr data-t="${r.t}"><td>${r.t}</td><td><b>${money(r.tot.g)}</b></td><td>${money(r.tot.n)}</td><td>${disc(r.tot.g,r.tot.n)}</td><td>₹${r.tot.sp}</td><td>${r.tot.o}%</td><td>${r.p}/3</td></tr>`).join('')+`</tbody>`;
 markSel('typeTbl',curType);
}
let curType,curBrand,tierChart;
function renderProduct(t){
 const r=TMAP[t];if(!r)return;curType=t;markSel('typeTbl',t);
 const pr=pres(r),tot=r.tot;
 document.getElementById('qtot').innerHTML=
  `<div class="lead">① ${r.t} — total size on Q-Commerce</div>
   <div class="big">${money(tot.g)}</div><div class="met" style="align-self:flex-end">gross&nbsp;MRP</div>
   <div class="met"><b>${money(tot.n)}</b><br>net (SP)</div><div class="met"><b>${disc(tot.g,tot.n)}</b><br>discount</div>
   <div class="met"><b>${tot.k.toLocaleString()}</b><br>SKUs</div><div class="met"><b>${tot.b}</b><br>brands</div>
   <div class="met"><b>₹${tot.sp}</b><br>avg SP</div><div class="met"><b>${tot.o}%</b><br>avg OSA</div><div class="met"><b>${r.p}/3</b><br>platforms</div>`;
 const segs=pr.map(k=>({k,g:r[k].g})).sort((a,b)=>b.g-a.g);
 document.getElementById('spreadBar').innerHTML=segs.map(s=>{const pct=tot.g?s.g/tot.g*100:0;return `<div class="spread-seg" style="background:${COL[s.k]};flex:${s.g}" title="${NAME[s.k]} ${money(s.g)}">${pct>=8?Math.round(pct)+'%':''}</div>`;}).join('');
 document.getElementById('spreadLeg').innerHTML=segs.map(s=>`<span><span class="dotc" style="background:${COL[s.k]}"></span>${NAME[s.k]} ${money(s.g)} (${tot.g?Math.round(s.g/tot.g*100):0}%)</span>`).join('')+(absent(r).length?`<span style="color:#bbb">absent: ${absent(r).map(k=>NAME[k]).join(', ')}</span>`:'');
 document.getElementById('leadQcom').innerHTML='<span class="tag">Across Q-Commerce</span> '+(r.lead||[]).map((b,i)=>`<span class="leadchip">${i+1}. <b>${b[0]}</b> ${money(b[1])}</span>`).join(' ');
 document.getElementById('leadPlat').innerHTML='<span class="tag">Platform #1</span> '+pr.map(k=>`<span class="leadchip"><span class="dotc" style="background:${COL[k]}"></span>${NAME[k]}: <b>${r[k].top||'–'}</b></span>`).join(' ');
 const strong=pr.reduce((a,k)=>r[k].g>r[a].g?k:a);
 document.getElementById('prodSpot').innerHTML=PK.map(([k])=>pcard(k,r[k],{bigKey:'g',bigLbl:'gross sales (MRP)',fmtBig:v=>money(v),badges:{[strong]:'<span class="badge bg-grn">biggest</span>'},
   rows:[['Net (SP)',x=>money(x.n)],['Discount',x=>disc(x.g,x.n)],['% of platform',x=>`${shareOf(k,x.g).toFixed(2)}%`],['SKUs',x=>x.k],['Brands',x=>x.b],['Avg SP',x=>'₹'+x.sp],['OSA',x=>`<b style="color:${x.o<40?'var(--red)':'var(--grn)'}">${x.o}%</b>`],['Top brand',x=>x.top||'–']]})).join('');
 renderTiers(r);
}
function renderTiers(r){
 const T=r.tiers,el=document.getElementById('tierChart'),v=document.getElementById('tierVerdict');
 if(tierChart)tierChart.destroy();
 if(!T){el.parentElement.style.display='none';v.className='verdict vary';v.innerHTML='Not enough price points across platforms to tier this product.';return;}
 el.parentElement.style.display='';
 const nb=T.edges.length-1,labels=[...Array(nb)].map((_,i)=>`₹${T.edges[i]}–${T.edges[i+1]}`),pr=pres(r);
 const ds=pr.map(k=>{const t=T.g[k].reduce((a,b)=>a+b,0)||1;return {label:NAME[k],data:T.g[k].map(x=>Math.round(x/t*100)),backgroundColor:COL[k],borderRadius:4,categoryPercentage:.7,barPercentage:.9};});
 tierChart=new Chart(el,{type:'bar',data:{labels,datasets:ds},options:{maintainAspectRatio:false,plugins:{legend:{position:'top'},tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${c.raw}% of its gross`}}},scales:{y:{title:{display:true,text:'% of platform gross'},ticks:{callback:v=>v+'%'},grid:{color:'#eee'}},x:{grid:{display:false}}}}});
 const topT={};pr.forEach(k=>{const a=T.g[k];let mi=0;a.forEach((x,i)=>{if(x>a[mi])mi=i;});topT[k]=mi;});
 const used=[...new Set(pr.map(k=>topT[k]))],lab=i=>`₹${T.edges[i]}–${T.edges[i+1]}`;
 if(used.length===1){v.className='verdict uniform';v.innerHTML=`✅ <b>One SP strategy can work.</b> Gross concentrates in the same tier (<b>${lab(used[0])}</b>) on all ${pr.length} platforms.`;}
 else{v.className='verdict vary';v.innerHTML=`⚠️ <b>Tailor pricing by platform.</b> Sweet-spot tier differs: `+pr.map(k=>`<span style="color:${COL[k]}">●</span> ${NAME[k]} <b>${lab(topT[k])}</b>`).join(' · ')+`.`;}
}

// ===== BRAND TABLE + DETAIL =====
function fillBrandTbl(qstr){
 let rs=BRANDS.filter(r=>r.p>=1);
 if(qstr)rs=rs.filter(r=>r.t.toLowerCase().includes(qstr)).slice(0,80); else rs=rs.slice(0,40);
 document.getElementById('brandNote2').textContent=qstr?`${rs.length} match`:`top 40 of ${BRANDS.length} brands`;
 document.getElementById('brandTbl').innerHTML=`<thead><tr><th>Brand</th><th>Gross</th><th>Net</th><th>Discount</th><th>Avg SP</th><th>OSA</th><th>On</th></tr></thead><tbody>`+
  rs.map(r=>`<tr data-t="${r.t}"><td>${r.t}</td><td><b>${money(r.tot.g)}</b></td><td>${money(r.tot.n)}</td><td>${disc(r.tot.g,r.tot.n)}</td><td>₹${r.tot.sp}</td><td>${r.tot.o}%</td><td>${r.p}/3</td></tr>`).join('')+`</tbody>`;
 markSel('brandTbl',curBrand);
}
function renderBrand(t){
 const r=BMAP[t];if(!r)return;curBrand=t;markSel('brandTbl',t);
 const pr=pres(r),tot=r.tot;
 const bench=pr.reduce((a,k)=>shareOf(k,r[k].g)>shareOf(a,r[a].g)?k:a);
 const weak=pr.length>1?pr.reduce((a,k)=>shareOf(k,r[k].g)<shareOf(a,r[a].g)?k:a):null;
 const badges={[bench]:'<span class="badge bg-grn">strongest</span>'};if(weak&&weak!==bench)badges[weak]='<span class="badge bg-amb">weakest</span>';
 document.getElementById('bqtot').innerHTML=`<div class="lead">① ${r.t} across Q-Commerce</div>
   <div class="big">${money(tot.g)}</div><div class="met" style="align-self:flex-end">gross&nbsp;MRP</div>
   <div class="met"><b>${money(tot.n)}</b><br>net (SP)</div><div class="met"><b>${disc(tot.g,tot.n)}</b><br>discount</div>
   <div class="met"><b>${tot.k.toLocaleString()}</b><br>SKUs</div><div class="met"><b>${tot.b}</b><br>product types</div>
   <div class="met"><b>₹${tot.sp}</b><br>avg SP</div><div class="met"><b>${tot.o}%</b><br>avg OSA</div><div class="met"><b>${r.p}/3</b><br>platforms</div>`;
 document.getElementById('brandSpot').innerHTML=PK.map(([k])=>pcard(k,r[k],{bigKey:'g',bigLbl:'gross sales (MRP)',fmtBig:v=>money(v),badges,
   rows:[['Net (SP)',x=>money(x.n)],['Discount',x=>disc(x.g,x.n)],['% of platform',x=>`<b>${shareOf(k,x.g).toFixed(2)}%</b>`],['SKUs',x=>x.k],['Product types',x=>x.b],['Avg SP',x=>'₹'+x.sp],['OSA',x=>`${x.o}%`],['SOV (visibility)',x=>`${x.sov}%`],['Top type',x=>x.top||'–']]})).join('');
 let s=`Strongest on <b>${NAME[bench]}</b> — ${money(r[bench].g)} (<b>${shareOf(bench,r[bench].g).toFixed(1)}%</b> of ${NAME[bench]}), led by <b>${r[bench].top}</b>. `;
 const ab=absent(r);if(ab.length)s+=`<b>Absent on ${ab.map(k=>NAME[k]).join(' & ')}</b>.`;
 document.getElementById('brandInsight').innerHTML='💡 '+s;
 renderDiag(r,bench);
}
function renderDiag(r,bench){
 const shb=shareOf(bench,r[bench].g);let html='';
 for(const [k,n] of PK){const v=r[k];let cls,head,body;
  if(!v){cls='bad';head='🔴 Not listed';body=`<span class="cause">distribution gap</span> Not present on ${n} — getting listed is step one.`;}
  else{const sh=shareOf(k,v.g);
   if(k===bench){cls='good';head='🟢 Lead platform';body=`${money(v.g)} · <b>${sh.toFixed(2)}%</b> of ${n} · OSA ${v.o}% · SOV ${v.sov}%. The model to replicate.`;}
   else if(sh>=shb*0.75){cls='good';head='🟢 On par';body=`${sh.toFixed(2)}% of ${n} (vs ${shb.toFixed(2)}% on ${NAME[bench]}). OSA ${v.o}%, SOV ${v.sov}%.`;}
   else{cls='warn';const c=[];
    if(v.k<r[bench].k*0.6)c.push(`<span class="cause">thin range</span> ${v.k} SKUs vs ${r[bench].k} on ${NAME[bench]}`);
    if(v.o<40||(r[bench].o&&v.o<r[bench].o*0.75))c.push(`<span class="cause">low availability</span> OSA ${v.o}%`);
    if(r[bench].sov&&v.sov<r[bench].sov*0.6)c.push(`<span class="cause">low visibility</span> SOV ${v.sov}% vs ${r[bench].sov}%`);
    if(!c.length){const tt=v.top,lt=(tt&&TMAP[tt]&&TMAP[tt][k])?TMAP[tt][k].top:null;
     if(lt&&lt.toLowerCase()!==r.t.toLowerCase())c.push(`<span class="cause">competition</span> ${tc(lt)} leads ${tt} on ${n}`);else c.push(`<span class="cause">crowded</span> share split thinly`);}
    head='🟠 Underperforming';body=`only <b>${sh.toFixed(2)}%</b> of ${n} (vs ${shb.toFixed(2)}% on ${NAME[bench]}). Likely cause: ${c.join(' ')}`;}}
  html+=`<div class="diagrow ${cls}" style="border-left-color:${COL[k]}"><span class="pt" style="color:${COL[k]}">${n}</span> — ${head}<br>${body}</div>`;}
 document.getElementById('brandDiag').innerHTML=html;
}

function markSel(id,t){document.querySelectorAll('#'+id+' tbody tr').forEach(tr=>tr.classList.toggle('sel',tr.dataset.t===t));}
document.getElementById('typeSearch').addEventListener('input',e=>fillTypeTbl(e.target.value.toLowerCase().trim()));
document.getElementById('brandSearch').addEventListener('input',e=>fillBrandTbl(e.target.value.toLowerCase().trim()));
document.getElementById('typeTbl').addEventListener('click',e=>{const tr=e.target.closest('tr[data-t]');if(tr){renderProduct(tr.dataset.t);document.getElementById('prodDetail').scrollIntoView({behavior:'smooth',block:'start'});}});
document.getElementById('brandTbl').addEventListener('click',e=>{const tr=e.target.closest('tr[data-t]');if(tr){renderBrand(tr.dataset.t);document.getElementById('brandDetail').scrollIntoView({behavior:'smooth',block:'start'});}});

fillTypeTbl(''); fillBrandTbl('');
renderProduct(TYPES[0].t); renderBrand(BRANDS[0].t);
</script>
</div></body></html>
"""

out = HTML.replace("__DATA__", json.dumps(DATA, separators=(",", ":")))
open("compare.html", "w").write(out)
print(f"Wrote compare.html ({len(out)//1024} KB) — context banners + top-40 tables + Product/Brand ReportCards")
print(f"Q-Commerce: {DATA['qcom']['g']/1e7:.1f}Cr gross, {DATA['qcom']['n']/1e7:.1f}Cr net, {DATA['qcom']['brands']} brands, {DATA['qcom']['types']} types")
