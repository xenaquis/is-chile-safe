---
phase: quick-260727-j6z
plan: 01
subsystem: news-pipeline, frontend
tags: [classifier, schema, repair, i18n, redirect]
tech_stack:
  added: []
  patterns: [pydantic-v2-validation, regex-repair, astro-is-inline-script, localStorage-lang-pref]
key_files:
  created:
    - pipeline/repair_sexual_family.py
    - pipeline/tests/test_repair_sexual_family.py
  modified:
    - pipeline/news/schema.py
    - pipeline/news/classifier.py
    - pipeline/tests/test_classifier.py
    - pipeline/tests/test_schema_incidents.py
    - site/src/lib/familyDefs.ts
    - site/src/layouts/BaseLayout.astro
    - site/src/components/PageHeader.astro
    - data/incidents/current.json
decisions:
  - "'sexuales' lives in pipeline/news/schema.py VALID_FAMILIES only — pipeline/shared/schema.py (CEAD 7-family contract) is untouched"
  - "Death-dominates rule: sexual+death co-hit stays 'vida'; matches classifier SYSTEM_PROMPT carve-out"
  - "Regex uses explicit stems (violacion, violad*, abuso sexual) not bare 'viol' to avoid false-hitting violento/violencia"
  - "Redirect uses window.location.replace (no Back-button bounce); reads hreflang link from DOM (no {expr} in <script> — Astro gotcha)"
  - "url-ledger.jsonl rows do not carry a 'family' field — no ledger rewrite needed"
metrics:
  duration: ~25 min
  completed: "2026-07-27"
  tasks: 3
  files_changed: 9
---

# Phase quick-260727-j6z Plan 01: Fix Granite Classifier Sexual Crimes Mis-classification Summary

**One-liner:** Added news-only "sexuales" family (Pydantic + prompt + frontend), repaired 24 mis-classified incidents in current.json via deterministic regex sweep (death-dominates rule), and wired browser-language redirect (EN->ES for Spanish browsers, explicit choice persisted in localStorage).

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Add sexuales family to classifier, schema, and frontend labels | 95769fc | pipeline/news/schema.py, classifier.py, familyDefs.ts, 2 test files |
| 2 | Deterministic keyword sweep to repair current.json | 9052f49 | pipeline/repair_sexual_family.py, test_repair_sexual_family.py, data/incidents/current.json |
| 3 | Browser-language redirect (EN -> ES for Spanish browsers) | 7ef2954 | BaseLayout.astro, PageHeader.astro |

## Outcomes

- `VALID_FAMILIES = set(FAMILY_KEYS) | {"sexuales"}` in pipeline/news/schema.py; pipeline/shared/schema.py unchanged.
- `_NEWS_FAMILY_ENUM_STR` drives both SYSTEM_PROMPT locations; sexual-routing rule + death-carve-out added.
- `FAMILY_LABELS_EN["sexuales"] = "Sexual Crimes"`, `FAMILY_LABELS_ES["sexuales"] = "Delitos Sexuales"`.
- 24 incidents flipped vida->sexuales; 2 death-dominated sexual incidents kept as vida; 604 vida remain (was 628).
- Idempotent repair script: re-running flips nothing new.
- R2 guard: treats empty strings as missing, skips R2 loudly, exits 0; logs secret names never values.
- EN pages emit inline redirect script reading hreflang link; ES pages emit no redirect.
- Language toggle persists choice in localStorage; explicit EN pick not bounced back.
- 37 tests pass (27 classifier/schema + 10 repair).
- Site builds: 834 pages, no new errors introduced (4 pre-existing ComparatorPairsLinks.astro errors unchanged).

## Deviations from Plan

None — plan executed exactly as written. Pre-existing astro-check errors in ComparatorPairsLinks.astro (4 implicit-any warnings) were present before this task and are out of scope.

## Known Stubs

None — sexuales incidents render with correct labels from FAMILY_LABELS_EN/ES; no placeholder text.

## Threat Flags

No new threat surface beyond what was covered in the plan's STRIDE register (T-j6z-01..SC all mitigated):
- VALID_FAMILIES closed-list prevents LLM tampering (T-j6z-01).
- R2 creds guard prevents empty-bucket write (T-j6z-02).
- Redirect wrapped in try/catch, no-ops on failure (T-j6z-03).
- Repair script only touches family field on matched incident IDs (T-j6z-04).

## Self-Check

Files exist:
- pipeline/repair_sexual_family.py: FOUND
- pipeline/tests/test_repair_sexual_family.py: FOUND
- data/incidents/current.json: FOUND (sexuales=24)

Commits:
- 95769fc: feat — classifier/schema/labels
- 9052f49: feat — repair script + current.json
- 7ef2954: feat — browser redirect

## Self-Check: PASSED

## Post-close R2 deep audit (2026-07-27, orchestrator)

Full bucket audit after push/deploy:
- Aggregates consistent at sexuales=29 / 1300 incidents: incidents.jsonl, incidents.csv, corpus-state.json, corpus-state-history/2026-07-27.json, manifest.json.
- url-ledger.jsonl (1350 rows, 565 fetched): carries no family field — nothing to fix.
- Per-article objects (research-archive/articles/{id}.json) freeze incident metadata at fetch time: 13 of 17 fetched sexuales articles carried stale family="vida" (fetched by the 08:52 UTC R2 cron, pre-repair). Patched in-place via boto3 (family field only; text/text_sha256 untouched) and re-verified: 0 stale remaining.
- 12 sexuales articles still pending fetch will inherit the corrected family from consolidated records on future cron runs.
- Older corpus-state-history snapshots retain pre-repair by_family by design (point-in-time records).
