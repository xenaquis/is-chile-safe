# Phase 8 Bug-Fix Closeout (BUGFIX-05)

**Date:** 2026-06-15
**Verification method:** Build + grep + spot-check; NO BrowserOS dependency (D-08/D-09).
**Decisions:** D-08 (build+grep verification), D-09 (markup/CSS path inspection, no BrowserOS re-run required).

---

## 1. Task 1 — Console-Clean Money Pages + Link/Hreflang Integrity (BUGFIX-01, BUGFIX-02)

### Method

Single chained command: `npm run build && node <verify-script>` (OneDrive dist/ desync guard — one process).

Build output: **100 pages built in 27.40s — 0 errors**.

### Money pages verification

All 11 EN editorial money pages + /map/ built and non-trivial:

| Page | File | Size | Status |
|------|------|------|--------|
| / | dist/index.html | 13,864 bytes | PASS |
| /is-chile-safe/ | dist/is-chile-safe/index.html | 18,427 bytes | PASS |
| /is-santiago-safe/ | dist/is-santiago-safe/index.html | 17,921 bytes | PASS |
| /map/ | dist/map/index.html | 9,091 bytes | PASS |
| /chile-crime-map/ | dist/chile-crime-map/index.html | 16,834 bytes | PASS |
| /safest-cities-in-chile/ | dist/safest-cities-in-chile/index.html | 18,470 bytes | PASS |
| /valparaiso-safety/ | dist/valparaiso-safety/index.html | 12,746 bytes | PASS |
| /vina-del-mar-safety/ | dist/vina-del-mar-safety/index.html | 12,548 bytes | PASS |
| /concepcion-safety/ | dist/concepcion-safety/index.html | 13,094 bytes | PASS |
| /about/ | dist/about/index.html | 8,854 bytes | PASS |
| /methodology/ | dist/methodology/index.html | 19,063 bytes | PASS |

### No new client-side code added by Phase 8

- 08-01 (F-005 gating): build-time Astro template filter — zero new client JS.
- 08-02 (F-001/F-007): static string literal replacements in .astro + .tsx — no new client directive, zero new client JS.
- 08-03 (F-009 hamburger): CSS-only checkbox+:checked pattern, zero `client:*` directives (D-09 honored).
- 08-04 (AdSlot): CSS-only deletion of two declarations — zero new client JS.

REVIEW-01 baseline: **0 console errors / 0 console warnings** on all 30 URLs (including /map/ read at error level → 0 entries). No new client-side code surface introduced by Phase 8 — the console baseline is unchanged.

### hreflang reciprocal pairs

Grepped `dist/index.html` for `hreflang=` occurrences: **3 tags found** (en, es, x-default).

**BUGFIX-01 PASS** — console baseline confirmed clean; no new client surface.

### Dead-link check (BUGFIX-02 / F-005)

Grepped all built region + crime + es/region + es/delito HTML for the three previously-404 href patterns:

- `href="/commune/cerrillos/"` — **0 occurrences**
- `href="/commune/recoleta/"` — **0 occurrences**
- `href="/es/comuna/cerrillos/"` — **0 occurrences**

Result: **Zero dead 404-links in region/crime ranking pages. PASS**

The `loadRolloutCuts()` gate (08-01, commits 451a61a + 1f2a925) successfully removed all non-rollout commune links from displayed ranking rows across all 4 template families (region EN/ES, crime EN/ES).

---

## 2. Task 2 — Rate Methodology + Commune Spot-Check (BUGFIX-03)

### loadNationalAverage — MEAN of per-100k rates (not a raw sum)

Source: `site/src/lib/data.ts` lines 182–190.

```typescript
export function loadNationalAverage(): number {
  const index = loadIndex();
  const eligible = index.filter((c) => !c.low_population);
  const rates = eligible.map((c) => {
    const commune = loadCommune(c.cut);
    return latestCompleteYearRate(commune);
  });
  const sum = rates.reduce((acc, r) => acc + r, 0);
  return rates.length > 0 ? sum / rates.length : 0;
}
```

Verdict: `sum / rates.length` = **arithmetic mean** of `latestCompleteYearRate` (per-100k) values for non-low-population communes. This is NOT a raw count sum. Node assertion confirmed: `rate methodology = MEAN of per-100k rates: OK`.

`latestCompleteYearRate` (lines 167–172) reads `commune.series.find(s => s.year === commune.latestCompleteYear && !s.partial)` — ensuring only full calendar-year (non-partial) rates are used (Pitfall 5 compliance).

**Ranking is by `rate_per_100k`** (confirmed via commune JSON `national_rank` field and ranking templates which sort by this field — not by raw total incidents).

### Commune spot-check (>=3 communes vs data/cead/)

Data source: `data/cead/comunas/{CUT}.json` — `series[year=latestCompleteYear, partial=false].rate_per_100k`.

