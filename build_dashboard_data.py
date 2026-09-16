import os, pandas as pd, json, numpy as np
from collections import defaultdict
from product_types import classify
from super_cats import super_of, SUPER_ORDER

# Platform-aware: PLATFORM=instamart/zepto reads <platform>_rca_combined.xlsx and
# writes <platform>_dashboard_data.json. Default 'blinkit' keeps the original
# blinkit_rca_combined.xlsx -> dashboard_data.json so nothing changes for Blinkit.
PLATFORM = os.environ.get('PLATFORM', 'blinkit').lower()
PLATFORM_LABEL = {'blinkit': 'Blinkit', 'instamart': 'Instamart', 'zepto': 'Zepto'}.get(PLATFORM, PLATFORM.title())
# Per-platform pre-filled MRP sales (₹ Cr). Blinkit = the agreed split; others
# start empty (dashboard shows value-share % until the user enters totals).
DEFAULT_SALES = {
    'blinkit': {'Appliances': 170.5, 'Kitchen & Dining Needs': 86.7, 'Home Furnishing': 80.3, 'Tissues & Disposables': 56.8, 'Decorative Lights': 54.8, 'Bags': 43.7, 'Sports & Fitness': 37.6, 'Pooja Needs': 34.3, 'Bathroom Essentials': 25.0, 'Clothing, Footwear & Accessories': 24.6, 'Flowers, Plants & Gardening': 24.1, 'Cleaning Tools': 22.6, 'Stationery Needs': 18.0, 'Festive & Occasion Needs': 15.4, 'Home Decor': 15.0, 'Party Essentials': 9.7, 'Garbage Bags': 9.7, 'Home Improvement': 9.5, 'Festive Gifting': 5.8},
    'instamart': {'Powerbanks Chargers Cables': 24.0, 'Home Decor': 20.4, 'Home Furnishing': 19.8, 'Sports & Gym': 18.0, 'Kitchen Appliances': 16.7, 'Cleaning Tools': 14.4, 'Bottles Flasks Tiffins': 13.3, 'Tissues & Disposables': 12.5, 'Bathware & Laundry': 12.4, 'Storage & Organizers': 10.5, 'Pooja Needs': 10.0, 'Personal Care Appliances': 9.4, 'Cookware': 9.3, 'Utility & Tools': 9.0, 'Jars Containers Holders': 8.9, 'Home Appliances': 8.0, 'Glasses Cups Mugs': 6.8, 'Kitchen Tools': 6.4, 'Plates Bowls Crockery': 6.1, 'Travel And Luggage': 4.0, 'Kitchen Cleaning': 3.8, 'Lights & Bulbs': 2.7, 'Bakeware & Bbq': 1.8, 'Linen And Furnishing': 1.5, 'Barware': 1.2, 'Gardening': 1.2, 'Serveware': 1.1, 'Cutlery & Ladles': 0.312},
    'zepto': {'Home Furnishing': 35.2, 'Pooja & Worship Needs': 29.3, 'Kitchen Appliances': 26.4, 'Household Utility': 26.0, 'Bulbs & Lights': 23.8, 'Cleaning Aids': 23.3, 'Home Appliances': 19.0, 'Tissues & Disposables': 17.1, 'Home Decor': 10.5, 'Kitchen Tools': 8.6, 'Kitchen Storage': 8.3, 'Cookware': 7.7, 'Extensions & Switches': 5.4, 'Drinkware & Bar': 4.3, 'Lunch Boxes': 4.2, 'Bath & Laundry': 3.9, 'Kitchen Aids': 3.9, 'Gas Stove & Accessories': 3.0, 'Gardening': 2.7, 'Stationery & Crafts': 2.6, 'Pressure Cooker': 2.6, 'Steel Utensils': 2.3, 'Hardware & Fittings': 1.8, 'Tableware': 1.5, 'Kitchen Cleaning': 0.764},
}.get(PLATFORM, {})
SALES_KEY = f'{PLATFORM}_mrp_sales_v3'   # bumped v2->v3: Jul-Aug data / Aug MRP totals, reset saved inputs
IN_XLSX = f'{PLATFORM}_rca_combined.xlsx'
OUT_JSON = 'dashboard_data.json' if PLATFORM == 'blinkit' else f'{PLATFORM}_dashboard_data.json'

