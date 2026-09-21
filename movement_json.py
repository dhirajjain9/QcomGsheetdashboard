"""Build movement_data.json — May vs Aug 2026 movement across Q-Commerce home
categories, sliced by platform (All / Blinkit / Instamart / Zepto).

May snapshot + May MRP totals recovered from git commit 367cf13; Aug from the
current combined files + current DEFAULT_SALES. Classified with the CURRENT
product_types + super_cats so both periods are directly comparable. 'Others'
super category excluded (home-only, matching the live dashboards)."""
import pandas as pd, json, sys
sys.path.insert(0, '/home/user/QcomGsheetdashboard')
from product_types import classify
from super_cats import super_of
SP = '/tmp/claude-0/-home-user-QcomGsheetdashboard/97d53f94-beb2-5fac-8173-4e1bbb358e71/scratchpad'

MAY_SALES = {
 'blinkit':{'Appliances':142.2,'Kitchen & Dining Needs':79.6,'Home Furnishing':55.5,'Tissues & Disposables':46.4,'Sports & Fitness':44.4,'Decorative Lights':31.3,'Bags':23.4,'Flowers, Plants & Gardening':20.3,'Pooja Needs':20.2,'Bathroom Essentials':20.2,'Cleaning Tools':19.8,'Clothing, Footwear & Accessories':18.7,'Home Decor':13.0,'Stationery Needs':11.4,'Festive & Occasion Needs':10.5,'Garbage Bags':9.6,'Party Essentials':7.6,'Home Improvement':7.1,'Festive Gifting':3.0},
 'instamart':{'Powerbanks Chargers Cables':25.2,'Sports & Gym':20.4,'Kitchen Appliances':19.1,'Home Furnishing':18.5,'Bottles Flasks Tiffins':13.6,'Home Decor':12.8,'Cleaning Tools':11.8,'Cookware':11.4,'Tissues & Disposables':11.1,'Home Appliances':9.6,'Bathware & Laundry':8.9,'Storage & Organizers':7.9,'Personal Care Appliances':7.6,'Utility & Tools':7.3,'Jars Containers Holders':7.1,'Pooja Needs':6.6,'Glasses Cups Mugs':5.7,'Plates Bowls Crockery':5.6,'Kitchen Tools':5.2,'Travel And Luggage':5.1,'Kitchen Cleaning':3.4,'Lights & Bulbs':2.9,'Bakeware & Bbq':1.4,'Gardening':1.3,'Barware':1.2,'Serveware':1.2,'Linen And Furnishing':1.1,'Cutlery & Ladles':0.0035},
 'zepto':{'Home Furnishing':23.9,'Kitchen Appliances':22.8,'Cleaning Aids':19.8,'Bulbs & Lights':19.2,'Pooja & Worship Needs':18.0,'Home Appliances':17.2,'Tissues & Disposables':13.6,'Household Utility':12.8,'Home Decor':8.8,'Kitchen Tools':8.0,'Kitchen Storage':7.1,'Cookware':6.9,'Extensions & Switches':5.6,'Drinkware & Bar':3.7,'Bath & Laundry':3.6,'Lunch Boxes':3.4,'Kitchen Aids':3.4,'Gardening':3.1,'Gas Stove & Accessories':2.3,'Pressure Cooker':2.2,'Steel Utensils':2.0,'Stationery & Crafts':1.7,'Hardware & Fittings':1.5,'Tableware':1.2,'Kitchen Cleaning':0.006},
}
AUG_SALES = {
 'blinkit':{'Appliances':170.5,'Kitchen & Dining Needs':86.7,'Home Furnishing':80.3,'Tissues & Disposables':56.8,'Decorative Lights':54.8,'Bags':43.7,'Sports & Fitness':37.6,'Pooja Needs':34.3,'Bathroom Essentials':25.0,'Clothing, Footwear & Accessories':24.6,'Flowers, Plants & Gardening':24.1,'Cleaning Tools':22.6,'Stationery Needs':18.0,'Festive & Occasion Needs':15.4,'Home Decor':15.0,'Party Essentials':9.7,'Garbage Bags':9.7,'Home Improvement':9.5,'Festive Gifting':5.8},
 'instamart':{'Powerbanks Chargers Cables':24.0,'Home Decor':20.4,'Home Furnishing':19.8,'Sports & Gym':18.0,'Kitchen Appliances':16.7,'Cleaning Tools':14.4,'Bottles Flasks Tiffins':13.3,'Tissues & Disposables':12.5,'Bathware & Laundry':12.4,'Storage & Organizers':10.5,'Pooja Needs':10.0,'Personal Care Appliances':9.4,'Cookware':9.3,'Utility & Tools':9.0,'Jars Containers Holders':8.9,'Home Appliances':8.0,'Glasses Cups Mugs':6.8,'Kitchen Tools':6.4,'Plates Bowls Crockery':6.1,'Travel And Luggage':4.0,'Kitchen Cleaning':3.8,'Lights & Bulbs':2.7,'Bakeware & Bbq':1.8,'Linen And Furnishing':1.5,'Barware':1.2,'Gardening':1.2,'Serveware':1.1,'Cutlery & Ladles':0.312},
 'zepto':{'Home Furnishing':35.2,'Pooja & Worship Needs':29.3,'Kitchen Appliances':26.4,'Household Utility':26.0,'Bulbs & Lights':23.8,'Cleaning Aids':23.3,'Home Appliances':19.0,'Tissues & Disposables':17.1,'Home Decor':10.5,'Kitchen Tools':8.6,'Kitchen Storage':8.3,'Cookware':7.7,'Extensions & Switches':5.4,'Drinkware & Bar':4.3,'Lunch Boxes':4.2,'Bath & Laundry':3.9,'Kitchen Aids':3.9,'Gas Stove & Accessories':3.0,'Gardening':2.7,'Stationery & Crafts':2.6,'Pressure Cooker':2.6,'Steel Utensils':2.3,'Hardware & Fittings':1.8,'Tableware':1.5,'Kitchen Cleaning':0.764},
}
PLATS = [('blinkit', 'Blinkit'), ('instamart', 'Instamart'), ('zepto', 'Zepto')]
JUNK = {'unbranded','generic','na','none','nan','n/a','no brand','other','others'}


