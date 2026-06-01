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
            w = s["_g"] or 1e-6
            a["osaW"] += s["osa"]*w; a["osaWN"] += w   # gross-weighted (demand-weighted) OSA
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


# ---- BIS compliance (SKU-level: driven by material + electrical + named product) ----
# Product type is too coarse for BIS (a plastic dustbin is exempt, a steel one isn't),
# so we judge each SKU from its name, then roll up to unique rows / % BIS exposure.
# Utensils & kitchen tableware: SS / aluminium versions fall under the 2024 utensils QCO
# (IS 14756 / IS 1660). "Hand Blender / Mixer" here = manual SS whisks & hand-mixers.
UTENSIL_TYPES = {
    "Cookware / Pan", "Milk Pan / Tope", "Sauce Pan / Appe Pan", "Casserole", "Dinner Set / Plate",
    "Bowl", "Mug / Cup", "Drinking Glass", "Cutlery (Spoon/Fork)", "Ladle / Skimmer", "Tong / Pakad",
    "Spatula / Turner", "Colander / Strainer", "Serving Tray", "Jar / Canister", "Storage Container",
    "Idli / Steamer Maker", "Jug", "Spice Box", "Plate Stand / Rack", "Butter / Serving Dish",
    "Cake Stand", "Lunch Box / Tiffin", "Tea Infuser", "Rice / Food Server",
    "Hand Blender / Mixer",
}
# Types we cannot auto-clear: a standard may apply depending on exact build / use.
# Knives are forged cutlery, outside the IS 14756 sheet-utensils QCO → Conditional, not Mandatory.
REVIEW_TYPES = {"Pad Lock", "Water/Shower Filter", "Faucet / Tap", "Health Faucet",
                "Kitchen Scale", "TDS / Water Tester", "Gas Lighter", "Knife"}
REVIEW_STD = {"Pad Lock": "IS 729 — confirm QCO", "Water/Shower Filter": "verify (water purifier rules)",
              "Kitchen Scale": "Legal Metrology + verify", "Faucet / Tap": "verify (plumbing)",
              "Knife": "forged cutlery — outside IS 14756 sheet-utensils QCO; verify"}
# Sensor / automatic homeware (touchless dustbin, automatic soap/fragrance dispenser): the
# finished product isn't named in a QCO, but it's battery-electronic (EEE) — so any built-in
# Li-ion battery / charging adaptor falls under CRS, plus RoHS/E-waste. Flag Conditional, not
# Mandatory (no product-level mark) and not Exempt (the manual majority stays Exempt).
EEE_AUTO_TYPES = {"Dustbin", "Soap Dispenser", "Air Freshener / Fragrance"}
_SENSOR_TOK = ("sensor", "touchless", "automatic", "motion", "infrared", "auto-open", "auto open", "smart")
_EEE_NOTE = "EEE (sensor/auto) — verify battery & adaptor CRS (IS 16046 / IS 13252) + RoHS"
# Regulated metals (SS & aluminium — the utensils QCO). NOTE: cast iron / copper /
# brass are NOT in this QCO, so they live in _OTHER.
_SS_AL = ("stainless steel", "stainless", " steel", "steel ", "s.s", "ss ", "aluminium",
          "aluminum", "hard anodised", "hard anodized", "anodised", "anodized")
# Genuinely electrical appliances only (scan showed toaster=gas, juicer/kettle mostly
# manual, "induction" usually = induction-base cookware). Induction Cooktop handled by type.
# Strong tokens are always electric; bare "electric " is electric UNLESS it's a care phrase
# ("electric & gas oven safe", "induction base") that describes compatibility, not the product.
_ELEC_STRONG = ("mixer grinder", "food processor", " otg", "air fryer", "induction cooktop",
                "induction cook top", "induction stove", "microwave oven", "electric kettle",
                "electric chopper", "electric whisk", "electric beater", "electric hand blender",
                "hand mixer", "immersion blender", "rice cooker", "egg boiler", "sandwich maker",
                "electric grill", "electric tandoor", "electric cooker")
_ELEC_CARE = ("oven safe", "oven-safe", "& gas", "and gas", "gas safe", "gas & electric",
              "induction friendly", "induction base", "induction bottom", "induction compatible",
              "induction & gas")
# Insulated-bottle QCO (IS 17526) is for vacuum bottles/flasks only — not insulated
# lunch boxes / casseroles / vacuum storage bags (those fall to utensils QCO or stay exempt).
FLASK_TYPES = {"Thermal/Insulated Flask", "Water Bottle", "Shaker / Sipper", "Jug"}
# Non-regulated materials (everything that ISN'T SS/aluminium)
_OTHER = ("glass", "borosilicate", "opalware", "opal ware", "crystal", "ceramic", "bone china",
          "stoneware", "porcelain", "plastic", "polypropylene", "tritan", "copolymer", "acrylic",
          "pvc", "abs", "nylon", "polyester", "melamine", "silicone", "wood", "wooden", "mdf",
          "bamboo", "cane", "rattan", "copper", "brass", "bronze", "cast iron", "iron", "clay",
          "terracotta", "marble", "granite stone", "stone", "jute", "cotton", "fabric", "felt",
          "leather", "resin", "polyresin", "enamel", "paper", "foam", "rubber", "fiber", "fibre")


