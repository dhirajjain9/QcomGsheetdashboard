# Metrics & Insights Spec — Blinkit RCA Dashboard

Reference for **what the data measures**, **how the scores are built**, and the
**remaining backlog**. See `CLAUDE.md` for the build pipeline and ₹-sales model.

Data state: **2 monthly snapshots** (2026-03-01 → 2026-04-01) × **~3,000 SKUs**
across 5 sub-categories (Kitchen & Dining, Home Decor, Bathroom Essentials,
Cleaning Tools, Home Improvement). Strategic views use **April only** (see P-Time).

---

## 1. Metric foundation (what we actually have)

Coverage = % of rows with a non-null value (latest month).

| Metric | Coverage | Meaning | Notes |
|---|---|---|---|
| **Est. Category Share** | 100% | share of category **volume**; sums to 100%/sub-cat | demand proxy (volume) |
| **Est. Category Share SP** | 99.8% | share of category **value at SP**; sums to 100% | **revenue proxy** (used for ₹) |
| **Overall / Organic / Ad SOV** | 78.6% | Share of Voice (visibility); each sums to 100%/sub-cat | Overall ≠ Org+Ad |
| **Wt. OSA %** | 99.8% | weighted On-Shelf Availability | mean **34.8%**; **55% of SKUs < 40%** |
| **SP / MRP / Wt. Discount %** | 97.6% | price / list / depth | discount median 40%, p75 55% |
| **Wt. PPU (x100)** | 97.6% | price per single unit | **still unused** (see P-Pack) |
| **Grammage** | 100% | pack/size label | 106 distinct values — **still unused** |
| **Brand / Product ID** | 100% | identity | Product ID enables entrant/exit tracking |
| Item ID / Offtake / Units | ~0% | **empty** | no native ₹/units → entered-MRP sales model |

**₹-sales model:** user enters total **MRP sales per sub-category** (≈ ₹122.6 Cr,
pre-filled & saved per device). Distributed across SKUs via Est. Category Share SP,
SP, MRP so Σ gross MRP reconciles to the entered total. **Show toggle defaults to
Gross (MRP)**; also Net (SP, ~56% realisation ≈ ₹68 Cr) and Units (~2.44M). Avg gross
≈ ₹4.1 L/SKU/month.

**Key signals:** corr(SOV, share) ≈ 0.74; ~25% of SKUs ad-reliant; 55% below 40% OSA.

---

## 2. Scoring methodology (current, in `lpTypeAgg`)

**Opportunity (Founder's Launchpad)** — per product type, scope-aware:
```
Opportunity = 100 × (0.50·Demand + 0.30·WhiteSpace + 0.20·AvailabilityGap) × demand-gate
```
weights tunable via sliders; demand-gate ≈ min(1, demandN/0.03) drops no-demand types.

- **Demand** = total sales of the type (₹ when entered, else value-share), normalised to scope max.
- **White space = √(under-served × beatable-leader)** — needs *both*:
  - **under-served** = demand per SKU, capped at ~p90 (thin assortment for the demand).
  - **beatable-leader** = 1 − **organic moat**, where organic moat = maxₚ share × (1 − ad-reliance),
    ad-reliance = Ad SOV / (Ad SOV + Organic SOV). Ad-propped share is discounted (rented visibility fades).
- **Availability gap** = 1 − sales-weighted OSA.

**Remark buckets** (per type, on the white-space drivers): *Organic fortress* (organically
entrenched leader), *Rented crown* (dominant but ad-propped → beatable), *Prime white space*
(under-served + un-dominated), *Crowded shelf* (saturated), *Open & contested*.

**Rev/SKU benchmark** = revenue per SKU vs the scope average (▲ higher / ▼ lower, ×avg).

---

## 3. What's in the dashboard now

KPIs · ₹-sales input · **Overall view** · **Market structure** (HHI, top-5) · **Top SKUs**
· **Brands** (leaderboard + visibility-vs-conversion, scope-aware, % of total) · **Product
types** (top-40 bar+donut, detail table w/ Rev/SKU, By-SKU/By-Brand drill-down) · **🚀
Founder's Launchpad** (opportunity map + ranking with remarks, price ladder, competitor
teardown w/ ad-reliance flags, launch shortlist) · **White spaces** (white-space map, bucket
breakdown, leaderboard w/ Rev/SKU) · **Availability & stockout loss** (est. ₹ lost, demand-
vs-availability map, biggest losses) · **Month-over-month** (SKU risers/fallers + entry/exit;
brand and product-type entry/exit per category; brand churn within a product type).

Scope selector (All categories default) drives SKUs/Brands/Product types. Interactivity:
drill-down modals, sortable tables with frozen headers, section nav, persisted MRP inputs,
neutral cream theme.

---

## 4. Open backlog (derivable from existing columns, no new data)

### Price-band tiering — **backend ready, frontend pending** · medium effort
**P5 backend is built:** `sku_level` now carries `ppu` (₹/unit), `pack` (count = SP÷PPU) and
`gram` (grammage) — so value can be compared per-unit, not by misleading headline SP (~30% of
SKUs are multipacks; in types like Drinking Glass / Tea Light Candle / Storage Container the
majority are). **Remaining (frontend):** a per-sub-category price-architecture view — bucket SKUs
into entry/mid/premium/luxury bands **on PPU**, showing demand / ₹ / supply (SKU & brand count) /
typical discount per band → under-served price bands + the price points to attack. Plus optional
pack-mix and PPU-value benchmarks by type.

_Decided / not pursuing: P7 (promo-dependency) and time-basis (**April-only is permanent**)._

---

## 5. Done / folded in (for the record)
- **Lost-sales from stockouts (₹)** → *Availability & stockout-loss* section (75% target assumption).
- **Ad-dependency (organic vs paid)** → baked into white space (organic-beatable) + competitor
  "renting visibility" flags. *Optional remainder:* a standalone brand ad-dependency scatter.
- **Competitive / white-space definition** → finalised as √(under-served × organic-beatable) with remark buckets.
- **P6 — month-over-month** → built: SKU risers/fallers + entry/exit, brand & product-type entry/exit per
  category, and brand churn within a product type. (Uses March; everything else stays April-only.)
- **Conversion efficiency (share ÷ SOV)** → dropped: already shown by the visibility-vs-conversion
  scatter (above/below the diagonal) and sharpened by the organic-vs-paid logic. If ever needed, add a
  sortable `share/SOV` column to the brand leaderboard (~10 min).

## 6. Dependencies & caveats
- SOV covers ~79% of SKUs — exclude nulls on SOV-based views.
- All ₹/units are **estimates** from the entered-MRP model; default basis is **Gross (MRP)**.
- Stockout lost-₹ uses a **75% target OSA** assumption (could be exposed as a slider).
- A **6th category** was mentioned but never provided — re-run the pipeline if it arrives.
- **Time basis is April-only by decision** (permanent); MoM is the only view that uses March.
