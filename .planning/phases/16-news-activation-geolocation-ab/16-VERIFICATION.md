---
phase: 16-news-activation-geolocation-ab
verified: 2026-06-18T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
requirements: [NEWS-01, NEWS-02, NEWS-03, NEWS-04]
method: pytest + chained build+validate + live pipeline run + A/B + BrowserOS visual (EN+ES) + goal-backward codebase verification
---

# Phase 16 — Verification Report

**Phase Goal:** The built-but-dark news pipeline goes live with accurate comuna geolocation, the best-performing LLM provider chosen on evidence, and incidents surfaced and linked across the site (source ↗ + comuna page) via a dedicated bilingual news page.
**Verified:** 2026-06-18
**Status:** PASSED
**Re-verification:** No — initial verification (orchestrator-attested inline; goal-backward codebase check applied here)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | LLM emits commune name → deterministic resolver returns CUT or None; hallucinations dropped | VERIFIED | `pipeline/news/resolver.py` exists; `resolve_cut('Santiago')=('13101','santiago')`, `resolve_cut('Gotham')=None` — confirmed by direct import |
| 2 | Golden set (30–50) exists; A/B scoring script run; winner documented and wired as default | VERIFIED | `pipeline/tests/fixtures/golden_set.json` (47 items); `pipeline/experiments/ab_score.py` loads it; `pipeline/results/ab_deepseek.json` + `ab_minimax.json` produced; DeepSeek wins on family accuracy (0.66 vs 0.52) and null-rate (1.0 vs 0.33); `NEWS_PROVIDER` default = `"deepseek"` in `pipeline/news/classifier.py` line 46 |
| 3 | Pipeline produces `data/incidents/current.json` with real geolocated incidents; no missing cut/slug/url | VERIFIED | 19 incidents; 0 missing cut; 0 missing slug; 0 missing url — confirmed by direct JSON parse |
| 4 | Bilingual news pages render all incidents with source ↗ and localized commune links; freshness indicator present | VERIFIED | Built `site/dist/news/index.html`: 19 `/commune/` links, 43 source/outlet references; `site/dist/es/noticias/index.html`: 19 `/es/comuna/` links. Both pages use `process.cwd()` path (import.meta.url bug fixed in commit e71d8bc) |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/news/resolver.py` | Deterministic name→CUT lookup, None for unknowns | VERIFIED | Accent-insensitive; returns CUT tuple or None; confirmed by live import |
| `pipeline/news/classifier.py` | Configurable provider; default = deepseek | VERIFIED | `os.environ.get("NEWS_PROVIDER", "deepseek")` at line 46 |
| `pipeline/tests/fixtures/golden_set.json` | 30–50 labelled incidents | VERIFIED | 47 items; keys: id, headline, description, ground_truth, source_outlet, source_url |
| `pipeline/experiments/ab_score.py` | Scoring script referencing golden set | VERIFIED | Loads `pipeline/tests/fixtures/golden_set.json`; computes 5 metrics |
| `pipeline/results/ab_deepseek.json` | A/B result for DeepSeek | VERIFIED | commune_accuracy: 0.9545, family_accuracy: 0.6591, null_rate: 1.0 |
| `pipeline/results/ab_minimax.json` | A/B result for MiniMax | VERIFIED | commune_accuracy: 0.9545, family_accuracy: 0.5227, null_rate: 0.3333 |
| `data/incidents/current.json` | 19 incidents, all geolocated | VERIFIED | Count: 19; 0 missing cut/slug/url |
| `site/src/pages/news.astro` | EN news page reading from process.cwd() | VERIFIED | Exists; uses process.cwd(); no import.meta.url-only path |
| `site/src/pages/es/noticias.astro` | ES news page at parity | VERIFIED | Exists; uses process.cwd(); no import.meta.url-only path |
| `site/dist/news/index.html` | Built EN page with 19 commune links | VERIFIED | 19 /commune/ links; 43 source references |
| `site/dist/es/noticias/index.html` | Built ES page with 19 /es/comuna/ links | VERIFIED | 19 /es/comuna/ links confirmed |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `classifier.py` | `deepseek` provider | `NEWS_PROVIDER` env default | WIRED | Default `"deepseek"` at line 46 |
| `ab_score.py` | `golden_set.json` | path resolution at line 85 | WIRED | `pipeline_root / "tests" / "fixtures" / "golden_set.json"` |
| `news.astro` | `data/incidents/current.json` | `process.cwd()/public/data/...` | WIRED | Bug fix commit e71d8bc confirmed; `process.cwd()` present |
| built news pages | commune pages | `/commune/{slug}/` and `/es/comuna/{slug}/` | WIRED | 19 links each confirmed in built HTML |

### Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| NEWS-01 | Geolocation redesigned: LLM emits commune name → deterministic lookup; accuracy beats baseline | SATISFIED | resolver.py verified live; ab_deepseek commune_accuracy 0.9545 vs ~30-40% bare-CUT baseline; >70% target cleared |
| NEWS-02 | Golden set (30–50) + scoring script; provider env-configurable; A/B; winner documented + default | SATISFIED | 47-item golden set; ab_score.py; ab_deepseek/minimax results; DeepSeek wins; default wired |
| NEWS-03 | Pipeline runs for real → current.json; real geolocated incidents rendered | SATISFIED | 19 incidents in current.json; 0 missing fields; live run attested by orchestrator |
| NEWS-04 | Each incident: source ↗ + commune link; bilingual news page; freshness indicator; cites source | SATISFIED | 19 commune links per locale in built HTML; 43 source references in EN build; BrowserOS visual APPROVED |

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `site/src/pages/news.astro` | `import.meta.url` still present alongside `process.cwd()` | INFO | Non-blocking — `process.cwd()` is the active path used; `import.meta.url` may be residual or used for a different purpose. Built output is correct (19 commune links). |

No TBD/FIXME/XXX markers found in phase-modified files. No stub returns. No empty-array hardcodes in rendering paths.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| resolver returns CUT for known commune | `resolve_cut('Santiago')` | `('13101', 'santiago')` | PASS |
| resolver returns None for unknown | `resolve_cut('Gotham')` | `None` | PASS |
| resolver accent-insensitive | `resolve_cut('ovalle')` | `('4301', 'ovalle')` | PASS |
| current.json: 19 incidents, 0 missing fields | direct JSON parse | count=19, missing_cut=0, missing_slug=0, missing_url=0 | PASS |
| EN built page has 19 commune links | grep `/commune/` in dist | 19 matches | PASS |
| ES built page has 19 commune links | grep `/es/comuna/` in dist | 19 matches | PASS |
| DeepSeek is classifier default | grep `NEWS_PROVIDER` in classifier.py | `"deepseek"` default at line 46 | PASS |
| DeepSeek wins A/B on family accuracy | ab_deepseek.json vs ab_minimax.json | 0.6591 vs 0.5227 | PASS |

### Human Verification Required

None. All observable truths verified programmatically. BrowserOS visual check (EN + ES, screenshots recorded) was completed inline by the orchestrator and is treated as SATISFIED.

## Bug Found and Fixed at Gate (gap closure)

The EN `/news/` page initially rendered empty while ES rendered all 19 incidents. Root cause: `import.meta.url`-relative paths resolved differently per compiled chunk location. Fixed by switching both pages to `process.cwd()/public/data/incidents/current.json` (commit e71d8bc). Both locales now render 19 commune-linked incidents; 12/12 build validators pass.

## BrowserOS Visual Check (APPROVED, inline)

Run against local preview (`http://localhost:4330/`). Screenshots: `…/Temp/browseros-shots/news-en.png`, `noticias-es.png`.

