---
phase: 31-docs-methodology-refresh
plan: 01
subsystem: docs
tags: [methodology, i18n, editorial, seo]
requires: []
provides:
  - "Corrected national_rank direction claim on EN+ES methodology pages"
  - "Corrected national-rank footnote on EN safest-cities-in-chile page"
  - "sexuales news-only family explainer on EN+ES methodology pages"
affects:
  - "site/src/pages/methodology.astro"
  - "site/src/pages/es/metodologia.astro"
  - "site/src/pages/safest-cities-in-chile.astro"
tech-stack:
  added: []
  patterns:
    - "Editorial prose fixes verified against forbidden-language.mjs before commit"
key-files:
  created: []
  modified:
    - "site/src/pages/methodology.astro"
    - "site/src/pages/es/metodologia.astro"
    - "site/src/pages/safest-cities-in-chile.astro"
decisions:
  - "Used the Fable-review-amended replacement sentences verbatim (not the plan body's original 'not the safest' / 'no la más segura' wording), since those tokens are banned by forbidden-language.mjs"
  - "Left site/src/pages/es/comunas-mas-seguras-chile.astro untouched — no equivalent national-rank footnote exists there, so no parity gap to close"
metrics:
  duration: "~25 min"
  completed: "2026-08-02"
---

# Phase 31 Plan 01: Docs Methodology Refresh — national_rank inversion fix + sexuales family docs Summary

Fixed the site's highest-priority documentation defect: the EN and ES methodology pages, plus the EN safest-cities-in-chile editorial page, all inverted what "national rank 1" means (they said rank 1 = lowest reported rate; `pipeline/cead/normalizer.py`'s `compute_ranks()` actually assigns rank 1 to the highest rate, descending sort). Also added the missing `sexuales` news-only family explainer to both methodology pages.

## What Was Built

### Task 1 — national_rank inversion fix (EN + ES methodology pages, same commit)

- `site/src/pages/methodology.astro` — "Ranking basis" list item under `id="comparison-criteria"` now reads: "...Rank 1 = highest reported rate in Chile for that year — rank 1 identifies the commune with the most reported crime, not the one with the least."
- `site/src/pages/es/metodologia.astro` — "Base del ranking" list item under `id="comparison-criteria"` now reads: "...Ranking 1 = mayor tasa reportada en Chile para ese año — identifica la comuna con más delincuencia reportada, no la que registra menos."
- Both sentences are the Fable-review-amended, ban-list-clean replacements specified in the plan's amendment block — NOT the plan body's original ("not the safest" / "no la más segura") wording, which is a forbidden term in `forbidden-language.mjs`.
- Commit: `a0ede74`

### Task 2 — safest-cities-in-chile footnote fix + sexuales family docs (single commit)

- `site/src/pages/safest-cities-in-chile.astro` — the `table-note` footnote sentence about what the National Rank column means was replaced with: "The National Rank column (a separate sitewide measure, not this table's own sort order) follows rank 1 = highest reported rate nationwide — most reported crime, not safest." The page's own ascending sort (lowest-rate-first list) and all "lowest reported crime rates" prose describing that list were left untouched — only the claim about the National Rank column's meaning was wrong.
- `site/src/pages/es/comunas-mas-seguras-chile.astro` — untouched, per plan instruction (no equivalent footnote exists there).
- `site/src/pages/methodology.astro` — new section `<h2 id="sexuales-family">News-only crime category: sexuales</h2>` inserted after "Underreporting (cifra negra)" and before `id="enusc-vhdv"`, explaining the 8-vs-7 family split, no CEAD rate/choropleth/composite-index input, and that it never merges into CEAD-derived stats.
- `site/src/pages/es/metodologia.astro` — Spanish twin: `<h2 id="familia-sexuales">Categoría exclusiva de noticias: sexuales</h2>`, same position, same three facts translated.
- Commit: `bac7eb0`

## Verification

All commands run from repo root, `cd "C:\Users\Carlo\OneDrive - pjud.cl\Documentos\GitHub\Is Chile Safe"`.

### Task 1 acceptance criteria (whitespace-normalized greps)

```
$ tr -s '[:space:]' ' ' < site/src/pages/methodology.astro | grep -c "highest reported rate in Chile"
1
$ tr -s '[:space:]' ' ' < site/src/pages/methodology.astro | grep -c "lowest reported rate in Chile"
0
$ tr -s '[:space:]' ' ' < site/src/pages/es/metodologia.astro | grep -c "mayor tasa reportada en Chile"
1
$ tr -s '[:space:]' ' ' < site/src/pages/es/metodologia.astro | grep -c "menor tasa reportada en Chile"
0
$ grep -c 'id="comparison-criteria"' site/src/pages/methodology.astro
1
$ grep -c 'id="comparison-criteria"' site/src/pages/es/metodologia.astro
1
```

### Task 2 acceptance criteria

```
$ grep -c "lowest reported rate among all non-low-population" site/src/pages/safest-cities-in-chile.astro
0
$ grep -c "highest reported rate nationwide" site/src/pages/safest-cities-in-chile.astro
1
$ grep -c "menor tasa reportada" site/src/pages/es/comunas-mas-seguras-chile.astro
0
$ grep -c 'id="sexuales-family"' site/src/pages/methodology.astro
1
$ grep -c 'id="familia-sexuales"' site/src/pages/es/metodologia.astro
1
$ grep -c "sexuales" site/src/pages/methodology.astro
2
$ grep -c "sexuales" site/src/pages/es/metodologia.astro
2
```

### Plan-level verification

```
$ grep -rn "lowest reported rate" site/src/pages/methodology.astro site/src/pages/es/metodologia.astro site/src/pages/safest-cities-in-chile.astro
(no output — 0 matches)
$ grep -rn "menor tasa reportada en Chile" site/src
(no output — 0 matches)
```

### Editorial gate (mandatory, run once per task, both times green)

```
$ cd site && npm run build && node scripts/validate/forbidden-language.mjs
...
[build] 834 page(s) built in 23.35s
[build] Complete!
forbidden-language: scanning 835 HTML files in dist/
forbidden-language: PASS — 835 pages scanned, 0 forbidden terms found
```

Exit code 0 both after Task 1's edits and again after Task 2's edits.

## Deviations from Plan

None — plan executed exactly as written, using the Fable-review amendment text (not the superseded plan-body original wording) as instructed.

## Self-Check: PASSED

- FOUND: site/src/pages/methodology.astro
- FOUND: site/src/pages/es/metodologia.astro
- FOUND: site/src/pages/safest-cities-in-chile.astro
- FOUND commit a0ede74 in `git log --oneline`
- FOUND commit bac7eb0 in `git log --oneline`
