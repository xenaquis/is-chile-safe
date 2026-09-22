---
status: partial
phase: 21-commune-comparator-a-vs-b-seo
source: [21-VERIFICATION.md]
started: 2026-06-20
updated: 2026-06-20
---

## Current Test

[GSC rollout gate pending — requires post-deploy Google Search Console access]

## Tests

### 1. Interactive comparator island UX (CMP-01)
expected: At `/compare/` and `/es/comparar/`, accent-insensitive autocomplete works ("nunoa" → "Ñuñoa"); selecting 2–3 communes renders side-by-side columns with composite index headline, per-family breakdown, trend arrows, a homicide-per-100k row, and a Chile/regional average column; ES parity holds; columns stack on mobile (≤640px); no absolute "safe/dangerous" verdict language anywhere.
result: passed
verified: 2026-06-20 via BrowserOS E2E (localhost:4321/compare/). Confirmed: autocomplete "nuno" → "Ñuñoa" (accent-insensitive); 2-commune side-by-side (Ñuñoa, Providencia) + Chile avg column with real national per-family rates; per-family table + distinct homicide-per-100k row (Ñuñoa 4.07 / Providencia 0.00, 0 preserved); remove buttons; no forbidden-verdict language. **Bug found & fixed**: composite-index headline rendered "No composite index" for every commune (island indexed composite_index by series latestCompleteYear 2025 instead of its own key 2024). Fixed in commit dabc82e; verified resolved against built data (Ñuñoa 21.5 #158, Providencia 38.1 #25, Santiago 39.0 #21).

### 2. A-vs-B prose visual acceptance (CMP-06)
expected: A random sample of ≥10 enabled A-vs-B pairs (EN+ES) reads naturally and is substantively non-swappable per pair; each page shows the 5 uniqueness blocks + CEAD attribution.
result: passed
verified: 2026-06-20. Programmatic acceptance 10/10 (executor) + spot-check of 3 enabled pairs EN+ES: ~852 EN / ~999 ES words (≫300 floor), per-family table + h1 present, directional non-swappable prose, no forbidden-verdict language (dedicated validator green). A full human eyeball of all 20 before wider rollout still recommended but not blocking.

### 3. GSC URL Inspection rollout gate (CMP-07)
expected: After deploy to ischilesafe.com, the first ~20-pair batch (3+ A-vs-B URLs + 2 commune URLs) passes Google Search Console URL Inspection (indexable) BEFORE flipping more pairs to `enabled: true` in `data/comparator-pairs.json`.
result: pending
how: requires Google Search Console access; external action post-deploy. Cannot be performed pre-deploy.

## Summary

total: 3
passed: 2
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
