# Metrics & Insights Spec — Blinkit RCA Dashboard

This is the reference for **what the data measures** and **what insights can be
built from it**. It is the backlog and definition layer behind `dashboard.html` /
`index.html`. See `CLAUDE.md` for the build pipeline and the ₹-sales model.

Data state: **2 monthly snapshots** (2026-03-01 → 2026-04-01) × **~3,000 SKUs**
across 5 sub-categories (Kitchen & Dining, Home Decor, Bathroom Essentials,
Cleaning Tools, Home Improvement). One row = one SKU in one month.

---

## 1. Metric foundation (what we actually have)

Coverage = % of rows with a non-null value (latest month).

| Metric | Coverage | Meaning / definition | Notes |
|---|---|---|---|
| **Est. Category Share** | 100% | Estimated share of category **volume/offtake**; sums to 100% per sub-cat/month | **demand proxy** |
| **Est. Category Share SP** | 99.8% | Estimated share of category **value at SP**; sums to 100% | **revenue proxy** — use for ₹ |
| **Overall SOV** | 78.6% | Share of Voice (visibility); sums to 100% per sub-cat | not = Org+Ad |
| **Organic SOV** | 78.6% | Unpaid visibility | sums to 100% |
| **Ad SOV** | 78.6% | Paid visibility | sums to 100% |
| **Wt. OSA %** | 99.8% | Weighted On-Shelf Availability (in-stock %) | mean **34.8%**; **55% of SKUs < 40%** |
| **SP** | 97.6% | Selling price (₹) | |
| **MRP** | 97.6% | Max retail price (₹) | |
| **Wt. Discount %** | 97.6% | (MRP−SP)/MRP weighted | median **40%**, p75 **55%** |
| **Wt. PPU (x100)** | 97.6% | Price per **single unit** = SP / pack count | normalizes across pack sizes — **currently unused** |
| **Grammage** | 100% | Pack/size label, e.g. "2 pcs" | **106 distinct values — unused** |
| **Brand** | 100% | Brand (casing inconsistent → normalise via lowercase key) | |
| **Product ID** | 100% | SKU id | enables entrant/exit tracking across months |
| Item ID / Offtake MRP / Offtake SP / Units | ~0% | **Empty** | no native ₹/units → drives the entered-MRP sales model |

### The ₹-sales model (already built)
No native revenue/units. The user enters total **MRP sales per sub-category**
(≈ ₹122.6 Cr). Per sub-cat, that total is distributed across SKUs using
**Est. Category Share SP, SP, MRP** so that Σ gross MRP reconciles to the entered
total. Toggle: Net ₹ / Gross ₹ / Units. Validated: gross 122.6 Cr, net ≈ 68.2 Cr
(~56% realisation), ~2.44M units.

### Key signals found in the data (design around these)
- **corr(SOV, share) = 0.74** → visibility converts, but the *residuals* are the
  prize: over-converters (efficient) vs under-converters (waste).
- **25% of SKUs are ad-reliant** (Ad SOV > Organic SOV) → ad-dependency lens is supported.
- **55% of SKUs below 40% OSA** → availability is the biggest structural gap =
  richest white-space / lost-sales vein.

---

## 2. Insights already built (9 dashboard sections)

1. **KPIs** — SKUs, brands, sub-cats, avg OSA, avg discount, avg SP, period.
2. **₹-sales input + Overall view** — gross/net/units/realisation, sales by sub-cat,
   top brands across the full brand universe.
3. **Market structure by sub-cat** — SKU/brand counts, avg OSA/disc/SP,
   **top-5 concentration**, **HHI**.
4. **Top SKUs** (product-wise, per sub-cat) by category share.
5. **Brand leaderboard** — share %, SOV %, OSA, discount, # SKUs, # sub-cats, MoM Δ.
6. **SOV vs Share scatter** — visibility vs conversion for top brands.
7. **Product types** — ~130 keyword-classified types; top types, sales-split, detail table.
8. **MoM momentum** — brand share gainers/losers.
9. **White spaces** — unmet-demand SKUs (high SOV + low OSA), SOV×OSA quadrant,
   category fragmentation + stockout demand.

---