df = pd.read_excel(IN_XLSX)
num = ['SP','MRP','Wt. OSA %','Wt. Discount %','Est. Category Share',
       'Est. Category Share SP','Overall SOV','Organic SOV','Ad SOV','Wt. PPU (x100)']
for c in num:
    df[c] = pd.to_numeric(df[c], errors='coerce')
df['Date'] = df['Date'].astype(str)
df['Brand'] = df['Brand'].astype(str).str.strip()
# normalise brand casing (e.g. 'indianshelf' vs 'IndianShelf')
df['BrandKey'] = df['Brand'].str.lower()
brand_disp = df.groupby('BrandKey')['Brand'].agg(lambda s: s.mode().iloc[0])

# Original platform category preserved in 'Category'; grouping dimension = Super Category.
df['Category'] = df['Category'].astype(str).str.strip()
df['Sub Category'] = df['Category'].map(super_of)   # <-- all grouping/scope now = Super Category

DATES = sorted(df['Date'].unique())
LATEST, PREV = DATES[-1], DATES[0]
SUBCATS = [s for s in SUPER_ORDER if s in set(df['Sub Category'])]
cur = df[df['Date'] == LATEST].copy()
prv = df[df['Date'] == PREV].copy()

# Super-category MRP totals (₹ Cr) = sum of member original-category totals (for the panel).
SUPER_SALES = defaultdict(float)
for _cat, _t in DEFAULT_SALES.items():
    SUPER_SALES[super_of(_cat)] += (_t or 0)
SUPER_SALES = {s: round(v, 3) for s, v in SUPER_SALES.items()}

def r(x, n=2):
    return None if pd.isna(x) else round(float(x), n)

# Per-SKU sales model runs at the ORIGINAL-category level (Est. Category Share SP sums to
# 100 within each original category, so distributing a merged super-category total by raw
# share would wrongly weight every category equally). We bake exact per-SKU net/gross/units
# here; the dashboards group by Super Category but read these baked ₹ values. _w = gross is
# the demand weight for Wt. OSA% averages.
def _bake(frame):
    frame = frame.copy()
    for col in ('_net', '_gross', '_units', '_w'):
        frame[col] = 0.0
    for catname, T in DEFAULT_SALES.items():
        if not T or T <= 0:
            continue
        sub = frame[(frame['Category'] == catname) & (frame['Est. Category Share SP'] > 0)
                    & (frame['SP'] > 0) & (frame['MRP'] > 0)]
        ss = sub['Est. Category Share SP'].sum()
        if ss <= 0:
            continue
        denom = ((sub['Est. Category Share SP'] / ss) * (sub['MRP'] / sub['SP'])).sum()
        if denom <= 0:
            continue
        Tsp = (T * 1e7) / denom
        net = (sub['Est. Category Share SP'] / ss) * Tsp
        frame.loc[sub.index, '_net'] = net
        frame.loc[sub.index, '_units'] = net / sub['SP']
        frame.loc[sub.index, '_gross'] = net / sub['SP'] * sub['MRP']
    frame['_w'] = frame['_gross']
    return frame

cur = _bake(cur)
prv = _bake(prv)

def wmean(frame, col, wcol='_w'):
    v = frame[col]; w = frame[wcol]
    mask = v.notna() & (w > 0)
    if mask.any() and w[mask].sum() > 0:
        return float((v[mask] * w[mask]).sum() / w[mask].sum())
    return float(v[v.notna()].mean()) if v.notna().any() else None

def wmean_by(frame, by, col, wcol='_w'):
    d = frame.dropna(subset=[col]).copy()
    d['_wv'] = d[col] * d[wcol]
    g = d.groupby(by).agg(_wv=('_wv', 'sum'), _w=(wcol, 'sum'))
    return (g['_wv'] / g['_w'].replace(0, np.nan)).fillna(d.groupby(by)[col].mean())

# ---------- KPIs ----------
kpis = {
    'skus': int(cur['Product ID'].nunique()),
    'brands': int(cur['BrandKey'].nunique()),
    'subcats': len(SUBCATS),
    'avg_osa': r(wmean(cur, 'Wt. OSA %'), 1),
    'avg_disc': r(cur['Wt. Discount %'].mean(), 1),
    'avg_sp': r(cur['SP'].mean(), 0),
    'months': f"{PREV[:7]} → {LATEST[:7]}",
}

