---
phase: 05-rss-news-pipeline
plan: "03"
subsystem: news-pipeline
tags: [python, dedup, store, atomic-write, pydantic, stdlib]
dependency_graph:
  requires: ["05-01"]
  provides: ["pipeline/news/dedup.py", "pipeline/news/store.py"]
  affects: ["pipeline/news/classifier.py", "data/incidents/current.json"]
tech_stack:
  added: []
  patterns:
    - "difflib.SequenceMatcher for title-similarity dedup (stdlib, no rapidfuzz)"
    - "sha256(url)[:16] deterministic incident id (D-11)"
    - "validate_incidents_file gate BEFORE atomic_write_json (D-15)"
    - "30-day rolling window partition + YYYY-MM monthly archive"
key_files:
  created:
    - pipeline/news/dedup.py
    - pipeline/news/store.py
  modified: []
decisions:
  - "Threshold 0.82 for SequenceMatcher — balances false-positive vs false-negative at launch; can tune without API changes"
  - "UTC timestamp via datetime.now(timezone.utc) instead of deprecated utcnow() — zero DeprecationWarning"
  - "archive validation mirrors current validation — same IncidentsFile schema gate applied before every atomic write"
metrics:
  duration: "12m"
  completed: "2026-06-13"
  tasks: 2
  files: 2
requirements: [NEWS-03, NEWS-04, NEWS-05]
---

# Phase 05 Plan 03: Dedup + Store Summary

**One-liner:** stdlib-difflib URL+title dedup and sha256-id idempotent 30-day rolling store with IncidentsFile schema gate before every atomic write.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | dedup.py — canonical-URL + title-similarity dedup (NEWS-03) | 1e5f004 | pipeline/news/dedup.py |
| 2 | store.py — idempotent merge + 30-day window + archive + validated atomic write | bdb4dff | pipeline/news/store.py |

## What Was Built

### pipeline/news/dedup.py

- `normalize_title(t)`: NFD-decompose + lowercase + ascii-encode(ignore) + strip non-alphanum + collapse whitespace
- `are_duplicates(t1, t2, threshold=0.82)`: difflib.SequenceMatcher ratio comparison
- `deduplicate(incidents)`: two-phase — phase 1 collapses same canonical URL (utm_* stripped via urllib.parse), phase 2 drops near-identical titles within (cut, date) buckets keeping first occurrence
- Pure stdlib: difflib, re, unicodedata, urllib.parse — no new dependency

### pipeline/news/store.py

- `make_id(url)`: hashlib.sha256(url.encode()).hexdigest()[:16] — deterministic (D-11)
- `merge_and_write(new_incidents, current_path, archive_dir, window_days=30, today=None)`:
  1. Load existing incidents from current_path (or [])
  2. Merge new_incidents by id (existing wins — idempotent)
  3. Partition: current (date >= cutoff) vs aged_out (date < cutoff)
  4. Archive each YYYY-MM group: load existing archive, merge by id, validate, atomic_write_json
  5. Validate current payload via `validate_incidents_file` BEFORE write; on ValidationError log + return without writing (D-15 last-good preservation)
  6. `atomic_write_json(current_path, payload)` exclusively — no raw open/write

## Verification

```
pytest pipeline/tests/test_dedup.py pipeline/tests/test_store.py -x -q
6 passed in 0.12s
```

All acceptance criteria met:
- `test_url_dedup`: same canonical URL collapses to one incident
- `test_title_similarity`: near-identical titles (ratio >= 0.82) in same commune+date deduplicated to one
- `test_no_false_positive`: distinct incidents in same commune both kept
- `test_30day_window`: incident 31 days old moves to archive, fresh one stays current
- `test_idempotent_merge`: re-merging same id produces no duplicates
- `test_archive_write`: archive/YYYY-MM.json created and contains aged-out incidents

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Replaced deprecated datetime.utcnow()**
- **Found during:** Task 2 implementation
- **Issue:** `datetime.datetime.utcnow()` raises DeprecationWarning in Python 3.12+
- **Fix:** Replaced with `datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")` — clean ISO-8601 with Z suffix, no warnings
- **Files modified:** pipeline/news/store.py
- **Commit:** bdb4dff

## Threat Model Coverage

| Threat ID | Status |
|-----------|--------|
| T-05-03-01 (Tampering: current.json write) | Mitigated — validate_incidents_file gate before every write |
| T-05-03-02 (Tampering: partial write) | Mitigated — atomic_write_json (.tmp + os.replace) exclusively |
| T-05-03-03 (Repudiation: missing attribution) | Mitigated — IncidentRecord schema requires non-empty outlet/url/date |
| T-05-03-04 (Tampering: duplicate pins) | Mitigated — make_id sha256(url)[:16] idempotent merge |

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, or trust boundary surface introduced.

## Self-Check: PASSED

- pipeline/news/dedup.py: FOUND
- pipeline/news/store.py: FOUND
- Commit 1e5f004 (dedup.py): FOUND
- Commit bdb4dff (store.py): FOUND
- 6/6 tests pass, no warnings
