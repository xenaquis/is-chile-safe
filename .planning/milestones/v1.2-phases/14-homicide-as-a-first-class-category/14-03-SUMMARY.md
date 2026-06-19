---
phase: 14-homicide-as-a-first-class-category
plan: "03"
subsystem: validation
tags: [validator, homicide, map-payload, data-integrity, regression-guard]
dependency_graph:
  requires:
    - "14-02: hr field in map-payload + featured_rates.homicidios in commune JSONs"
  provides:
    - "Check 8: 'hr' key presence asserted in first 10 map-payload entries"
    - "Check 9: featured_rates.homicidios non-empty asserted in Santiago (13101)"
    - "site/public/data/cead mirror confirmed carrying homicide data"
  affects:
    - "site/scripts/validate/map.mjs — 44 lines added (Check 8 + Check 9)"
tech_stack:
  added: []
  patterns:
    - "existsSync guard + Object.keys().length assertion (not truthiness) per Pitfall 5"
    - "Abbreviated 'hr' key asserted (not 'homicide_rate') — matches 14-02 D-09 compact encoding decision"
key_files:
  created: []
  modified:
    - site/scripts/validate/map.mjs
decisions:
  - "Assert 'hr' in map-payload (not 'homicide_rate') — matches 14-02 budget escape: abbreviated key saves 10B/entry"
  - "Both checks run pre-build (no dist/ required) — committed data asset assertions"
  - "Task 2 had no new file commits: site/public/data/cead was already synced and committed by 14-02; sync confirmed it is current"
metrics:
  duration: "~5m"
  completed: "2026-06-16"
  tasks_completed: 2
  files_changed: 1
requirements: [HOM-01]
---

# Phase 14 Plan 03: Build Validator — Homicide Data Presence Gates Summary

Build validator extended with Check 8 (hr key in map-payload) and Check 9 (featured_rates.homicidios non-empty in Santiago commune JSON); all 18 checks pass against 14-02 data; site/public mirror confirmed current.

## Tasks Completed

| Task | Description | Commit | Key Files |
|------|-------------|--------|-----------|
| 1 | Add Check 8 + Check 9 to map.mjs validator | 37945d6 | site/scripts/validate/map.mjs |
| 2 | Sync data to site/public + full validator green | (no new files — already committed by 14-02) | site/public/data/cead/ verified |

## Validator Output (18/18 PASS)

```
PASS [TopoJSON raw budget (353696 bytes < 420 KB)]
PASS [TopoJSON gzip budget (87672 B < 140 KB)]
PASS [TopoJSON features (346)]
PASS [TopoJSON CUT join (Santiago 13101 present)]
PASS [map EN page exists]
PASS [map ES page exists]
PASS [EN map island marker]
PASS [EN map locate aria-label]
PASS [ES map island marker]
PASS [ES map locate aria-label]
PASS [zero-React guard [commune/santiago] — no astro-island]
PASS [zero-Leaflet guard [commune/santiago] — no leaflet reference]
PASS [runtime data served — dist/data/cead/geo/communes.topo.json]
PASS [runtime data served — dist/data/cead/map-payload.json]
PASS [runtime data served — dist/data/cead/meta/index.json]
PASS [runtime data served — dist/data/cead/comunas/13101.json]
PASS [homicide_rate in map-payload]
PASS [homicide in 13101.json (22 years)]

map.mjs: PASSED — all map validator checks passed
```

## Deviations from Plan

### Auto-applied Key-Name Correction

**1. [Upstream Fact] Check 8 asserts 'hr' not 'homicide_rate'**

- **Found during:** Plan review (upstream facts from 14-02-SUMMARY.md)
- **Issue:** Plan prose and 14-PATTERNS.md template use `'homicide_rate' in c`, but 14-02 shipped abbreviated key `'hr'` (D-09 compact encoding, saves 10B/entry × 346).
- **Fix:** Check 8 asserts `'hr' in c` — the actual field name in the committed data.
- **Files modified:** site/scripts/validate/map.mjs
- **Commit:** 37945d6

## Known Stubs

None.

## Threat Flags

None — no new network endpoints or auth paths introduced.

## Self-Check: PASSED

- [x] site/scripts/validate/map.mjs contains Check 8 referencing `'hr' in c`
- [x] site/scripts/validate/map.mjs contains Check 9 referencing `featured_rates?.homicidios`
- [x] Both checks use existsSync guards and Object.keys().length (not truthiness)
- [x] node site/scripts/validate/map.mjs exits 0 with 18 PASS lines, 0 FAIL
- [x] site/public/data/cead/map-payload.json confirmed to carry `hr` field (node -e verified)
- [x] Commit: 37945d6
