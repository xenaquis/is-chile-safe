---
phase: 05-rss-news-pipeline
plan: 01
subsystem: pipeline
tags: [python, pydantic, rss, feedparser, deepseek, topojson, pytest, centroids]

requires:
  - phase: 03-map-integration
    provides: IncidentPinLayer.ts TypeScript interface (LOCKED output contract)
  - phase: 04-cead-data
    provides: data/cead/comunas/*.json (346 CUT codes); data/cead/geo/communes.topo.json

provides:
  - "pipeline/news/schema.py: Pydantic v2 IncidentRecord/ClassifierOutput/IncidentsFile (LOCKED)"
  - "data/incidents/cut_list.json: 346 valid CUT codes (static, no live CEAD per run)"
  - "data/incidents/centroids.json: 346 commune lat/lng centroids (Shoelace + Node decode)"
  - "pipeline/scripts/build_centroids.py: one-shot TopoJSON->centroids generator"
  - "pipeline/scripts/audit_incidents.py: D-16 human-UAT audit tool"
  - "pipeline/tests/test_schema_incidents.py: 13 schema validation tests (green)"
  - "pipeline/tests/test_centroids.py: 5 centroid tests (green)"
  - "pipeline/tests/test_feeds/classifier/dedup/store.py: Wave-1 scaffolds (skip cleanly)"
  - "pipeline/tests/fixtures/feed_*.xml: 3 RSS fixtures (5 items each, feedparser-parseable)"
  - "pipeline/tests/fixtures/deepseek_response_sample.json: mocked DeepSeek response"
  - "feedparser==6.0.11 and openai==2.34.0 pinned in pipeline/requirements.txt"

affects:
  - 05-02-feeds (imports pipeline.news.schema, uses feed_*.xml fixtures)
  - 05-03-classifier (imports ClassifierOutput, uses deepseek_response_sample.json)
  - 05-04-store (imports IncidentsFile, uses centroids.json)

tech-stack:
  added:
    - "feedparser==6.0.11 (RSS/Atom parsing)"
    - "openai==2.34.0 (DeepSeek API client, OpenAI-compatible)"
  patterns:
    - "Pydantic v2 @field_validator only (no @validator / parse_obj / class Config)"
    - "VALID_CUTS loaded at module import from static cut_list.json (no live CEAD per news run)"
    - "FAMILY_KEYS imported from pipeline.shared.schema (never redefined)"
    - "TopoJSON decoded via Node subprocess using site/node_modules/topojson-client"
    - "Shoelace centroid formula; largest ring for MultiPolygon; bbox fallback for degenerate"
    - "Wave-1 test scaffolds skip via try/except ImportError at module top + pytestmark"

key-files:
  created:
    - pipeline/news/__init__.py
    - pipeline/news/schema.py
    - pipeline/scripts/build_centroids.py
    - pipeline/scripts/audit_incidents.py
    - data/incidents/cut_list.json
    - data/incidents/centroids.json
    - pipeline/tests/test_schema_incidents.py
    - pipeline/tests/test_centroids.py
    - pipeline/tests/test_feeds.py
    - pipeline/tests/test_classifier.py
    - pipeline/tests/test_dedup.py
    - pipeline/tests/test_store.py
    - pipeline/tests/fixtures/feed_biobio_sample.xml
    - pipeline/tests/fixtures/feed_cooperativa_sample.xml
    - pipeline/tests/fixtures/feed_latercera_sample.xml
    - pipeline/tests/fixtures/deepseek_response_sample.json
  modified:
    - pipeline/requirements.txt (added feedparser==6.0.11, openai==2.34.0)

key-decisions:
  - "CUT list sourced from data/cead/comunas/*.json filenames (346 files = 346 CUTs) — no live CEAD call per news run (resolves Open Question 2)"
  - "TopoJSON decoded via Node subprocess using already-installed topojson-client (zero new Python geo deps)"
  - "4 communes with null geometry in TopoJSON (La Granja 13111, Lo Prado 13117, San Ramon 13131, Iquique 1101) get hardcoded fallback centroids within bounds"
  - "Chilean Antarctic Territory (12202) centroid at -63 lat is valid — bounds widened to -90 to include legitimate Chilean territory"
  - "Wave-1 test scaffolds use pytestmark + try/except ImportError so collection never errors before Wave-1 modules exist"

patterns-established:
  - "IncidentRecord/IncidentsFile field names are NON-NEGOTIABLE — match IncidentPinLayer.ts Incident/IncidentsFile exactly"
  - "validate_incidents_file() is the all-or-nothing gate before any write (D-15)"
  - "title_es/title_en/summary are plain str — IncidentPinLayer escapes on render (V5/T-05-01-01)"

requirements-completed: [NEWS-02, NEWS-05]

duration: 35min
completed: 2026-06-13
---

# Phase 05 Plan 01: RSS News Pipeline Foundation Summary

**Pydantic v2 output schema locked to IncidentPinLayer.ts contract, 346-commune centroid lookup generated via Node+Shoelace, 6 test modules + 4 fixtures scaffold Wave-1 implementation with DeepSeek mocked**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-06-13T17:20:00Z
- **Completed:** 2026-06-13T17:55:00Z
- **Tasks:** 3
- **Files modified:** 18

## Accomplishments

- IncidentRecord/ClassifierOutput/IncidentsFile Pydantic v2 models serialize to exact TS interface field names; reject CUT not in 346, invalid family, empty attribution
- 346-commune centroids.json generated deterministically via Node topojson-client decode + Shoelace formula; zero new Python geo dependencies
- 6 pytest modules + 4 fixtures present; full suite 113 passed + 16 skipped (Wave-1 scaffolds), 0 errors; DeepSeek never called live

## Task Commits

1. **Task 1: Incident schema models + CUT list + dependency declaration** - `1e7b824` (feat)
2. **Task 2: Centroid generator + centroids.json + centroid tests** - `71965a1` (feat)
3. **Task 3: RSS fixtures + DeepSeek mock + audit tool + Wave-1 test scaffolds** - `5d607ca` (feat)

## Files Created/Modified

- `pipeline/news/__init__.py` - Empty package marker
- `pipeline/news/schema.py` - Pydantic v2 IncidentRecord/ClassifierOutput/IncidentsFile + validate_incidents_file()
- `pipeline/scripts/build_centroids.py` - TopoJSON -> centroids.json via Node + Shoelace (one-shot)
- `pipeline/scripts/audit_incidents.py` - D-16 human-UAT read-only audit tool
- `data/incidents/cut_list.json` - 346 CUT codes (static, sourced from comunas filenames)
- `data/incidents/centroids.json` - 346 commune lat/lng centroids
- `pipeline/requirements.txt` - Added feedparser==6.0.11 and openai==2.34.0
- `pipeline/tests/test_schema_incidents.py` - 13 schema validation tests
- `pipeline/tests/test_centroids.py` - 5 centroid file tests + 2 Wave-1 module tests (skip)
- `pipeline/tests/test_feeds.py` - 5 Wave-1 scaffold tests (skip until feeds.py exists)
- `pipeline/tests/test_classifier.py` - 3 Wave-1 scaffold tests with mocked openai (skip)
- `pipeline/tests/test_dedup.py` - 3 Wave-1 scaffold tests with inline fixtures (skip)
- `pipeline/tests/test_store.py` - 3 Wave-1 scaffold tests with tmp_path (skip)
- `pipeline/tests/fixtures/feed_biobio_sample.xml` - 5-item RSS (link!=guid, exercises Pitfall 2)
- `pipeline/tests/fixtures/feed_cooperativa_sample.xml` - 5-item policial RSS (guid=canonical)
- `pipeline/tests/fixtures/feed_latercera_sample.xml` - 5-item RSS with content:encoded (proves D-01)
- `pipeline/tests/fixtures/deepseek_response_sample.json` - ClassifierOutput mock (no live API)

## Decisions Made

- CUT list sourced from data/cead/comunas/*.json filenames — eliminates live CEAD dependency per news run
- Node subprocess to decode TopoJSON avoids any new Python geometry dependency (shapely, topojson)
- Hardcoded fallback centroids for 4 communes with null geometry in TopoJSON asset
- Chilean bounds widened to -90 lat to include Antarctic Territory (CUT 12202)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 4 communes have null geometry in TopoJSON — added hardcoded fallbacks**
- **Found during:** Task 2 (build_centroids.py execution)
- **Issue:** TopoJSON feature geometry was null for CUTs 13111 (La Granja), 13117 (Lo Prado), 13131 (San Ramón), 1101 (Iquique); script would have produced only 342 centroids (missing 4 valid CUTs)
- **Fix:** Added `NULL_GEOMETRY_FALLBACKS` dict with verified coordinates for all 4 communes; falls through to fallback when `geometry is None` and key is in map
- **Files modified:** pipeline/scripts/build_centroids.py
- **Verification:** `len(centroids)==346`; all 4 CUTs present with valid Chilean bounds coords
- **Committed in:** 71965a1 (Task 2 commit)

**2. [Rule 1 - Bug] Chilean Antarctic Territory centroid at lat -63 triggered bounds check**
- **Found during:** Task 2 (build_centroids.py sanity check)
- **Issue:** Original bounds check was `(-56, -17)` for lat; CUT 12202 (Territorio Chileno Antártico) has centroid near -63°S, which is legitimate Chilean territory
- **Fix:** Widened lat bounds to `(-90, -17)` to include Antarctic Territory
- **Files modified:** pipeline/scripts/build_centroids.py
- **Verification:** All 346 centroids pass bounds check
- **Committed in:** 71965a1 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 x Rule 1 bugs in build_centroids.py data)
**Impact on plan:** Both fixes necessary for correct 346-centroid output. No scope creep.

## Issues Encountered

None beyond the two auto-fixed deviations above.

## Known Stubs

None — no data flows to UI rendering from this plan. centroids.json and cut_list.json are static assets; schema.py defines the contract; test scaffolds are placeholders for Wave-1 implementation.

## Threat Flags

No new threat surfaces introduced beyond those documented in the plan's threat_model. Node subprocess (`build_centroids.py`) decodes a committed, trusted local asset with no network/user input.

## Self-Check

- [x] `data/incidents/cut_list.json` — 346 unique CUTs
- [x] `data/incidents/centroids.json` — 346 entries, Santiago in bounds
- [x] `pipeline/news/schema.py` — exists, uses @field_validator only
- [x] `pipeline/scripts/build_centroids.py` — exists, main()+__main__ guard
- [x] `pipeline/scripts/audit_incidents.py` — exists, read-only, main()+__main__ guard
- [x] `pipeline/tests/test_schema_incidents.py` — 13 passed
- [x] `pipeline/tests/test_centroids.py` — 5 passed, 2 skipped
- [x] Wave-1 scaffolds (4 modules) — collected cleanly, skip on missing import
- [x] `pytest pipeline/tests/ -x -q` — 113 passed, 16 skipped, 0 errors
- [x] `pipeline/requirements.txt` — feedparser==6.0.11, openai==2.34.0 present
- [x] Commits: 1e7b824, 71965a1, 5d607ca

## Self-Check: PASSED

## Next Phase Readiness

- Wave-1 plans (05-02 feeds, 05-03 classifier, 05-04 dedup/store) can implement against fixed schema/centroid contracts
- Test function names in Wave-1 scaffolds are fixed — implementations must satisfy these exact signatures
- `feedparser` and `openai` are now pinned; CI will install them
- D-16 audit tool ready for use after first real scrape run

---
*Phase: 05-rss-news-pipeline*
*Completed: 2026-06-13*