def sku_attrs(name, pt):
    """Lowest-common-identifier for BIS is the SKU: material × manual/electric, plus
    named-product QCO overrides (cooker, stove, flask)."""
    n = str(name).lower()
    elec = (pt == "Induction Cooktop" or any(w in n for w in _ELEC_STRONG)
            or ("electric " in n and not any(c in n for c in _ELEC_CARE)))
    op = "Electric" if elec else "Manual"
    if any(m in n for m in _SS_AL):
        mat = "Steel/Aluminium"
    elif any(m in n for m in _OTHER):
        mat = "Plastic/Non-metal"
    else:
        mat = "Unknown"
    insulated = any(w in n for w in ("insulated", "vacuum", "thermosteel", "thermos", "flask"))
    eee_auto = pt in EEE_AUTO_TYPES and any(w in n for w in _SENSOR_TOK)
    std = None
    if pt == "Pressure Cooker" or "pressure cooker" in n:
        std = "IS 2347"
    elif pt == "Gas Stove":
        std = "IS 4246"
    elif pt == "Thermal/Insulated Flask" or (pt in FLASK_TYPES and insulated):
        std = "IS 17526"
    elif elec:
        std = "IS 302 / CRS"
    elif mat == "Steel/Aluminium" and pt in UTENSIL_TYPES:
        std = "IS 14756 / IS 1660"
    if eee_auto:
        flag, std = "Conditional", _EEE_NOTE   # overrides a stray IS 302 / Exempt call
    elif std:
        flag = "Mandatory"
    elif (mat == "Unknown" and pt in UTENSIL_TYPES) or pt in REVIEW_TYPES:
        flag, std = "Conditional", (REVIEW_STD.get(pt) or "verify material")
    else:
        flag = "Exempt"
    return {"mat": mat, "op": op, "flag": flag, "std": std or "—"}


type_aggs, brand_aggs, totals, OPP = {}, {}, {}, {}
BRAND_DISP = {}
TYPE_BRAND = defaultdict(lambda: defaultdict(float))
BRAND_TYPES = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # bk -> pt -> platform -> gross
TYPE_SP = defaultdict(lambda: {"B": [], "I": [], "Z": []})
BIS_COMBOS = defaultdict(int)   # (product type, material, operation, flag, standard) -> #SKUs

for name, f, key in PLATS:
    d = json.load(open(f))
    sku = sales_per_sku(d)
    for s in sku:
        bk = s["b"].lower(); BRAND_DISP.setdefault(bk, s["b"])
        if s["pt"] != "Other":
            TYPE_BRAND[s["pt"]][bk] += s["_g"]
            BRAND_TYPES[bk][s["pt"]][key] += s["_g"]
            if s.get("sp") and s["sp"] > 0:
                TYPE_SP[s["pt"]][key].append((s["sp"], s["_g"]))
            at = sku_attrs(s["n"], s["pt"])
            BIS_COMBOS[(s["pt"], at["mat"], at["op"], at["flag"], at["std"])] += 1
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
                   "osa": round(sum(s["osa"]*(s["_g"] or 1e-6) for s in sku if s.get("osa") is not None)
                                / (sum((s["_g"] or 1e-6) for s in sku if s.get("osa") is not None) or 1), 1),
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


# (BIS compliance classifier is defined above, before the platform loop.)


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
                    ow = v["g"] or 1e-6
                    oW += v["o"]*ow; oWN += ow   # gross-weighted across platforms (demand-weighted)
                if v["sp"] > 0:
                    spS += v["sp"]*v["k"]; spN += v["k"]
            else:
                row[k] = None
        row["tot"] = {"g": tg, "n": tn, "k": tk, "u": tu, "b": len(union),
                      "sp": round(spS/spN) if spN else 0, "o": round(oW/oWN, 1) if oWN else 0}
        if with_extras:
            allg = sorted(TYPE_BRAND[kk].values(), reverse=True)
            row["c5"] = round(sum(allg[:5])/(sum(allg) or 1)*100)   # top-5 brand concentration
            lead = sorted(TYPE_BRAND[kk].items(), key=lambda x: -x[1])[:5]
            row["lead"] = [[BRAND_DISP.get(bk, bk), round(g)] for bk, g in lead]
            row["tiers"] = sp_tiers(kk)
            row["opp"] = {k: OPP[k].get(kk) for k in ("B", "I", "Z")}
        rows.append(row)
    rows.sort(key=lambda r: -r["tot"]["g"])
    return rows


type_rows = build_rows(type_aggs, use_disp=False, with_extras=True)
brand_rows = build_rows(brand_aggs, use_disp=True)
# brand -> top product types (combined across platforms) + each platform's #1 type
for row in brand_rows:
    bk = row["t"].lower()
    pts = BRAND_TYPES.get(bk, {})
    combined = sorted(((pt, sum(pv.values())) for pt, pv in pts.items()), key=lambda x: -x[1])
    row["topTypes"] = [[pt, round(g)] for pt, g in combined[:5]]
    plat_top = {}
    for k in ("B", "I", "Z"):
        best = max(((pt, pv.get(k, 0)) for pt, pv in pts.items()), key=lambda x: x[1], default=(None, 0))
        plat_top[k] = best[0] if best[1] > 0 else None
    row["platTop"] = plat_top
