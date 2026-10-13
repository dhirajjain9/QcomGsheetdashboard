# Quick-Commerce RCA Dashboard — complete handover

Live site: **https://qcom-gsheetdashboard.vercel.app**
Repo: `dhirajjain9/qcomgsheetdashboard` (this is a full snapshot of it).

This archive contains **everything that's live** — the real source data, the build
pipeline, and the generated pages. You can open the dashboards as-is, or rebuild them
from the data.

---

## Open it (no build needed)
Every `.html` here is self-contained (data embedded, Chart.js from CDN). Just open:
- `index.html` — Blinkit dashboard (also the Vercel root)
- `instamart.html`, `zepto.html` — the other two platforms
- `compare.html` — ⇄ Cross-Platform
- `movement.html` — 📈 May → Aug movement
- `platforms.html` — landing / chooser

## The real data (what's live)
| File | What it is |
|---|---|
| `blinkit_rca_combined.xlsx`, `instamart_rca_combined.xlsx`, `zepto_rca_combined.xlsx` | **Source RCA data** — Jul + Aug 2026 snapshots, all categories, one workbook per platform |
| `dashboard_data.json` (Blinkit), `instamart_dashboard_data.json`, `zepto_dashboard_data.json` | Built per-platform datasets (derived from the xlsx) |
| `movement_data.json` | May→Aug movement dataset (per platform) |
| `build_dashboard_data.py` → `DEFAULT_SALES` | **The MRP category-size totals (₹ Cr) per platform** — the anchor for every ₹ figure (there's no native revenue in the export) |

> The May snapshot used by the Movement tab is not in these files — it was recovered
> from an earlier git commit. `movement_json.py` carries both May and Aug MRP totals.

## Rebuild from data
```bash
python3 -m pip install pandas openpyxl

# per-platform dashboards (blinkit writes dashboard.html + index.html)
for P in blinkit instamart zepto; do
  PLATFORM=$P python3 build_dashboard_data.py   # xlsx -> <platform>_dashboard_data.json
  PLATFORM=$P python3 make_dashboard.py         # json -> <platform>.html
done

python3 make_compare.py     # the 3 jsons -> compare.html
python3 build_movement.py   # movement_data.json -> movement.html
# (to regenerate movement_data.json itself: python3 movement_json.py — needs the
#  recovered May workbooks; see that script's header)
```

## File map
| File | Role |
|---|---|
| `build_dashboard_data.py` | CSV/xlsx → `<platform>_dashboard_data.json`; holds `DEFAULT_SALES`, the sales model, and the "Others" exclusion |
| `make_dashboard.py` | injects a platform's JSON into `dashboard_template.html` → its `.html` |
| `dashboard_template.html` | the HTML/CSS/JS template (a `/*__DATA__*/` placeholder) shared by all 3 platform tabs |
| `make_compare.py` | builds `compare.html` (Cross-Platform). **Platforms hard-coded as B/I/Z** |
| `movement_json.py` / `build_movement.py` | build `movement_data.json` / `movement.html`. **Platforms hard-coded** |
| `super_cats.py` | maps each platform Category → one of 4 home Super Categories (unmapped → "Others" = excluded) |
| `product_types.py` | keyword classifier: Product Name → ~250 product types |
| `combine_csvs.py` | raw per-category CSVs in `raw_csvs[_<platform>]/` → `<platform>_rca_combined.xlsx` |
| `platforms.html` | landing page / tab chooser |
| `CLAUDE.md` | project context + data dictionary + the sales model |
| `INSIGHTS.md` | analytics/scoring methodology (source of truth for the logic) |
| `handoff/ADD_A_PLATFORM.md` | step-by-step for adding a **new** platform |

## Deploy
Static site on Vercel (framework: Other, no build command — it serves `index.html`).
Pushing to `main` on GitHub auto-deploys. Production alias: `qcom-gsheetdashboard.vercel.app`.

## Adding a new platform
See **`handoff/ADD_A_PLATFORM.md`**. In short: add the platform's `*_rca_combined.xlsx`,
map its categories in `super_cats.py`, add its totals to `DEFAULT_SALES`, then
`PLATFORM=<name> python3 build_dashboard_data.py && PLATFORM=<name> python3 make_dashboard.py`.
Folding a 4th platform into `compare.html` and `movement.html` needs a code change
(both currently hard-code the three platforms).
