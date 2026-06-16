---
phase: 14-homicide-as-a-first-class-category
verified: 2026-06-16T12:00:00Z
status: verified
score: 2/2 must-haves verified
human_checks: 4/4 browser-verified by orchestrator 2026-06-16
overrides_applied: 0
human_verification:
  - test: "Click the 'Homicidios' chip on the map (/map/ or /es/mapa/), verify the choropleth recolors to the independent homicide scale (lighter teal for zero-homicide comunas, graduated color for the rest)"
    expected: "All 346 polygons update color; zero-homicide comunas show fillOpacity 0.25; non-zero comunas show graduated 5-level scale independent of the main crime-rate scale"
    why_human: "Client-side Leaflet layer recolor via applyStyleMap — cannot verify the visual output or the quantile break computation result without a browser"
  - test: "Click a commune polygon (e.g. Santiago) with the homicide chip active, open ResultPanel, verify the homicide section shows rate and count"
    expected: "Section 7 renders 'Homicide (2025)' / 'Homicidios (2025)', a rate like '9 per 100,000 inhab. (48 cases)', and 'Source: CEAD, subgroup 101 Life Crimes (2025)'"
    why_human: "ResultPanel data path fetches per-commune JSON at runtime in the browser — cannot execute that fetch and verify the rendered output without browser context"
  - test: "With the homicide chip active, verify the 7 family bars in the ResultPanel are still present and unchanged (regression guard for HOM-02)"
    expected: "PanelFamilyBars renders 7 bars (vida, robos_violentos, vif, drogas, armas, propiedad, incivilidades); no bar removed or reordered"
    why_human: "Visual regression — requires browser render"
  - test: "Click a rural commune (e.g. Cochamó, CUT 10202) and verify the homicide section renders 0 or 'no reported cases' — not a blank or error"
    expected: "Either '0 per 100,000 inhab. (0 cases)' or 'No reported cases — CEAD 2025'; never blank or JS error"
    why_human: "null-vs-0 invariant in featured_rates.homicidios is only observable when the panel fetches and renders a real low-crime commune"
---

# Phase 14: Homicide as a First-Class Category — Verification Report

**Phase Goal:** Expose the existing per-commune `homicidios` data as its own map filter/layer + commune-panel breakdown (currently folded inside "vida"/Life crimes).
**Verified:** 2026-06-16
**Status:** human_needed (automated checks PASS; 4 browser-render items require human UAT)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Requirements)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | HOM-01: homicidios selectable as independent map filter/choropleth layer with its own color scale, distinct from the "vida" family layer; pipeline emits homicide rate to map-payload for all 346 communes | VERIFIED | See artifact evidence below |
| 2 | HOM-02: commune detail panel shows a separate homicide rate + count (not just the vida aggregate), CEAD-attributed, bilingual EN/ES, null-vs-0 invariant preserved | VERIFIED | See artifact evidence below |

