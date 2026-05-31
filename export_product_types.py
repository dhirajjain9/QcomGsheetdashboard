"""Export a product-type-wise dataset matching the dashboard's Launchpad logic.

Scope = All categories. Sales = default per-sub-cat MRP (₹122.6 Cr total).
Weights = default 30/50/20. Replicates computeSales + lpTypeAgg + lpBands +
lpCompetitors from dashboard_template.html so numbers match the live dashboard.
"""
import json, math, csv

DATA = json.load(open("dashboard_data.json"))
SKU = DATA["sku_level"]
SUBCATS = DATA["subcats"]

DEFAULT_SALES = {  # ₹ Crore per sub-category (same as dashboard)
    "Kitchen & Dining Needs": 68.6, "Cleaning Tools": 17,
    "Bathroom Essentials": 16.6, "Home Decor": 14, "Home Improvement": 6.4,
}
W = {"d": 0.30, "o": 0.50, "a": 0.20}   # default opportunity weights

# ---- Sales model: entered MRP per sub-cat -> net(SP)/gross(MRP) per SKU ----
for s in SKU:
    s["_net"] = 0.0; s["_gross"] = 0.0
for sub in SUBCATS:
    T = DEFAULT_SALES.get(sub, 0) * 1e7  # Cr -> ₹
    if T <= 0:
        continue
    rows = [s for s in SKU if s["s"] == sub and (s.get("csp") or 0) > 0
            and (s.get("sp") or 0) > 0 and (s.get("mrp") or 0) > 0]
    shareSum = sum(s["csp"] for s in rows)
    if not shareSum:
        continue
    denom = sum((s["csp"]/shareSum)*(s["mrp"]/s["sp"]) for s in rows)
    if not denom:
        continue
    Tsp = T/denom
    for s in rows:
        f = s["csp"]/shareSum
        s["_net"] = f*Tsp
        s["_gross"] = (s["_net"]/s["sp"])*s["mrp"]

# ---- lpTypeAgg (scope = ALL) ----
rows = [s for s in SKU if s.get("pt") and s["pt"] != "Other"]
agg = {}
for s in rows:
    t = s["pt"]
    a = agg.setdefault(t, {"t": t, "skus": 0, "brands": {}, "csp": 0.0,
                           "gross": 0.0, "net": 0.0, "osaW": 0.0, "osaWN": 0.0,
                           "spSum": 0.0, "spN": 0})
    w = s.get("csp") or 0
    a["skus"] += 1; a["csp"] += w
    a["gross"] += s["_gross"]; a["net"] += s["_net"]
    bk = s["b"].lower()
    b = a["brands"].setdefault(bk, {"csp": 0.0, "osov": 0.0, "asov": 0.0, "disp": s["b"]})
    b["csp"] += w; b["osov"] += (s.get("osov") or 0); b["asov"] += (s.get("asov") or 0)
    if s.get("osa") is not None:
        ww = w or 1e-4; a["osaW"] += s["osa"]*ww; a["osaWN"] += ww
    if s.get("sp"):
        a["spSum"] += s["sp"]; a["spN"] += 1

arr = []
for a in agg.values():
    v = list(a["brands"].values())
    tot = sum(y["csp"] for y in v) or 1
    cr1 = max((y["csp"] for y in v), default=0)/tot
    moat = max([0]+[ (y["csp"]/tot)*(1-((y["asov"]/(y["asov"]+y["osov"])) if (y["asov"]+y["osov"])>0 else 0)) for y in v])
    wOSA = a["osaW"]/a["osaWN"] if a["osaWN"] else 0
    arr.append({
        "t": a["t"], "skus": a["skus"], "brands": len(a["brands"]),
        "gross": a["gross"], "net": a["net"],
        "cr1": cr1, "moat": moat, "beat": 1-moat,
        "wOSA": wOSA, "gap": max(0, 1-wOSA/100),
        "avgSP": a["spSum"]/a["spN"] if a["spN"] else 0,
        "leaderName": max(v, key=lambda y: y["csp"])["disp"] if v else "—",
        "sizeRaw": a["gross"],  # sales active -> gross
    })