## 3. Insight backlog (new — derivable from existing columns, no new data)

Each item notes the **signal**, the **formula**, and the **build surface**
(new aggregation in `build_dashboard_data.py` + a template section).

### P1 — Lost-sales from stockouts (₹)  ·  highest business impact
- **Signal:** 55% of SKUs < 40% OSA, while demand (share/SOV) exists.
- **Idea:** quantify revenue left on the table where demand is high but availability
  is low. Combine the entered ₹ model with the OSA gap.
- **Formula (per SKU):** `lost_₹ ≈ realized_₹ × (target_OSA − OSA) / OSA`, capped at
  a sensible target (e.g. 80–90%); aggregate by sub-cat, brand, product type.
- **Why:** turns the white-space section from descriptive → quantified ₹ at risk.

### P2 — Conversion efficiency  ·  strong competitive lens, low effort
- **Signal:** corr(SOV, share)=0.74; residuals identify winners/wasters.
- **Formula:** `efficiency = Est. Category Share / Overall SOV` per SKU/brand.
  >1 = converts above its visibility; <1 = visible but not converting.
- **Surface:** ranked tables (top over-converters / under-converters) + colour the
  existing SOV-vs-share scatter by efficiency.

### P3 — Ad-dependency (organic vs paid)  ·  low effort
- **Signal:** 25% ad-reliant.
- **Formulas:** `ad_dependency = Ad SOV / (Organic SOV + Ad SOV)` per brand;
  flag **"paying but not converting"** = high Ad SOV + low share (wasted spend),
  and **"organic champions"** = high share + low Ad SOV (defensible).
- **Surface:** brand table + organic-vs-paid scatter.

### P4 — Price-band analysis  ·  medium effort
- **Signal:** SP ranges 24 → 7,538, median 507 — real tiering.
- **Idea:** bucket SP into entry / mid / premium (per sub-cat quantiles) and show
  where **demand (share)** and **₹** concentrate; spot empty/underserved bands.
- **Surface:** stacked bars per sub-cat (share & ₹ by price band).

### P5 — Pack-size / PPU architecture  ·  medium effort
- **Signal:** 106 grammages + Wt. PPU both unused.
- **Idea:** which pack sizes own demand; true value-for-money (PPU) across packs;
  flag SKUs that are expensive per unit despite a low headline price.
- **Surface:** pack-mix bars + PPU benchmarks by product type.

### P6 — SKU-level momentum & entrants/exits  ·  medium effort
- **Signal:** two months + stable Product IDs.
- **Ideas:** SKU share risers/fallers (today only brand-level); **new entrants vs
  exited SKUs** (Product ID set diff across months); **OSA MoM** (improving/worsening
  availability); **discount MoM** (deepening promos); **price changes MoM**.
- **Surface:** extend the MoM section with SKU-level + entrant/exit tables.

### P7 — Promo-dependency / pricing power  ·  low effort
- **Signal:** discount median 40%, p75 55%.
- **Idea:** SKUs/brands holding share at **low** discount (pricing power) vs those
  whose share rides on **deep** discounts (promo-dependent / margin-fragile).
- **Surface:** discount-vs-share scatter + flagged tables.

---

## 4. Recommended build order
P1 (lost-sales ₹) → P2 (conversion efficiency) → P3 (ad-dependency) →
P7 (promo-dependency) → P4 (price bands) → P5 (pack/PPU) → P6 (SKU momentum).

Rationale: P1 is the biggest "so what" (₹ at risk) and reuses the sales model;
P2/P3/P7 are low-effort, high-signal competitive lenses; P4/P5 open new dimensions;
P6 deepens trends and grows naturally as more monthly snapshots arrive.

## 5. Dependencies & caveats
- SOV metrics cover ~79% of SKUs — exclude nulls; note coverage on SOV-based views.
- All ₹/units insights inherit the entered-MRP model — they are **estimates**, label them so.
- Lost-sales (P1) needs a `target_OSA` assumption — make it a dashboard input, like the MRP totals.
- A **6th category** was mentioned but never provided — re-run the pipeline if it arrives.
- More monthly snapshots will make P6 (momentum) and ₹-growth far stronger.