**Score:** 2/2 truths verified (automated code evidence)

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/cead/client.py` | `fetch_subgroup_batch()` with `grupo[]=101` | VERIFIED | Lines 135–181: function exists, `grupo[]` param confirmed (CEAD confirmed behavior: `subgrupo[]` silently returns zeros) |
| `data/cead/map-payload.json` | `hr` field on all 346 commune entries, payload < 30,720 bytes | VERIFIED | 346/346 entries have `hr` (non-null integers); payload = 29,993 bytes (under limit) |
| `data/cead/comunas/13101.json` | `featured_rates.homicidios` with 2005–2026 series; `featured_rates.homicidios_count` with counts | VERIFIED | Both keys present; `homicidios` has 22 year entries (2005–2026); `homicidios_count` has 22 year entries |
| `site/src/components/map/FiltersRow.tsx` | 8th chip `{ key: 'homicidios', familyIndex: null, featured: true }` | VERIFIED | Line 42: chip definition present with correct sentinel values |
| `site/src/components/map/ChoroplethLayer.ts` | `CommunaPayload.hr` field; `buildStyleMapFromHomicide()` function | VERIFIED | Lines 19 (`hr: number | null`), 120–138 (`buildStyleMapFromHomicide` reads `c.hr`, quantile on non-zero rates) |
| `site/src/components/map/MapIsland.tsx` | `crimeIsHomicide` state; three-way branch in chip and year effects | VERIFIED | Line 100 (`crimeIsHomicide` state); lines 265–271, 292–298 (three-way branch: homicide → family → level); line 410 (`setCrimeIsHomicide(key === 'homicidios')`) |
| `site/src/components/map/ResultPanel.tsx` | Section 7 homicide breakdown, reads `featured_rates.homicidios` + `homicidios_count`, bilingual, CEAD-attributed | VERIFIED | Lines 318–351: section present, reads both keys with `!== undefined` (not truthiness) guard, renders rate + count, EN/ES strings, CEAD attribution |
| `site/scripts/validate/map.mjs` | Check 8 (`hr` in payload) + Check 9 (13101.json non-empty homicidios) | VERIFIED | Lines 254–295: both checks implemented, assert on committed data assets |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `FiltersRow` chip click | `MapIsland.crimeIsHomicide` | `onFamilyChange(key, idx) → setCrimeIsHomicide(key === 'homicidios')` | WIRED | MapIsland.tsx line 405–411 |
| `crimeIsHomicide` state | `buildStyleMapFromHomicide()` | Crime-chip effect (lines 285–301) and year effect (lines 263–274) | WIRED | Both effects have the three-way branch |
| `buildStyleMapFromHomicide` | `c.hr` field | `comunas.map(c => c.hr ?? 0)` | WIRED | ChoroplethLayer.ts line 123 |
| `data/cead/map-payload.json` | `hr` values | Pipeline `scrape_cead.py` → emits `hr: int|null` per commune | WIRED | Confirmed by live data: 346/346 non-null |
| `ResultPanel` | `featured_rates.homicidios` + `homicidios_count` | Fetches `/data/cead/comunas/{cut}.json`, reads both keys | WIRED | Lines 320–324; data confirmed in 13101.json |
| 7 `by_family` bars | `PanelFamilyBars` | `byFamilyArray` still 7-element; homicide section is additive (section 7, after bars) | WIRED | ResultPanel line 315 + 318; no by_family array change |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `ChoroplethLayer.buildStyleMapFromHomicide` | `c.hr` | `data/cead/map-payload.json` → `payload.comunas[].hr` | Yes — 346/346 non-null integers from CEAD subgroup-101 scrape | FLOWING |
| `ResultPanel` homicide section | `hom[String(year)]`, `homCount[String(year)]` | `/data/cead/comunas/{cut}.json` → `featured_rates.homicidios`, `homicidios_count` | Yes — 13101.json has 22 years of rate and count data | FLOWING |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 346/346 communes have non-null `hr` in payload | `node -e` inspect map-payload.json | `non-null hr: 346, missing: 0, total: 346` | PASS |
| Payload stays under 30,720 byte limit | `Buffer.byteLength(JSON.stringify(p))` | `29,993 bytes` | PASS |
| Santiago `hr` value plausible (single-digit homicide rate) | `comunas.find(c => c.id === '13101').hr` | `9` (vs expected ~5–12/100k) | PASS |
| Santiago `featured_rates.homicidios` non-empty | Read 13101.json | 22 year entries (2005–2026) | PASS |
| Santiago `homicidios_count` 2023 = 48 | Read 13101.json | `"2023": 48` | PASS |
| `fetch_subgroup_batch` uses `grupo[]` (not `subgrupo[]`) | Read client.py line 167 | `"grupo[]": str(subgrupo_id)` with comment confirming | PASS |
| 8th chip has `familyIndex: null` (homicide sentinel) | Read FiltersRow.tsx line 42 | `{ key: 'homicidios', familyIndex: null, featured: true }` | PASS |
| Three-way choropleth branch in both effects | Read MapIsland.tsx lines 265, 292 | `if (crimeIsHomicide)` → `buildStyleMapFromHomicide` in chip AND year effects | PASS |
| 7-element `by_family` contract untouched | Read ChoroplethLayer.ts interface | `by_family: number[]` unchanged; `hr` is a SEPARATE field | PASS |
| Homicide section uses `!== undefined` guard (not truthiness) | Read ResultPanel.tsx line 323 | `hom[String(year)] !== undefined` — correct null-vs-0 handling | PASS |

---

## Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| HOM-01 | `homicidios` selectable as filter/layer with independent choropleth; pipeline emits rate to map-payload | SATISFIED | `hr` field in 346/346 payload entries; `buildStyleMapFromHomicide` function; 8th chip; `crimeIsHomicide` state branch |
| HOM-02 | Commune panel shows separate homicide figure (not just vida aggregate), CEAD-attributed, bilingual, null-vs-0 correct | SATISFIED | ResultPanel section 7 (lines 318–351); reads `homicidios` + `homicidios_count`; EN/ES strings; `!== undefined` guard |

---

## Anti-Patterns Found

No blockers detected. Scanned `client.py`, `MapIsland.tsx`, `ChoroplethLayer.ts`, `FiltersRow.tsx`, `ResultPanel.tsx`:

- No `TBD`, `FIXME`, or `XXX` markers in any of the above files.
- No empty handlers or placeholder returns.
- `homicide_count` intentionally omitted from map-payload (payload budget decision D-09 — count is read from per-commune JSON by ResultPanel; this is the documented design, not a stub).

---

## Human Verification Required

### 1. Homicide Choropleth Recolor

**Test:** On `/map/` (EN) or `/es/mapa/` (ES), click the "Homicide" / "Homicidios" chip.
**Expected:** All 346 polygons recolor to an independent homicide scale; zero-homicide communes render noticeably lighter (fillOpacity 0.25 vs 0.55); the scale is NOT the same as the main crime-rate or vida-family scale.
**Why human:** Client-side `applyStyleMap` executes in the browser; quantile break output and visual differentiation cannot be verified without rendering.

### 2. ResultPanel Homicide Section — Data-Rich Commune

**Test:** With the homicide chip active, click Santiago (or any high-traffic commune). Wait for the ResultPanel to open.
**Expected:** Section "Homicide (2025)" / "Homicidios (2025)" renders with a rate like "9 per 100,000 inhab. (48 cases)" (values may differ by selected year) and "Source: CEAD, subgroup 101 Life Crimes (2025)".
**Why human:** `ResultPanel` fetches `/data/cead/comunas/{cut}.json` at runtime in the browser; the rendered output requires browser execution.

### 3. ResultPanel Family Bars Regression

**Test:** With any commune panel open (homicide chip active or not), verify the "Incidence by category" section still shows exactly 7 colored bars.
**Expected:** 7 bars (vida, robos violentos, VIF, drogas, armas, propiedad, incivilidades) present; no bar removed, added, or reordered; homicide section appears BELOW the family bars as a separate section.
**Why human:** Visual regression — PanelFamilyBars render requires browser.

### 4. ResultPanel Homicide Section — Zero-Case Commune

**Test:** Click a rural commune expected to have 0 or very few homicide cases (e.g. Cochamó or a small Patagonian commune). Open the panel.
**Expected:** Section renders "No reported cases — CEAD 2025" / "Sin casos reportados — CEAD 2025" — NOT blank, NOT a JS error, NOT "0 per 100,000 inhab." if CEAD returned zero (the `!== undefined` guard must distinguish actual zero from missing year).
**Why human:** Edge-case rendering path for null/absent year keys — only exercisable in browser with real commune data.

---

## Gaps Summary

No gaps. All automated evidence points to full implementation of HOM-01 and HOM-02.

The phase-context claim that homicide_count was intentionally excluded from the map-payload (`hr` only, no `homicide_count` in payload) is confirmed correct: `CommunaPayload.homicide_count` exists as a TypeScript field with comment "dropped from map-payload per budget; read from per-commune JSON" — the count is correctly read from `featured_rates.homicidios_count` in the per-commune JSON by ResultPanel.

The only open items are 4 visual/behavioral checks that require a real browser render to confirm end-to-end wiring beyond what static code analysis can verify.

---

_Verified: 2026-06-16_
_Verifier: Claude (gsd-verifier)_

---

## Orchestrator Browser Verification (2026-06-16) — all 4 human checks CLOSED

Performed live against `npm run dev` (localhost:4321) via BrowserOS. 0 console errors throughout.

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Homicide choropleth recolor | ✅ PASS | Clicked the Homicide chip on `/map/`; all polygons recolored to the independent homicide quantile scale — legend brackets switch to single-digit per-100k values (`0–4.464 … 7.121+`), distinct from the family scale (thousands). Zero/low communes render faded (0.25 opacity). Screenshot: `hom_choropleth.png`. |
| 2 | ResultPanel rate+count (data-rich) | ✅ PASS | `/map/?cut=13101` (Santiago): "Homicide (2025) — 9 per 100,000 inhab. (48 cases) — Source: CEAD, subgroup 101 Life Crimes (2025)". ES `/es/mapa/?cut=13101`: "Homicidios (2025) — 9 por 100.000 hab. (48 casos) — Fuente: CEAD, subgrupo 101 Delitos contra la Vida (2025)". |
| 3 | 7 family bars regression | ✅ PASS | Family bars (Life/Property/Violent robbery/Disorder/Domestic violence/Drug/Weapons) render above the additive homicide section; none removed/reordered. |
| 4 | Zero-case commune (null-vs-0) | ✅ PASS | `/map/?cut=10103` (Cochamó, confirmed 0 in data): renders "Homicide (2025) — 0 per 100,000 inhab. (0 cases)". This is the **confirmed-zero** path (year key present, value 0) — correctly distinct from the absent-data path ("No reported cases"). The `!== undefined` guard works: a real 0 shows as 0, not as "no data". |

**Status upgraded: human_needed → verified.** Both HOM-01 and HOM-02 are achieved and browser-confirmed end-to-end.
