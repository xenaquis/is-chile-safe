---
status: partial
phase: 21-commune-comparator-a-vs-b-seo
source: [21-VERIFICATION.md]
started: 2026-06-20
updated: 2026-06-20
---

## Current Test

[awaiting human testing]

## Tests

### 1. Interactive comparator island UX (CMP-01)
expected: At `/compare/` and `/es/comparar/`, accent-insensitive autocomplete works ("nunoa" → "Ñuñoa"); selecting 2–3 communes renders side-by-side columns with composite index headline, per-family breakdown, trend arrows, a homicide-per-100k row, and a Chile/regional average column; ES parity holds; columns stack on mobile (≤640px); no absolute "safe/dangerous" verdict language anywhere.
result: [pending]
how: `cd site && npx astro preview --port 4321 --host` then load both locales (BrowserOS mobile via 375px iframe per memory).

### 2. A-vs-B prose visual acceptance (CMP-06)
expected: A random sample of ≥10 enabled A-vs-B pairs (EN+ES) reads naturally and is substantively non-swappable per pair; each page shows the 5 uniqueness blocks + CEAD attribution.
result: [pending]
how: open ≥10 `/compare/<a>-vs-<b>/` and `/es/comparar/<a>-vs-<b>/` pages from the 20 enabled pairs.

### 3. GSC URL Inspection rollout gate (CMP-07)
expected: After deploy to ischilesafe.com, the first ~20-pair batch (3+ A-vs-B URLs + 2 commune URLs) passes Google Search Console URL Inspection (indexable) BEFORE flipping more pairs to `enabled: true` in `data/comparator-pairs.json`.
result: [pending]
how: requires Google Search Console access; external action post-deploy.

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
