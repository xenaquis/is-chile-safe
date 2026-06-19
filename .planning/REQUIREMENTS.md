# REQUIREMENTS — Milestone v2.0 Composite Index, Comparators & Launch

**Defined:** 2026-06-19
**Source:** v2.0 milestone research (`.planning/research/SUMMARY.md` + STACK/FEATURES/ARCHITECTURE/PITFALLS) and SEED-001 (comparator + A-vs-B, locked constraints).
**Goal:** Redesign the core safety metric into an exposure-adjusted composite index, build a commune comparator + curated A-vs-B SEO pages on top of it, and execute the production go-live.

**Tracks & dependency:** Track 1 (Composite Index, Phase 18 — reserved #) → Track 2 (Comparator + A-vs-B, Phase 21) is a **hard dependency** (the comparator headline number and A-vs-B prose need a computed index). Track 3 (Go-Live, Phase 22) has no code dependency and can run in parallel with Phase 21.

**Locked constraints (carry through all tracks):** hybrid rollout (display all comunas, never 404/link to non-rollout pages); never an absolute "seguro/peligroso / safe/dangerous" verdict — a sortable single score implies a verdict through rank + color alone, so editorial framing + the CI validator must guard it; no thin content; static / SEO-indexable; every displayed figure explained + sourced + caveated with EN/ES parity (figure-registry zero-orphan).

---

## v2.0 Requirements

### Track 1 — Composite Crime Index (→ Phase 18)

- [x] **CI-01**: The pipeline computes a 0–100 composite crime-exposure index per comuna from the 7 defined metrics and writes it (additive, non-breaking) into per-comuna JSON, in an isolated `build_composite_index.py` step that does not break the CEAD scraper if it fails.
- [x] **CI-02**: The index normalizes per-metric distributions with winsorization or percentile-rank (never raw min-max), so right-skewed micro-comuna outliers don't collapse the scale; a pytest distribution assertion guards the spread.
- [x] **CI-03**: SPD VHC is the homicide input to the index (M5), reference year capped at the latest fully-consolidated year (≤2024); CEAD grupo-101 `featured_rates.homicidios` is preserved unchanged for backward compatibility.
- [x] **CI-04**: The index applies an SII economic-activity exposure denominator with a documented cap (fall back to INE population when `sii_workers / ine_population` exceeds the threshold) to prevent firm-HQ-domicile distortion.
- [x] **CI-05**: A user sees the index as an integer 0–100 with one of 5 labeled bands in the map popup, the ResultPanel, and comuna pages, plus the comuna's national and regional rank on the index.
- [x] **CI-06**: Every page that displays the index renders a mandatory bilingual caveat block (composite of *reported* crime burden, the sources, the data vintage, and the SII firm-domicile caveat) — no absolute safety verdict.
- [x] **CI-07**: The choropleth offers a toggle between index mode and the existing per-family rate mode (5 binned classes each); the popup shows the exact index score.
- [x] **CI-08**: The EN + ES methodology pages document the composite formula, the chosen normalization method, the SPD homicide switch, and the SII exposure caveat; every new figure is registered (figure-registry zero-orphan passes).
- [x] **CI-09**: The forbidden-language CI validator is extended to flag "safest / most dangerous / más segura / más peligrosa" (and equivalents) when not qualified by "reported / reportado", and runs in `npm run validate`.
- [x] **CI-10**: The `featured_rates`→7-metric schema migration is verified non-breaking across every consumer (commune panel, choropleth, Astro templates, figure-registry validator, pytest), with TypeScript types added and `@astrojs/check` + full validator suite green; `comparator_table.json` is emitted for Track 2.

### Track 2 — Commune Comparator + A-vs-B SEO (→ Phase 21)

- [ ] **CMP-01**: A user can compare 2–3 comunas side by side in an interactive island showing the composite index headline, per-family breakdown, per-family trend indicator, and a "compare to national/regional average" column.
- [ ] **CMP-02**: The comparator offers accent-insensitive autocomplete search across all 346 comunas, layered on a pre-rendered static HTML shell (comparator landing page is indexable).
- [ ] **CMP-03**: Bilingual A-vs-B programmatic pages are generated from a curated priority-pair allowlist (`data/comparator-pairs.json`), using CUT-code URL slugs with alphabetical ordering so each pair has a single canonical page (no A-vs-B / B-vs-A duplication).
- [ ] **CMP-04**: Each A-vs-B page carries ≥5 differentiating uniqueness blocks and ≥300 words of non-swappable prose (index difference, per-family rate table, trend narrative, national rank, regional context); a build-time thin-content assertion blocks pages that fall short.
- [ ] **CMP-05**: The build asserts total page count stays under the Cloudflare free-tier safety bound (<18,000 files).
- [ ] **CMP-06**: hreflang reciprocity and the cross-link spine validators are extended to cover A-vs-B pages, and every comuna page links to 3–5 relevant A-vs-B pairs.
- [ ] **CMP-07**: A-vs-B prose quality is acceptance-checked on a random sample (≥10 pairs) before deploy, and pages publish in staged batches (~20 pairs) with GSC indexing verified between batches.

### Track 3 — Go-Live / Launch Ops (→ Phase 22)

- [ ] **GL-01**: The `CF_DEPLOY_HOOK_URL` GitHub secret is set and verified with a test push (CF dashboard shows the triggered build) — done before any v2.0 code merge depends on a live deploy.
- [ ] **GL-02**: Production is rebuilt from `master` and reflects v2.0 content, and the rebuild-loop guard is confirmed intact (data-only commits do not increment the CF build count).
- [ ] **GL-03**: A live news pipeline run executes (`DEEPSEEK_API_KEY` secret) followed by a 50-incident commune-assignment hallucination audit.
- [ ] **GL-04**: An updated sitemap is submitted to Google Search Console immediately after first deploy, with URL Inspection on 5–10 representative comuna + A-vs-B pages.

### Track 4 — ENUSC Communal Victimization Layer (→ Phase 23, runs before Phase 22)

_Origin: SEED-002 feasibility study (Design A) — `.planning/research/SEED-002-FINDINGS.md`. Anti-infra-representation: ENUSC is the only inventoried source measuring **unreported** crime (cifra negra) at comuna level. Strictly additive vs Phase 18._

- [x] **VL-01**: A new isolated pipeline step ingests the INE ENUSC 2024 SAE VHDV (Victimización en Hogares por Delitos Violentos) Excel from a **versioned in-repo snapshot** into a data artifact with provenance (source URL, retrieval date, INE experimental disclaimer, checksum); it runs after the CEAD scraper and fails gracefully without breaking the CEAD pipeline if absent/malformed. (Manual/assisted annual acquisition — no stable static URL; behind INE's JS "Cuadros Estadísticos" widget.)
- [x] **VL-02**: The ~136 covered comunas map to valid CUT codes (reusing the existing name→CUT resolver); a build-time assertion confirms every ingested row resolves to a valid CUT and the coverage count equals the published N; unresolved rows fail the build loudly.
- [x] **VL-03**: Each covered comuna page (EN + ES) shows the VHDV victimization figure with value + reference year (2024) + a mandatory bilingual caveat labeling it an INE **experimental, SAE-modeled** estimate distinct from CEAD reported-crime — never an absolute verdict; the forbidden-language validator exits 0.
- [x] **VL-04**: The ~210 non-covered comunas render an explicit bilingual "no ENUSC victimization estimate for this comuna (coverage: 136 comunas)" note with no broken layout and no implied value.
- [x] **VL-05**: Every new figure is registered in the F-series figure registry (zero-orphan passes) and documented in SOURCES.md + EN/ES methodology pages (source, SAE method, experimental status, coverage limitation, victimization ≠ reported-crime distinction); a verification confirms the composite index and **all Phase-18 outputs are byte-unchanged** (additive-only).

---

## Future Requirements (deferred)

- **AdSense activation + Consent Mode v2** — wire `gtag` consent default (`ad_storage: denied`) + cookie banner, verify via Tag Assistant, then flip `ADSENSE_ENABLED`. Deferred out of v2.0 by decision (ads stay off this milestone); monetization is a later cycle.
- **A-vs-B expansion beyond the priority allowlist** — only after GSC validates the initial staged batches.
- **3-column comparator polish / additional comparator dimensions** — incremental over the 2–3 comuna baseline.

## Out of Scope

- **User-configurable index weight sliders** — incompatible with static pre-rendering; invites false-precision misuse.
- **Confidence intervals / error bars on the index** — backfires with lay users (CEAD error is systematic, not random); use data-vintage caveats instead.
- **Star ratings / absolute "safe/dangerous" verdicts** — editorial-language constraint; the site reports relative incidence only.
- **Real-time index updates** — CEAD is quarterly, SPD VHC annual; rebuild cadence suffices.
- **New backend / database / state manager** — v2.0 stays 100% static JSON-in-repo.

## Traceability

| REQ-ID | Phase | Status | Notes |
|--------|-------|--------|-------|
| CI-01 | Phase 18 | Complete | Isolated build_composite_index.py step |
| CI-02 | Phase 18 | Complete | Winsorization / percentile-rank normalization + pytest assertion |
| CI-03 | Phase 18 | Complete | SPD VHC as M5; CEAD featured_rates.homicidios preserved |
| CI-04 | Phase 18 | Complete | SII exposure denominator with documented cap |
| CI-05 | Phase 18 | Complete | 0–100 integer + 5 bands + national/regional rank in UI |
| CI-06 | Phase 18 | Complete | Mandatory bilingual caveat block on all index-displaying pages |
| CI-07 | Phase 18 | Complete | Choropleth toggle: index mode vs per-family rate mode |
| CI-08 | Phase 18 | Complete | Methodology pages updated; figure-registry zero-orphan |
| CI-09 | Phase 18 | Complete | Forbidden-language validator extended; npm run validate green |
| CI-10 | Phase 18 | Complete | Schema migration non-breaking; TypeScript types; comparator_table.json emitted |
| CMP-01 | Phase 21 | Pending | 2–3 commune comparator island; depends on Phase 18 |
| CMP-02 | Phase 21 | Pending | Accent-insensitive autocomplete; pre-rendered static shell |
| CMP-03 | Phase 21 | Pending | A-vs-B pages from curated allowlist; CUT-code slugs; alphabetical ordering |
| CMP-04 | Phase 21 | Pending | ≥5 uniqueness blocks + ≥300 non-swappable words; build-time assertion |
| CMP-05 | Phase 21 | Pending | Total page count < 18,000 asserted at build time |
| CMP-06 | Phase 21 | Pending | hreflang + spine validators extended; commune pages link to 3–5 pairs |
| CMP-07 | Phase 21 | Pending | Sample acceptance check ≥10 pairs; staged batches ~20 pairs |
| GL-01 | Phase 22 | Pending | CF_DEPLOY_HOOK_URL secret set + verified; parallel with Phase 21 |
| GL-02 | Phase 22 | Pending | Production rebuilt from master; rebuild-loop guard confirmed |
| GL-03 | Phase 22 | Pending | Live news pipeline run + 50-incident commune audit |
| GL-04 | Phase 22 | Pending | Sitemap submitted to GSC; URL Inspection on 5–10 pages |
| VL-01 | Phase 23 | Complete | Isolated ENUSC SAE VHDV ingest from versioned snapshot + provenance; fails gracefully |
| VL-02 | Phase 23 | Complete | ~136 comunas → valid CUT via existing resolver; build-time coverage assertion |
| VL-03 | Phase 23 | Complete | EN/ES victimization figure + experimental/SAE caveat; forbidden-language green |
| VL-04 | Phase 23 | Complete | ~210 uncovered comunas degrade with explicit bilingual "no estimate" note |
| VL-05 | Phase 23 | Complete | F-series zero-orphan + SOURCES/methodology; Phase-18 outputs byte-unchanged (additive) |

**Coverage:** 26/26 requirements mapped — CI-01..CI-10 → Phase 18, CMP-01..CMP-07 → Phase 21, GL-01..GL-04 → Phase 22, VL-01..VL-05 → Phase 23 (runs before 22). No orphans.

---
*Defined 2026-06-19 for milestone v2.0. 26 requirements across 4 tracks (Track 4 / VL added 2026-06-19 from SEED-002).*