# ---------- Sub-category structure ----------
subcat = []
for s in SUBCATS:
    c = cur[cur['Sub Category'] == s]
    p = prv[prv['Sub Category'] == s]
    # top-5 brand concentration (share of category captured by top 5 brands)
    bshare = c.groupby('BrandKey')['Est. Category Share'].sum().sort_values(ascending=False)
    top5 = float(bshare.head(5).sum())
    hhi = float(((bshare)**2).sum())  # Herfindahl on category-share points
    subcat.append({
        'name': s,
        'skus': int(c['Product ID'].nunique()),
        'brands': int(c['BrandKey'].nunique()),
        'avg_osa': r(wmean(c, 'Wt. OSA %'), 1),
        'avg_disc': r(c['Wt. Discount %'].mean(), 1),
        'avg_sp': r(c['SP'].mean(), 0),
        'top5_conc': r(top5, 1),
        'hhi': r(hhi, 0),
    })

# ---------- Top SKUs per sub-category (product-wise) ----------
top_skus = {}
for s in SUBCATS:
    c = cur[cur['Sub Category'] == s].copy()
    g = (c.groupby('Product Name')
           .agg(share=('Est. Category Share','sum'),
                brand=('Brand','first'),
                sp=('SP','mean'),
                osa=('Wt. OSA %','mean'),
                disc=('Wt. Discount %','mean'))
           .sort_values('share', ascending=False).head(12))
    top_skus[s] = [{'name': i[:55], 'brand': row.brand, 'share': r(row.share,2),
                    'sp': r(row.sp,0), 'osa': r(row.osa,0), 'disc': r(row.disc,0)}
                   for i, row in g.iterrows()]

# ---------- Top brands overall (avg category share across sub-cats + SOV) ----------
# A brand's "category share" is averaged over the sub-cats it competes in (so it stays on a 0-100 scale)
def brand_table(frame):
    g = frame.groupby('BrandKey').agg(
        cat_share=('Est. Category Share','sum'),
        sov=('Overall SOV','sum'),
        ad_sov=('Ad SOV','sum'),
        org_sov=('Organic SOV','sum'),
        osa=('Wt. OSA %','mean'),
        disc=('Wt. Discount %','mean'),
        skus=('Product ID','nunique'),
        subcats=('Sub Category','nunique'),
    )
    return g

bcur = brand_table(cur)
bprv = brand_table(prv)
osa_w = wmean_by(cur, 'BrandKey', 'Wt. OSA %')   # demand-weighted OSA per brand
# normalise share/sov to % of total tracked points in the period (5 sub-cats => 500 share pts, 1000 sov pts)
tot_share = cur['Est. Category Share'].sum()
tot_sov = cur['Overall SOV'].sum()
bcur['share_pct'] = bcur['cat_share'] / tot_share * 100
bcur['sov_pct'] = bcur['sov'] / tot_sov * 100
bprv_share = bprv['cat_share'] / prv['Est. Category Share'].sum() * 100

top_brands = []
for k, row in bcur.sort_values('cat_share', ascending=False).head(20).iterrows():
    delta = float(bcur.loc[k,'share_pct'] - bprv_share.get(k, 0))
    top_brands.append({
        'brand': brand_disp[k],
        'share_pct': r(row.share_pct, 2),
        'sov_pct': r(row.sov_pct, 2),
        'osa': r(osa_w.get(k, row.osa), 0),
        'disc': r(row.disc, 0),
        'skus': int(row.skus),
        'subcats': int(row.subcats),
        'delta': r(delta, 2),
    })

# ---------- SOV vs Share scatter (visibility vs conversion) for top brands ----------
sov_scatter = []
for k, row in bcur.sort_values('cat_share', ascending=False).head(30).iterrows():
    sov_scatter.append({'brand': brand_disp[k], 'x': r(row.sov_pct,2),
                        'y': r(row.share_pct,2), 'osa': r(osa_w.get(k, row.osa),0)})

