---
phase: 05-rss-news-pipeline
verified: 2026-06-13T00:00:00Z
status: human_needed
score: 10/10 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Run scrape_news.py with a real DEEPSEEK_API_KEY against the 3 live RSS feeds"
    expected: "current.json written with at least 1 incident; pipeline exits 0; seen.json updated"
    why_human: "Live DeepSeek API key unavailable in autonomous context; live feed URLs unverifiable without network access to Chilean press sites"
  - test: "Run pipeline/scripts/audit_incidents.py after a live run; inspect 50 sampled incidents"
    expected: "D-16 audit: commune assignments are plausible (e.g., Santiago robbery -> 13101, not a random CUT); no hallucinated communes visible in the random 50"
    why_human: "This is the NEWS-02 success criterion #5 manual commune-hallucination audit (D-16). Requires a live run with real data to produce incidents to audit."
---

# Phase 5: RSS News Pipeline Verification Report

**Phase Goal:** Recent crime incidents from national press are automatically classified, geolocated, and surfaced as incident pins on the map.
**Verified:** 2026-06-13
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | IncidentsFile Pydantic model serializes to exactly the IncidentPinLayer.ts Incident/IncidentsFile interface field names | VERIFIED | `IncidentsFile.model_dump()` top keys: `generated, incidents, window_days`; incident keys: `cut, date, family, id, lat, lng, outlet, title_en, title_es, url` — exact match to TS interface |
| 2 | An incident with a CUT not in the 346-commune set is rejected by the schema | VERIFIED | `pipeline/news/schema.py` line 54: `@field_validator("cut")` raises `ValueError` when `v not in VALID_CUTS`; `test_schema_incidents.py` asserts `ValidationError` raised |
| 3 | An incident with an invalid family key is rejected by the schema | VERIFIED | `@field_validator("family")` rejects any value not in `VALID_FAMILIES`; confirmed by test suite (135 passed) |
| 4 | Classifier uses model `deepseek-v4-flash`, temperature 0.0, json_object response format; LLM never emits lat/lng | VERIFIED | `classifier.py` line 147-148: `model="deepseek-v4-flash", temperature=0.0, response_format={"type": "json_object"}`; `centroids.py` provides deterministic lat/lng from `centroids.json` — never from LLM output |
| 5 | Every CUT in the 346 set resolves to a (lat, lng) centroid inside Chile's bounds | VERIFIED | `centroids.json` has 346 keys; all lat in (-90, -17), lng in (-110, -65); CUT 12202 (Antártica Chilena) at lat -63 is legitimate Chilean sovereign territory; test_centroids.py uses correct wide bounds and passes |
| 6 | RSS feeds fail gracefully per-feed; one down feed does not block others | VERIFIED | `feeds.py` `fetch_feed()` catches all exceptions and returns `[]`; `scrape_news.py` wraps per-feed loop in try/except; `test_per_feed_failure_isolated` asserts main() returns 0 with one bad feed |
| 7 | Incidents are deduplicated before publishing (canonical URL + title similarity) | VERIFIED | `dedup.py` implements URL dedup (utm stripping) + SequenceMatcher title-similarity within (cut, date) buckets at threshold 0.82; `test_main_happy_path` asserts 3 crime entries with 1 duplicate URL → 2 incidents |
| 8 | `current.json` maintains a 30-day rolling window with monthly archive | VERIFIED | `store.py` `merge_and_write()` partitions by cutoff date, archives aged incidents to `archive/YYYY-MM.json` via `atomic_write_json`; `test_store.py` tests all three behaviors |
| 9 | Every published incident includes outlet name, source URL, and date (NEWS-05 attribution) | VERIFIED | `IncidentRecord` has `@field_validator` rejecting empty `outlet` and `url`; `build_incident()` requires all attribution fields; `test_main_happy_path` asserts attribution fields present on each incident |
| 10 | Full pytest suite passes with DeepSeek mocked (no live API) | VERIFIED | `python -m pytest pipeline/tests/ -q` → **135 passed**, 12 deprecation warnings (feedparser internal, not our code) |

