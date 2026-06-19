---
status: passed
phase: 16-news-activation-geolocation-ab
gate: phase-verification
requirements: [NEWS-01, NEWS-02, NEWS-03, NEWS-04]
verified: 2026-06-18
method: pytest + chained build+validate + live pipeline run + A/B + BrowserOS visual (EN+ES)
---

# Phase 16 — Verification Gate

**Phase Goal:** The built-but-dark news pipeline goes live with accurate comuna geolocation, the best-performing LLM provider chosen on evidence, and incidents surfaced and linked across the site (source ↗ + comuna page) via a dedicated bilingual news page.

**Result: PASSED.** All four requirements attested with concrete, live evidence.

## Automated gate

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| pytest (pipeline) | green | 153 tests pass | ✅ |
| Chained `npm run build && npm run validate` (OneDrive-safe) | exit 0, validators green | 792 pages built; **12/12 validators PASS** (incl. forbidden-language) | ✅ |
| `data/incidents/current.json` schema + geolocation | every incident non-null cut+slug+url | 19 incidents, 0 missing cut/slug, 19/19 with source url | ✅ |
| Incidents JSON served by site | HTTP 200 | 200, 19 incidents at `/data/incidents/current.json` | ✅ |

## Per-requirement attestation

| Req | Statement | Evidence | Status |
|-----|-----------|----------|--------|
| **NEWS-01** | Geolocation redesigned: LLM emits comuna NAME → deterministic name→CUT resolver (None for unknown); accuracy beats bare-CUT baseline | `pipeline/news/resolver.py` (accent-insensitive from `index.json`, `Gotham`→None); golden-set **commune_accuracy 0.9545** vs ~30-40% bare-CUT baseline (>70% target cleared); resolver returns None → orchestrator drops hallucinations | ✅ PASS |
| **NEWS-02** | Labelled golden set (30-50) + scoring script; provider env-configurable; A/B DeepSeek vs MiniMax; winner documented + default | `golden_set.json` (47 items); `ab_score.py` (5 metrics) → `results/ab_{deepseek,minimax}.json`; **DeepSeek wins** (family 0.66 vs 0.52, null-rate 1.0 vs 0.33, ~2.7× cheaper, faster) → `16-AB-RESULTS.md`; `NEWS_PROVIDER` default = `deepseek` | ✅ PASS |
| **NEWS-03** | Pipeline runs for real → `current.json`; pins + recent-incidents render real geolocated incidents, no errors | live `python -m pipeline.scrape_news` → 19 incidents (classified=19, rejected=16, exit 0); all geolocated correctly (Sotaquí→Ovalle, Bellavista→Recoleta, Colchane, Lo Espejo, Ercilla, Melipilla…); malformed LLM JSON gracefully rejected | ✅ PASS |
| **NEWS-04** | Each incident links to source ↗ AND comuna page; dedicated bilingual news page; freshness indicator; every incident cites+links source | `/news/` (EN) + `/es/noticias/` (ES) both render all 19 incidents with "Source/Fuente ↗" + "View/Ver comuna" links (EN `/commune/`, ES `/es/comuna/` — localized slug correct); "Updated/Actualizado 18 jun 2026" freshness; legal-safe intro; `IncidentsList.tsx` + pin popup extended (slug-guarded, escHtml) | ✅ PASS |

## Bug found & fixed at the gate (gap closure)

The EN `/news/` page initially rendered **empty** (empty-state) while ES rendered all 19 — a bilingual-parity defect. Root cause: `import.meta.url`-relative data paths are unstable at Astro build time (compiled chunk locations differ per page; EN's `../../../` resolved to a missing path). Fixed both pages to resolve from `process.cwd()/public/data/incidents/current.json` (the prebuild-synced copy, identical for both files). Commit `e71d8bc`. Rebuilt → both EN+ES render 19 commune-links; 12/12 validators still pass. See memory `news-page-build-path-drift`.

## BrowserOS visual check (checkpoint, APPROVED)

Driven inline against local preview (`http://localhost:4330/`). Screenshots: `…/Temp/browseros-shots/news-en.png`, `noticias-es.png`.
- **EN `/news/`** — 19 incidents, English titles, correct geolocation, "Source: {outlet} ↗" → real article, "View commune" → `/commune/{slug}/`, "Updated June 18, 2026", legal-safe "no absolute risk verdicts" intro.
- **ES `/es/noticias/`** — full parity; "Fuente ↗" + "Ver comuna" → `/es/comuna/{slug}/` (localized slug correct); "Actualizado 18 de junio de 2026"; "no se emiten veredictos absolutos".
- **Map incident layer** — incidents JSON served HTTP 200 (19); map island (`map-island`/`IncidentPinLayer`) present; pin popup uses the same slug-guarded, escHtml-protected comuna link (unit-tested + built). Pin-click not exercised live (BrowserOS console tool unavailable) — covered indirectly by served data + component tests + identical news-page render.

## Scope / editorial attestation

Composite crime index and go-live infra cutover remain out of scope (deferred). Every surfaced incident cites and links its press source (`rel="noopener noreferrer"`); sober tone; no absolute safe/dangerous verdicts. Anti-hallucination centroid-from-CUT design preserved; resolver rejects unknown names.
