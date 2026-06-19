---
phase: 5
slug: rss-news-pipeline
status: draft
nyquist_compliant: true
nyquist_reconciled: "v1.3 P19 TD-07 — milestone shipped; superseded by v1.2 audit (0 blockers)"
wave_0_complete: false
created: 2026-06-13
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from 05-RESEARCH.md "## Validation Architecture".

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (already in pipeline/requirements.txt; reuse pipeline/tests/conftest.py) |
| **Config file** | pipeline/pytest.ini |
| **Quick run command** | `pytest pipeline/tests/ -x -q` |
| **Full suite command** | `pytest pipeline/tests/ -v` |
| **Estimated runtime** | ~5–15s (all unit; DeepSeek mocked, no live API) |

---

## Sampling Rate

- **After every task commit:** `pytest pipeline/tests/ -x -q`
- **After every plan wave:** `pytest pipeline/tests/ -v`
- **Before `/gsd:verify-work`:** Full suite green + D-16 50-incident manual audit complete
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Wave | Requirement | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|-------------|-----------------|-----------|-------------------|-------------|--------|
| 5-?-? | 0 | infra | new test files + fixtures present | n/a | `ls pipeline/tests/test_feeds.py` | ❌ W0 | ⬜ |
| 5-?-? | 1 | NEWS-01 | feed failure → [] not exception; keyword filter; seen-ledger skip | unit | `pytest pipeline/tests/test_feeds.py -x` | ❌ W0 | ⬜ |
| 5-?-? | 1 | NEWS-02 | reject CUT∉346; reject confidence<thr; reject invalid family | unit | `pytest pipeline/tests/test_classifier.py -x` (mocked openai) | ❌ W0 | ⬜ |
| 5-?-? | 1 | NEWS-02 | centroid lookup returns (lat,lng) for valid CUT | unit | `pytest pipeline/tests/test_centroids.py -x` | ❌ W0 | ⬜ |
| 5-?-? | 1 | NEWS-03 | url-dedup + title-similarity dedup; no false positive | unit | `pytest pipeline/tests/test_dedup.py -x` | ❌ W0 | ⬜ |
| 5-?-? | 1 | NEWS-04 | 30-day window; idempotent merge; archive/YYYY-MM.json append | unit | `pytest pipeline/tests/test_store.py -x` | ❌ W0 | ⬜ |
| 5-?-? | 1 | NEWS-05 | outlet/url/date non-nullable; serializes to exact TS interface field names | unit | `pytest pipeline/tests/test_schema.py -x` | ❌ W0 | ⬜ |
| 5-?-? | 2 | NEWS-01..05 | orchestrator wires fetch→filter→classify→dedup→store; atomic write | integration | `pytest pipeline/tests/ -v` | ❌ W0 | ⬜ |
| 5-?-? | 2 | D-16 | 50 random incidents dumped (title/outlet/url/commune) for human spot-check | manual | `python pipeline/scripts/audit_incidents.py` | ❌ W0 | ⬜ |

*Status: ⬜ pending · ✅ green · ❌ red. Plan/Task IDs finalized by planner.*

---

## Wave 0 Requirements (all test files + fixtures are new)

- [ ] `pipeline/tests/test_feeds.py`, `test_classifier.py`, `test_dedup.py`, `test_store.py`, `test_centroids.py`, `test_schema.py` (extend existing schema tests)
- [ ] `pipeline/tests/fixtures/feed_biobio_sample.xml`, `feed_cooperativa_sample.xml`, `feed_latercera_sample.xml` (5-item each, mixed crime/non-crime)
- [ ] Mock fixture for `openai.Client.chat.completions.create` (known JSON response) — NEVER call live DeepSeek in tests
- [ ] `pipeline/scripts/audit_incidents.py` (D-16 manual audit tool)
- [ ] Add `feedparser` to `pipeline/requirements.txt` (only new dep)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 50-incident commune-hallucination audit | NEWS-02 / success #5 | Classification quality is a human judgment call (correct commune assigned vs article) | Run `python pipeline/scripts/audit_incidents.py`, review 50 random incidents' assigned commune against the linked article; confirm no hallucinations before declaring production-ready |
| Live feed availability | NEWS-01 | External endpoints can change; live network | Run pipeline against live feeds once; confirm ≥1 feed returns items and a down feed is skipped+logged |
| Confidence/dedup threshold calibration | NEWS-02/03 | Thresholds (conf 0.6, title-sim 0.82) are starting guesses requiring empirical tuning | After first real run + audit, adjust thresholds if false accept/reject observed |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] DeepSeek is MOCKED in all unit tests (no live API calls in CI)
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (6 test modules + 3 fixtures + audit script)
- [ ] Output Pydantic model serializes to EXACTLY the IncidentPinLayer.ts Incident/IncidentsFile interface
- [ ] No watch-mode flags
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
