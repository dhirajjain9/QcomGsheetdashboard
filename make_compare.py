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
import math
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
        a = m.setdefault(k, {"disp": disp_fn(s), "g": 0.0, "n": 0.0, "k": 0, "sov": 0.0, "u": 0.0,
                             "spread": {}, "spS": 0.0, "spN": 0, "osaW": 0.0, "osaWN": 0.0})
        a["g"] += s["_g"]; a["n"] += s["_n"]; a["k"] += 1; a["sov"] += (s.get("sov") or 0)
        if s.get("sp") and s["sp"] > 0:
            a["u"] += s["_n"]/s["sp"]   # units = net SP revenue / SP
        sd = sub_fn(s)
        a["spread"][sd] = a["spread"].get(sd, 0.0) + s["_g"]
        if s.get("sp"):
            a["spS"] += s["sp"]; a["spN"] += 1
        if s.get("osa") is not None:
            a["osaW"] += s["osa"]; a["osaWN"] += 1   # simple mean (matches platform dashboards)
    out = {}
    for k, a in m.items():
        top = max(a["spread"].items(), key=lambda x: x[1])[0] if a["spread"] else ""
        out[k] = {"disp": a["disp"], "g": round(a["g"]), "n": round(a["n"]), "k": a["k"],
                  "b": len(a["spread"]), "keys": set(a["spread"].keys()), "sovsum": a["sov"],
                  "u": round(a["u"]),
                  "sp": round(a["spS"]/a["spN"]) if a["spN"] else 0,
                  "o": round(a["osaW"]/a["osaWN"], 1) if a["osaWN"] else 0, "top": top}
    return out


def opp_for_platform(sku):
    """Replicate the Founder's Launchpad opportunity scoring (lpTypeAgg) for one
    platform: per product type -> opportunity score, white-space remark, attack band."""
    T = defaultdict(lambda: {"skus": 0, "csp": 0.0, "g": 0.0, "osaW": 0.0, "osaWN": 0.0,
                             "brands": defaultdict(lambda: {"csp": 0.0, "osov": 0.0, "asov": 0.0}), "sps": []})
    for s in sku:
        t = s["pt"]
        if t == "Other":
            continue
        a = T[t]; w = s.get("csp") or 0
        a["skus"] += 1; a["csp"] += w; a["g"] += s["_g"]
        b = a["brands"][s["b"].lower()]; b["csp"] += w; b["osov"] += (s.get("osov") or 0); b["asov"] += (s.get("asov") or 0)
        if s.get("osa") is not None:
            ww = w or 1e-4; a["osaW"] += s["osa"]*ww; a["osaWN"] += ww
        if s.get("sp") and s["sp"] > 0:
            a["sps"].append((s["sp"], s["_g"]))
    if not T:
        return {}
    for a in T.values():
        v = list(a["brands"].values()); tot = sum(x["csp"] for x in v) or 1
        a["cr1"] = max((x["csp"] for x in v), default=0)/tot
        a["moat"] = max([0]+[(x["csp"]/tot)*(1-((x["asov"]/(x["asov"]+x["osov"])) if (x["asov"]+x["osov"]) > 0 else 0)) for x in v])
        wOSA = a["osaW"]/a["osaWN"] if a["osaWN"] else 0
        a["gap"] = max(0, 1-wOSA/100); a["beat"] = 1-a["moat"]; a["size"] = a["g"]
    maxSize = max(a["size"] for a in T.values()) or 1e-9
    us = sorted(a["size"]/max(1, a["skus"]) for a in T.values())
    cap = us[int(0.9*(len(us)-1))] or 1e-9
    out = {}
    for t, a in T.items():
        underN = min(1, (a["size"]/max(1, a["skus"]))/cap); demandN = a["size"]/maxSize
        ws = math.sqrt(underN*a["beat"]); gate = min(1, demandN/0.03)
        score = round(100*(0.30*demandN + 0.50*ws + 0.20*a["gap"])*gate)
        if a["moat"] >= 0.45:
            rem = "Organic fortress"
        elif a["cr1"] >= 0.45:
            rem = "Rented crown"
        elif ws >= 0.5:
            rem = "Prime white space"
        elif underN < 0.25:
            rem = "Crowded shelf"
        else:
            rem = "Open & contested"
        band = None
        sps = [sp for sp, g in a["sps"]]
        if sps:
            mn, mx = min(sps), max(sps); span = (mx-mn) or 1; n = 5
            bands = [{"lo": mn+span*i/n, "hi": mn+span*(i+1)/n, "g": 0.0, "k": 0} for i in range(n)]
            for sp, g in a["sps"]:
                idx = min(n-1, int((sp-mn)/span*n)); bands[idx]["g"] += g; bands[idx]["k"] += 1
            best, bv = None, -1
            for b in bands:
                if b["g"] <= 0:
                    continue
                val = b["g"]/(b["k"] or 1)
                if val > bv:
                    bv = val; best = b
            if best:
                band = [round(best["lo"]), round(best["hi"])]
        out[t] = {"score": score, "rem": rem, "ws": round(ws*100), "gap": round(a["gap"]*100), "band": band}
    return out