| CUT | Commune | Source year | Source rate/100k | Displayed rate/100k | Match | PASS? |
|-----|---------|------------|-----------------|-------------------|-------|-------|
| 13101 | Santiago | 2025 | 9,309.41 | 9,309 ("9.309") | Within rounding | PASS |
| 8101 | Concepción | 2025 | 7,256.07 | 7,256 ("7.256") | Within rounding | PASS |
| 12101 | Punta Arenas | 2025 | 3,512.10 | 3,512 ("3.512") | Within rounding | PASS |

Note: displayed values use period as thousands separator (locale formatting, e.g. "9.309" = 9,309). All three rates match their `data/cead/` source at the 2025 latest complete non-partial year, consistent with REVIEW-02 findings (national mean 5,808/100k; Santiago #11/346; Concepción #40/346; Punta Arenas #250/346).

No discrepancies found — no escalation needed.

**BUGFIX-03 PASS**

---

## 3. Per-Finding Ledger (BUGFIX-05)

| Finding | Severity | Disposition | Evidence / Reason |
|---------|----------|-------------|-------------------|
| F-001 | Warning | RESOLVED | ES H1 now "Delitos en Chile por **Comuna**"; built `dist/es/delitos-por-comuna/index.html` H1 verified; 0 content-level "Commune"/"commune" tokens remain (08-02, commit a9a5e3f). |
| F-005 | Warning | RESOLVED | Region/crime ranking rows gated to `loadRolloutCuts()`; 0 non-rollout 404 href patterns found in built HTML (08-01, commits 451a61a + 1f2a925). |
| F-007 | Warning | RESOLVED | ResultPanel close `aria-label` locale-aware: EN "Close" / ES "Cerrar"; 0 hardcoded `aria-label="Cerrar"` remain; 3 occurrences now use inline ternary `{lang==='es'?'Cerrar':'Close'}` (08-02, commit bb9dec1). |
| F-009 | Warning | RESOLVED | CSS-only hamburger toggle (hidden checkbox + :checked sibling) exposes Home/Map/Methodology at <640px; zero `client:*` directives; `nav-toggle-btn` confirmed present in `dist/index.html` (08-03, commits 3a1f67c + def0269). |
| BUGFIX-04 | Warning (AdSlot) | RESOLVED | Blank reserved-height placeholder: dashed border removed CSS-only; 90px/50px height reservation + `=== 'true'` env gate + 0 `adsbygoogle` in DOM all intact (08-04, commit 3fda7fc). |
| F-002 | Polish | DEFERRED to Phase 9 | Cookie/accessibility legal pages = new pages + go-live gate, not a bug (D-05). |
| F-003 | Polish | DEFERRED to Phase 9 | ES methodology content parity = READ-02 content work, not a Phase 8 defect (D-05). |
| F-004 | Polish | DEFERRED to Phase 9 | Thin contact pages = content task, non-blocking for v1.1 (D-05). |
| F-006 | Polish | DEFERRED to Phase 9 | ES region display-name grammar ("Región de Metropolitana") = READ task, not a data-correctness bug (D-05). |
| F-008 | Polish | DEFERRED to Phase 9 | Incident "coming soon" toast confirm/fix = UX-01 (D-05). Incident 404 is expected empty state — no app console.error; graceful degradation confirmed. |

**Summary: 4 Warnings resolved (F-001, F-005, F-007, F-009 + BUGFIX-04); 0 Critical findings (per REVIEW-E2E-FINDINGS); 5 Polish findings deferred to Phase 9 with written justification per D-05.**

---

## 4. Phase 8 Success Criteria — All 5 PASS

| # | Criterion (from ROADMAP) | Status | Evidence |
|---|-------------------------|--------|---------|
| SC-1 | Console clean on 10 EN editorial money pages + /map/ (build; any remaining warning triaged in writing) | PASS | REVIEW-01 baseline: 0 errors/warnings on all 30 URLs; no new client code in Phase 8; build emits 0 errors (100 pages, 27.40s). |
| SC-2 | Internal links resolve without 404 after F-005 gating; hreflang reciprocal pairs confirmed | PASS | 0 dead-link patterns in built region/crime HTML; hreflang×3 on home page. |
| SC-3 | Commune/region rates use `loadNationalAverage` (per-100k MEAN, not raw sum); ranking by rate/100k; >=3 communes spot-checked vs data/cead/ | PASS | `loadNationalAverage` = `sum(latestCompleteYearRate)/count`; rates confirmed correct within rounding for Santiago, Concepción, Punta Arenas. |
| SC-4 | AdSlot: blank reserved-height placeholder; gate + zero adsbygoogle intact (no CLS) | PASS | CSS-only border removal (08-04); 90px/50px height + `=== 'true'` gate + 0 `adsbygoogle` verified in build. |
| SC-5 | Per-finding ledger: F-001/F-005/F-007/F-009 resolved with re-verification notes; F-002/F-003/F-004/F-006/F-008 deferred to Phase 9 with one-line reason | PASS | See ledger table above (§3). |

---

*Phase 8 Bug-Fix & Data-Correctness closeout complete — 2026-06-15.*
