---
phase: 14-homicide-as-a-first-class-category
plan: "05"
subsystem: frontend-map-island
tags: [homicide, choropleth, chip, filters, react, typescript, HOM-01]
dependency_graph:
  requires:
    - "14-04: buildStyleMapFromHomicide in ChoroplethLayer.ts, CommunaPayload.hr, FAMILY_DEFS EN/ES homicidios"
  provides:
    - "FiltersRow.tsx: 8th homicidios chip (featured, familyIndex: null)"
    - "MapIsland.tsx: crimeIsHomicide state + three-way choropleth branch (chip effect + year effect)"
  affects:
    - site/src/components/map/FiltersRow.tsx
    - site/src/components/map/MapIsland.tsx
tech_stack:
  added: []
  patterns:
    - "Three-way choropleth branch: crimeIsHomicide → buildStyleMapFromHomicide; crimeFamilyIndex !== null → buildStyleMapFromFamily; else → buildStyleMapFromLevel"
    - "Exclusive chip selection: homicide chip passes familyIndex null, deactivating family chips"
    - "crimeIsHomicide in chip effect AND year effect dep arrays so homicide layer survives year change"
key_files:
  created: []
  modified:
    - site/src/components/map/FiltersRow.tsx
    - site/src/components/map/MapIsland.tsx
decisions:
  - "crimeIsHomicide set to (key === 'homicidios') in the same onFamilyChange handler — no separate handler needed; works because homicide chip passes familyIndex null which also clears crimeFamilyIndex"
  - "crimeIsHomicide added to year-effect dep array so selecting homicide then changing year still recolors via buildStyleMapFromHomicide"
metrics:
  duration: "~8m"
  completed: "2026-06-16"
  tasks_completed: 2
  files_changed: 2
requirements: [HOM-01]
---

# Phase 14 Plan 05: Homicide Chip + MapIsland Wiring Summary

8th featured homicide chip wired into FiltersRow and MapIsland: selecting the chip recolors the choropleth via the independent D-05 quantile scale (buildStyleMapFromHomicide), survives year changes, and stays exclusive with family chips — all without touching the 7-element by_family FAMILY_ORDER contract from 14-04.

## Tasks Completed

| Task | Description | Commit | Key Files |
|------|-------------|--------|-----------|
| 1 | Add homicidios chip to FiltersRow CHIP_DEFS | 64fb9bc | site/src/components/map/FiltersRow.tsx |
| 2 | crimeIsHomicide state + three-way choropleth branch in MapIsland | c7c70c5 | site/src/components/map/MapIsland.tsx |

## Contract Surface for 14-06

**14-06 (detail panel) will need:**

- `selected` CUT is already tracked in MapIsland state; ResultPanel receives `cut`, `lang`, `year`
- `CommuneData.featured_rates.homicidios_count[year]` from per-commune JSON (type added in 14-04 via data.ts) — load in ResultPanel via `loadCommune(cut)`

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints or auth paths. T-14-11 mitigated: buildStyleMapFromHomicide reads `c.hr ?? 0` so null/missing fields degrade to lightest bucket. T-14-12 accepted: same in-place setStyle path as existing effects.

## Self-Check: PASSED

- [x] FiltersRow.tsx CHIP_DEFS contains `{ key: 'homicidios', familyIndex: null, ... featured: true }`
- [x] Chip label is 'Homicidios'/'Homicide' (not a vida-aggregate label)
- [x] MapIsland.tsx imports buildStyleMapFromHomicide
- [x] crimeIsHomicide state declared after crimeFamilyIndex
- [x] Chip recolor effect uses three-way branch; crimeIsHomicide in dep array
- [x] Year effect uses three-way branch; crimeIsHomicide in dep array
- [x] onFamilyChange sets setCrimeIsHomicide(key === 'homicidios')
- [x] homicidios NOT in FAMILY_ORDER (7-element contract preserved)
- [x] `cd site && npx tsc --noEmit` exits 0
- [x] Commits: 64fb9bc, c7c70c5