type_aggs, brand_aggs, totals, OPP = {}, {}, {}, {}
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
    OPP[key] = opp_for_platform(sku)
    type_aggs[key] = aggregate(sku, lambda s: s["pt"] if s["pt"] != "Other" else None,
                               lambda s: s["b"].lower(), lambda s: s["pt"])
    brand_aggs[key] = aggregate(sku, lambda s: s["b"].lower(),
                                lambda s: s["pt"], lambda s: s["b"])
    totals[key] = {"g": round(sum(d["meta"]["default_sales"].values()) * 1e7),
                   "k": d["kpis"]["skus"], "subs": len(d["subcats"]),
                   "types": len(type_aggs[key]), "brands": len(brand_aggs[key]),
                   "sov": sum((s.get("sov") or 0) for s in sku),
                   "n": round(sum(s["_n"] for s in sku)),
                   "osa": round(sum(s["osa"] for s in sku if s.get("osa") is not None)
                                / (sum(1 for s in sku if s.get("osa") is not None) or 1), 1),
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
        union, tg, tn, tk, tu, oW, oWN, spS, spN = set(), 0, 0, 0, 0, 0.0, 0.0, 0, 0
        for k in ("B", "I", "Z"):
            v = aggs[k].get(kk)
            if v:
                row["p"] += 1
                row[k] = {"g": v["g"], "n": v["n"], "k": v["k"], "b": v["b"], "sp": v["sp"], "u": v["u"],
                          "o": v["o"], "top": v["top"], "sov": round(v["sovsum"]/(totals[k]["sov"] or 1)*100, 2)}
                union |= v["keys"]; tg += v["g"]; tn += v["n"]; tk += v["k"]; tu += v["u"]
                if v["o"] is not None:
                    oW += v["o"]*v["k"]; oWN += v["k"]   # SKU-weighted = simple mean across the type's SKUs
                if v["sp"] > 0:
                    spS += v["sp"]*v["k"]; spN += v["k"]
            else:
                row[k] = None
        row["tot"] = {"g": tg, "n": tn, "k": tk, "u": tu, "b": len(union),
                      "sp": round(spS/spN) if spN else 0, "o": round(oW/oWN, 1) if oWN else 0}
        if with_extras:
            allg = sorted(TYPE_BRAND[kk].values(), reverse=True)
            row["c5"] = round(sum(allg[:5])/(sum(allg) or 1)*100)   # top-5 brand concentration
            lead = sorted(TYPE_BRAND[kk].items(), key=lambda x: -x[1])[:4]
            row["lead"] = [[BRAND_DISP.get(bk, bk), round(g)] for bk, g in lead]
            row["tiers"] = sp_tiers(kk)
            row["opp"] = {k: OPP[k].get(kk) for k in ("B", "I", "Z")}
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
        "osa": round(sum(totals[k]["osa"]*totals[k]["k"] for k in ("B", "I", "Z"))/(tk or 1), 1),
        "sp": round(sum(totals[k]["sp"]*totals[k]["k"] for k in ("B", "I", "Z"))/(tk or 1))}
