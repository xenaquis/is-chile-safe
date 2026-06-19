---
phase: 16
slug: news-activation-geolocation-ab
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-18
---

# Phase 16 — Validation Strategy

> Derived from `16-RESEARCH.md` § Validation Architecture. The fix is the geolocation DESIGN
> (LLM emits comuna NAME → deterministic name→CUT resolver), not a vendor switch.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (`pipeline/tests/`) + Node validators (`site/scripts/validate/all.mjs`) + Vitest (frontend, if present) |
| **Config file** | `pipeline/pytest.ini` / `pipeline/pyproject.toml` |
| **Quick run command** | `cd pipeline && python -m pytest tests/test_resolver.py tests/test_classifier.py -x -q` |
| **Full suite command** | `cd pipeline && python -m pytest tests/ -q ; cd ../site && npm run build && npm run validate` |
| **Estimated runtime** | ~90–150s (build dominates) |

---

## Sampling Rate

- **After every task commit:** `cd pipeline && python -m pytest tests/test_resolver.py tests/test_classifier.py -x -q`
- **After every wave:** full pytest + (for frontend waves) chained `npm run build && npm run validate`
- **Phase gate:** full suite green + golden-set accuracy beats baseline + BrowserOS render check (EN+ES news page, pins, both link types)
- **Max feedback latency:** ~150s

---

## Per-Requirement Verification Map

| Req | Behavior | Test Type | Automated Signal | File Exists |
|-----|----------|-----------|------------------|-------------|
| NEWS-01 | Resolver: known headline → correct CUT | unit | `pytest tests/test_resolver.py -x` | ❌ W0 |
| NEWS-01 | Resolver: accent-insensitive (Cochamó→cochamo) | unit | `pytest tests/test_resolver.py::test_accent_insensitive` | ❌ W0 |
| NEWS-01 | Resolver: unknown name → None (no hallucinated CUT) | unit | `pytest tests/test_resolver.py::test_unknown_name_returns_none` | ❌ W0 |
| NEWS-01 | Golden-set comuna accuracy beats bare-CUT baseline (~30-40%), target >70% | integration | golden-set scoring output | ❌ W0 |
| NEWS-02 | A/B: DeepSeek + MiniMax scored on comuna/family accuracy, latency, cost, reliability | integration | `python pipeline/experiments/ab_score.py --provider {deepseek,minimax}` → `results/ab_*.json` | ❌ W0 |
| NEWS-02 | Winner documented + wired as env default | doc + config | `16-VERIFICATION.md` records winner; provider env-configurable | ❌ W0 |
| NEWS-03 | `data/incidents/current.json` validates against schema; all incidents non-null cut+slug | unit | `pytest tests/test_schema_incidents.py -x` + schema check | partial |
| NEWS-03 | Pipeline runs without error (keys set); graceful exit-0 if absent | smoke | `python pipeline/scrape_news.py` | manual/gated |
| NEWS-04 | `IncidentsList.tsx` renders source link + comuna link | unit/build | build + BrowserOS | ❌ W0 |
| NEWS-04 | `/news/` + `/es/noticias/` build with correct hreflang | smoke | `npm run build && npm run validate` | automated |
| NEWS-04 | Incident pin popup + news page render real geolocated incidents, no console error | BrowserOS | navigate + console check | manual |

---

## Wave 0 Requirements (new files)

- [ ] `pipeline/news/resolver.py` — deterministic name→CUT (source: `data/cead/meta/index.json`; NFD accent-insensitive)
- [ ] `pipeline/tests/test_resolver.py` — exact / accent / unknown / disambiguation
- [ ] `pipeline/tests/fixtures/golden_set.json` — 30–50 labelled incidents (ground-truth comuna + family)
- [ ] `pipeline/experiments/ab_score.py` — A/B scoring harness (5 metrics)
- [ ] `site/src/pages/news.astro` + `site/src/pages/es/noticias.astro` — bilingual news page

---

## Manual / Gated Verifications

| Behavior | Requirement | Why | Instructions |
|----------|-------------|-----|--------------|
| Live pipeline run + A/B | NEWS-02/03 | Needs `DEEPSEEK_API_KEY`+`MINIMAX_API_KEY` (.env) | If keys present: run live → current.json + ab results. If absent: do no-key parts (resolver, golden set, frontend) and leave live-run/A-B as a checkpoint. |
| News page + pins + both link types render (EN+ES) | NEWS-04 | Visual/console correctness | BrowserOS (port 9200): navigate `/news/` + `/es/noticias/`, confirm each incident has source↗ + comuna link; map pin popup has working comuna link; no console errors |

---

## Security (ASVS L1)

- **V5 Input Validation:** LLM output validated via Pydantic; resolver returns `None` for unknown names (no hallucinated CUT reaches the store). XSS: `escHtml()` in `IncidentPinLayer.ts` already escapes incident strings — extend to new fields; `slug` is a URL-safe path segment. Every incident cites + links its press source (`rel="noopener noreferrer"`, no `dangerouslySetInnerHTML`).
- No auth/sessions/crypto surface. API keys read from gitignored `.env` (python-dotenv) — never committed, never in output JSON.

---

## Validation Sign-Off

- [ ] Every task has an automated verify or a Wave-0 dependency
- [ ] No 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all new-file references
- [ ] Feedback latency < 150s
- [x] `nyquist_compliant: true`

**Approval:** pending
