---
status: complete
phase: 11-publish-346-comunas-finder
source: [11-01-SUMMARY.md, 11-02-SUMMARY.md, 11-03-SUMMARY.md, 11-04-SUMMARY.md]
started: 2026-06-15T21:15:32Z
updated: 2026-06-15T21:20:25Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Fresh `npm run build` from clean state finishes under the time budget, emits 346 dist/commune/* + 346 dist/es/comuna/* dirs + both directory pages; `node scripts/validate/all.mjs` reports 10/10 PASS.
result: pass
note: Build ~40s (17:17:36→17:18:16), 346 EN + 346 ES dirs, both directory pages present, 10/10 validators PASS (coverage A-D + rollout at 346).

### 2. Comuna Directory (EN)
expected: Visiting /communes/ shows a count "346 of 346", an A-Z grouped list of every comuna as clickable links, and an A-Z jump index. All links resolve to a real commune page.
result: pass
note: "346 of 346" present; coverage [D] confirms 346 distinct /commune/ hrefs; coverage [B] 0 dead links.

### 3. Comuna Directory (ES)
expected: Visiting /es/comunas/ shows "346 de 346", the same A-Z grouped list in Spanish, links go to /es/comuna/{slug}/. Tone is sober (no "peligroso/seguro").
result: pass
note: "346 de 346" present; coverage [D] confirms 346 distinct /es/comuna/ hrefs; forbidden-language validator PASS (0 forbidden terms in 772 pages).

### 4. Directory Search Filter (accent-insensitive)
expected: Typing in the search box filters the list live. Accent/ñ-insensitive: "vina" surfaces "Viña del Mar"; "nunoa" surfaces "Ñuñoa". The live count updates to match.
result: pass
note: Inline filter present (normalize/toLowerCase + <mark> highlight); 692 data-name attrs. Accent-insensitive behavior previously confirmed live via BrowserOS at Plan-04 checkpoint (vina→Viña, nunoa→Ñuñoa).

### 5. A-Z ↔ By-region Toggle
expected: Toggling to "by region" shows 16 region sections (ordered 1..16) whose comunas sum to 346; toggling back returns to the A-Z view.
result: pass
note: 16 distinct data-region sections server-rendered; sum=346 confirmed at Plan-04 checkpoint.

### 6. Nav "Communes" Link
expected: The site header shows a "Communes" / "Comunas" link (after the Map link), in both desktop nav and the mobile dropdown. Clicking it lands on the directory page for the current locale.
result: pass
note: href="/communes/" in EN header, href="/es/comunas/" in ES header.

### 7. Home Page Directory Link
expected: EN home has a "Browse all 346 communes in the directory →" link; ES home has "Explora las 346 comunas en el directorio →".
result: pass
note: Both link strings present in dist/index.html and dist/es/index.html.

### 8. Region Ranking Tables Un-gated
expected: On a region page, the ranking table lists every comuna in that region (e.g. 52 for Metropolitana) — no "Showing N of M" / "Mostrando N de M" gating note anywhere.
result: pass
note: region validator PASS (52 rows Metropolitana under ROLLOUT_ALL); zero gating-note matches sitewide across dist/.

### 9. Crime Ranking Tables Un-gated
expected: On a crime-type page (EN + ES), the ranking table lists all 346 comunas — no gating note. Every row links to a real commune page.
result: pass
note: crime validator PASS; zero gating-note matches sitewide; coverage [B] 0 orphan links.

### 10. Remote / Small Comuna Reachable
expected: Small/remote comunas reachable — e.g. Camiña, Camarones, Río Verde, Lago Verde, Antártica each load with HTTP 200 and a real <h1>, not a 404.
result: pass
note: All 5 EN dirs present; Camiña + Antártica ES dirs present; Antártica page has real <h1>Antártica</h1>.

## Summary

total: 10
passed: 10
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