DATA = {"totals": totals, "qcom": qcom, "typeRows": type_rows, "brandRows": brand_rows}

HTML = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>QcomDashboard-EverydayEssentials</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{
 --bg:#f5f5f7;--panel:#fff;--ink:#1d1d1f;--ink2:#6e6e73;--ink3:#86868b;
 --hair:#e8e8ed;--hair2:#d2d2d7;--acc:#0071e3;
 --grn:#34c759;--red:#ff3b30;--amb:#ff9500;
 --B:#e8930c;--I:#fc6a1a;--Z:#7b3fe4;
 --sh:0 1px 2px rgba(0,0,0,.04),0 12px 32px -18px rgba(0,0,0,.18);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","SF Pro Display","Segoe UI",Roboto,Helvetica,Arial,sans-serif;
 font-size:14px;line-height:1.5;-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
.wrap{max-width:1080px;margin:0 auto;padding:30px 22px 80px}
header{display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:12px;margin-bottom:22px}
h1{font-size:30px;font-weight:600;letter-spacing:-.022em;margin:0}h1 span{color:var(--acc)}
.sub{color:var(--ink2);font-size:14px;margin:6px 0 0;max-width:700px}
a.back{font-size:13px;color:var(--acc);text-decoration:none;padding:7px 15px;border-radius:980px;background:rgba(0,113,227,.08);font-weight:500}
a.back:hover{background:rgba(0,113,227,.15)}
/* hero total */
.qtot{background:var(--panel);color:var(--ink);border:1.5px solid #c2c2cc;border-radius:20px;padding:22px 26px;margin:0 0 14px;box-shadow:var(--sh)}
.qtot .lead{font-size:12px;font-weight:600;color:var(--ink2);text-transform:uppercase;letter-spacing:.07em;margin-bottom:10px}
.qtot .big{font-size:38px;font-weight:600;letter-spacing:-.03em;line-height:1}
.qtot .cap{font-size:14px;color:var(--ink3);margin-left:10px;font-weight:400}
.qtot .mets{display:flex;flex-wrap:wrap;gap:14px 0;margin-top:18px;border-top:1px solid var(--hair);padding-top:15px}
.qtot .met{padding:0 22px;border-left:1px solid var(--hair)}
.qtot .met:first-child{padding-left:0;border-left:0}
.qtot .met .v{font-size:18px;font-weight:600;letter-spacing:-.01em}
.qtot .met .l{font-size:12px;color:var(--ink2);margin-top:3px}
.qtot.detail{border-radius:18px;padding:20px 24px;background:#fbfbfd;border:1px solid var(--hair);box-shadow:none}
.qtot.detail .big{font-size:32px}
/* platform context cards */
.platrow{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:26px}
@media(max-width:760px){.platrow{grid-template-columns:1fr}.spot{grid-template-columns:1fr!important}.grid2{grid-template-columns:1fr!important}.qtot .met{padding:0 16px}}
.pban{background:var(--panel);border:1.5px solid #c2c2cc;border-radius:18px;padding:18px 20px 16px;box-shadow:var(--sh);position:relative;overflow:hidden}
.pban::before{content:"";position:absolute;top:0;left:0;right:0;height:4px;background:var(--pc)}
.pban.B{--pc:var(--B)}.pban.I{--pc:var(--I)}.pban.Z{--pc:var(--Z)}
.pban .pn{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--pc);display:flex;align-items:center;gap:7px}
.pban .pn::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--pc)}
.pban .big{font-size:24px;font-weight:600;letter-spacing:-.02em;margin:7px 0 0}
.pban .cap2{font-size:11.5px;color:var(--ink3);margin-bottom:8px}
.pban .mets{display:grid;grid-template-columns:repeat(3,1fr);gap:16px 14px;border-top:1px solid var(--hair);padding-top:15px;margin-top:13px}
.pban .mets .m .l{font-size:10px;color:var(--ink3);text-transform:uppercase;letter-spacing:.02em;white-space:nowrap}
.pban .mets .m .v{font-size:14.5px;font-weight:600;color:var(--ink);margin-top:3px;white-space:nowrap}
/* sections + cards */
.sec{font-size:22px;font-weight:600;letter-spacing:-.02em;margin:38px 0 14px}
.card{background:var(--panel);border-radius:18px;padding:20px 22px;margin-bottom:14px;box-shadow:var(--sh)}
.card h3{margin:0;font-size:17px;font-weight:600;letter-spacing:-.01em}
.step{font-size:11px;font-weight:600;color:var(--acc);text-transform:uppercase;letter-spacing:.07em;display:block;margin-bottom:4px}
.h3sub{color:var(--ink2);font-size:13px;margin:4px 0 16px}
.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
input.search{border:1px solid var(--hair2);border-radius:980px;padding:10px 17px;font-size:14px;min-width:300px;background:var(--panel);color:var(--ink);outline:none}
input.search:focus{border-color:var(--acc);box-shadow:0 0 0 4px rgba(0,113,227,.15)}
.tag{font-size:12.5px;color:var(--ink2)}
.qtot.detail{margin:0 0 14px}
/* scorecard */
.spot{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.pcard{background:#fbfbfd;border:1px solid var(--hair);border-radius:16px;padding:16px 17px;--pc:var(--ink3)}
.pcard.B{--pc:var(--B)}.pcard.I{--pc:var(--I)}.pcard.Z{--pc:var(--Z)}
.pcard.absent{opacity:.6;border-style:dashed;background:#fafafa}
.pcard .pn{font-size:11.5px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--pc)}
.pcard .big{font-size:24px;font-weight:600;letter-spacing:-.02em;margin:4px 0 1px}
.pcard .biglbl{font-size:11px;color:var(--ink3);text-transform:uppercase;letter-spacing:.04em}
.pcard .row{display:flex;justify-content:space-between;font-size:13px;margin-top:7px;padding-top:6px;border-top:1px solid var(--hair)}
.pcard .row .k{color:var(--ink2)}
.badge{display:inline-block;font-size:10.5px;font-weight:600;padding:2px 9px;border-radius:980px;margin-left:7px;vertical-align:middle}
.bg-grn{background:rgba(52,199,89,.15);color:#1c7c3a}.bg-amb{background:rgba(255,149,0,.16);color:#9a5b00}
.insight{background:rgba(0,113,227,.06);border:1px solid rgba(0,113,227,.14);border-radius:14px;padding:14px 16px;margin-top:14px;font-size:13.5px;line-height:1.6}.insight b{color:var(--acc)}
.diagrow{border-radius:14px;padding:13px 16px;margin-bottom:10px;font-size:13px;line-height:1.55;background:#fbfbfd;border:1px solid var(--hair);border-left:4px solid var(--pc,#ccc)}
.diagrow .pt{font-weight:600}
.diagrow.good{background:rgba(52,199,89,.07)}.diagrow.warn{background:rgba(255,149,0,.08)}.diagrow.bad{background:rgba(255,59,48,.07)}
.cause{display:inline-block;background:var(--panel);border:1px solid var(--hair2);border-radius:980px;padding:2px 10px;font-size:12px;margin:3px 5px 0 0;font-weight:500}
.verdict{border-radius:14px;padding:14px 16px;margin-top:14px;font-size:13.5px;line-height:1.6}
.verdict.uniform{background:rgba(52,199,89,.09);border:1px solid rgba(52,199,89,.25)}.verdict.uniform b{color:#1c7c3a}
.verdict.vary{background:rgba(255,149,0,.10);border:1px solid rgba(255,149,0,.28)}.verdict.vary b{color:#9a5b00}
.spread-bar{display:flex;height:38px;border-radius:11px;overflow:hidden;margin:6px 0 10px;box-shadow:inset 0 0 0 1px var(--hair)}
.spread-seg{display:flex;align-items:center;justify-content:center;color:#fff;font-size:12px;font-weight:600;min-width:2px}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:12.5px;color:var(--ink2)}
.dotc{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle}
.leadrow{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.leadchip{font-size:13px;border:1px solid var(--hair);border-radius:980px;padding:6px 12px;background:#fbfbfd}.leadchip b{color:var(--ink)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
table{border-collapse:collapse;width:100%;font-size:13px}
thead th{position:sticky;top:0;background:rgba(255,255,255,.82);backdrop-filter:blur(8px);z-index:2;text-align:right;padding:10px 12px;border-bottom:1px solid var(--hair2);white-space:nowrap;cursor:pointer;font-weight:600;color:var(--ink2);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
thead th:first-child,tbody td:first-child{text-align:left}
tbody td{padding:10px 12px;text-align:right;border-bottom:1px solid var(--hair);white-space:nowrap}
tbody tr{cursor:pointer}tbody tr:hover{background:#f5f5f7}tbody tr.sel{background:rgba(0,113,227,.07)}
.tableScroll{max-height:360px;overflow:auto;border-radius:12px;border:1px solid var(--hair)}
.cwrap{position:relative;height:300px}
.miss{color:var(--ink3)}
</style></head>
<!--__STYLE_END__-->
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
<div class="sec">Product ReportCard</div>
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
 <div class="card"><div class="step">⑥ Opportunity to launch</div><h3>Where the opening is — per platform</h3><div class="h3sub">Founder's Launchpad scoring computed within each platform: opportunity score (0–100), white-space signal, availability gap & the attack price band.</div><div class="spot" id="oppSpot"></div></div>
</div>

<!-- ===== BRAND ===== -->
<div class="sec">Brand ReportCard</div>
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
const money=v=>v==null?'–':v>=1e7?'₹'+(v/1e7).toFixed(1)+'Cr':v>=1e5?'₹'+(v/1e5).toFixed(1)+'L':v>=1e3?'₹'+(v/1e3).toFixed(1)+'K':'₹'+Math.round(v);
const unitsFmt=v=>v==null?'–':v>=1e6?(v/1e6).toFixed(2)+'M':v>=1e3?(v/1e3).toFixed(0)+'K':''+Math.round(v);
const disc=(g,n)=>(g>0&&n!=null)?Math.round((1-n/g)*100)+'%':'–';
const pres=r=>['B','I','Z'].filter(k=>r[k]);const absent=r=>['B','I','Z'].filter(k=>!r[k]);
const tc=s=>String(s).replace(/\b\w/g,c=>c.toUpperCase());
const TYPES=DATA.typeRows,BRANDS=DATA.brandRows;
const TMAP={},BMAP={};TYPES.forEach(r=>TMAP[r.t]=r);BRANDS.forEach(r=>BMAP[r.t]=r);
const shareOf=(k,g)=>DATA.totals[k].g?(g/DATA.totals[k].g*100):0;

// ===== CONTEXT BANNERS =====
const q=DATA.qcom;
// hero builder: eyebrow + big figure + caption + a row of value/label metrics
function hero(lead,big,cap,mets){
 return `<div class="lead">${lead}</div><span class="big">${big}</span><span class="cap">${cap}</span>
  <div class="mets">${mets.map(m=>`<div class="met"><div class="v">${m[1]}</div><div class="l">${m[0]}</div></div>`).join('')}</div>`;
}
document.getElementById('qcomBanner').innerHTML=hero('Q-Commerce · all platforms',money(q.g),'gross MRP',
 [['Net (SP)',money(q.n)],['Discount',disc(q.g,q.n)],['Brands',q.brands.toLocaleString()],['Product types',q.types],['Avg OSA',q.osa+'%'],['Avg SP','₹'+q.sp]]);
document.getElementById('platBanners').innerHTML=PK.map(([k,n])=>{const t=DATA.totals[k];
 const cells=[['Net (SP)',money(t.n)],['Discount',disc(t.g,t.n)],['Brands',t.brands],['Prod Type',t.types],['Avg OSA',t.osa+'%'],['Avg SP','₹'+t.sp]];
 return `<div class="pban ${k}"><div class="pn">${n}</div><div class="big">${money(t.g)}</div><div class="cap2">gross MRP</div>
  <div class="mets">${cells.map(c=>`<div class="m"><div class="l">${c[0]}</div><div class="v">${c[1]}</div></div>`).join('')}</div></div>`;}).join('');

// ===== shared card =====
function pcard(k,r,opts){
 if(!r)return `<div class="pcard ${k} absent"><div class="pn">${NAME[k]}</div><div class="big" style="font-size:15px;color:#a99">— not tracked —</div><div class="biglbl">absent on this platform</div></div>`;
 const badge=opts.badges&&opts.badges[k]?opts.badges[k]:'';
 return `<div class="pcard ${k}"><div class="pn">${NAME[k]}</div><div class="big">${opts.fmtBig(r[opts.bigKey])}${badge}</div><div class="biglbl">${opts.bigLbl}</div>
  ${opts.rows.map(([l,v])=>`<div class="row"><span class="k">${l}</span><span>${v(r)}</span></div>`).join('')}</div>`;
}

// ===== PRODUCT TABLE + DETAIL =====
let typeSort={k:'g',d:-1},brandSort={k:'g',d:-1};
const tval=(r,k)=>k==='disc'?(r.tot.g?1-r.tot.n/r.tot.g:0):k==='c5'?(r.c5||0):(r.tot[k]||0);
function headRow(cols,sort){return '<thead><tr>'+cols.map(c=>c[1]?`<th data-k="${c[1]}">${c[0]}${sort.k===c[1]?(sort.d<0?' ↓':' ↑'):''}</th>`:`<th>${c[0]}</th>`).join('')+'</tr></thead>';}
function fillTypeTbl(qstr){
 let rs=TYPES.filter(r=>r.p>=1);
 if(qstr)rs=rs.filter(r=>r.t.toLowerCase().includes(qstr));
 rs=rs.sort((a,b)=>typeSort.d*(tval(a,typeSort.k)-tval(b,typeSort.k)));
 if(!qstr)rs=rs.slice(0,40);
 document.getElementById('typeNote').textContent=qstr?`${rs.length} match`:`top 40 of ${TYPES.length} product types`;
 const cols=[['Product Type',''],['Gross','g'],['Net','n'],['Discount','disc'],['Units','u'],['Avg SP','sp'],['OSA','o'],['Brands','b'],['Top-5','c5']];
 document.getElementById('typeTbl').innerHTML=headRow(cols,typeSort)+'<tbody>'+
  rs.map(r=>`<tr data-t="${r.t}"><td>${r.t}</td><td><b>${money(r.tot.g)}</b></td><td>${money(r.tot.n)}</td><td>${disc(r.tot.g,r.tot.n)}</td><td>${unitsFmt(r.tot.u)}</td><td>₹${r.tot.sp}</td><td>${r.tot.o}%</td><td>${r.tot.b}</td><td>${r.c5}%</td></tr>`).join('')+'</tbody>';
 markSel('typeTbl',curType);
}
let curType,curBrand,tierChart;
function renderProduct(t){
 const r=TMAP[t];if(!r)return;curType=t;markSel('typeTbl',t);
 const pr=pres(r),tot=r.tot;
 document.getElementById('qtot').innerHTML=hero(`① ${r.t} · total size on Q-Commerce`,money(tot.g),'gross MRP',
   [['Net (SP)',money(tot.n)],['Discount',disc(tot.g,tot.n)],['SKUs',tot.k.toLocaleString()],['Brands',tot.b],['Avg SP','₹'+tot.sp],['Avg OSA',tot.o+'%']]);
 const segs=pr.map(k=>({k,g:r[k].g})).sort((a,b)=>b.g-a.g);
 document.getElementById('spreadBar').innerHTML=segs.map(s=>{const pct=tot.g?s.g/tot.g*100:0;return `<div class="spread-seg" style="background:${COL[s.k]};flex:${s.g}" title="${NAME[s.k]} ${money(s.g)}">${pct>=8?Math.round(pct)+'%':''}</div>`;}).join('');
 document.getElementById('spreadLeg').innerHTML=segs.map(s=>`<span><span class="dotc" style="background:${COL[s.k]}"></span>${NAME[s.k]} ${money(s.g)} (${tot.g?Math.round(s.g/tot.g*100):0}%)</span>`).join('')+(absent(r).length?`<span style="color:#bbb">absent: ${absent(r).map(k=>NAME[k]).join(', ')}</span>`:'');
 document.getElementById('leadQcom').innerHTML='<span class="tag">Across Q-Commerce</span> '+(r.lead||[]).map((b,i)=>`<span class="leadchip">${i+1}. <b>${b[0]}</b> ${money(b[1])}</span>`).join(' ');
 document.getElementById('leadPlat').innerHTML='<span class="tag">Platform #1</span> '+pr.map(k=>`<span class="leadchip"><span class="dotc" style="background:${COL[k]}"></span>${NAME[k]}: <b>${r[k].top||'–'}</b></span>`).join(' ');
 const strong=pr.reduce((a,k)=>r[k].g>r[a].g?k:a);
 document.getElementById('prodSpot').innerHTML=PK.map(([k])=>pcard(k,r[k],{bigKey:'g',bigLbl:'gross sales (MRP)',fmtBig:v=>money(v),badges:{[strong]:'<span class="badge bg-grn">biggest</span>'},
   rows:[['Net (SP)',x=>money(x.n)],['Discount',x=>disc(x.g,x.n)],['% of platform',x=>`${shareOf(k,x.g).toFixed(2)}%`],['SKUs',x=>x.k],['Brands',x=>x.b],['Avg SP',x=>'₹'+x.sp],['OSA',x=>`<b style="color:${x.o<40?'var(--red)':'var(--grn)'}">${x.o}%</b>`],['Top brand',x=>x.top||'–']]})).join('');
 renderTiers(r);
 // ⑥ opportunity cards (per platform)
 const RC={'Prime white space':'#34c759','Rented crown':'#0a84c2','Organic fortress':'#ff3b30','Crowded shelf':'#ff9500','Open & contested':'#86868b'};
 document.getElementById('oppSpot').innerHTML=PK.map(([k])=>{const o=(r.opp||{})[k];
   if(!o)return `<div class="pcard ${k} absent"><div class="pn">${NAME[k]}</div><div class="big" style="font-size:15px;color:#a99">— not tracked —</div></div>`;
   const c=RC[o.rem]||'#86868b';
   return `<div class="pcard ${k}"><div class="pn">${NAME[k]}</div><div class="big">${o.score}</div><div class="biglbl">opportunity score</div>
    <div class="row"><span class="k">Signal</span><span style="color:${c};font-weight:600">${o.rem}</span></div>
    <div class="row"><span class="k">White space</span><span>${o.ws}</span></div>
    <div class="row"><span class="k">Availability gap</span><span>${o.gap}%</span></div>
    <div class="row"><span class="k">Attack band</span><span>${o.band?('₹'+o.band[0]+'–'+o.band[1]):'–'}</span></div></div>`;}).join('');
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
 if(qstr)rs=rs.filter(r=>r.t.toLowerCase().includes(qstr));
 rs=rs.sort((a,b)=>brandSort.d*(tval(a,brandSort.k)-tval(b,brandSort.k)));
 rs=rs.slice(0,qstr?80:40);
 document.getElementById('brandNote2').textContent=qstr?`${rs.length} match`:`top 40 of ${BRANDS.length} brands`;
 const cols=[['Brand',''],['Gross','g'],['Net','n'],['Discount','disc'],['Units','u'],['Avg SP','sp'],['OSA','o'],['Product types','b']];
 document.getElementById('brandTbl').innerHTML=headRow(cols,brandSort)+'<tbody>'+
  rs.map(r=>`<tr data-t="${r.t}"><td>${r.t}</td><td><b>${money(r.tot.g)}</b></td><td>${money(r.tot.n)}</td><td>${disc(r.tot.g,r.tot.n)}</td><td>${unitsFmt(r.tot.u)}</td><td>₹${r.tot.sp}</td><td>${r.tot.o}%</td><td>${r.tot.b}</td></tr>`).join('')+'</tbody>';
 markSel('brandTbl',curBrand);
}
function renderBrand(t){
 const r=BMAP[t];if(!r)return;curBrand=t;markSel('brandTbl',t);
 const pr=pres(r),tot=r.tot;
 const bench=pr.reduce((a,k)=>shareOf(k,r[k].g)>shareOf(a,r[a].g)?k:a);
 const weak=pr.length>1?pr.reduce((a,k)=>shareOf(k,r[k].g)<shareOf(a,r[a].g)?k:a):null;
 const badges={[bench]:'<span class="badge bg-grn">strongest</span>'};if(weak&&weak!==bench)badges[weak]='<span class="badge bg-amb">weakest</span>';
 document.getElementById('bqtot').innerHTML=hero(`① ${r.t} · across Q-Commerce`,money(tot.g),'gross MRP',
   [['Net (SP)',money(tot.n)],['Discount',disc(tot.g,tot.n)],['SKUs',tot.k.toLocaleString()],['Product types',tot.b],['Avg SP','₹'+tot.sp],['Avg OSA',tot.o+'%'],['Platforms',r.p+'/3']]);
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
document.getElementById('typeTbl').addEventListener('click',e=>{
 const th=e.target.closest('th[data-k]');
 if(th){const k=th.dataset.k;if(typeSort.k===k)typeSort.d*=-1;else{typeSort.k=k;typeSort.d=-1;}fillTypeTbl(document.getElementById('typeSearch').value.toLowerCase().trim());return;}
 const tr=e.target.closest('tr[data-t]');if(tr){renderProduct(tr.dataset.t);document.getElementById('prodDetail').scrollIntoView({behavior:'smooth',block:'start'});}});
document.getElementById('brandTbl').addEventListener('click',e=>{
 const th=e.target.closest('th[data-k]');
 if(th){const k=th.dataset.k;if(brandSort.k===k)brandSort.d*=-1;else{brandSort.k=k;brandSort.d=-1;}fillBrandTbl(document.getElementById('brandSearch').value.toLowerCase().trim());return;}
 const tr=e.target.closest('tr[data-t]');if(tr){renderBrand(tr.dataset.t);document.getElementById('brandDetail').scrollIntoView({behavior:'smooth',block:'start'});}});

fillTypeTbl(''); fillBrandTbl('');
renderProduct(TYPES[0].t); renderBrand(BRANDS[0].t);
</script>
</div></body></html>
"""

out = HTML.replace("__DATA__", json.dumps(DATA, separators=(",", ":")))
open("compare.html", "w").write(out)
print(f"Wrote compare.html ({len(out)//1024} KB) — context banners + top-40 tables + Product/Brand ReportCards")
print(f"Q-Commerce: {DATA['qcom']['g']/1e7:.1f}Cr gross, {DATA['qcom']['n']/1e7:.1f}Cr net, {DATA['qcom']['brands']} brands, {DATA['qcom']['types']} types")