def bake(frame, sales):
    frame = frame.copy(); frame['_g'] = 0.0
    for cat, T in sales.items():
        if not T or T <= 0:
            continue
        sub = frame[(frame['Category'] == cat) & (frame['Est. Category Share SP'] > 0)
                    & (frame['SP'] > 0) & (frame['MRP'] > 0)]
        ss = sub['Est. Category Share SP'].sum()
        if ss <= 0:
            continue
        denom = ((sub['Est. Category Share SP'] / ss) * (sub['MRP'] / sub['SP'])).sum()
        if denom <= 0:
            continue
        Tsp = (T * 1e7) / denom
        frame.loc[sub.index, '_g'] = (sub['Est. Category Share SP'] / ss) * Tsp / sub['SP'] * sub['MRP']
    return frame


def norm_brand(b):
    k = str(b).strip().lower()
    return k[4:] if k.startswith('the ') else k


def load(period):
    frames = []
    sales_all = MAY_SALES if period == 'may' else AUG_SALES
    for pk, _ in PLATS:
        fn = f'{SP}/{pk}_aprmay.xlsx' if period == 'may' else f'/home/user/QcomGsheetdashboard/{pk}_rca_combined.xlsx'
        d = pd.read_excel(fn)
        for c in ['SP', 'MRP', 'Est. Category Share SP']:
            d[c] = pd.to_numeric(d[c], errors='coerce')
        d['Date'] = d['Date'].astype(str); d['Category'] = d['Category'].astype(str).str.strip()
        d = d[d['Date'] == sorted(d['Date'].unique())[-1]].copy()
        d = bake(d, sales_all[pk])
        d['super'] = d['Category'].map(super_of); d['pt'] = d['Product Name'].map(classify)
        d['bk'] = d['Brand'].map(norm_brand); d['bd'] = d['Brand'].astype(str).str.strip()
        d['plat'] = pk
        frames.append(d[d['super'] != 'Others'])
    return pd.concat(frames, ignore_index=True)


MAY, AUG = load('may'), load('aug')


def cr(df, col):
    return df.groupby(col)['_g'].sum() / 1e7