arr = [x for x in arr if x["sizeRaw"] > 0]
maxSize = max((x["sizeRaw"] for x in arr), default=1e-9)
for x in arr:
    x["under"] = x["sizeRaw"]/max(1, x["skus"])
us = sorted(x["under"] for x in arr)
cap = us[int(0.9*(len(us)-1))] if us else 1e-9
for x in arr:
    x["demandN"] = x["sizeRaw"]/maxSize
    x["underN"] = min(1, x["under"]/cap)
    x["ws"] = math.sqrt(x["underN"]*x["beat"])
    gate = min(1, x["demandN"]/0.03)
    x["score"] = 100*(W["d"]*x["demandN"]+W["o"]*x["ws"]+W["a"]*x["gap"])*gate
    if x["moat"] >= 0.45:
        x["remark"] = "Organic fortress"
    elif x["cr1"] >= 0.45:
        x["remark"] = "Rented crown"
    elif x["ws"] >= 0.5:
        x["remark"] = "Prime white space"
    elif x["underN"] < 0.25:
        x["remark"] = "Crowded shelf"
    else:
        x["remark"] = "Open & contested"

arr.sort(key=lambda z: -z["score"])
totGross = sum(x["gross"] for x in arr) or 1

# ---- price band (lpBands/lpBestBand) + competitors per type ----
def best_band(type_rows):
    sps = [s["sp"] for s in type_rows if s.get("sp") and s["sp"] > 0]
    if not sps:
        return None
    mn, mx = min(sps), max(sps); n = 5; span = (mx-mn) or 1
    bands = [{"lo": mn+span*i/n, "hi": mn+span*(i+1)/n, "skus": 0, "val": 0.0} for i in range(n)]
    for s in type_rows:
        if not s.get("sp"):
            continue
        idx = min(n-1, int((s["sp"]-mn)/span*n))
        bands[idx]["skus"] += 1; bands[idx]["val"] += s["_gross"]
    best, bv = None, -1
    for b in bands:
        if b["val"] <= 0:
            continue
        v = b["val"]/(b["skus"] or 1)
        if v > bv:
            bv = v; best = b
    return best

def competitors(type_rows):
    m = {}
    for s in type_rows:
        k = s["b"].lower()
        c = m.setdefault(k, {"b": s["b"], "val": 0.0})
        c["val"] += s["_gross"]
    return sorted(m.values(), key=lambda c: -c["val"])

def money(v):
    if v >= 1e7:
        return f"₹{v/1e7:.2f} Cr"
    if v >= 1e5:
        return f"₹{v/1e5:.2f} L"
    if v >= 1e3:
        return f"₹{v/1e3:.1f}K"
    return f"₹{v:.0f}"

out = []
for x in arr:
    trows = [s for s in SKU if s.get("pt") == x["t"]]
    bb = best_band(trows)
    band = f"₹{bb['lo']:.0f}–{bb['hi']:.0f}" if bb else "–"
    comp = competitors(trows)
    c = [comp[i]["b"] if i < len(comp) else "" for i in range(3)]
    out.append({
        "Product Type": x["t"],
        "No of Brands": x["brands"],
        "No of SKUs": x["skus"],
        "Gross Sales": round(x["gross"]),
        "Net Sales": round(x["net"]),
        "Average SP": round(x["avgSP"]),
        "OSA %": round(x["wOSA"], 1),
        "% of Total": round(x["gross"]/totGross*100, 2),
        "Opportunity Score": round(x["score"]),
        "White Space Remark": x["remark"],
        "Price Band to Launch In": band,
        "Competing Brand 1": c[0],
        "Competing Brand 2": c[1],
        "Competing Brand 3": c[2],
    })

cols = list(out[0].keys())
with open("product_types_export.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader(); w.writerows(out)

print(f"{len(out)} product types written to product_types_export.csv")
print(f"Total gross across types: {money(totGross)}")
print("\nTop 12 by opportunity:")
print(f"{'Product Type':<32}{'Brnd':>5}{'SKU':>5}{'Gross':>12}{'Opp':>5}  Remark")
for r in out[:12]:
    print(f"{r['Product Type'][:31]:<32}{r['No of Brands']:>5}{r['No of SKUs']:>5}"
          f"{money(r['Gross Sales']):>12}{r['Opportunity Score']:>5}  {r['White Space Remark']}")
