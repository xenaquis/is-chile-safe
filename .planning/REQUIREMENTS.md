# REQUIREMENTS — Milestone v1.3 Data Quality Hardening & Methodology

**Defined:** 2026-06-19
**Source:** v1.3 swarm review (`v1.3-REVIEW-FINDINGS.md`, `v1.3-METHODOLOGY-SPEC.md`, `v1.3-DECISIONS.md`). 0 blockers, 4 high, 24 actionable.
**Goal:** Eliminate accumulated tech debt AND make every quantitative figure on the site explained + sourced+linked + caveated + EN/ES-parity — zero displayed number without a registry entry.

Each requirement traces to one or more review finding IDs. Severity from the review carries over (high = strongly recommended this milestone).

---

## v1.3 Requirements

### Tech Debt & Correctness (→ Phase 19)

- [x] **TD-01**: Methodology EN+ES correctly state the national mean is an **unweighted** mean of non-low-population commune rates (a typical-commune figure), matching `data.ts` and the is-chile-safe FAQ — no "population-weighted" claim anywhere user-facing. *(MC-01, MC-07 — high)*
- [x] **TD-02**: The stale `map_placeholder_text` ("map coming soon" / "disponible próximamente") no longer renders anywhere; the live map is the only map surface. *(charter §2; map is live)*
- [x] **TD-03**: News incidents render newest-first (sorted by `date` desc) on `/news/` and `/es/noticias/` (and any pin list). *(IN-03)*
- [ ] **TD-04**: `/crime/homicide/` (vida-family aggregate, ambiguous "homicide" slug) redirects to its canonical target — no orphaned, editorially-ambiguous duplicate URL. *(COMU-03; DECISIONS c = redirect)*
- [x] **TD-05**: Incident source URLs are validated by `new URL()` + protocol whitelist (http/https) both in `news.astro`/`noticias.astro` and in the pipeline (`build_incident`/`canonical_url`); non-http(s) URLs are dropped, not rendered. *(CQ-01, CQ-02)*
- [x] **TD-06**: `map-payload-*.json` carries an explicit `partial_year` flag so the frontend can caveat partial years (e.g. 2025). *(DQ-MAP-PAYLOAD-2025-NO-PARTIAL-FLAG)*
- [x] **TD-07**: Residual code tech-debt from PROJECT.md is closed: CI assertion for `FAMILY_KEYS` order, typed `by_family`, dynamic `AVAILABLE_YEARS`, `nyquist_compliant` flags reconciled for phases 4–6, and any skipif/xfail test cruft removed. *(PROJECT.md tech-debt line)*

### Bilingual Parity (→ Phase 19)

- [x] **BIL-01**: All user-visible Spanish strings use "comuna" (not the English/French "commune") — including meta descriptions, JSON-LD, and RateTooltip labels; JS identifiers (`communeCount`, `loadCommune`) untouched. *(BP-02 — high)*
- [x] **BIL-02**: `/es/delitos-por-region/` is no longer an orphan: it has a reciprocal EN counterpart with correct bidirectional hreflang, and the language toggle does not self-loop. *(BP-01 — high)*
- [x] **BIL-03**: No stray English words remain in Spanish prose (e.g. "la adjacent ciudad" → "la ciudad vecina"). *(BP-03)*
- [x] **BIL-04**: Hardcoded section headings, table headers, and the cookie-consent strings are sourced from `i18n.ts` (single source of truth), not duplicated literals per locale. *(BP-04, BP-05, BP-06, BP-08)*

### SEO & Spine (→ Phase 19)

- [ ] **SEO-01**: `/is-santiago-safe/` and `/es/mapa-seguridad-santiago/` form a correct reciprocal hreflang pair; ES users are not sent to the EN page by the toggle. *(SEO-01)*
- [ ] **SEO-02**: `site/public/robots.txt` exists with an `Allow` rule and a `Sitemap:` pointer to the sitemap index. *(SEO-04)*
- [ ] **SEO-03**: Glossary is reachable from nav and/or footer (locale-aware `/glossary/`, `/es/glosario/`), and ranking routes have explicit sitemap inclusion rules (no silent catch-all). *(SEO-02, SEO-03)*

### Methodology Completeness (→ Phase 20)

