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
  `blinkit_rca_combined.xlsx` with a **Sub Category** column derived from each
  file name (`<hash>-blinkitrcadownload_<SubCategory>.csv`).
- Sub-categories: Kitchen and Dining needs, Home Decor, Bathroom Essentials,
  Cleaning Tools, Home Improvement.
- Two monthly snapshots: 2026-03-01 and 2026-04-01. Latest month drives the views;
  MoM deltas use both.
- **A 6th category file was mentioned but never provided** — re-run the pipeline if it arrives.

## Data dictionary (source columns)
| Column | Meaning | Notes |
|---|---|---|
| Date | Monthly snapshot | 2 months present |
| Sub Category | Added by us, from filename | |
| Category | Blinkit's own label | == sub-category here |
| Product ID | SKU id | |
| Item ID | secondary id | **empty** |
| Product Name | SKU name | |
| Grammage | pack/size, e.g. "2 pcs" | |
| Brand | brand (casing inconsistent → normalise via lowercase key) | |
| MRP / SP | max retail price / selling price (₹) | |
| Wt. Discount % | (MRP−SP)/MRP weighted | |
| Wt. PPU (x100) | price per **single unit** = SP / pack count | verified |
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
`product_types.py` maps each Product Name → one of ~130 product types
(e.g. Laundry Basket, Induction Cooktop, Pressure Cooker, Scented Candle) via an
ordered keyword rule list (first match wins). ~96% of SKUs classified; rest = "Other".
Edit the `RULES` list to refine. Used for the Product-type section and detail table.

## Dashboard sections
1. KPIs · 2. Sales input panel (per-sub-cat MRP) · 3. **Overall view**
(gross/net/units/realisation, sales by sub-cat, top brands across the *full* brand
universe) · 4. Market structure by sub-cat · 5. Top SKUs (product-wise, per sub-cat)
· 6. Top brands & market share (visibility-vs-conversion) · 7. **Product types**
(top types, sales-split donut, detail table) · 8. MoM momentum · 9. White spaces
(demand-vs-availability map, unmet-demand SKUs, category fragmentation).

Known methodological caveat: cross-category brand "market share %" equal-weights
sub-categories; once MRP totals are entered, all ₹/units aggregation is sales-weighted
and correct. The brand **leaderboard** is the top-20-by-share re-ranked by ₹; the
**Overall view** ranks the full brand universe by ₹.

## Build pipeline
```
python3 build_dashboard_data.py   # CSVs/xlsx → dashboard_data.json (+ product types, sku-level)
python3 make_dashboard.py         # inject JSON into template → dashboard.html + index.html
```
- `dashboard_template.html` holds the HTML/CSS/JS with a `/*__DATA__*/` placeholder.
- `combine_csvs.py` rebuilds `blinkit_rca_combined.xlsx` from the raw CSV uploads.

## Open items / next ideas
- Add the missing **6th category** file when provided.
- MoM **₹ growth** now that real sales exist; export per-SKU units/revenue to Excel.
- Optionally rank the brand leaderboard by the **global top sellers by ₹** (not just
  top-20-by-share).
