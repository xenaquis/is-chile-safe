---
phase: 36-classification-fidelity-attribution
plan: 03
subsystem: news-frontend
tags: [astro, react, leaflet, i18n, FID-01, G-28, G-36, headline-disclosure]

requires:
  - phase: 36-classification-fidelity-attribution
    provides: "36-01: IncidentRecord.title_src/via_url contract (optional, back-compat)"
provides:
  - "site/src/lib/incidentHeadline.ts: headlineFor(incident, locale) / headlineLabel(kind, locale) / HEADLINE_LABELS"
  - "All 6 news-facing surfaces (news.astro, es/noticias.astro, CommuneNewsSection.astro, HomeNewsPulse.astro, IncidentPinLayer.ts, IncidentsList.tsx) render via this one rule"
  - "Headline policy disclosed in both news intros and both methodology pages"
affects: [36-09, 36-11]

tech-stack:
  added: []
  patterns:
    - "One pure display-decision helper shared by Astro build-time, React islands, and a client <script> enhancer alike"
    - "Client-created DOM nodes styled via :global() under the scoped ancestor (map.css for non-Astro-scoped map surfaces)"

key-files:
  created:
    - site/src/lib/incidentHeadline.ts
    - site/src/lib/incidentHeadline.test.ts
  modified:
    - site/src/pages/news.astro
    - site/src/pages/es/noticias.astro
    - site/src/components/CommuneNewsSection.astro
    - site/src/components/home/HomeNewsPulse.astro
    - site/src/components/map/IncidentPinLayer.ts
    - site/src/components/map/IncidentsList.tsx
    - site/src/components/map/map.css
    - site/src/pages/methodology.astro
    - site/src/pages/es/metodologia.astro

key-decisions:
  - "G-36 (amends G-28, premortem R-01): legacy EN rows (no title_src) get 'Automatically generated headline', not 'Machine-translated headline' — the EN text translates the classifier's own Spanish headline, not the outlet's."
  - "map.css (not in the plan's files_modified) gained .pin-headline-note/.event-note rules — the map surfaces (IncidentPinLayer.ts popup HTML, IncidentsList.tsx React) have no Astro <style> scope of their own, unlike the other 4 surfaces."
  - "CommuneNewsSection's forbidden-term filter now also checks title_src (T-36-08), defense-in-depth against a hostile verbatim outlet headline."

requirements-completed: [FID-01]

duration: ~45 min
completed: 2026-09-25
---

# Phase 36 Plan 03: Headline verbatim/translation display + disclosure Summary

Adds one pure helper, `incidentHeadline.ts` (`headlineFor`/`headlineLabel`), that decides the displayed headline text and its disclosure label for all 6 news-facing surfaces (2 Astro pages, 1 Astro component, 1 client-script-enhanced Astro component, 1 Leaflet popup builder, 1 React component). With today's all-legacy data (787 incidents, no `title_src` yet), Spanish surfaces show the classifier-written `title_es` labelled "Titular generado automáticamente" and English surfaces show the classifier's translation labelled "Automatically generated headline" (G-36) — never "Machine-translated headline", which is reserved for rows that actually carry a stored outlet headline. The news intros (EN/ES) and methodology pages (EN/ES) now disclose the policy, including the BF-04 transition clause for legacy rows.

## Performance

- **Duration:** ~45 min
- **Tasks:** 3
- **Files modified:** 11 (2 created, 9 modified)

## Accomplishments

- `incidentHeadline.ts`: single rule producing `{text, kind}` + a per-locale label table (`HeadlineKind = 'verbatim' | 'machine_translated' | 'original_spanish' | 'legacy_generated'`). 8 vitest cases cover every behavior in the plan, including the G-36 legacy-EN case and the 36-04 kinship-guard fallback (`title_en === title_src`).
- All 6 surfaces wired to the helper — no surface re-implements the locale ternary. `.news-headline-note` (Astro scoped style), `.pulse-note` (client-created, `:global()`), `.pin-headline-note` and `.event-note` (map.css) render the label wherever `headlineLabel()` is non-null.
- News intros (news.astro / es/noticias.astro) and methodology pages (#news-headlines / #titulares-noticias) disclose the verbatim/machine-translation policy, including the BF-04 transition clause for rows without a stored outlet headline, worded (NB-14) as "without a stored source headline" / "sin titular fuente almacenado" so it stays literally true once backfill rows (which carry `title_src`) exist.

## Task Commits

1. **Task 1a (RED): incidentHeadline.test.ts + stub** - `340191c` (test)
2. **Task 1b (GREEN): incidentHeadline.ts implementation** - `06c4b0a` (feat)
3. **Task 2: wire helper into all 6 surfaces + forbidden-term filter on title_src** - `43d7010` (feat)
4. **Task 3: headline-policy disclosure on news intros + methodology (EN/ES)** - `c8182db` (docs)

## Files Created/Modified

- `site/src/lib/incidentHeadline.ts` - `headlineFor`/`headlineLabel`/`HEADLINE_LABELS`, the single display-decision rule
- `site/src/lib/incidentHeadline.test.ts` - 8 vitest cases
- `site/src/pages/news.astro` / `es/noticias.astro` - card link text + `.news-headline-note`; intro disclosure sentence + BF-04 clause
- `site/src/components/CommuneNewsSection.astro` - helper-driven title + ` · {label}` in `.cnews-meta`; forbidden-term filter now also checks `title_src`
- `site/src/components/home/HomeNewsPulse.astro` - client `<script>` imports the helper, appends `.pulse-note` into the meta element
- `site/src/components/map/IncidentPinLayer.ts` - popup title via `headlineFor().text` (escHtml'd); `.pin-headline-note` appended when labelled (also escHtml'd)
- `site/src/components/map/IncidentsList.tsx` - `event-title` renders `h.text` + `.event-note` (React text, auto-escaped)
- `site/src/components/map/map.css` - `.pin-headline-note`, `.event-note` styles (map surfaces have no Astro-scoped `<style>`)
- `site/src/pages/methodology.astro` / `es/metodologia.astro` - new `#news-headlines` / `#titulares-noticias` section

## Decisions Made

See `key-decisions` in frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] `map.css` styling for the new disclosure labels**
- **Found during:** Task 2
- **Issue:** The plan's `files_modified` list does not include `map.css`. `IncidentPinLayer.ts`'s popup HTML and `IncidentsList.tsx`'s React markup have no scoped `<style>` of their own (unlike the other 4 surfaces, which are Astro pages/components with their own `<style>` block) — without adding rules to the shared `map.css`, `.pin-headline-note` and `.event-note` would render unstyled.
- **Fix:** Added two small rules to `map.css`, matching the existing muted/small-text convention used by `.ev-meta`/`.event-meta` in the same file.
- **Files modified:** site/src/components/map/map.css
- **Verification:** `npx astro check` 0 errors; `node scripts/validate/map.mjs` PASS; visual convention matches existing `.ev-meta`/`.pulse-meta` styling.
- **Committed in:** 43d7010 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2, out-of-list file needed for correct rendering)
**Impact on plan:** Necessary for the labels to be visible/legible on the two map surfaces. No scope creep — the CSS additions are two small, narrowly-scoped rules matching existing conventions.