- [ ] **MTH-01**: Every displayed aggregate figure that is an unweighted commune mean (per-family `familyNationalMean`, per-region breakdowns) carries an inline caveat AND is explained in the methodology (EN+ES). *(MC-02, MC-04)*
- [ ] **MTH-02**: The 1–5 LevelChip incidence classification shown on every commune hero is explained in the methodology as a relative tier scale derived from the non-low-pop rate distribution (EN+ES). *(MC-05)*
- [ ] **MTH-03**: The drogas scope note (Ley 20.000 only) renders inline where the drogas figure appears (FamilyBreakdownBars), and trend/sparkline links deep-link to `#trend-formula`. *(MC-09, MC-06)*
- [ ] **MTH-04**: `methodology.astro` and `es/metodologia.astro` are at structural parity (matching H2 sections + attribution/table-note blocks), and a CI validator asserts forbidden-language (no non-attributed absolute "safe/dangerous" / "seguro/peligroso"). *(MC-10; charter validator #9)*

### Sources Expansion (→ Phase 20)

- [ ] **SRC-01**: `data/SOURCES.md` has a first-class **INE** section (official URL, measure semantics, vintage, fetch script, third-party-mirror caveat), and a CI spot-check compares ≥5 commune populations against official INE. *(SC-01, SC-02)*
- [ ] **SRC-02**: `data/SOURCES.md` has an **ENUSC** section (URL, publisher, measure semantics, vintage, licence), and the methodology's underreporting/cifra-negra claims carry an inline citation link to it. *(SC-03 — high)*
- [ ] **SRC-03**: `data/SOURCES.md` documents the **Subsecretaría de Prevención del Delito** (parent of CEAD) and the CEAD grupo/subgrupo **taxonomy provenance** (ajax_2.php seleccion=9), clarifying the chain of authority. *(SC-04, SC-07)*
- [ ] **SRC-04**: The editorial methodology parameters (5% trend threshold, 3-year window, 10,000-inhabitant low-pop exclusion) are documented in `data/SOURCES.md`/methodology as editorial with rationale. *(SC-05, SC-06)*
- [ ] **SRC-05**: Every quantitative figure displayed on the site maps to a `data/SOURCES.md` registry entry (the figure registry from `v1.3-METHODOLOGY-SPEC.md`) — zero orphan numbers. *(METHODOLOGY-SPEC goal; milestone definition of done)*

---

## Future Requirements (deferred)

- **Phase 18 — Composite Crime Index & Metric Redesign** (next milestone after v1.3): exposure-adjusted composite index (SII denominator), SPD VHC homicide metric, `featured_rates`→7-metric schema, secuestro (Fiscalía, region-level), index-driven choropleth. Inputs hardened by v1.3.
- SII / Fiscalía-secuestro / SPD-VHC snapshots promoted to first-class sources **at Phase 18** (when wired into displayed figures) — kept as stubs in v1.3. *(DECISIONS b)*
- Interactive commune comparator + A-vs-B programmatic SEO pages (SEED-001 leftovers) — future SEO milestone.

## Out of Scope (v1.3)

- **Go-live / deploy infra** (set `CF_DEPLOY_HOOK_URL`, CF redeploy, DNS, AdSense consent) — human/ops, tracked in `DEPLOYMENT.md` + STATE Deferred Items; not a code requirement. (Note: prod is currently stale because the hook secret is unset.)
- **New data sources beyond INE/ENUSC/SPD** — only authoritative backers of an already-displayed figure are in scope; no new datasets.
- **Prior-milestone P08/P10 human-UAT items** — closed as superseded (DECISIONS a); not carried.
- **Any new displayed metric or index** — reserved for Phase 18.

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| TD-01 | 19 | Complete |
| TD-02 | 19 | Complete |
| TD-03 | 19 | Complete |
| TD-04 | 19 | Pending |
| TD-05 | 19 | Complete |
| TD-06 | 19 | Complete |
| TD-07 | 19 | Complete |
| BIL-01 | 19 | Complete |
| BIL-02 | 19 | Complete |
| BIL-03 | 19 | Complete |
| BIL-04 | 19 | Complete |
| SEO-01 | 19 | Pending |
| SEO-02 | 19 | Pending |
| SEO-03 | 19 | Pending |
| MTH-01 | 20 | Pending |
| MTH-02 | 20 | Pending |
| MTH-03 | 20 | Pending |
| MTH-04 | 20 | Pending |
| SRC-01 | 20 | Pending |
| SRC-02 | 20 | Pending |
| SRC-03 | 20 | Pending |
| SRC-04 | 20 | Pending |
| SRC-05 | 20 | Pending |

*Confirmed by roadmapper 2026-06-19. Coverage: 23/23 individual requirements mapped (TD-01..07 = 7, BIL-01..04 = 4, SEO-01..03 = 3, MTH-01..04 = 4, SRC-01..05 = 5 — total 23). Zero orphans.*
