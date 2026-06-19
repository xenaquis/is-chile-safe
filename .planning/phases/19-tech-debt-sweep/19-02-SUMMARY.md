---
phase: 19-tech-debt-sweep
plan: "02"
status: complete
one_liner: "Sort news incidents date-desc on both news pages and harden incident URL validation with new URL() scheme whitelist in frontend and pipeline"
subsystem: [news-pages, pipeline-store]
tags: [td-03, td-05, security, sorting, url-validation]
dependency_graph:
  requires: []
  provides: [news-sorted-date-desc, safe-url-frontend, safe-url-pipeline]
  affects: [site/src/pages/news.astro, site/src/pages/es/noticias.astro, pipeline/news/store.py]
tech_stack:
  added: []
  patterns: [new-URL-scheme-whitelist, urlparse-scheme-check]
key_files:
  created:
    - pipeline/tests/test_store.py (7 new tests added for scheme validation)
  modified:
    - site/src/pages/news.astro
    - site/src/pages/es/noticias.astro
    - pipeline/news/store.py
decisions:
  - "Mirror IncidentPinLayer.ts safeUrl() pattern in Astro frontmatter (server-side, not <script>)"
  - "build_incident returns None on bad URL — callers filter with list comprehension"
  - "merge_and_write also filters on entry to defend against stale stored data with bad URLs"
metrics:
  duration: "~15 minutes"
  completed: "2026-06-19"
  tasks_completed: 2
  tasks_total: 2
  files_changed: 4
---

# Phase 19 Plan 02: Sort + URL Scheme Guard (TD-03, TD-05) Summary

Sort news incidents newest-first and harden incident source-URL validation with `new URL()` scheme whitelist in both news pages and pipeline store.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Sort + scheme-guard both news pages | a43acb5 | news.astro, noticias.astro |
| 2 (RED) | Failing tests for URL scheme validation | 0ef367f | test_store.py |
| 2 (GREEN) | Implement is_safe_url in store.py | e180ae8 | store.py |

## Verification

**Build:** `cd site && npm run build && npm run validate` — 12/12 validators passed.

**Grep confirmation:**
- `grep -c "new URL" site/src/pages/news.astro` → 1
- `grep -c "new URL" site/src/pages/es/noticias.astro` → 1
- `grep -c "startsWith('http" site/src/pages/news.astro` → 0 (fragile guard removed)

**Pipeline tests:** `python -m pytest pipeline/tests/ -q` → 167 passed, 12 warnings.

## Changes Summary

### Task 1: news.astro and noticias.astro

Both pages received:
1. `incidents.sort((a, b) => b.date.localeCompare(a.date))` — newest-first sort (TD-03).
2. `safeUrl(url: string): string` helper in frontmatter using `new URL()` + protocol whitelist (`http:` or `https:`), returning `'#'` otherwise (TD-05). Mirrors `IncidentPinLayer.ts safeUrl()`.
3. `href={safeUrl(incident.url)}` replacing the fragile `startsWith('http://')` ternary.

The `process.cwd()/public` data path resolution is unchanged (memory: news-page-build-path-drift).

### Task 2: pipeline/news/store.py

Added:
- `is_safe_url(url)` using `urlparse(url).scheme in ("http", "https")` (TD-05, T-19-04).
- `build_incident` returns `None` (with warning log) for non-http(s) URLs.
- `merge_and_write` filters `None` and non-http(s) incidents before merge as defense-in-depth.

New tests in `test_store.py` (7 new tests):
- `test_build_incident_accepts_http_url` — http URL passes through
- `test_build_incident_accepts_https_url` — https URL passes through
- `test_build_incident_rejects_javascript_url` — javascript: → None
- `test_build_incident_rejects_data_url` — data: → None
- `test_build_incident_rejects_ftp_url` — ftp: → None
- `test_build_incident_rejects_malformed_url` — unparseable → None
- `test_merge_and_write_excludes_invalid_url_incidents` — bad URLs not written to current.json

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — both T-19-03 and T-19-04 mitigations implemented as planned.

## Self-Check: PASSED

- site/src/pages/news.astro — modified, contains new URL() ✓
- site/src/pages/es/noticias.astro — modified, contains new URL() ✓
- pipeline/news/store.py — modified, contains is_safe_url ✓
- pipeline/tests/test_store.py — 7 new tests, all pass ✓
- Commits: a43acb5, 0ef367f, e180ae8 — all exist in git log ✓
