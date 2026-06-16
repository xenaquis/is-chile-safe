# Phase 14: Homicide as a First-Class Category - Context

**Gathered:** 2026-06-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Expose homicide (CEAD featured subgroup `101`, currently folded inside the
aggregated `vida`/Life-crimes family) as its own first-class crime type:

1. A selectable map **filter/layer** with its own choropleth.
2. A separate **commune-panel** homicide figure (rate + absolute count + year,
   CEAD-cited), distinct from the aggregated `vida` family.

**Scope expansion vs roadmap wording — confirmed in discussion:** the roadmap
says "expose the *existing* per-commune `homicidios` data," but that data does
**not exist**. `featured_rates.homicidios = {}` in all 346 comuna files;
`scrape_cead.py:448` hardcodes `"homicidios_by_year": {}` (CEAD subgroup-101
scrape never implemented — Phase-1 Open Question 3, deferred since Plan 03). The
scraper fetches only the 7 high-level families (`familia_id` 1–7) at rates-only
(`medida=2`). **Therefore Phase 14 includes the CEAD subgroup-101 data
acquisition** (scrape → populate data model → emit to payload) BEFORE the UI
work. This is in scope, not scope creep — the data is a hard prerequisite for
the roadmap goal.

**Out of scope:** the `secuestros` subgroup (still no confirmed subgroup ID);
crime-type SEO ranking pages (Phase 15, depends on this phase's data); the
Tarapacá `region_id` collision (backlog 999.1).

</domain>

<decisions>
## Implementation Decisions

### Data acquisition (the prerequisite)
- **D-01:** Scrape CEAD homicide subgroup `101` **in this phase**, then build
  the filter/layer/panel on top. Two-stage within the phase: data first, UI
  second.
- **D-02:** Pull the **full historical series (2005–2025), like the families** —
  store homicide into each comuna's `series` AND `featured_rates.homicidios_by_year`.
  Rationale: enables the homicide trend arrow, the panel breakdown, and feeds
  Phase 15's "comunas con más homicidios" SEO ranking pages without a second
  scrape.
- **D-03:** Fetch **both measures** for homicide: rate-per-100k (`medida=2`,
  existing) **and** absolute count (`medida=1`), even though it roughly doubles
  the homicide-subgroup request count. Required to honor the panel decision
  (D-07). Keep polite — reuse the existing inter-batch courtesy delays (D-03 of
  Phase 1). **Research checkpoint:** confirm live the exact CEAD param that
  selects subgroup 101 within the `vida` family (the current `fetch_communes_batch`
  only takes `familia_id`, not a subgroup selector) and whether count+rate come
  back in one response or need two requests.

### Filter UX
- **D-04:** Homicide appears as an **8th chip** in `FiltersRow.tsx`, alongside
  the 7 family chips, with the existing `featured` accent-dot treatment (like
  `vida`/`propiedad`). Discoverable, consistent with the current chip pattern.
  Note for planner: it is a *subgroup of `vida`*, not a sibling family — label
  honestly but placement is a peer chip.

### Choropleth
- **D-05:** The homicide layer gets an **independent color scale** — its own
  quantile/bucket breakpoints and its own legend computed when the homicide
  layer is active. Reason: homicide rates are an order of magnitude smaller than
  total/family rates (single digits vs hundreds /100k); reusing the shared
  5-bucket scale would collapse every comuna into the lowest 1–2 buckets and the
  map would read as uniform. **Research:** recommend the bucketing method
  (quantile vs jenks vs fixed) for a sparse, right-skewed, low-count distribution.

### Commune panel
- **D-06:** Add a separate homicide figure to the commune detail panel
  (`ResultPanel.tsx`), distinct from the aggregated `vida` family bar — no
  regression to existing family rendering (HOM-02).
- **D-07:** Panel shows **rate-per-100k + absolute case count + CEAD year**.
  Rationale: homicide is rare; many small comunas have 0 or very few cases where
  rate-per-100k is volatile and easily misread. Showing the raw count + year
  alongside the rate is the most honest framing and satisfies the editorial rule
  (never label "dangerous/safe"; always cite CEAD + year). A `0` / "no reported
  cases" state must be explicit and non-alarmist.

### Claude's Discretion
- Exact bucketing algorithm for D-05 (research-recommended).
- Whether the 8th chip reuses the `featured` flag path or a new field in
  `CHIP_DEFS` — planner's call, keep consistent with existing structure.
- Panel layout/placement of the homicide figure within `ResultPanel.tsx`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap / requirements
- `.planning/ROADMAP.md` §"Phase 14: Homicide as a First-Class Category" — goal,
  depends-on (Phase 10), success criteria, HOM-01/HOM-02.
- `.planning/REQUIREMENTS.md` HOM-01, HOM-02 (lines 37–38) — locked requirement text.

### Data pipeline (scrape + normalize — the prerequisite work)
- `pipeline/scrape_cead.py` — main runner; `homicidios_by_year: {}` hardcoded at
  line 448 (the gap to fill); `build_map_payload` (~line 96) emits the per-comuna
  `{id, rate, level, by_family}` records (needs a homicide slot); family fetch
  loop ~lines 343–366.
- `pipeline/cead/normalizer.py` — `FEATURED_SUBGROUPS = {"homicidios": 101, ...}`
  (line 26); `attach_featured` (~line 215) builds `featured_rates`.
- `pipeline/cead/client.py` — `fetch_communes_batch(session, cut_codes, year,
  familia_id)` (line 82); `medida='2'` rates-only, `tipoVal='1,2'`, `descarga='true'`
  (~lines 110+). Needs a subgroup-101 + `medida='1'` count path.
- `pipeline/cead/catalog.py` — `FAMILIA_IDS` (line 44); `get_commune_catalog`
  uses `ajax_2.php` `seleccion=101` (note: that `101` is the *catalog* selector,
  not the homicide rate — do not conflate).
- `data/cead/meta/catalog.json` — `featured_subgroups.homicidios = 101`,
  `family_keys` order (drives `by_family` array indexing).

### Map frontend (the UI work)
- `site/src/components/map/FiltersRow.tsx` — `CHIP_DEFS` array (the 8th chip goes
  here); `familyIndex` maps to `by_family` array position.
- `site/src/components/map/ResultPanel.tsx` — commune detail panel (homicide
  figure target).
- `site/src/components/map/PanelFamilyBars.tsx` — existing family-bar rendering
  (must not regress).
- `site/src/lib/familyDefs.ts` — family labels/defs EN+ES (add homicide
  label/def, both locales).
- `site/src/lib/data.ts` — map payload / commune data loading helpers.
- `data/cead/map-payload-*.json` — per-year payload; comuna entry shape
  `{id, rate, level, by_family[7]}` — needs a homicide value.

### Constraints / patterns to honor
- `CLAUDE.md` — editorial/legal constraint (never "peligroso/seguro"; cite CEAD +
  year); scraping courtesy (delays to gov server); i18n parity EN/ES; static
  pre-render for SEO.
- `.planning/STATE.md` Decisions — L.canvas renderer scoped to L.geoJSON layer
  (Pitfall 6); OneDrive `dist/` desync → chain build+validate in one command.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `FiltersRow.tsx` `CHIP_DEFS` + featured-dot rendering — extend with one chip
  entry; no new component needed for the filter.
- `attach_featured` / `featured_rates` schema already reserves a `homicidios` key
  (currently `{}`) — populate it rather than reshape the schema.
- The per-familia fetch+accumulate loop in `scrape_cead.py` is the template for
  the subgroup-101 fetch; `fetch_communes_batch` already handles batching,
  latin-1 decode, courtesy delays.
- Existing choropleth `level` bucketing logic in payload build — clone/parametrize
  for an independent homicide scale (D-05).

### Established Patterns
- `by_family` stored as an **ordered int array** matching `FAMILY_KEYS` (compact,
  <30KB budget). Homicide is a subgroup, not a family — decide whether it rides
  as an extra payload field (e.g. `homicide: {rate, count}`) rather than
  appended to `by_family` (which would break the family-index contract used by
  the chips). **Likely a separate payload field, not a `by_family[7]` append.**
- Bilingual everything: any new label/def needs EN + ES (`familyDefs.ts`, chip
  labels, panel strings).

### Integration Points
- Pipeline: `scrape_cead.py` (fetch + normalize + payload emit) → `data/cead/`
  JSON → `sync-data.mjs` mirror to `site/public/data` → map island fetch.
- Frontend: `FiltersRow` (select) → `MapIsland` (layer/choropleth swap) →
  `ResultPanel` (panel figure).
- Build validators: `site/scripts/validate/map.mjs` (+ others) likely need a new
  assertion that homicide data is present/keyed correctly — planner to confirm.

</code_context>

<specifics>
## Specific Ideas

- Homicide chip must read as the *featured* subgroup it is (accent-dot), but the
  honest taxonomy is "subgroup of vida" — wording/tooltip should not imply it's a
  parallel family to the other 7.
- Zero-homicide comunas: explicit "no reported cases" + year, never blank, never
  alarmist.

</specifics>

<deferred>
## Deferred Ideas

- **`secuestros` subgroup as a first-class category** — same pattern as homicide
  but the subgroup ID is still unconfirmed (`FEATURED_SUBGROUPS["secuestros"] = None`).
  Out of scope for Phase 14; candidate for a future phase if/when the ID is confirmed.
- **Crime-type SEO ranking pages for homicide** ("las N comunas con más
  homicidios") — explicitly Phase 15 (CSEO-01/02), depends on this phase's data.

### Reviewed Todos (not folded)
None — no matching todos for this phase.

</deferred>

---

*Phase: 14-homicide-as-a-first-class-category*
*Context gathered: 2026-06-16*
