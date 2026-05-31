# Quick-Commerce (Blinkit) RCA Dashboard

A self-contained, interactive HTML dashboard built from Blinkit RCA (Retail
Competitive Analytics) CSV exports across 5 home categories. It opens in any
browser with no server — [Chart.js](https://www.chartjs.org/) loads from a CDN
and all data is embedded directly in the page as JSON.

**Categories covered:** Kitchen & Dining, Home Decor, Bathroom Essentials,
Cleaning Tools, Home Improvement.

## The dashboard

- **`index.html`** — the Vercel root (deployed as a static site: framework
  "Other", no build command).
- **`dashboard.html`** — the same self-contained dashboard, for download / local use.

### Sections
1. KPIs
2. Sales input panel (per-sub-category MRP)
3. Overall view (gross/net/units/realisation, sales by sub-cat, top brands)
4. Market structure by sub-category
5. Top SKUs (product-wise, per sub-category)
6. Top brands & market share (visibility vs. conversion)
7. Product types (top types, sales-split donut, detail table)
8. MoM momentum
9. White spaces (demand vs. availability, unmet-demand SKUs, fragmentation)

## Source data

- 5 CSVs (same schema), one per sub-category, in `raw_csvs/`.
- Combined into `blinkit_rca_combined.xlsx` with a **Sub Category** column derived
  from each file name.
- Two monthly snapshots: **2026-03-01** and **2026-04-01**. The latest month drives
  the views; month-over-month deltas use both.

## The sales model

The source data has **no native revenue/units**. Instead, the user enters **total
MRP sales per sub-category** (≈ ₹122.6 Cr total). Per sub-category, that total is
distributed across SKUs using **Est. Category Share SP**, **SP**, and **MRP**, so
that gross MRP reconciles exactly to the entered total. The dashboard has a
**Show:** toggle for Net ₹ / Gross ₹ / Units.

Validated: gross reconciles to ₹122.6 Cr, net ≈ ₹68.2 Cr (~56% realisation),
~2.44M units.

## Product-type classification

`product_types.py` maps each Product Name to one of ~130 product types (e.g.
Laundry Basket, Induction Cooktop, Pressure Cooker, Scented Candle) via an ordered
keyword rule list (first match wins). ~96% of SKUs are classified; the rest fall
into "Other". Edit the `RULES` list to refine.

## Build pipeline

```bash
python3 build_dashboard_data.py   # raw CSVs / xlsx -> dashboard_data.json
python3 make_dashboard.py         # inject JSON into template -> dashboard.html + index.html
```

- `dashboard_template.html` holds the HTML/CSS/JS with a `/*__DATA__*/` placeholder.
- `combine_csvs.py` rebuilds `blinkit_rca_combined.xlsx` from the raw CSV uploads.

See [`CLAUDE.md`](./CLAUDE.md) for the full project context, data dictionary, and
methodological notes.

## Open items

- A 6th category file was mentioned but never provided — re-run the pipeline if it
  arrives.
- MoM ₹ growth now that real sales exist; export per-SKU units/revenue to Excel.

<!-- redeploy 20260530T205549Z -->

<!-- redeploy 20260530T210341Z -->

<!-- redeploy nudge 20260531T160209Z (webhook missed d57aab8, f3d4845) -->