# ---------- Market-share momentum (MoM) by sub-category brand leaders ----------
momentum = []
merged = bcur[['share_pct']].join(bprv_share.rename('prev'), how='outer').fillna(0)
merged['delta'] = merged['share_pct'] - merged['prev']
gain = merged.sort_values('delta', ascending=False).head(8)
loss = merged.sort_values('delta').head(8)
gainers = [{'brand': brand_disp.get(k,k), 'delta': r(v.delta,2), 'now': r(v.share_pct,2)} for k,v in gain.iterrows()]
losers  = [{'brand': brand_disp.get(k,k), 'delta': r(v.delta,2), 'now': r(v.share_pct,2)} for k,v in loss.iterrows()]

# ---------- WHITE SPACES ----------
# 1) SKU-level unmet demand: high Share-of-Voice (shoppers see/search it) but low On-Shelf Availability
ws = cur.copy()
ws = ws[ws['Overall SOV'].notna() & ws['Wt. OSA %'].notna()]
sov_hi = ws['Overall SOV'].quantile(0.75)
white_skus = ws[(ws['Overall SOV'] >= sov_hi) & (ws['Wt. OSA %'] < 40)] \
    .sort_values('Overall SOV', ascending=False).head(15)
white_space_skus = [{
    'name': row['Product Name'][:50], 'brand': row['Brand'], 'subcat': row['Sub Category'],
    'sov': r(row['Overall SOV'],2), 'osa': r(row['Wt. OSA %'],0),
    'share': r(row['Est. Category Share'],2), 'disc': r(row['Wt. Discount %'],0),
    'csp': r(row['Est. Category Share SP'],4), 'sp': r(row['SP'],0), 'mrp': r(row['MRP'],0),
    'g': round(float(row['_gross']))
} for _, row in white_skus.iterrows()]

# 2) Quadrant scatter: x = SOV, y = OSA for all SKUs with both (sample/aggregate by product)
quad = ws.groupby(['Product Name','Sub Category']).agg(
    sov=('Overall SOV','mean'), osa=('Wt. OSA %','mean'), share=('Est. Category Share','mean')
).reset_index()
# keep meaningful points
quad = quad[quad['sov'] > 0.05]
quad_pts = {}
for s in SUBCATS:
    qq = quad[quad['Sub Category']==s]
    quad_pts[s] = [{'x': r(rr.sov,2), 'y': r(rr.osa,0), 'r2': r(rr.share,2)} for _, rr in qq.iterrows()]

# 3) Category-level white space: fragmentation (low top-5 conc) + availability gap
cat_ws = []
for sc in subcat:
    c = cur[cur['Sub Category']==sc['name']]
    # demand not met: avg SOV among low-availability SKUs
    low = c[c['Wt. OSA %'] < 40]
    cat_ws.append({
        'name': sc['name'],
        'fragmentation': r(100 - sc['top5_conc'],1),   # higher = more open / fragmented
        'avg_osa': sc['avg_osa'],
        'stockout_demand': r(low['Overall SOV'].sum(),1),  # SOV sitting in low-availability SKUs
        'skus_low_osa': int(low['Product ID'].nunique()),
    })

# ---------- SKU-level dataset for live ₹-sales recalculation ----------
g = (cur.groupby(['Product Name', 'Sub Category'])
       .agg(brand=('Brand', 'first'),
            cat=('Category', 'first'),
            cs=('Est. Category Share', 'sum'),
            csp=('Est. Category Share SP', 'sum'),
            sp=('SP', 'mean'),
            mrp=('MRP', 'mean'),
            net=('_net', 'sum'),
            gross=('_gross', 'sum'),
            units=('_units', 'sum'),
            osa=('Wt. OSA %', 'mean'),
            disc=('Wt. Discount %', 'mean'),
            sov=('Overall SOV', 'mean'),
            osov=('Organic SOV', 'mean'),
            asov=('Ad SOV', 'mean'),
            ppu=('Wt. PPU (x100)', 'mean'),
            gram=('Grammage', 'first'))
       .reset_index())