**Score:** 10/10 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/news/schema.py` | IncidentRecord + IncidentsFile + ClassifierOutput + validate_incidents_file() | VERIFIED | All 4 models present; VALID_CUTS loaded from cut_list.json; FAMILY_KEYS imported from shared.schema (not redefined) |
| `pipeline/news/classifier.py` | DeepSeek v4-flash classifier; anti-hallucination guards | VERIFIED | model=deepseek-v4-flash, temp=0.0, json_object; rejects CUT not in VALID_CUTS; rejects confidence < 0.6; no lat/lng from LLM |
| `pipeline/news/feeds.py` | RSS fetch + keyword filter + seen ledger | VERIFIED | FEEDS registry (3 sources); per-feed try/except; keyword pre-filter (D-02); seen-URL ledger with save/load/prune |
| `pipeline/news/dedup.py` | Cross-source deduplication | VERIFIED | URL canonicalization + SequenceMatcher title-similarity dedup |
| `pipeline/news/store.py` | 30-day rolling window + archive + atomic write | VERIFIED | merge_and_write(); validate_incidents_file gate; atomic_write_json; monthly archive partitioning |
| `pipeline/news/centroids.py` | Deterministic CUT → lat/lng lookup | VERIFIED | Lazy-loads centroids.json; returns None for unknown CUT |
| `pipeline/scrape_news.py` | Orchestrator entry point | VERIFIED | Full pipeline orchestration; socket timeout (CR-01); seen-ledger marks rejected URLs (CR-02); fail-loud on missing key; exit codes 0/1 |
| `data/incidents/centroids.json` | 346 CUT → {lat, lng} | VERIFIED | 346 entries; all within Chilean bounds (incl. Antarctic territory for CUT 12202) |
| `data/incidents/cut_list.json` | 346 CUT strings | VERIFIED | 346 unique strings confirmed |
| `pipeline/scripts/audit_incidents.py` | D-16 audit dump tool | VERIFIED | Parses; has main() + __main__ guard; read-only (no writes) |
| `pipeline/scripts/build_centroids.py` | One-shot TopoJSON → centroids generator | VERIFIED | Node subprocess decode + Shoelace; atomic_write_json; main() + __main__ guard |
| `pipeline/tests/fixtures/deepseek_response_sample.json` | Mocked DeepSeek response | VERIFIED | Present; used in classifier tests |
| `pipeline/tests/test_schema_incidents.py` | Schema validation tests | VERIFIED | Part of 135-test suite; passes |
| `pipeline/tests/test_centroids.py` | Centroid tests | VERIFIED | 346 entries, bounds, Santiago check — all pass |
| `pipeline/tests/test_feeds.py` | Feed + keyword filter tests | VERIFIED | 12 tests pass |
| `pipeline/tests/test_classifier.py` | Classifier tests (DeepSeek mocked) | VERIFIED | Passes with mock |
| `pipeline/tests/test_dedup.py` | Dedup tests | VERIFIED | Passes |
| `pipeline/tests/test_store.py` | Store tests | VERIFIED | 30-day window, idempotent merge, archive write — all pass |
| `pipeline/tests/test_scrape_news.py` | Integration orchestrator tests | VERIFIED | 5 tests; happy path, no-key, per-feed failure, classifier-None, centroid-None, TS field names |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `pipeline/news/schema.py` | `data/incidents/cut_list.json` | `_CUT_FILE` pathlib load at import | VERIFIED | Line 22-30: file loaded at module import; fails loud if absent (CR-03) |
| `pipeline/news/schema.py` | `pipeline/shared/schema.py` | `from pipeline.shared.schema import FAMILY_KEYS` | VERIFIED | Line 14: explicit import; VALID_FAMILIES not redefined |
| `pipeline/news/classifier.py` | `pipeline/news/schema.py` | imports ClassifierOutput, VALID_CUTS, VALID_FAMILIES | VERIFIED | Lines 22-23 |
| `pipeline/news/centroids.py` | `data/incidents/centroids.json` | lazy-load at first `get_centroid()` call | VERIFIED | Lines 17-43 |
| `pipeline/scrape_news.py` | all `pipeline.news.*` modules | local imports inside main() | VERIFIED | Lines 100-115 |
| `pipeline/news/store.py` | `pipeline/shared/atomic_write.py` | `from pipeline.shared.atomic_write import atomic_write_json` | VERIFIED | Line 23 |
| Output `data/incidents/current.json` | `site/src/components/map/IncidentPinLayer.ts` | `fetch('/data/incidents/current.json')` in IncidentPinLayer | VERIFIED | IncidentPinLayer.ts line 101; `sync-data.mjs` prebuild syncs to public/data |

### Data-Flow Trace (Level 4)

| Component | Data Variable | Source | Produces Real Data | Status |
|-----------|---------------|--------|--------------------|--------|
| `scrape_news.py` → `current.json` | `new_incidents` | DeepSeek via `classify()` + `centroids.json` | Yes (mocked in tests; live pending human gate) | VERIFIED (build-complete; live data deferred to human gate) |
| `IncidentPinLayer.ts` | `data.incidents` | `fetch('/data/incidents/current.json')` | Passes through to map pins | VERIFIED — wiring was Phase 3; this phase produces the file it reads |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full pytest suite (DeepSeek mocked) | `python -m pytest pipeline/tests/ -q` | 135 passed, 12 warnings | PASS |
| cut_list.json has 346 unique CUTs | `python -c "import json; c=json.load(open(...)); assert len(c)==346 and len(set(c))==346"` | cut_list len: 346 unique: 346 | PASS |
| centroids.json has 346 entries; Santiago in bounds | `python -c "c=json.load(...); assert len(c)==346; v=c['13101']; assert -34<v['lat']<-33..."` | centroids len: 346; 13101: {'lat': -33.446981, 'lng': -70.721768} | PASS |
| IncidentsFile serializes to exact TS field names | Python model_dump() check | incident keys match TS Incident interface exactly | PASS |
| requirements.txt pins correct deps | `grep feedparser openai pipeline/requirements.txt` | feedparser==6.0.11; openai==2.34.0 | PASS |
| No debt markers (TBD/FIXME/XXX) in pipeline files | grep across pipeline/news/*.py, scrape_news.py | No matches | PASS |

### Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|---------|
| NEWS-01 | RSS ingest with per-feed fallback | SATISFIED | `feeds.py` per-feed try/except; `fetch_feed()` returns [] on failure; 3 confirmed feeds (BioBioChile, Cooperativa, LaTercera) |
| NEWS-02 | DeepSeek v4-flash closed-list classification; no-match rejected | SATISFIED | `classifier.py`: model=deepseek-v4-flash, temp=0.0, json_object; commune_cut validated against VALID_CUTS; confidence gate 0.6; LLM never emits lat/lng |
| NEWS-03 | Cross-source deduplication before publish | SATISFIED | `dedup.py`: URL canonical dedup + title-similarity (SequenceMatcher, threshold 0.82) within (cut, date) buckets |
| NEWS-04 | 30-day rolling window + monthly archive | SATISFIED | `store.py` `merge_and_write()`: window cutoff + `archive/YYYY-MM.json` partitioning |
| NEWS-05 | Each incident cites outlet + URL + date | SATISFIED | `IncidentRecord` field_validators reject empty outlet/url; `build_incident()` requires all attribution fields |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `pipeline/news/centroids.py` | 29 | Lazy client init (`_CENTROIDS = None` loaded on first call) | INFO | WR-06 noted in review: lazy init means monkeypatching `_CENTROID_PATH` before first call works, but `_CENTROIDS` must also be reset. Test handles this correctly with `monkeypatch.setattr(centroids_mod, "_CENTROIDS", None)`. No production impact. |

No TBD/FIXME/XXX debt markers found in any pipeline file. No stubs. No hardcoded empty returns in production paths.

### Human Verification Required

#### 1. Live Pipeline Run

**Test:** Set `DEEPSEEK_API_KEY` in `pipeline/.env`, then run `python pipeline/scrape_news.py` from repo root.
**Expected:** Pipeline exits 0; `data/incidents/current.json` is written with at least 1 incident having valid `cut`, `lat`, `lng`, `title_es`, `title_en`, `date`, `outlet`, `url`, `family`; `data/incidents/seen.json` is updated.
**Why human:** Live DeepSeek API key unavailable in autonomous context. Network access to Chilean press RSS feeds (BioBioChile, Cooperativa, LaTercera) cannot be verified without real HTTP calls.

#### 2. D-16 Commune Hallucination Audit (NEWS-02 success criterion #5)

**Test:** After a live run produces incidents, run `python pipeline/scripts/audit_incidents.py`. Review the printed table of up to 50 random incidents (title_es, outlet, url, assigned CUT + commune name).
**Expected:** Commune assignments are geographically plausible given the incident titles (e.g., "Robo en Las Condes" → CUT 13114, not a random southern commune). No systematic pattern of obviously wrong CUT assignments visible in the sample.
**Why human:** This audit requires real LLM-classified incidents from actual news content. The auditor must judge plausibility — automated tools cannot evaluate whether a Chilean commune assignment "makes sense" for a given news headline. This is the anti-hallucination quality gate defined in D-16.

### Gaps Summary

No code gaps. All must-haves are verified. The two human verification items are deferred-by-design gates (live API run and manual audit) documented in the phase context as D-16 and the CLAUDE.md deferred note. They are not implementation gaps.

---

_Verified: 2026-06-13_
_Verifier: Claude (gsd-verifier)_