## Issues Encountered

None beyond the deviation above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The `title_src` verbatim-headline path (`kind: 'verbatim'` / `'machine_translated'` / `'original_spanish'`) is proven by Task 1's vitest but has no live data to exercise yet — every current row is legacy. 36-09's live check (once backfill/new rows carry `title_src`) is the first place these three kinds will actually render.
- 36-11 (twin fix per Revision R1) should reuse `HEADLINE_LABELS`/`headlineFor` rather than re-deriving the EN label rule.
- No STATE.md/ROADMAP.md/REQUIREMENTS.md/directive changes were made per the execution instructions; the orchestrator owns those updates.

---

## Verification

- **Task 1:** `npx vitest run src/lib/incidentHeadline.test.ts` — 8/8 pass (RED: 8/8 fail with stub throwing; negative control confirmed FAIL then reverted).
- **Task 2:** `npm run build` succeeds (834 pages). With 787 incidents (all legacy, no `title_src`): EN cards=787, EN notes=787, `Automatically generated headline` count=787, `Machine-translated headline` count=0 (G-36 confirmed). ES cards=787, ES notes=787 (NB-15). No `set:html`/`innerHTML` in the helper. `facets`/`forbidden-language`/`news-freshness`/`map`/`hreflang` validators PASS. `npx vitest run` 192/192 pass (≥ 184 + 8 new). `npx astro check` 0 errors.
- **Task 3:** All 6 grep assertions (`#news-headlines`, `#titulares-noticias`, EN/ES intro sentences, EN/ES BF-04 transition clause) print 1. EN card count (787) still equals `Automatically generated headline` count (clause adds no label string). `forbidden-language`/`hreflang`/`cead-vintage`/`structure` validators PASS.
- **Plan-level:** `npm run build && npm run validate` — 18/18 validators PASS. `npx vitest run` — 192/192 pass. `npx astro check` — 0 errors, 0 warnings, 48 hints.

## Threat Model

- T-36-07 (Tampering/XSS, mitigated): only escaping paths used — Astro text (news.astro/es/noticias.astro/CommuneNewsSection.astro), `escHtml` (IncidentPinLayer.ts, both title and label), React text (IncidentsList.tsx), `textContent` (HomeNewsPulse.astro). No `set:html`/`innerHTML` added; grep guard confirmed clean in the helper.
- T-36-08 (Repudiation/editorial, mitigated): CommuneNewsSection's forbidden-term filter now also checks `title_src`.
- T-36-SC (installs, accepted): no new dependency added.

## Known Stubs

None — the helper's `verbatim`/`machine_translated`/`original_spanish` paths are unreachable with today's all-legacy data by design (no row carries `title_src` yet); this is the documented, intentional state per the plan's objective ("safe to ship before new rows exist").

## Self-Check: PASSED

- FOUND: site/src/lib/incidentHeadline.ts, site/src/lib/incidentHeadline.test.ts
- FOUND: site/src/pages/news.astro, site/src/pages/es/noticias.astro, site/src/components/CommuneNewsSection.astro, site/src/components/home/HomeNewsPulse.astro, site/src/components/map/IncidentPinLayer.ts, site/src/components/map/IncidentsList.tsx, site/src/components/map/map.css, site/src/pages/methodology.astro, site/src/pages/es/metodologia.astro
- FOUND commits: 340191c, 06c4b0a, 43d7010, c8182db

---
*Phase: 36-classification-fidelity-attribution*
*Completed: 2026-09-25*
