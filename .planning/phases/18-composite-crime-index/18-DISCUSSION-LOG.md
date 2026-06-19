# Phase 18: Composite Crime Index - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-19
**Phase:** 18-composite-crime-index
**Areas discussed:** Index method & weights, SII exposure adjustment, Choropleth toggle UX, Editorial framing & bands

---

## Index Method (normalization)

| Option | Description | Selected |
|--------|-------------|----------|
| Winsorized min-max | scipy winsorize(limits=[0.01,0.01]) then min-max; keeps real spacing, clips 1% tails | ✓ |
| Percentile-rank | Rank 0–100; outlier-immune but loses magnitude | |
| You decide | Let planning run distribution check and pick | |

**User's choice:** Winsorized min-max (Recommended)
**Notes:** Adds scipy dep; guarded by pytest spread assertion (25th pct > 10% of max).

## Metric Weights

| Option | Description | Selected |
|--------|-------------|----------|
| Severity-weighted | Homicide 0.30 highest → violent → property → incivilidades | ✓ |
| Equal weights | All 7 families 1/7 | |
| You decide | Planning proposes vector for review | |

**User's choice:** Severity-weighted (Recommended)
**Notes:** Exact vector to be documented in composite_config.py + methodology; 0.30 homicide is the anchor.

---

## SII Exposure Adjustment

| Option | Description | Selected |
|--------|-------------|----------|
| Apply with cap fallback | SII denominator; fall back to INE pop when ratio exceeds threshold | ✓ |
| Apply, no cap | Pure SII denominator everywhere | |
| Defer SII to v3 | INE population only this phase | |

**User's choice:** Apply with cap fallback (Recommended)

## SII Cap Threshold

| Option | Description | Selected |
|--------|-------------|----------|
| 5.0 | Earlier fallback, more conservative | ✓ |
| 10.0 | Only extreme business-district cases fall back | |
| You decide | Pick after inspecting ratio distribution | |

**User's choice:** 5.0 (Recommended)
**Notes:** Planning may confirm placement against actual 346-commune ratio distribution.

---

## Choropleth Toggle (default mode)

| Option | Description | Selected |
|--------|-------------|----------|
| Composite index | Lead with new 0–100 index; toggle to rate mode | ✓ |
| Per-family rate (current) | Keep current default; index opt-in | |
| You decide | Pick once palette/bands wired | |

**User's choice:** Composite index (Recommended)
**Notes:** Popup shows exact integer + band in index mode.

---

## Editorial Framing (caveat block)

| Option | Description | Selected |
|--------|-------------|----------|
| Always-visible block | Inline, never collapsed, on every surface | ✓ |
| Expandable 'How is this calculated?' | Short line + click-to-expand | |
| You decide | Per-surface during UI design | |

**User's choice:** Always-visible block (Recommended)

## Band Labels & Precision

| Option | Description | Selected |
|--------|-------------|----------|
| Standard 5 bands + integer | Very Low…Very High / Muy Bajo…Muy Alto; integer headlines, 1 decimal per-family | ✓ |
| Adjust wording | Different band labels | |
| You decide | Lock standard now, revisit in UI | |

**User's choice:** Standard 5 bands + integer (Recommended)

## Reference Year Alignment

| Option | Description | Selected |
|--------|-------------|----------|
| Latest fully-consolidated, ≤2024 | All three sources final; pipeline assertion | ✓ |
| Latest available per source | Freshest but mixes vintages | |

**User's choice:** Latest fully-consolidated, ≤2024 (Recommended)
**Notes:** Partial 2025 SPD VHC never used.

---

## Claude's Discretion

- Exact severity weight vector (planning proposes for review; 0.30 homicide anchor).
- Map-payload `ci` field encoding (level 1–5; omitted pre-2018).
- `comparator_table.json` exact schema (must carry composite_index for Phase 21).

## Deferred Ideas

- Weight sliders, confidence intervals, real-time updates, star ratings → v3+.
- Comparator island + A-vs-B SEO pages → Phase 21.
- Go-live / deploy / GSC / AdSense + Consent Mode → Phase 22 (AdSense deferred even there).
- Reviewed-not-folded todo: `adsense-consent-mode-phase6.md` (out of v2.0 scope).
