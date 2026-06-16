---
phase: 14-homicide-as-a-first-class-category
plan: "04"
subsystem: frontend-contract
tags: [homicide, choropleth, contract-layer, typescript, i18n, family-defs]
dependency_graph:
  requires:
    - "14-02: hr field in map-payload (29993B), homicidios_count in per-commune JSON"
    - "14-03: RED scaffold / test harness"
  provides:
    - "buildStyleMapFromHomicide(comunas) in ChoroplethLayer.ts — D-05 independent quantile scale"
    - "CommunaPayload.hr: number|null — reads abbreviated 'hr' map-payload field (D-09)"
    - "CommunaPayload.homicide_count: number|null — placeholder for per-commune count reads"
    - "FAMILY_LABELS_EN/ES['homicidios'] — bilingual chip labels"
    - "FAMILY_DEFS_EN/ES['homicidios'] — sober CEAD-cited chip tooltip definitions"
    - "CommuneData.featured_rates.homicidios_count: Record<string,number> — per-commune JSON type"
  affects:
    - "site/src/components/map/ChoroplethLayer.ts"
    - "site/src/lib/familyDefs.ts"
    - "site/src/lib/data.ts"
tech_stack:
  added: []
  patterns:
    - "D-05 independent homicide quantile scale: computeQuantileBreaks on positive rates only"
    - "D-09 abbreviated key: CommunaPayload reads hr (not homicide_rate) from map-payload"
    - "Zero/null rate fillOpacity 0.25 vs 0.55 to visually distinguish zero-homicide comunas"
    - "homicidios outside FAMILY_ORDER — lookup-only via open Record<string,string> dicts"
key_files:
  created: []
  modified:
    - site/src/components/map/ChoroplethLayer.ts
    - site/src/lib/familyDefs.ts
    - site/src/lib/data.ts
decisions:
  - "CommunaPayload uses hr (not homicide_rate) — matches D-09 abbreviated map-payload key shipped in 14-02; 14-05 wiring must read c.hr"
  - "homicide_count field in CommunaPayload is null in map-payload context; detail panel (14-06) reads homicidios_count from per-commune JSON via CommuneData.featured_rates"
  - "homicidios not added to FAMILY_ORDER — chip lookup uses open Record<string,string> dicts, not the array; Phase 15 SEO will extend FAMILY_ORDER separately"
metrics:
  duration: "~10m"
  completed: "2026-06-16"
  tasks_completed: 2
  files_changed: 3
requirements: [HOM-01]
---

# Phase 14 Plan 04: Homicide Contract Layer Summary

Independent homicide choropleth function (buildStyleMapFromHomicide) on its own D-05 quantile scale, CommunaPayload extended with the `hr` abbreviated field (matching 14-02's D-09 compact key), and bilingual sober CEAD-cited homicidios label/definition added to all four familyDefs dicts.

## Contract Surface for 14-05

**14-05 wiring will consume these exact exports:**

| Export | File | Field/Key | Notes |
|--------|------|-----------|-------|
| `buildStyleMapFromHomicide(comunas)` | ChoroplethLayer.ts | reads `c.hr ?? 0` | independent quantile breaks on positiveRates |
| `CommunaPayload.hr` | ChoroplethLayer.ts | `number \| null` | abbreviated map-payload key (D-09) |
| `CommunaPayload.homicide_count` | ChoroplethLayer.ts | `number \| null` | null in map context; per-commune JSON for 14-06 |
| `FAMILY_LABELS_EN['homicidios']` | familyDefs.ts | `'Homicide'` | chip label EN |
| `FAMILY_LABELS_ES['homicidios']` | familyDefs.ts | `'Homicidios'` | chip label ES |
| `FAMILY_DEFS_EN['homicidios']` | familyDefs.ts | sober EN definition | subgroup 101, CEAD-cited |
| `FAMILY_DEFS_ES['homicidios']` | familyDefs.ts | sober ES definition | subgrupo 101, CEAD-citado |
| `CommuneData.featured_rates.homicidios_count` | data.ts | `Record<string,number>` | per-commune JSON type for 14-06 detail panel |

**14-06 reads:** `commune.featured_rates.homicidios_count[year]` for count display in the detail panel.

## homicide_count Status

`homicide_count` was dropped from the map-payload in 14-02 (budget escape: adding `"homicide_count":N,` per entry would push payload to >37KB). The count lives in `featured_rates.homicidios_count` in per-commune JSON only. The `CommunaPayload.homicide_count` field is typed as `number | null` for potential future use but will be `null` when reading from map-payload. 14-06 (detail panel) reads the count from `loadCommune(cut).featured_rates.homicidios_count`, not from the payload.

## Tasks Completed

| Task | Description | Commit | Key Files |
|------|-------------|--------|-----------|
| 1 | buildStyleMapFromHomicide + CommunaPayload.hr extension | 84607b9 | site/src/components/map/ChoroplethLayer.ts |
| 2 | Bilingual homicidios label/def + homicidios_count type | 67d81b3 | site/src/lib/familyDefs.ts, site/src/lib/data.ts |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CommunaPayload field name: hr not homicide_rate**

- **Found during:** Task 1 (pre-implementation review of upstream facts)
- **Issue:** Plan action text said `homicide_rate: number | null` but the critical upstream fact from 14-02 specifies the actual map-payload field is abbreviated `hr` (D-09 compact encoding). Using `homicide_rate` would cause a runtime mismatch when 14-05 wires against the payload.
- **Fix:** Named the field `hr: number | null` in CommunaPayload to match the actual payload key. Added JSDoc comment explaining the D-09 abbreviation and that 14-05 must read `c.hr`.
- **Files modified:** site/src/components/map/ChoroplethLayer.ts

## Known Stubs

None — all exported symbols are fully typed and implemented. The `homicide_count` field is intentionally `null`-typed in the map-payload context (not a stub; the count lives in per-commune JSON).

## Threat Flags

None — no new network endpoints or auth paths. T-14-09 mitigated: `buildStyleMapFromHomicide` reads via `c.hr ?? 0` so null/missing values degrade to lightest bucket.

## Self-Check: PASSED

- [x] site/src/components/map/ChoroplethLayer.ts exports `buildStyleMapFromHomicide`
- [x] CommunaPayload includes `hr: number | null` and `homicide_count: number | null`
- [x] buildStyleMapFromHomicide filters `r > 0` for positiveRates (D-05 independent scale)
- [x] Zero-rate comunas get `fillOpacity: 0.25`; data-bearing comunas get `0.55`
- [x] site/src/lib/familyDefs.ts has `homicidios` in all four dicts (LABELS_EN, LABELS_ES, DEFS_EN, DEFS_ES)
- [x] `homicidios` is NOT in FAMILY_ORDER
- [x] site/src/lib/data.ts CommuneData.featured_rates has `homicidios_count: Record<string, number>`
- [x] `cd site && npx tsc --noEmit` exits 0 (no errors)
- [x] Commits: 84607b9, 67d81b3
