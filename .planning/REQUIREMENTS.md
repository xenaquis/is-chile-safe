# REQUIREMENTS — Milestone v2.0 Composite Index, Comparators & Launch

**Defined:** 2026-06-19
**Source:** v2.0 milestone research (`.planning/research/SUMMARY.md` + STACK/FEATURES/ARCHITECTURE/PITFALLS) and SEED-001 (comparator + A-vs-B, locked constraints).
**Goal:** Redesign the core safety metric into an exposure-adjusted composite index, build a commune comparator + curated A-vs-B SEO pages on top of it, and execute the production go-live.

**Tracks & dependency:** Track 1 (Composite Index, Phase 18 — reserved #) → Track 2 (Comparator + A-vs-B, Phase 21) is a **hard dependency** (the comparator headline number and A-vs-B prose need a computed index). Track 3 (Go-Live, Phase 22) has no code dependency and can run in parallel with Phase 21.

**Locked constraints (carry through all tracks):** hybrid rollout (display all comunas, never 404/link to non-rollout pages); never an absolute "seguro/peligroso / safe/dangerous" verdict — a sortable single score implies a verdict through rank + color alone, so editorial framing + the CI validator must guard it; no thin content; static / SEO-indexable; every displayed figure explained + sourced + caveated with EN/ES parity (figure-registry zero-orphan).

---

## v2.0 Requirements

### Track 1 — Composite Crime Index (→ Phase 18)

- [ ] **CI-01**: The pipeline computes a 0–100 composite crime-exposure index per comuna from the 7 defined metrics and writes it (additive, non-breaking) into per-comuna JSON, in an isolated `build_composite_index.py` step that does not break the CEAD scraper if it fails.
- [ ] **CI-02**: The index normalizes per-metric distributions with winsorization or percentile-rank (never raw min-max), so right-skewed micro-comuna outliers don't collapse the scale; a pytest distribution assertion guards the spread.
- [ ] **CI-03**: SPD VHC is the homicide input to the index (M5), reference year capped at the latest fully-consolidated year (≤2024); CEAD grupo-101 `featured_rates.homicidios` is preserved unchanged for backward compatibility.
- [ ] **CI-04**: The index applies an SII economic-activity exposure denominator with a documented cap (fall back to INE population when `sii_workers / ine_population` exceeds the threshold) to prevent firm-HQ-domicile distortion.
- [ ] **CI-05**: A user sees the index as an integer 0–100 with one of 5 labeled bands in the map popup, the ResultPanel, and comuna pages, plus the comuna's national and regional rank on the index.
- [ ] **CI-06**: Every page that displays the index renders a mandatory bilingual caveat block (composite of *reported* crime burden, the sources, the data vintage, and the SII firm-domicile caveat) — no absolute safety verdict.
- [ ] **CI-07**: The choropleth offers a toggle between index mode and the existing per-family rate mode (5 binned classes each); the popup shows the exact index score.
- [ ] **CI-08**: The EN + ES methodology pages document the composite formula, the chosen normalization method, the SPD homicide switch, and the SII exposure caveat; every new figure is registered (figure-registry zero-orphan passes).
- [ ] **CI-09**: The forbidden-language CI validator is extended to flag "safest / most dangerous / más segura / más peligrosa" (and equivalents) when not qualified by "reported / reportado", and runs in `npm run validate`.
- [ ] **CI-10**: The `featured_rates`→7-metric schema migration is verified non-breaking across every consumer (commune panel, choropleth, Astro templates, figure-registry validator, pytest), with TypeScript types added and `@astrojs/check` + full validator suite green; `comparator_table.json` is emitted for Track 2.

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

| REQ-ID | Phase | Notes |
|--------|-------|-------|
| CI-01..CI-10 | Phase 18 | (filled by roadmap) |
| CMP-01..CMP-07 | Phase 21 | depends on Phase 18 |
| GL-01..GL-04 | Phase 22 | parallel with Phase 21 |

---
*Defined 2026-06-19 for milestone v2.0. 21 requirements across 3 tracks.*