import re
def pack_count(gram, name):
    # derive pack count from grammage piece-count; volume/weight/'unit' => single (pack 1).
    # Falls back to an explicit count in the product name. Source Wt. PPU is ignored
    # (it divides by volume numbers, e.g. "800 ml" -> 8, corrupting per-unit price).
    g = str(gram).lower().strip()
    m = re.match(r'^\s*(\d+)\s*(pcs|pc|pieces|piece|pair)\b', g)
    if m:
        return max(1, int(m.group(1)))
    m = re.search(r'set of (\d+)', g) or re.match(r'^\s*(\d+)\s*sets?\b', g)
    if m:
        return max(1, int(m.group(1)))
    n = str(name).lower()
    m = (re.search(r'set of (\d+)', n) or re.search(r'pack of (\d+)', n)
         or re.search(r'\b(\d+)\s*(pcs|pieces)\b', n))
    if m:
        return max(1, int(m.group(1)))
    return 1
def ppu_of(sp, gram, name):
    if sp is None or pd.isna(sp) or sp <= 0:
        return None
    return round(sp / pack_count(gram, name))
sku_level = [{
    'n': row['Product Name'][:60], 'b': row['brand'], 's': row['Sub Category'], 'cat': row['cat'],
    'pt': classify(row['Product Name']),
    'cs': r(row['cs'], 4), 'csp': r(row['csp'], 4),
    'sp': r(row['sp'], 0), 'mrp': r(row['mrp'], 0), 'osa': r(row['osa'], 0),
    'disc': r(row['disc'], 0), 'sov': r(row['sov'], 3),
    'osov': r(row['osov'], 3), 'asov': r(row['asov'], 3),
    '_n': round(float(row['net'])), '_g': round(float(row['gross'])), '_u': r(row['units'], 1),
    'ppu': ppu_of(row['sp'], row['gram'], row['Product Name']),
    'pack': float(pack_count(row['gram'], row['Product Name'])),
    'gram': (str(row['gram']).strip()[:14] if pd.notna(row['gram']) else '')
} for _, row in g.iterrows()]

# ---------- SKU-level month-over-month (entrants / exits / risers / fallers) ----------
def sku_month(frame):
    return frame.groupby('Product ID').agg(
        n=('Product Name', 'first'), b=('Brand', 'first'), s=('Sub Category', 'first'),
        csp=('Est. Category Share SP', 'sum'),
        osa=('Wt. OSA %', 'mean'), disc=('Wt. Discount %', 'mean'), sp=('SP', 'mean'))
ma, mp = sku_month(cur), sku_month(prv)
sku_mom = []
for pid in (set(ma.index) | set(mp.index)):
    inA, inP = pid in ma.index, pid in mp.index
    a = ma.loc[pid] if inA else None
    p = mp.loc[pid] if inP else None
    ref = a if inA else p
    sku_mom.append({
        'n': str(ref['n'])[:60], 'b': str(ref['b']), 's': str(ref['s']),
        'pt': classify(str(ref['n'])),
        'st': 'both' if (inA and inP) else ('new' if inA else 'exit'),
        'ac': r(a['csp'], 4) if inA else None, 'pc': r(p['csp'], 4) if inP else None,
        'ao': r(a['osa'], 0) if inA else None, 'po': r(p['osa'], 0) if inP else None,
        'ad': r(a['disc'], 0) if inA else None, 'pd': r(p['disc'], 0) if inP else None,
        'asp': r(a['sp'], 0) if inA else None, 'psp': r(p['sp'], 0) if inP else None,
    })

out = {
    'meta': {'latest': LATEST, 'prev': PREV, 'generated': str(pd.Timestamp.now())[:16],
             'platform': PLATFORM, 'platform_label': PLATFORM_LABEL,
             'sales_key': SALES_KEY, 'default_sales': SUPER_SALES, 'cat_sales': DEFAULT_SALES},
    'sku_level': sku_level, 'sku_mom': sku_mom,
    'kpis': kpis, 'subcat': subcat, 'top_skus': top_skus, 'top_brands': top_brands,
    'sov_scatter': sov_scatter, 'gainers': gainers, 'losers': losers,
    'white_space_skus': white_space_skus, 'quad_pts': quad_pts, 'cat_ws': cat_ws,
    'subcats': SUBCATS,
}
with open(OUT_JSON,'w') as f:
    json.dump(out, f)
print(f'[{PLATFORM}] Data written to {OUT_JSON}. KPIs:', kpis)
print('Sub-cats:', [s['name'] for s in subcat])
print('White-space SKUs found:', len(white_space_skus))
