import os, pandas as pd, json, numpy as np
from product_types import classify

# Platform-aware: PLATFORM=instamart/zepto reads <platform>_rca_combined.xlsx and
# writes <platform>_dashboard_data.json. Default 'blinkit' keeps the original
# blinkit_rca_combined.xlsx -> dashboard_data.json so nothing changes for Blinkit.
PLATFORM = os.environ.get('PLATFORM', 'blinkit').lower()
PLATFORM_LABEL = {'blinkit': 'Blinkit', 'instamart': 'Instamart', 'zepto': 'Zepto'}.get(PLATFORM, PLATFORM.title())
# Per-platform pre-filled MRP sales (₹ Cr). Blinkit = the agreed split; others
# start empty (dashboard shows value-share % until the user enters totals).
DEFAULT_SALES = {
    'blinkit': {'Kitchen & Dining Needs': 68.6, 'Cleaning Tools': 17,
                'Bathroom Essentials': 16.6, 'Home Decor': 14, 'Home Improvement': 6.4},
}.get(PLATFORM, {})
SALES_KEY = f'{PLATFORM}_mrp_sales_v1'   # localStorage namespace (per platform, no collisions)
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

DATES = sorted(df['Date'].unique())
LATEST, PREV = DATES[-1], DATES[0]
SUBCATS = sorted(df['Sub Category'].unique())
cur = df[df['Date'] == LATEST].copy()
prv = df[df['Date'] == PREV].copy()

def r(x, n=2):
    return None if pd.isna(x) else round(float(x), n)

# ---------- KPIs ----------
kpis = {
    'skus': int(cur['Product ID'].nunique()),
    'brands': int(cur['BrandKey'].nunique()),
    'subcats': len(SUBCATS),
    'avg_osa': r(cur['Wt. OSA %'].mean(), 1),
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
        'avg_osa': r(c['Wt. OSA %'].mean(), 1),
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
        'osa': r(row.osa, 0),
        'disc': r(row.disc, 0),
        'skus': int(row.skus),
        'subcats': int(row.subcats),
        'delta': r(delta, 2),
    })

# ---------- SOV vs Share scatter (visibility vs conversion) for top brands ----------
sov_scatter = []
for k, row in bcur.sort_values('cat_share', ascending=False).head(30).iterrows():
    sov_scatter.append({'brand': brand_disp[k], 'x': r(row.sov_pct,2),
                        'y': r(row.share_pct,2), 'osa': r(row.osa,0)})

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
    'csp': r(row['Est. Category Share SP'],4), 'sp': r(row['SP'],0), 'mrp': r(row['MRP'],0)
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
            cs=('Est. Category Share', 'sum'),
            csp=('Est. Category Share SP', 'sum'),
            sp=('SP', 'mean'),
            mrp=('MRP', 'mean'),
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
    'n': row['Product Name'][:60], 'b': row['brand'], 's': row['Sub Category'],
    'pt': classify(row['Product Name']),
    'cs': r(row['cs'], 4), 'csp': r(row['csp'], 4),
    'sp': r(row['sp'], 0), 'mrp': r(row['mrp'], 0), 'osa': r(row['osa'], 0),
    'disc': r(row['disc'], 0), 'sov': r(row['sov'], 3),
    'osov': r(row['osov'], 3), 'asov': r(row['asov'], 3),
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
             'sales_key': SALES_KEY, 'default_sales': DEFAULT_SALES},
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
