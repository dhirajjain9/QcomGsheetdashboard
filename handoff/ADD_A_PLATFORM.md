# Adding a new platform to the Quick-Commerce RCA Dashboard

This kit lets you add a **brand-new platform** (e.g. BigBasket / Flipkart Minutes /
Amazon / DMart) alongside the three already live: **Blinkit, Instamart, Zepto**.

The live dashboard: https://qcom-gsheetdashboard.vercel.app

There are **two ways to contribute** — pick the one that matches you:

| | **Path A — Just supply the data** (no code) | **Path B — Run the pipeline yourself** (needs Python) |
|---|---|---|
| You provide | 2 files in the templates' format | The same 2 files **and** you run the build scripts |
| You need | Excel / any CSV editor | Python 3 + `pandas` + `openpyxl` |
| You hand back | The raw files | A rebuilt `<platform>.html` + `<platform>_dashboard_data.json` |
| Effort | Low | Medium |

**Recommendation:** unless you're comfortable with Python, use **Path A** — send the two
data files and we'll integrate them. Either way, the **two input files are identical**, so
start by preparing those.

---

## The two input files (both paths need these)

### 1. The RCA export — `<platform>_rca_download.csv`
One CSV containing **all categories** for the platform, ideally with **two monthly snapshots**
(the dashboard compares the latest two months). Use `templates/rca_download_TEMPLATE.csv`
as the exact header. Columns:

| Column | Meaning | Required? |
|---|---|---|
| `Date` | Monthly snapshot, `YYYY-MM-01` (e.g. `2026-08-01`) | **Yes** |
| `Category` | The platform's own category label (this becomes the grouping key) | **Yes** |
| `Product ID` | SKU id | Yes |
| `Product Name` | SKU name (drives product-type classification) | **Yes** |
| `Grammage` | Pack/size text, e.g. `2 pcs`, `500 ml` | Yes |
| `Brand` | Brand name (casing can be inconsistent; we normalise) | **Yes** |
| `SP` | Selling price ₹ (post-discount) | **Yes** |
| `MRP` | Max retail price ₹ | **Yes** |
| `Wt. OSA %` | Weighted on-shelf availability (in-stock %) | Yes |
| `Wt. Discount %` | Weighted discount | Yes |
| `Est. Category Share` | Est. share of category **volume**, sums to 100% per category/month | Yes |
| `Est. Category Share SP` | Est. share of category **value at SP**, sums to 100% — **this drives revenue** | **Yes** |
| `Overall SOV`, `Organic SOV`, `Ad SOV` | Share of voice (visibility), each sums to 100%/category/month | Yes |
| `Wt. PPU (x100)` | Price per single unit × 100 | Optional |
| `Item ID`, `Offtake MRP`, `Offtake SP`, `Units` | Present in the export but **always empty** — leave blank | No |

Notes:
- **The two revenue-critical columns are `Est. Category Share SP`, `SP`, `MRP`.** A SKU missing
  any of these is dropped from the ₹ model (still fine, just not counted in sales).
- Keep the platform's **own category names** — don't rename them to match other platforms.
  We map them to Super Categories ourselves (see below).

### 2. The category sizing — `<platform>_mrp_category_size.csv`
The **total MRP sales (₹ Cr) per category** for the latest month. There is **no native
revenue** in the RCA export, so this is the one number that sets each category's size.
Use `templates/mrp_category_size_TEMPLATE.csv`. Columns: `Platform`, `Category`,
`Est. Category Size (Rs Cr)`. One row per category. The `Category` values **must match**
the `Category` labels in the RCA export exactly.

---

## Path A — just supply the data

1. Fill in the two files above (keep the template headers exactly).
2. Name them `<platform>_rca_download.csv` and `<platform>_mrp_category_size.csv`
   (e.g. `bigbasket_rca_download.csv`).
3. Send both back. That's it — we handle the rest.