allb = set()
for k in ("B", "I", "Z"):
    allb |= set(brand_aggs[k])
tg = sum(totals[k]["g"] for k in ("B", "I", "Z"))
tn = sum(totals[k]["n"] for k in ("B", "I", "Z"))
tk = sum(totals[k]["k"] for k in ("B", "I", "Z"))
qcom = {"g": tg, "n": tn, "k": tk, "brands": len(allb), "types": len(type_rows),
        "osa": round(sum(totals[k]["osa"]*totals[k]["g"] for k in ("B", "I", "Z"))/(sum(totals[k]["g"] for k in ("B", "I", "Z")) or 1), 1),
        "sp": round(sum(totals[k]["sp"]*totals[k]["k"] for k in ("B", "I", "Z"))/(tk or 1))}
# exhaustive unique BIS rows — but collapse a dimension where it doesn't affect the flag:
# operation only shows for appliance-capable types; material only for utensils (3 buckets).
ELEC_TYPES = {pt for (pt, mat, op, flag, std) in BIS_COMBOS if op == "Electric"}


def _matbucket(pt, mat):
    if pt not in UTENSIL_TYPES:
        return "—"
    return "Steel/Aluminium" if mat == "Steel/Aluminium" else ("Unknown" if mat == "Unknown" else "Non-metal")


collapsed = defaultdict(int)
for (pt, mat, op, flag, std), cnt in BIS_COMBOS.items():
    dmat = _matbucket(pt, mat)
    dop = op if pt in ELEC_TYPES else "—"
    collapsed[(pt, dmat, dop, flag, std)] += cnt
_ford = {"Mandatory": 0, "Conditional": 1, "Exempt": 2}
bis_rows = [{"pt": pt, "mat": mat, "op": op, "flag": flag, "std": std, "n": cnt}
            for (pt, mat, op, flag, std), cnt in collapsed.items()]
bis_rows.sort(key=lambda r: (_ford[r["flag"]], -r["n"], r["pt"]))
bis_summary = {"Mandatory": [0, 0], "Conditional": [0, 0], "Exempt": [0, 0]}  # [#rows, #SKUs]
for r in bis_rows:
    bis_summary[r["flag"]][0] += 1; bis_summary[r["flag"]][1] += r["n"]
