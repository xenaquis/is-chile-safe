# Phase 18: Composite Crime Index - Context

**Gathered:** 2026-06-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver an exposure-adjusted **0–100 composite crime-exposure index per comuna**, computed from 7 hardened metrics, surfaced in the map choropleth (toggle), the popup, the ResultPanel, and commune pages — each accompanied by a mandatory bilingual caveat block and never an absolute safety verdict. Schema migration is additive/non-breaking; `comparator_table.json` is emitted as the Phase 21 input.

**In scope:** index computation (`build_composite_index.py`), normalization, weighting, SII exposure adjustment, SPD VHC homicide input, additive schema migration + TS types, choropleth toggle, index display in popup/panel/commune pages with national+regional rank, mandatory caveat block, forbidden-language validator extension, methodology page updates + figure registry, `comparator_table.json`.

**Out of scope (other phases / deferred):** comparator island + A-vs-B SEO pages (Phase 21), go-live/deploy/GSC/AdSense (Phase 22), user-configurable weight sliders, confidence intervals/error bars, real-time updates, star ratings (v3+).

</domain>

<decisions>
## Implementation Decisions

### Index Method & Weights
- **D-01:** Normalization = **winsorized min-max** via `scipy.stats.mstats.winsorize(limits=[0.01, 0.01])` then min-max. Preserves real spacing between communes; clips only the extreme 1% tails (e.g. Sierra Gorda 43,369/100k). Adds `scipy>=1.13,<2` to `pipeline/requirements.txt`. Guard with the pytest spread assertion: `index_scores.describe()["25%"] > index_scores.max() * 0.10`.
- **D-02:** Weights = **severity-weighted**, not equal. Homicide highest (0.30 recommended starting point), then violent families, then property, then incivilidades. Exact weight vector lives in a `composite_config.py` (or equivalent) and MUST be documented in `data/SOURCES.md` + both methodology pages. (Equal weights explicitly rejected — would equate a homicide with graffiti.)

### SII Exposure Adjustment
- **D-03:** **Apply** the SII economic-activity denominator (the key v2.0 differentiator) with a **cap fallback**: when `sii_workers / ine_population > 5.0`, fall back to INE population as the denominator. Prevents firm-HQ-domicile distortion for business-district communes (Las Condes, Santiago Centro). (SII deferral to v3 rejected.)
- **D-04:** Cap threshold value = **5.0** (the more conservative of the 5.0/10.0 candidates). Planning may inspect the actual `sii_workers/ine_population` ratio distribution across 346 communes to confirm 5.0 is well-placed, but 5.0 is the locked default.

### Choropleth Toggle UX
- **D-05:** **Composite index mode loads by default**; the toggle switches to the existing per-family rate mode. The index is the headline v2.0 feature and the cleanest single-number story for first-time visitors. Both modes use the existing 5-level palette via `chroma-js` + `L.geoJSON()`.
- **D-06:** Popup shows the **exact integer 0–100 score** plus its band label when in index mode.

### Editorial Framing & Bands
- **D-07:** Caveat block = **always-visible inline**, never collapsed, on every index-displaying surface (popup, ResultPanel, commune page). Discloses: composite of *reported* crime burden, the sources, data vintage, and the SII firm-domicile limitation. Bilingual (EN + ES). Strongest defense against the index reading as an absolute verdict.
- **D-08:** Band labels = standard 5 bands. EN: **Very Low / Low / Moderate / High / Very High**; ES: **Muy Bajo / Bajo / Moderado / Alto / Muy Alto**.
- **D-09:** Display precision = **integer 0–100 in all headline contexts**; one decimal only in per-family comparator rows (Phase 21 consumer).

### Reference Year Alignment
- **D-10:** Index anchors to the **latest fully-consolidated year where SPD VHC + CEAD + SII are ALL final (≤ 2024)**. A pipeline assertion enforces all-three-available; partial/unconsolidated 2025 SPD VHC data is never used. CEAD grupo-101 `featured_rates.homicidios` is preserved unchanged; SPD VHC is the index homicide input (M5).

### Pipeline Isolation (carried from research — locked)
- **D-11:** `build_composite_index.py` runs as an **isolated step after the CEAD scraper and before `build_map_payload.py`** (the latter extracted from `scrape_cead.py`). If the index step fails, CEAD data still refreshes. Three-step GitHub Actions order: scrape → index → payload.

### Schema Migration (carried from research — locked)
- **D-12:** Migration is **additive and non-breaking**: existing `featured_rates` fields remain intact; new fields (`composite_index`, `spd_homicide_rate`, `sii_exposure_index`) added alongside with optional TypeScript types. Every consumer (commune panel, choropleth, Astro templates, figure-registry validator, pytest) must be enumerated and verified; `@astrojs/check` + full validator suite must pass green.

