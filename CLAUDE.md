# Quick-Commerce (Blinkit) RCA Dashboard — Project Context

A self-contained, interactive HTML dashboard built from Blinkit RCA (Retail
Competitive Analytics) CSV exports for 5 home categories. Originally built in repo
`dhirajjain9/chapter-gobblecube-dashboard`; moved here (`qcomGsheetdashboard`).

## What the deliverable is
- **`index.html`** / **`dashboard.html`** — the same self-contained dashboard
  (Chart.js from CDN, all data embedded as JSON). `index.html` is the Vercel root.
- Opens in any browser, no server. Deployed on Vercel as a static site
  (framework: Other, no build command — it just serves `index.html`).

## Source data
- 5 CSVs (same schema), one per sub-category, combined into
  `blinkit_rca_combined.xlsx`. The **Sub Category** column is taken from each file's
  own **Category** column (the canonical label); the filename
  (`<hash>-blinkitrcadownload_<SubCategory>.csv`) is only a fallback.
- Sub-categories: Kitchen & Dining Needs, Home Decor, Bathroom Essentials,
  Cleaning Tools, Home Improvement.
- Two monthly snapshots: 2026-03-01 and 2026-04-01. **April-only is the permanent
  basis for all strategic views** (by decision); the Month-over-month section is the
  only view that uses March.
- **A 6th category file was mentioned but never provided** — re-run the pipeline if it arrives.

## Data dictionary (source columns)
| Column | Meaning | Notes |
|---|---|---|
| Date | Monthly snapshot | 2 months present |
| Sub Category | Added by us = the source **Category** column (filename fallback) | |
| Category | Blinkit's own label | == sub-category here |
| Product ID | SKU id | |
| Item ID | secondary id | **empty** |
| Product Name | SKU name | |
| Grammage | pack/size, e.g. "2 pcs" | |
| Brand | brand (casing inconsistent → normalise via lowercase key) | |
| MRP / SP | max retail price / selling price (₹) | |
| Wt. Discount % | (MRP−SP)/MRP weighted | |
| Wt. PPU (x100) | price per **single unit** = SP / pack count | **~3.7% of rows corrupt (PPU > SP, impossible)** — build clamps `ppu ≤ sp`, `pack ≥ 1`. A few jugs etc. encode volume as pack-count (residual noise). |
| Wt. OSA % | weighted On-Shelf Availability (in-stock %) | avg ~35% |
| **Est. Category Share** | est. share of category **volume/offtake**; sums to 100% per sub-cat/month | sales proxy (volume) |
| **Est. Category Share SP** | est. share of category **value at SP**; sums to 100% | sales proxy (value) — **use this for revenue** |
| Units / Offtake MRP / Offtake SP | actual sold | **empty** — no native ₹/units |
| Overall / Organic / Ad SOV | Share of Voice (visibility); each sums to 100% per sub-cat/month | Overall is NOT Organic+Ad — three independent measures |

## The sales model (IMPORTANT — agreed with user)
There is **no native revenue/units** in the data. The user enters **total MRP sales
per sub-category** (they gave ≈ **₹122.6 Cr** total; per-cat split entered in the
panel: Kitchen 68.6, Cleaning 17, Bathroom 16.6, Home Decor 14, Home Improvement 6.4 — all in ₹ Cr).

Per sub-category, distribute the entered MRP total `T` using **Est. Category Share SP,
SP and MRP**:
- net SP revenue_i = shareSP_i × T_sp
- units_i = net_i / SP_i
- gross MRP_i = units_i × MRP_i
- solve `T_sp = T / Σ[ shareSP_i × (MRP_i / SP_i) ]` so that **Σ gross MRP = T** exactly.

SKUs missing SP/MRP/shareSP are excluded; remaining shares are renormalised so totals
reconcile. The dashboard has a **Show:** toggle (Net ₹ / Gross ₹ / Units). Validated:
gross reconciles to 122.6 Cr, net ≈ 68.2 Cr (~56% realisation), ~2.44M units.

## Product-type classification
`product_types.py` maps each Product Name → one of ~133 product types via an ordered
keyword rule list (first match wins). ~96% of SKUs classified; rest = "Other". Edit the
`RULES` list to refine (order matters — specific before general). A data-quality pass
split mis-tagged holders/stands (e.g. *Candle / Diya Holder* out of candles, *Cloth
Drying Stand* out of ropes, *Napkin Holder / Ring* out of kitchen cloth). Used across
the Product-type, Launchpad, White-space, MoM and Price-Band sections.

## Scope selector
A dropdown above **Top SKUs** (default **All categories**, plus each sub-category) is the
global scope and drives the **Top SKUs, Brands, and Product-types** sections; Availability,
MoM and Price-Band sections also follow it. The Launchpad has its own independent scope.

## Dashboard sections (current)
1. **KPIs** · 2. **Founder's Launchpad** (opportunity map + ranking with remark buckets,
   price ladder, competitor teardown w/ ad-reliance flags, launch shortlist) ·
3. **Sales input** (per-sub-cat MRP) · 4. **Overall view** (gross/net/units/realisation,
   sales by sub-cat, full brand universe) · 5. **Market structure** by sub-cat (HHI, top-5) ·
6. **Top SKUs** (scope-aware) · 7. **Brands** (leaderboard with **% of Total**, visibility-
   vs-conversion scatter — all scope-aware) · 8. **Product types** (top-40 bar+donut,
   detail table w/ Rev/SKU, By-SKU/By-Brand drill-down) · 9. **White spaces** (white-space
   map, bucket breakdown, leaderboard w/ Rev/SKU) · 10. **Availability & stockout loss**
   (est. ₹ lost, demand-vs-availability map) · 11. **Month-over-month** (SKU risers/fallers
   + entry/exit; brand & product-type entry/exit per category; brand-churn chart ranked by
   gross sales) · 12. **Price Band Analysis** (PPU value tiers — bands adaptive per product
   type — demand-vs-supply, pack-mix, tier detail).

**Scoring methodology** (opportunity score weights, white space = √(under-served ×
organic-beatable-leader), remark buckets, Rev/SKU benchmark) is documented in **`INSIGHTS.md`**
— keep that file as the source of truth for analytics logic.

Known caveat: the old cross-category brand "market share %" equal-weighted sub-categories;
the leaderboard is now scope-aware with a sales-weighted **% of Total** column. UX: drill-down
modals, sortable tables with frozen headers, section nav, persisted MRP inputs, cream theme.

## Build pipeline
```
python3 build_dashboard_data.py   # CSVs/xlsx → dashboard_data.json
python3 make_dashboard.py         # inject JSON into template → dashboard.html + index.html
```
- `dashboard_template.html` holds the HTML/CSS/JS with a `/*__DATA__*/` placeholder.
- `combine_csvs.py` rebuilds `blinkit_rca_combined.xlsx` from `raw_csvs/`.
- Key emitted datasets in `dashboard_data.json`:
  - `sku_level` (April per SKU): `cs, csp, sp, mrp, osa, disc, sov, osov, asov, ppu, pack, gram, pt`.
  - `sku_mom` (Mar↔Apr per Product ID): `ac/pc` (Apr/Mar value-share), `ao/po` (OSA),
    `ad/pd` (disc), `asp/psp` (SP), `pt`, `st` = `both|new|exit` — powers the MoM section.

## Open items / next ideas
- Add the missing **6th category** file when provided.
- MoM **₹ growth** (March isn't in the ₹ model — MoM is value-share only); per-SKU
  units/revenue export to Excel.
- Parked by decision: promo-dependency, averaged/month-toggle time basis.
- Backlog is otherwise clear (see `INSIGHTS.md`).