**Please also send a one-line note** listing the platform's distinct `Category` values, so we
can map any new category into the right **Super Category** (see the mapping step below) — a
category we don't map is treated as non-home "Others" and **excluded** from the dashboard.

---

## Path B — run the pipeline yourself

### Setup (once)
```bash
python3 -m pip install pandas openpyxl
```

### Step 1 — Combine the raw CSV into the workbook
Put the RCA CSV in a folder named `raw_csvs_<platform>/` (e.g. `raw_csvs_bigbasket/`), then:
```bash
PLATFORM=bigbasket python3 combine_csvs.py
# -> writes bigbasket_rca_combined.xlsx
```
(You can drop one combined CSV or several per-category CSVs in that folder — both work.)

### Step 2 — Map every category to a Super Category  ⟵ most important edit
Open **`super_cats.py`** and add each of the platform's categories to the `SUPER_CAT`
dictionary, mapping it to one of the four home Super Categories:
`Kitchen` · `Appliances` · `Soft Furnishings` · `General Home Improvement / Decor`.

> ⚠️ Any category **not** in `SUPER_CAT` falls to `Others` and is **dropped** from the
> dashboard (the dashboard is home-only). So map everything you want shown.

### Step 3 — Enter the category MRP totals
Open **`build_dashboard_data.py`** and add your platform to the `DEFAULT_SALES` dict:
```python
'bigbasket': {'Cookware': 9.3, 'Home Furnishing': 19.8, ...},   # ₹ Cr per category
```
(Same numbers as `<platform>_mrp_category_size.csv`, as a Python dict.)

### Step 4 — Build the platform's dashboard tab
```bash
PLATFORM=bigbasket python3 build_dashboard_data.py   # -> bigbasket_dashboard_data.json
PLATFORM=bigbasket python3 make_dashboard.py         # -> bigbasket.html
```
Open `bigbasket.html` in any browser — it's a complete, standalone dashboard for that platform.

### Step 5 — (optional) add it to the navigation
- **`platforms.html`** — copy one of the three `<a class="card" …>` blocks and point it at
  `bigbasket.html` with the platform's stats.
- **`dashboard_template.html`** — add the platform to the `PLATS` array in the platform
  switcher (~line 415), then re-run `make_dashboard.py` for **every** platform so the new tab
  appears in all switchers.

### What you hand back
`bigbasket.html`, `bigbasket_dashboard_data.json`, `bigbasket_rca_combined.xlsx`, and your
edits to `super_cats.py` / `build_dashboard_data.py` (or just the whole folder).

---

## Important: the Cross-Platform & Movement tabs need a code change

Adding a platform's **own tab** is what the steps above cover, and it's self-contained.

The **⇄ Cross Platform** tab (`make_compare.py`) and the **📈 Movement** tab
(`movement_json.py`) currently have the three platforms **hard-coded** (`"B"`, `"I"`, `"Z"`).
Wiring a 4th platform into those two comparison views is a code refactor — **please leave those
to us**; send the per-platform files and we'll fold the new platform into the cross-platform and
movement views and redeploy.

---

## How the ₹ sales model works (context)
There's no native revenue in the data. For each category we take the MRP total `T` you provide and
distribute it across that category's SKUs using `Est. Category Share SP`, `SP` and `MRP`:
net SP revenue, units, and gross MRP are solved so **Σ gross MRP = T** exactly. That's why the
category sizing file matters: it's the anchor for every ₹ figure on the dashboard.

## Data-quality notes
- `Wt. PPU` is corrupt in ~4% of rows (PPU > SP); the build clamps `ppu ≤ sp` automatically.
- `Wt. OSA %` averages are demand-weighted by modelled gross.
- Product types are inferred from `Product Name` by a keyword classifier (`product_types.py`),
  so clean, descriptive names classify best. It's platform-agnostic — usually no edits needed.

## Questions
Anything unclear about the format — send a sample of a few rows and we'll sanity-check it before
you do the full export.