DATA = {"totals": totals, "qcom": qcom, "typeRows": type_rows, "brandRows": brand_rows,
        "bisRows": bis_rows, "bisSummary": bis_summary}

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
.qtot .mets{display:flex;flex-wrap:wrap;margin-top:18px;border-top:1px solid var(--hair);padding-top:15px}
.qtot .met{flex:1;min-width:92px;padding:0 18px;border-left:1px solid var(--hair)}
.qtot .met:first-child{padding-left:0;border-left:0}
.qtot .met .v{font-size:18px;font-weight:600;letter-spacing:-.01em}
.qtot .met .l{font-size:12px;color:var(--ink2);margin-top:3px}
.qtot.detail{border-radius:20px;padding:22px 26px;background:var(--panel);border:1.5px solid #c2c2cc;box-shadow:var(--sh)}
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
.seg{display:inline-flex;border:1px solid var(--hair2);border-radius:980px;overflow:hidden}
.seg button{border:0;background:var(--panel);color:var(--ink2);padding:8px 16px;font-size:13px;cursor:pointer;font-weight:500;border-right:1px solid var(--hair)}
.seg button:last-child{border-right:0}
.seg button.on{background:var(--ink);color:#fff;font-weight:600}
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
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:12.5px;color:var(--ink2)}
.dotc{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle}
/* ② platform-wise spread — aligned rows */
.spread{display:flex;flex-direction:column;gap:13px;margin-top:8px}
.spread .row{display:grid;grid-template-columns:84px 1fr 116px;align-items:center;gap:11px}
.spread .nm{display:flex;align-items:center;gap:8px;font-weight:600;font-size:13px}
.spread .track{height:10px;background:var(--hair);border-radius:6px;overflow:hidden}
.spread .track i{display:block;height:100%;border-radius:6px;min-width:3px;transition:width .3s ease}
.spread .val{text-align:right;font-variant-numeric:tabular-nums;font-size:13px}
.spread .val b{font-weight:700}
.spread .val .pct{display:inline-block;min-width:38px;color:var(--ink3);font-weight:600}
.spread .absent{font-size:12px;color:var(--ink3);margin-top:3px;padding-left:95px}
/* ③ who leads — ranked list + platform leader tiles */
.blbl{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink3);font-weight:600;margin:0 0 11px}
.blbl.mt{margin-top:18px}
.brank{display:flex;flex-direction:column;gap:12px}
.brank .r{display:grid;grid-template-columns:22px 1fr auto;align-items:center;gap:13px}
.brank .rk{width:21px;height:21px;border-radius:50%;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;background:#eef0f3;color:var(--ink2)}
.brank .r:first-child .rk{background:var(--ink);color:#fff}
.brank .nb .bn{font-weight:600;font-size:13px;margin-bottom:5px}
.brank .nb .mini{height:6px;background:var(--hair);border-radius:4px;overflow:hidden}
.brank .nb .mini i{display:block;height:100%;border-radius:4px;background:linear-gradient(90deg,var(--acc),#5aa9ff)}
.brank .bv{text-align:right;font-variant-numeric:tabular-nums;font-size:13px;font-weight:700;line-height:1.25}
.brank .bv .bvp{display:block;font-size:11px;font-weight:600;color:var(--ink3)}
.leadfoot{margin-top:15px;padding-top:13px;border-top:1px solid var(--hair);font-size:12.5px;color:var(--ink2);line-height:1.5}
.leadfoot b{color:var(--ink);font-weight:700}
.c5cell{text-decoration:underline;text-decoration-style:dotted;text-decoration-color:var(--hair2);text-underline-offset:3px}
tbody tr:hover .c5cell{text-decoration-color:var(--acc);color:var(--acc)}
.plead{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.plead .pl{border:1px solid var(--hair);border-top:3px solid var(--pc,#ccc);border-radius:12px;padding:11px 13px;background:#fbfbfd}
.plead .pl .h{font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--ink3);font-weight:600;margin-bottom:5px;display:flex;align-items:center;gap:6px}
.plead .pl .v{font-weight:600;font-size:13.5px;text-transform:capitalize;line-height:1.3}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:stretch}
.gcol{display:flex;flex-direction:column;gap:14px}
.pl-card{flex:1;display:flex;flex-direction:column}
.pl-card .plead.v{flex:1;grid-template-columns:1fr;grid-auto-rows:1fr}
.plead.v .pl{border-top:0;border-left:3px solid var(--pc,#ccc);display:flex;flex-direction:column;justify-content:center}
#leadCard{display:flex;flex-direction:column}
#leadCard .brank{flex:1;justify-content:space-between;gap:16px}
#leadCard .leadfoot{margin-top:16px}
table{border-collapse:collapse;width:100%;font-size:13px;table-layout:fixed}
thead th{position:sticky;top:0;background:rgba(255,255,255,.85);backdrop-filter:blur(8px);z-index:2;text-align:center;padding:11px 10px;border-bottom:1px solid var(--hair2);white-space:nowrap;cursor:pointer;font-weight:600;color:var(--ink2);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
thead th:first-child,tbody td:first-child{text-align:left;width:23%;padding-left:16px}
tbody td{padding:12px 10px;text-align:center;border-bottom:1px solid var(--hair);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
tbody tr{cursor:pointer}tbody tr:hover{background:#f5f5f7}tbody tr.sel{background:rgba(0,113,227,.07)}
.tableScroll{max-height:360px;overflow:auto;border-radius:12px;border:1px solid var(--hair)}
.tiers{margin-top:10px;border-top:1px solid var(--hair);padding-top:10px}
.trow{display:flex;align-items:center;gap:9px;font-size:11.5px;margin-top:7px}
.trow .tl{width:88px;color:var(--ink2);white-space:nowrap;text-align:left;font-variant-numeric:tabular-nums}
.trow .tbar{flex:1;height:8px;background:var(--hair);border-radius:5px;overflow:hidden}
.trow .tbar i{display:block;height:100%;border-radius:5px}
.trow .tp{width:34px;text-align:right;color:var(--ink2);font-variant-numeric:tabular-nums}
.trow.peak .tl,.trow.peak .tp{font-weight:700;color:var(--ink)}
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
  <div class="gcol">
   <div class="card"><div class="step">② Platform-wise spread</div><h3>Where the demand sits</h3><div class="h3sub">Share of this product's total Q-Commerce gross by platform.</div><div class="spread" id="spreadBar"></div></div>
   <div class="card pl-card"><div class="blbl" style="margin-bottom:13px">Platform leaders · brand #1</div><div class="plead v" id="leadPlat"></div></div>
  </div>
  <div class="card" id="leadCard"><div class="step">③ Who leads</div><h3>Top 5 brands</h3><div class="h3sub">Biggest brands across Q-Commerce by gross, with each one's share of this category.</div><div class="brank" id="leadQcom"></div><div class="leadfoot" id="leadFoot"></div></div>
 </div>
 <div class="card"><div class="step">④ All attributes across platforms</div><h3>Platform scorecard</h3><div class="h3sub">Gross, net, discount, share, assortment, price & availability.</div><div class="spot" id="prodSpot"></div></div>
 <div class="card"><div class="step">⑤ SP distribution across value tiers</div><h3>Pricing — one strategy or platform-by-platform?</h3><div class="h3sub">Each platform's <b>own</b> price-tier mix on the <b>same shared ₹ tiers</b> — read independently (the gross on each card shows its true size, so a small platform never looks like it "leads"). Bar = % of that platform's gross.</div><div class="spot" id="tierCards"></div></div>
 <div class="card"><div class="step">⑥ Opportunity to launch</div><h3>Where the opening is — per platform</h3><div class="h3sub">Founder's Launchpad scoring computed within each platform: opportunity score (0–100), white-space signal, availability gap & the attack price band.</div><div class="spot" id="oppSpot"></div></div>
 <div class="card"><div class="step">⑦ Cross-platform opportunity</div><h3>Penetration vs fair share — where a platform is under-developed</h3>
  <div class="h3sub">Each platform's share of <i>this product</i> benchmarked to its <b>fair share</b> (its overall share of Q-Commerce gross). Far below fair share ⇒ the product is under-developed there ⇒ untapped ₹ for that platform.</div>
  <div id="fairHead"></div><div class="spot" id="fairCards"></div></div>
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
 <div class="card"><div class="step">③ Who leads — where the brand sells</div><h3>Top product types across Q-Commerce</h3><div class="h3sub">The brand's biggest product types, combined across all three platforms, with each one's share of the brand.</div><div class="brank" id="brandTypes"></div><div style="margin-top:16px"><div class="step" style="margin-bottom:9px">Platform leaders · top type</div><div class="plead" id="brandPlatTop"></div></div></div>
 <div class="card"><div class="step">④ Why it isn't scaling — gap diagnosis</div><h3>What's holding it back, platform by platform</h3><div class="h3sub">Benchmarked to the brand's strongest platform. Root cause = distribution, assortment (SKUs), availability (OSA), visibility (SOV) or competition.</div><div id="brandDiag"></div></div>
</div>

<!-- ===== BIS COMPLIANCE ===== -->
<div class="sec">BIS Compliance</div>
<div class="card">
 <div class="h3sub">BIS applicability is decided at the <b>SKU level</b> — by <b>material</b> (stainless-steel/aluminium vs plastic/glass/ceramic) and <b>manual vs electric</b>, plus a few named products (pressure cooker, gas stove, insulated flask). Below is the exhaustive list of unique <b>Product type × Material × Operation</b> rows with a confident flag. <b>Mandatory</b> = certification required to sell · <b>Conditional</b> = depends on the actual material/spec, verify · <b>Exempt</b> = no current BIS mandate.</div>
 <div id="bisSummary" class="platrow" style="grid-template-columns:repeat(3,1fr)"></div>
 <div class="controls" style="margin-top:14px">
  <div class="seg" id="bisFilter">
   <button data-f="all" class="on">All</button><button data-f="Mandatory">Mandatory</button><button data-f="Conditional">Conditional</button><button data-f="Exempt">Exempt</button>
  </div>
  <input class="search" id="bisSearch" placeholder="search product type / standard…"><span class="tag" id="bisNote"></span>
 </div>
 <div class="tableScroll" style="max-height:520px"><table id="bisTbl"></table></div>
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
// biggest under-indexed platform for a product type (share of product vs fair share), with untapped ₹
function fairGap(r){const tot=r.tot.g||1;let best=null;for(const k of['B','I','Z']){const fair=DATA.qcom.g?DATA.totals[k].g/DATA.qcom.g:0;const g=r[k]?r[k].g:0;const idx=fair?(g/tot)/fair:0;const up=fair*tot-g;if(idx<0.7&&up>2e5&&(!best||up>best.up))best={k,up,idx};}return best;}
TYPES.forEach(r=>r._gap=fairGap(r));
const shareOf=(k,g)=>DATA.totals[k].g?(g/DATA.totals[k].g*100):0;

// ===== CONTEXT BANNERS =====
const q=DATA.qcom;
// hero builder: eyebrow + big figure + caption + a row of value/label metrics
function hero(lead,big,cap,mets){
 return `<div class="lead">${lead}</div><span class="big">${big}</span><span class="cap">${cap}</span>
  <div class="mets">${mets.map(m=>`<div class="met"><div class="v">${m[1]}</div><div class="l">${m[0]}</div></div>`).join('')}</div>`;
}
document.getElementById('qcomBanner').innerHTML=hero('Q-Commerce · all platforms',money(q.g),'gross MRP',
 [['Net (SP)',money(q.n)],['Discount',disc(q.g,q.n)],['Brands',q.brands.toLocaleString()],['Product types',q.types],['Wt. OSA%',q.osa+'%'],['Avg SP','₹'+q.sp]]);
document.getElementById('platBanners').innerHTML=PK.map(([k,n])=>{const t=DATA.totals[k];
 const cells=[['Net (SP)',money(t.n)],['Discount',disc(t.g,t.n)],['Brands',t.brands],['Prod Type',t.types],['Wt. OSA%',t.osa+'%'],['Avg SP','₹'+t.sp]];
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
 const cols=[['Product Type',''],['Gross','g'],['Net','n'],['Discount','disc'],['Units','u'],['Avg SP','sp'],['Wt. OSA%','o'],['Brands','b'],['Top-5','c5']];
 document.getElementById('typeTbl').innerHTML=headRow(cols,typeSort)+'<tbody>'+
  rs.map(r=>`<tr data-t="${r.t}"><td>${r.t}</td><td><b>${money(r.tot.g)}</b></td><td>${money(r.tot.n)}</td><td>${disc(r.tot.g,r.tot.n)}</td><td>${unitsFmt(r.tot.u)}</td><td>₹${r.tot.sp}</td><td>${r.tot.o}%</td><td>${r.tot.b}</td><td class="c5cell" title="see the top 5 brands">${r.c5}%</td></tr>`).join('')+'</tbody>';
 markSel('typeTbl',curType);
}
let curType,curBrand,tierChart;
function renderProduct(t){
 const r=TMAP[t];if(!r)return;curType=t;markSel('typeTbl',t);
 const pr=pres(r),tot=r.tot;
 document.getElementById('qtot').innerHTML=hero(`① ${r.t} · total size on Q-Commerce`,money(tot.g),'gross MRP',
   [['Net (SP)',money(tot.n)],['Discount',disc(tot.g,tot.n)],['SKUs',tot.k.toLocaleString()],['Brands',tot.b],['Avg SP','₹'+tot.sp],['Wt. OSA%',tot.o+'%']]);
 const segs=pr.map(k=>({k,g:r[k].g})).sort((a,b)=>b.g-a.g);
 document.getElementById('spreadBar').innerHTML=segs.map(s=>{const pct=tot.g?s.g/tot.g*100:0;return `<div class="row"><div class="nm"><span class="dotc" style="background:${COL[s.k]}"></span>${NAME[s.k]}</div><div class="track"><i style="width:${pct}%;background:${COL[s.k]}"></i></div><div class="val"><b>${money(s.g)}</b> <span class="pct">${pct<1?pct.toFixed(1):Math.round(pct)}%</span></div></div>`;}).join('')+(absent(r).length?`<div class="absent">Absent on ${absent(r).map(k=>NAME[k]).join(', ')}</div>`:'');
 const lead=r.lead||[],lmax=lead[0]?lead[0][1]:1;
 document.getElementById('leadQcom').innerHTML=lead.map((b,i)=>{const pct=tot.g?b[1]/tot.g*100:0;return `<div class="r"><span class="rk">${i+1}</span><div class="nb"><div class="bn">${b[0]}</div><div class="mini"><i style="width:${Math.max(4,b[1]/lmax*100)}%"></i></div></div><div class="bv">${money(b[1])}<span class="bvp">${pct.toFixed(1)}%</span></div></div>`;}).join('');
 document.getElementById('leadFoot').innerHTML=`Top 5 = <b>${r.c5}%</b> of this category's Q-Commerce gross — the same <b>Top-5</b> figure in the table above.`;
 document.getElementById('leadPlat').innerHTML=PK.map(([k])=>`<div class="pl" style="--pc:${COL[k]}"><div class="h"><span class="dotc" style="background:${COL[k]}"></span>${NAME[k]}</div><div class="v">${r[k]?(r[k].top||'–'):'<span class="miss">absent</span>'}</div></div>`).join('');
 const strong=pr.reduce((a,k)=>r[k].g>r[a].g?k:a);
 document.getElementById('prodSpot').innerHTML=PK.map(([k])=>pcard(k,r[k],{bigKey:'g',bigLbl:'gross sales (MRP)',fmtBig:v=>money(v),badges:{[strong]:'<span class="badge bg-grn">biggest</span>'},
   rows:[['Net (SP)',x=>money(x.n)],['Discount',x=>disc(x.g,x.n)],['% of platform',x=>`${shareOf(k,x.g).toFixed(2)}%`],['SKUs',x=>x.k],['Brands',x=>x.b],['Avg SP',x=>'₹'+x.sp],['Wt. OSA%',x=>`<b style="color:${x.o<40?'var(--red)':'var(--grn)'}">${x.o}%</b>`],['Top brand',x=>x.top||'–']]})).join('');
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
 renderFair(r);
}
// ⑦ penetration vs fair share (a platform's share of this product vs its overall Q-Commerce share)
function renderFair(r){
 const tot=r.tot.g||1;
 const data=PK.map(([k,n])=>{const fair=DATA.qcom.g?DATA.totals[k].g/DATA.qcom.g:0; const g=r[k]?r[k].g:0;
   return {k,n,fair,actual:g/tot,idx:fair?(g/tot)/fair:0,upside:fair*tot-g,present:!!r[k]};});
 document.getElementById('fairCards').innerHTML=data.map(d=>{
   const col=!d.present?'#ff3b30':d.idx>=1.25?'#34c759':d.idx>=0.8?'#86868b':d.idx>=0.6?'#ff9500':'#ff3b30';
   const verdict=!d.present?'Not listed':d.idx>=1.25?'Over-developed':d.idx>=0.8?'On par':d.idx>=0.6?'Slightly under':'Under-indexed';
   const up=(d.upside>2e5&&d.idx<1)?`<div class="row"><span class="k">To fair share</span><span style="color:${col};font-weight:600">+${money(d.upside)}</span></div>`:'';
   return `<div class="pcard ${d.k}"><div class="pn">${d.n}</div><div class="big" style="color:${col}">${d.present?d.idx.toFixed(2)+'×':'—'}</div><div class="biglbl">actual ÷ fair share</div>
     <div class="row"><span class="k">Actual share</span><span>${(d.actual*100).toFixed(1)}%</span></div>
     <div class="row"><span class="k">Fair share</span><span>${(d.fair*100).toFixed(1)}%</span></div>
     <div class="row"><span class="k">Verdict</span><span style="color:${col};font-weight:600">${verdict}</span></div>${up}</div>`;}).join('');
 const opp=data.filter(d=>d.idx<0.7&&d.upside>2e5).sort((a,b)=>b.upside-a.upside)[0];
 const el=document.getElementById('fairHead');
 if(opp){el.className='insight';el.style.marginBottom='14px';
   el.innerHTML=`💡 <b>Biggest cross-platform opportunity:</b> <b>${opp.n}</b> is under-developed here — only <b>${(opp.actual*100).toFixed(1)}%</b> of this product${opp.present?'':' (not even listed)'} vs a <b>${(opp.fair*100).toFixed(0)}%</b> fair share → about <b>${money(opp.upside)}</b> to capture at parity. <span style="color:var(--ink3);font-weight:400">May also reflect the category being thinly listed there — worth a look.</span>`;}
 else{el.className='insight';el.style.marginBottom='14px';el.innerHTML=`✓ No platform is materially under-developed on this product — every platform is at or above its fair share.`;}
}
function renderTiers(r){
 const T=r.tiers,host=document.getElementById('tierCards');
 if(!T){host.innerHTML='<div class="h3sub">Not enough price points across platforms to tier this product.</div>';return;}
 const lab=i=>`₹${T.edges[i]}–${T.edges[i+1]}`, pr=pres(r);
 const topT={};pr.forEach(k=>{const a=T.g[k];let mi=0;a.forEach((x,i)=>{if(x>a[mi])mi=i;});topT[k]=mi;});
 // one card per platform: its own SP-tier mix on the same shared tiers, with its real gross shown
 host.innerHTML=PK.map(([k,n])=>{
   if(!r[k])return `<div class="pcard ${k} absent"><div class="pn">${n}</div><div class="big" style="font-size:15px;color:#a99">— not tracked —</div></div>`;
   const arr=T.g[k], tot=arr.reduce((a,b)=>a+b,0)||1;
   const rows=arr.map((x,i)=>{const pct=Math.round(x/tot*100);
     return `<div class="trow${i===topT[k]?' peak':''}"><span class="tl">${lab(i)}</span><span class="tbar"><i style="width:${pct}%;background:${COL[k]}"></i></span><span class="tp">${pct}%</span></div>`;}).join('');
   return `<div class="pcard ${k}"><div class="pn">${n}</div><div class="big">${money(r[k].g)}</div><div class="biglbl">gross · price-tier mix ↓</div><div class="tiers">${rows}</div></div>`;}).join('');
}

// ===== BRAND TABLE + DETAIL =====
function fillBrandTbl(qstr){
 let rs=BRANDS.filter(r=>r.p>=1);
 if(qstr)rs=rs.filter(r=>r.t.toLowerCase().includes(qstr));
 rs=rs.sort((a,b)=>brandSort.d*(tval(a,brandSort.k)-tval(b,brandSort.k)));
 rs=rs.slice(0,qstr?80:40);
 document.getElementById('brandNote2').textContent=qstr?`${rs.length} match`:`top 40 of ${BRANDS.length} brands`;
 const cols=[['Brand',''],['Gross','g'],['Net','n'],['Discount','disc'],['Units','u'],['Avg SP','sp'],['Wt. OSA%','o'],['Product types','b']];
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
   [['Net (SP)',money(tot.n)],['Discount',disc(tot.g,tot.n)],['SKUs',tot.k.toLocaleString()],['Product types',tot.b],['Avg SP','₹'+tot.sp],['Wt. OSA%',tot.o+'%']]);
 document.getElementById('brandSpot').innerHTML=PK.map(([k])=>pcard(k,r[k],{bigKey:'g',bigLbl:'gross sales (MRP)',fmtBig:v=>money(v),badges,
   rows:[['Net (SP)',x=>money(x.n)],['Discount',x=>disc(x.g,x.n)],['% of platform',x=>`<b>${shareOf(k,x.g).toFixed(2)}%</b>`],['SKUs',x=>x.k],['Product types',x=>x.b],['Avg SP',x=>'₹'+x.sp],['Wt. OSA%',x=>`${x.o}%`],['SOV (visibility)',x=>`${x.sov}%`],['Top type',x=>x.top||'–']]})).join('');
 const tt=r.topTypes||[],tmx=tt[0]?tt[0][1]:1;
 document.getElementById('brandTypes').innerHTML=tt.length?tt.map((b,i)=>`<div class="r"><span class="rk">${i+1}</span><div class="nb"><div class="bn">${b[0]}</div><div class="mini"><i style="width:${Math.max(4,b[1]/tmx*100)}%"></i></div></div><div class="bv">${money(b[1])}<span class="bvp">${tot.g?(b[1]/tot.g*100).toFixed(1):0}%</span></div></div>`).join(''):'<span class="miss">No classified product types.</span>';
 document.getElementById('brandPlatTop').innerHTML=PK.map(([k])=>`<div class="pl" style="--pc:${COL[k]}"><div class="h"><span class="dotc" style="background:${COL[k]}"></span>${NAME[k]} · top type</div><div class="v">${r.platTop&&r.platTop[k]?r.platTop[k]:'<span class="miss">absent</span>'}</div></div>`).join('');
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
 const tr=e.target.closest('tr[data-t]');if(tr){const jumpLead=!!e.target.closest('.c5cell');renderProduct(tr.dataset.t);document.getElementById(jumpLead?'leadCard':'prodDetail').scrollIntoView({behavior:'smooth',block:jumpLead?'center':'start'});}});
document.getElementById('brandTbl').addEventListener('click',e=>{
 const th=e.target.closest('th[data-k]');
 if(th){const k=th.dataset.k;if(brandSort.k===k)brandSort.d*=-1;else{brandSort.k=k;brandSort.d=-1;}fillBrandTbl(document.getElementById('brandSearch').value.toLowerCase().trim());return;}
 const tr=e.target.closest('tr[data-t]');if(tr){renderBrand(tr.dataset.t);document.getElementById('brandDetail').scrollIntoView({behavior:'smooth',block:'start'});}});

// ===== BIS COMPLIANCE =====
const BIS=DATA.bisRows,BSUM=DATA.bisSummary;
const FLAGMETA={Mandatory:{c:'var(--red)',d:'Certification needed to sell'},Conditional:{c:'var(--amb)',d:'Depends on material / spec — verify'},Exempt:{c:'var(--grn)',d:'No current BIS mandate'}};
const flagBadge=f=>`<span class="badge" style="background:${FLAGMETA[f].c};color:#fff">${f}</span>`;
let bisF='all';
function renderBisSummary(){
 const order=['Mandatory','Conditional','Exempt'];
 const totSku=order.reduce((a,f)=>a+(BSUM[f]?BSUM[f][1]:0),0)||1;
 document.getElementById('bisSummary').innerHTML=order.map(f=>{
  const [rows,sk]=BSUM[f]||[0,0];const m=FLAGMETA[f];
  return `<div class="qtot detail" style="cursor:pointer" data-bf="${f}">
   <div class="met" style="border-left:3px solid ${m.c};padding-left:12px">
    <div class="l" style="color:${m.c};font-weight:600">${f}</div>
    <div class="v" style="font-size:30px">${sk.toLocaleString()}<span style="font-size:14px;color:var(--ink3)"> SKUs</span></div>
    <div class="l">${rows} unique rows · ${Math.round(sk/totSku*100)}% of classified SKUs</div>
    <div class="l" style="margin-top:4px;color:var(--ink2)">${m.d}</div>
   </div></div>`;
 }).join('');
}
function fillBisTbl(qstr){
 let rs=BIS.slice();
 if(bisF!=='all')rs=rs.filter(r=>r.flag===bisF);
 if(qstr)rs=rs.filter(r=>(r.pt+' '+r.mat+' '+r.std+' '+r.op).toLowerCase().includes(qstr));
 const tot=rs.reduce((a,r)=>a+r.n,0);
 document.getElementById('bisNote').textContent=`${rs.length} rows · ${tot.toLocaleString()} SKUs`;
 const head='<thead><tr><th>Product Type</th><th>Material</th><th>Operation</th><th>BIS</th><th>IS Standard / Note</th><th style="text-align:right">SKUs</th></tr></thead>';
 document.getElementById('bisTbl').innerHTML=head+'<tbody>'+
  rs.map(r=>`<tr><td><b>${r.pt}</b></td><td>${r.mat==='—'?'<span class="miss">any</span>':r.mat}</td><td>${r.op==='—'?'<span class="miss">–</span>':r.op}</td><td>${flagBadge(r.flag)}</td><td>${r.std==='—'?'<span class="miss">–</span>':r.std}</td><td style="text-align:right">${r.n.toLocaleString()}</td></tr>`).join('')+'</tbody>';
}
document.getElementById('bisFilter').addEventListener('click',e=>{
 const b=e.target.closest('button[data-f]');if(!b)return;
 bisF=b.dataset.f;document.querySelectorAll('#bisFilter button').forEach(x=>x.classList.toggle('on',x===b));
 fillBisTbl(document.getElementById('bisSearch').value.toLowerCase().trim());
});
document.getElementById('bisSearch').addEventListener('input',e=>fillBisTbl(e.target.value.toLowerCase().trim()));
document.getElementById('bisSummary').addEventListener('click',e=>{
 const c=e.target.closest('[data-bf]');if(!c)return;
 bisF=c.dataset.bf;
 document.querySelectorAll('#bisFilter button').forEach(x=>x.classList.toggle('on',x.dataset.f===bisF));
 document.getElementById('bisSearch').value='';fillBisTbl('');
 document.getElementById('bisTbl').scrollIntoView({behavior:'smooth',block:'nearest'});
});

fillTypeTbl(''); fillBrandTbl('');
renderProduct(TYPES[0].t); renderBrand(BRANDS[0].t);
renderBisSummary(); fillBisTbl('');
</script>
</div></body></html>
"""

out = HTML.replace("__DATA__", json.dumps(DATA, separators=(",", ":")))
open("compare.html", "w").write(out)
print(f"Wrote compare.html ({len(out)//1024} KB) — context banners + top-40 tables + Product/Brand ReportCards")
print(f"Q-Commerce: {DATA['qcom']['g']/1e7:.1f}Cr gross, {DATA['qcom']['n']/1e7:.1f}Cr net, {DATA['qcom']['brands']} brands, {DATA['qcom']['types']} types")