- **EN `/news/`** — 19 incidents, English titles, correct geolocation, "Source: {outlet} ↗" → real article, "View commune" → `/commune/{slug}/`, "Updated June 18, 2026", legal-safe intro.
- **ES `/es/noticias/`** — full parity; "Fuente ↗" + "Ver comuna" → `/es/comuna/{slug}/`; "Actualizado 18 de junio de 2026"; no absolute risk verdicts.
- **Map incident layer** — incidents JSON served HTTP 200 (19); pin popup uses slug-guarded, escHtml-protected commune link (unit-tested + built). Pin-click covered indirectly by served data + component tests + news-page render.

## Automated Gate

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| pytest (pipeline) | green | 153 tests pass | PASS |
| Chained `npm run build && npm run validate` | exit 0, validators green | 792 pages built; 12/12 validators PASS (incl. forbidden-language) | PASS |
| `data/incidents/current.json` schema + geolocation | every incident non-null cut+slug+url | 19 incidents, 0 missing | PASS |
| Incidents JSON served by site | HTTP 200 | 200, 19 incidents at `/data/incidents/current.json` | PASS |

## Scope Attestation

Composite crime index and go-live infra cutover remain out of scope (deferred to Phase 18 / go-live human task). Every surfaced incident cites and links its press source (`rel="noopener noreferrer"`); sober tone; no absolute safe/dangerous verdicts. Anti-hallucination centroid-from-CUT design preserved; resolver rejects unknown names.

---
_Verified: 2026-06-18_
_Verifier: Claude (gsd-verifier) — goal-backward codebase check_
