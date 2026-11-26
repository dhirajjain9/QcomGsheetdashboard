# Quick-Commerce RCA Dashboard

A self-contained, interactive dashboard that turns **Retail Competitive Analytics (RCA)**
exports from **Blinkit, Instamart and Zepto** into a comparable, strategic view of the
home-category quick-commerce market. Every page opens in any browser with no server —
[Chart.js](https://www.chartjs.org/) loads from a CDN and all data is embedded in the page.

**Live:** https://qcom-gsheetdashboard.vercel.app

## Tabs

| Page | What it shows |
|---|---|
| `index.html` (Blinkit), `instamart.html`, `zepto.html` | Per-platform dashboards: KPIs, Founder's Launchpad, sales input, overall view, market structure, top SKUs, brands, product types, white spaces, availability & stockout loss, month-over-month, price bands |
| `compare.html` | **⇄ Cross-Platform** — whole-of-Q-Commerce context, then drill into any product type or brand (the only axes comparable across platforms) |
| `movement.html` | **📈 Movement** — period-over-period shift (currently May → Aug 2026): categories, brands and product types rising, falling, new and gone, sliceable by platform |
| `platforms.html` | Landing page / tab chooser |

## Super Categories

The many platform categories roll up into **4 home Super Categories** — a shared, apples-to-apples
axis across platforms:

- **Kitchen** · **Appliances** · **Soft Furnishings** · **General Home Improvement / Decor**

A non-home **"Others"** bucket (electronics, apparel, sports, stationery, etc.) is mapped but
**excluded** from the dashboards by decision. Mapping lives in `super_cats.py` — any category not
mapped falls to "Others" and is dropped.

## Source data

- One workbook per platform: `blinkit_rca_combined.xlsx`, `instamart_rca_combined.xlsx`,
  `zepto_rca_combined.xlsx`, each holding **two monthly snapshots** (latest currently
  **Jul & Aug 2026**). The latest month drives the strategic views; month-over-month uses both.
- Built per-platform datasets: `dashboard_data.json` (Blinkit), `instamart_dashboard_data.json`,
  `zepto_dashboard_data.json`. Movement: `movement_data.json`.
- Current Q-Commerce home gross ≈ **₹1,092 Cr** (Blinkit ₹620 Cr · Instamart ₹208 Cr · Zepto ₹264 Cr).

## The sales model

The RCA export has **no native revenue/units** (Offtake/Units columns are blank). Instead we take a
**total MRP sales figure (₹ Cr) per category** (external GobbleCube category sizing) and distribute
it across that category's SKUs using **Est. Category Share SP**, **SP** and **MRP**, solving so that
**Σ gross MRP = the entered total** exactly. This yields net ₹, gross ₹ and units per SKU. The
per-category totals live in `build_dashboard_data.py → DEFAULT_SALES`.

## Product-type classification

`product_types.py` maps each Product Name to one of ~250 product types via an ordered keyword rule
list (first match wins). It's platform-agnostic. ~93% of gross is classified; the rest is "Other".
Edit the `RULES` list to refine (specific rules before general — order matters).

## Build pipeline

```bash
python3 -m pip install pandas openpyxl

# per-platform dashboards (blinkit writes dashboard.html + index.html)
for P in blinkit instamart zepto; do
  PLATFORM=$P python3 build_dashboard_data.py   # xlsx -> <platform>_dashboard_data.json
  PLATFORM=$P python3 make_dashboard.py         # json -> <platform>.html
done

python3 make_compare.py     # the 3 jsons -> compare.html
python3 build_movement.py   # movement_data.json -> movement.html
```

- `dashboard_template.html` holds the HTML/CSS/JS with a `/*__DATA__*/` placeholder, shared by all
  three platform tabs.
- `combine_csvs.py` rebuilds a platform's `*_rca_combined.xlsx` from raw CSVs in
  `raw_csvs[_<platform>]/`.

## Deploy

Static site on Vercel (framework "Other", no build command — serves `index.html`). Pushing to
`main` auto-deploys. Production alias: `qcom-gsheetdashboard.vercel.app`.

## Adding a platform / handover

- **`handoff/ADD_A_PLATFORM.md`** — step-by-step to add a brand-new 4th platform (input formats,
  super-category mapping, `DEFAULT_SALES`, build commands). Note: `compare.html` and `movement.html`
  currently hard-code the three platforms, so folding a 4th into those two needs a code change.
- **`HANDOVER.md`** — complete-handover guide (file map, full rebuild, data map).

## More docs

- **`CLAUDE.md`** — full project context, source-column data dictionary, the sales model, scope rules.
- **`INSIGHTS.md`** — analytics & scoring methodology (opportunity score, white-space formula, Rev/SKU
  benchmarks) — the source of truth for the analytics logic.