### Claude's Discretion
- Exact severity weight vector numbers (D-02 gives 0.30 homicide as the anchor; planning proposes the full vector for user review before lock).
- Map-payload `ci` field encoding (level 1–5; omitted for pre-2018 years) — research-recommended, planner finalizes.
- `comparator_table.json` exact schema/field set (must carry `composite_index` per commune for Phase 21).

### Reviewed Todos (not folded)
- `adsense-consent-mode-phase6.md` — matched on generic keywords only; AdSense + Consent Mode are explicitly **deferred out of v2.0** (Phase 22 note). Not folded into Phase 18.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### v2.0 Research (primary — read first)
- `.planning/research/SUMMARY.md` — executive synthesis; "Key decisions to lock in Phase 18 planning" section maps 1:1 to decisions above.
- `.planning/research/PITFALLS.md` — all 8 composite-index pitfalls (CI-1..CI-8); normalization-collapse, verdict-by-IA, schema-break consumers.
- `.planning/research/ARCHITECTURE.md` — pipeline isolation, file schemas, integration points, additive migration plan.
- `.planning/research/STACK.md` — scipy addition; confirms no scikit-learn / D3 / react-leaflet GeoJSON component / state manager.
- `.planning/research/FEATURES.md` — must-have feature list for Track 1, defer list for v3+.

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` §CI-01..CI-10 — the 10 locked requirements for this phase.
- `.planning/ROADMAP.md` → "Phase 18: Composite Crime Index" — goal + 5 success criteria.

### Data sources & methodology
- `data/SOURCES.md` — canonical source registry; normalization method + weight vector + SPD switch + SII caveat MUST be documented here.
- `site/src/pages/methodology.astro` (EN) + `site/src/pages/es/metodologia.astro` (ES) — must document composite formula, normalization method, SPD VHC homicide switch, SII exposure caveat; every new figure registered (figure-registry zero-orphan).
- `data/snapshots/spd_homicide.json` — SPD VHC homicide input (M5); note 2025 partial-data caveat.
- `data/snapshots/sii_exposure.json` — SII economic-activity exposure denominator; HQ-domicile caveat.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `site/src/components/map/ChoroplethLayer.ts` — existing `L.geoJSON()` + chroma-js choropleth; extend with a `ci` field on `CommunaPayload` and a `buildStyleMapFromCompositeIndex()` for the index-mode toggle (reuse 5-level palette).
- `site/src/components/map/ResultPanel.tsx` — commune detail panel; add index score + band + national/regional rank + caveat block here.
- `pipeline/cead/normalizer.py` — `CHIP_DEFS` ordering (0=vida..6=incivilidades) is the canonical 7-family taxonomy the index weights map onto.
- `pipeline/scrape_cead.py` — `build_map_payload.py` is to be **extracted** from this (do not break the stable scraper).

### Established Patterns
- Additive, backward-compatible JSON schema evolution (pydantic 2.x validation) — existing `featured_rates` stays; new fields added alongside.
- Forbidden-language CI validator (from P20) — extend to flag "safest / most dangerous / más segura / más peligrosa" unless qualified by "reported / reportado".
- Figure-registry zero-orphan validator — every new methodology figure must register.

### Integration Points
- Pipeline order (GitHub Actions): CEAD scrape → `build_composite_index.py` (NEW, isolated) → `build_map_payload.py` (extracted) → emits `map-payload*.json` (+`ci`) and `data/cead/comparator_table.json`.
- Schema migration consumers to verify non-breaking: commune panel, choropleth, Astro templates, figure-registry validator, pytest assertions.
- `comparator_table.json` is the hard handoff to Phase 21 (comparator + A-vs-B).

</code_context>

<specifics>
## Specific Ideas

- Index is the **lead/default** map view, not opt-in — the v2.0 headline.
- Caveat is **always visible**, never behind an expander — editorial-risk-first posture.
- Conservative on SII distortion (cap 5.0) and on data vintage (≤2024, never partial 2025).

</specifics>

<deferred>
## Deferred Ideas

- User-configurable weight sliders — incompatible with static pre-rendering + false-precision risk (v3+).
- Confidence intervals / error bars — confuses lay users; CEAD error is systematic not random (v3+).
- Real-time index updates, star ratings — out of v2.0 (v3+).
- Comparator island + A-vs-B SEO pages — **Phase 21** (consumes `comparator_table.json` + `composite_index`).
- Go-live / deploy hook / GSC / AdSense + Consent Mode — **Phase 22** (AdSense explicitly deferred even there).

</deferred>

---

*Phase: 18-composite-crime-index*
*Context gathered: 2026-06-19*