def movers(mc, ac, n=12, drop=('Other',), floor=3.0, rank='pct'):
    keys = [k for k in set(mc.index) | set(ac.index) if k not in drop and str(k).strip().lower() not in JUNK]
    rows = []
    for k in keys:
        a, b = mc.get(k, 0), ac.get(k, 0)
        if max(a, b) < floor:
            continue
        pct = ((b / a - 1) * 100) if a > 0 else (999 if b > 0 else 0)
        rows.append({'name': k, 'may': round(a, 1), 'aug': round(b, 1),
                     'delta': round(b - a, 1), 'pct': round(pct)})
    rows.sort(key=(lambda r: r['delta']) if rank == 'delta' else (lambda r: r['pct']))
    return {'risers': rows[-n:][::-1], 'fallers': rows[:n]}


def entryexit(mc, ac, dispmap, thr=0.03):
    keys = set(mc.index) | set(ac.index)
    new = [{'name': dispmap.get(k, k), 'aug': round(ac.get(k, 0), 1)} for k in keys if mc.get(k, 0) == 0 and ac.get(k, 0) >= thr]
    ext = [{'name': dispmap.get(k, k), 'may': round(mc.get(k, 0), 1)} for k in keys if ac.get(k, 0) == 0 and mc.get(k, 0) >= thr]
    new.sort(key=lambda r: -r['aug']); ext.sort(key=lambda r: -r['may'])
    newc = sum(1 for k in keys if mc.get(k, 0) == 0 and ac.get(k, 0) > 0)
    extc = sum(1 for k in keys if ac.get(k, 0) == 0 and mc.get(k, 0) > 0)
    return new[:12], ext[:12], newc, extc


def scope(pk, floors):
    m = MAY if pk == 'all' else MAY[MAY['plat'] == pk]
    a = AUG if pk == 'all' else AUG[AUG['plat'] == pk]
    bdisp = {**a.groupby('bk')['bd'].agg(lambda s: s.mode().iloc[0]).to_dict(),
             **m.groupby('bk')['bd'].agg(lambda s: s.mode().iloc[0]).to_dict()}
    mb, ab = cr(m, 'bk'), cr(a, 'bk')
    newb, extb, newc, extc = entryexit(mb, ab, bdisp)
    fc, ft, fb = floors
    return {
        'totals': {'may': round(m['_g'].sum() / 1e7), 'aug': round(a['_g'].sum() / 1e7)},
        'supers': [{'name': s, 'may': round(cr(m, 'super').get(s, 0), 1), 'aug': round(cr(a, 'super').get(s, 0), 1)}
                   for s in ['Kitchen', 'Appliances', 'Soft Furnishings', 'General Home Improvement / Decor']],
        'categories': movers(cr(m, 'Category'), cr(a, 'Category'), 10, floor=fc),
        'brands': movers(cr(m, 'bk').rename(index=bdisp), cr(a, 'bk').rename(index=bdisp), 12, floor=fb, rank='delta'),
        'types': movers(cr(m, 'pt'), cr(a, 'pt'), 12, floor=ft),
        'newBrands': newb, 'exitBrands': extb, 'newCount': newc, 'exitCount': extc,
    }


scopes = {'all': scope('all', (3.0, 3.0, 2.0))}
for pk, _ in PLATS:
    scopes[pk] = scope(pk, (1.2, 1.0, 0.8))

platGrowth = [{'key': pk, 'label': lab,
               'may': scopes[pk]['totals']['may'], 'aug': scopes[pk]['totals']['aug']}
              for pk, lab in PLATS]

data = {
    'months': ['May 2026', 'Aug 2026'],
    'platforms': [{'key': 'all', 'label': 'All Q-Commerce'}] + [{'key': pk, 'label': lab} for pk, lab in PLATS],
    'platformGrowth': platGrowth,
    'scopes': scopes,
}
json.dump(data, open('/home/user/QcomGsheetdashboard/movement_data.json', 'w'), separators=(',', ':'))
print('wrote movement_data.json')
for pk in ['all'] + [p for p, _ in PLATS]:
    t = scopes[pk]['totals']
    print(f"  {pk:10s} May {t['may']:5d} -> Aug {t['aug']:5d} Cr  ({round((t['aug']/t['may']-1)*100):+d}%)")
