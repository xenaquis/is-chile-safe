---
phase: 1
slug: data-foundation
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-12
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pipeline/pytest.ini` (created in Plan 01 Task 1) |
| **Quick run command** | `python -m pytest pipeline/tests/ -x -q` |
| **Full suite command** | `python -m pytest pipeline/tests/ -q` |
| **Estimated runtime** | ~30 seconds (all unit tests are offline; live calls are checkpoint-only) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest pipeline/tests/ -x -q`
- **After every plan wave:** Run `python -m pytest pipeline/tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-T1 scaffold + deps | 01 | 1 | DATA-02,03 | T-01-SC | Pinned deps; cache + .env git-ignored | infra | `pip install -r pipeline/requirements.txt && python -m pytest --version` | ❌ W0 | ⬜ pending |
| 01-T2 schema gate | 01 | 1 | DATA-02,03 | T-01-01 | All-or-nothing validation rejects bad data before write | unit | `python -m pytest pipeline/tests/test_schema.py -q` | ❌ W0 | ⬜ pending |
| 01-T3 atomic write | 01 | 1 | DATA-03 | T-01-02 | No partial files; os.replace | unit | `python -m pytest pipeline/tests/test_atomic_write.py -q` | ❌ W0 | ⬜ pending |
| 02-T1 INE fetch+JSON | 02 | 1 | DATA-04 | T-02-01,02 | Count-guarded conversion; no silent partial | data | `python -c "..346 count check.."` | ❌ W0 | ⬜ pending |
| 02-T2 population lookup | 02 | 1 | DATA-04 | T-02-01 | 10000 threshold; unknown CUT excluded | unit | `python -m pytest pipeline/tests/test_population.py -q` | ❌ W0 | ⬜ pending |
| 02-T3 INE spot-check | 02 | 1 | DATA-04 | T-02-01 | 5 communes match official INE | manual | checkpoint (human-verify) | n/a | ⬜ pending |
| 03-T1 client+catalog | 03 | 2 | DATA-01 | T-03-01,03 | latin-1 decode; verified params; str CUTs | unit (mocked) | `python -m pytest pipeline/tests/test_client.py pipeline/tests/test_catalog.py -q` | ❌ W0 | ⬜ pending |
| 03-T2 parser+fixture | 03 | 2 | DATA-01 | T-03-02 | Chilean decimal; missing→None | unit | `python -m pytest pipeline/tests/test_parser.py -q` | ❌ W0 | ⬜ pending |
| 03-T3 live endpoint | 03 | 2 | DATA-01 | T-03-04 | Live 200 + real rows; subgroup IDs | manual | checkpoint (human-verify) | n/a | ⬜ pending |
| 04-T1 normalizer | 04 | 3 | DATA-01,04 | T-04-02 | rate-desc ranks; low-pop null | unit | `python -m pytest pipeline/tests/test_normalizer.py -q` | ❌ W0 | ⬜ pending |
| 04-T2 orchestrator+output | 04 | 3 | DATA-01,02,03 | T-04-01,04 | validate-before-write; <30KB guard; exit-1 on fail | unit (mocked) | `python -m pytest pipeline/tests/test_output.py -q` | ❌ W0 | ⬜ pending |
| 04-T3 live full run | 04 | 3 | DATA-01,02,03,04 | T-04-01,05 | 346 files; rate matches CEAD published | manual | checkpoint (human-verify) | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

All Wave 0 test scaffolding is created inside Plan 01 Task 1/2/3 and the test files accompany each implementation task (TDD: tests written with their module):

- [ ] `pipeline/pytest.ini` + `pipeline/__init__.py` + package `__init__.py` files (Plan 01 T1)
- [ ] `pipeline/tests/conftest.py` — shared fixtures incl. sample_commune_dict, sample_cead_html (Plan 01 T2; sample_cead_html fixture file produced in Plan 03 T2)
- [ ] `pytest==8.*` pinned in `pipeline/requirements.txt` (Plan 01 T1)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live CEAD endpoint returns 200 with real commune rows | DATA-01 | Hits live government server; not suitable for CI | Plan 03 T3 checkpoint: one live call confirms 200 + formato_4 rows |
| Full scrape produces all 346 commune files | DATA-01 | Live full run against government server | Plan 04 T3 checkpoint: run scraper locally; confirm 346 commune files |
| Published rates match CEAD's own figures | DATA-04 (D-10) | Requires cross-reference to CEAD's live site | Plan 04 T3: spot-check Santiago latest-year rate vs CEAD published |
| INE population matches official source | DATA-04 (D-11) | Third-party mirror must be spot-checked | Plan 02 T3: 5 communes vs official INE projections |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or are explicit checkpoint/manual tasks with Wave 0 dependencies noted
- [x] Sampling continuity: no 3 consecutive code tasks without automated verify (each code task ships its own test)
- [x] Wave 0 covers all MISSING references (pytest install, pytest.ini, conftest fixtures)
- [x] No watch-mode flags
- [x] Feedback latency < 60s (offline unit suite)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planned
