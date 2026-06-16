---
status: passed
quick_id: 260616-ldi
date: 2026-06-16
---

# Verification — region_id grouping fix (backlog 999.1)

## Goal
Derive region_id from CUT length so regions 1–9 group correctly and the 11/14
province-code collision (Tarapacá vs Aysén/Los Ríos) disappears; migrate data,
regenerate aggregates, simplify frontend compensations. Regions 1–9 must
populate.

## Evidence

| Must-have | Result | Evidence |
|---|---|---|
| region_id derived by CUT length | PASS | `region_id_from_cut()` in scrape_cead.py; used at commune build |
| Collision resolved | PASS | Iquique 1101 `11→1`, Alto Hospicio 1107 `11→1`, Aysén 11201 stays `11`, Valparaíso 5101 `51→5` |
| All 16 regions populated | PASS | migration report: "regions with empty series: NONE" (were 1–9 empty) |
| Region membership correct | PASS | Tarapacá=7 communes (no Aysén); Aysén=10 (no Tarapacá); Los Ríos=12; Valparaíso=38 |
| regional_rank recomputed | PASS | compute_ranks re-run on corrected grouping; 217 commune files updated |
| national_rank stable | PASS | Santiago national_rank=11 unchanged (national aggregate is region-independent; national.json byte-identical) |
| Schema validation | PASS | validate_all_communes (346 + plausibility) green |
| No re-scrape | PASS | migration reads existing per-commune JSON only |
| Frontend simplified | PASS | regionFileId→identity; inline floor() removed; REGION_NAMES "56" dropped; 999.1 notes → RESOLVED |
| Build + validators | PASS | `astro build` 790 pages; `npm run validate` 12/12; `astro check` 0 errors; pytest 139 passed |

## Migration reproducibility
`migrate_region_id.py` (this dir) is idempotent and re-runs the whole migration
from per-commune JSON. Pipeline source fix means future scrapes are already correct.

## Verdict
PASSED — backlog 999.1 (tarapaca-region-id-collision) resolved end-to-end.
