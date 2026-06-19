---
phase: 23
slug: enusc-communal-victimization-layer
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-19
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `23-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (pipeline) + Node.js validators (site) |
| **Config file** | `pipeline/pytest.ini` |
| **Quick run command** | `cd pipeline && python -m pytest tests/test_fetch_enusc_vhdv.py tests/test_build_enusc_enrichment.py -x -q` |
| **Full suite command** | `cd pipeline && python -m pytest tests/ && cd ../site && npm run build && npm run validate` |
| **Estimated runtime** | ~60 seconds (pytest) + site build/validate |

---

## Sampling Rate

- **After every task commit:** Run quick command (ENUSC pytest subset)
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green (all validators + all pytest)
- **Max feedback latency:** ~60 seconds (pytest); site validators add build time

---

## Per-Task Verification Map

> Task IDs are assigned by the planner. This map binds each requirement to its
> verifiable signal; the executor / `/gsd:validate-phase` fills concrete task IDs.

| Plan area | Wave | Requirement | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|-----------|------|-------------|-----------------|-----------|-------------------|-------------|--------|
| Fetcher | 1 | VL-01 | sha256-guarded CACHE_ONLY parse; non-zero exit if cache absent | pytest | `pytest tests/test_fetch_enusc_vhdv.py -x` | ❌ W0 | ⬜ pending |
| Enrichment | 1 | VL-01 | exits 0 if snapshot absent (graceful degrade, CEAD unaffected) | pytest | `pytest tests/test_build_enusc_enrichment.py::test_missing_snapshot_graceful -x` | ❌ W0 | ⬜ pending |
| Enrichment | 1 | VL-02 | all 136 CUTs resolve to valid index CUT; count == 136; unresolved fails build | pytest | `pytest tests/test_build_enusc_enrichment.py::test_coverage_assertion -x` | ❌ W0 | ⬜ pending |
| Commune page | 2 | VL-03 | EN+ES covered pages contain VHDV section + experimental/SAE caveat | validator | `node site/scripts/validate/commune.mjs` (extend) | ⚠️ extend | ⬜ pending |
| Editorial | 2 | VL-03 | forbidden-language exits 0 (no absolute verdict) | validator | `node site/scripts/validate/forbidden-language.mjs` | ✅ exists | ⬜ pending |
| Commune page | 2 | VL-04 | uncovered pages contain explicit bilingual "no estimate" note, no broken layout | validator | `node site/scripts/validate/commune.mjs` (extend) | ⚠️ extend | ⬜ pending |
| Figure registry | 2 | VL-05 | F16 registered + SOURCES.md token present; zero-orphan passes | validator | `node site/scripts/validate/figure-registry.mjs` | ✅ exists | ⬜ pending |
| Additive guard | 1 | VL-05 | Phase-18 composite_index fields byte-unchanged after enrichment | pytest | `pytest tests/test_build_enusc_enrichment.py::test_phase18_byte_unchanged -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pipeline/tests/test_fetch_enusc_vhdv.py` — VL-01 (CACHE_ONLY parse, sha256 guard, column detection)
- [ ] `pipeline/tests/test_build_enusc_enrichment.py` — VL-01 (graceful degrade), VL-02 (coverage assertion), VL-05 (byte-unchanged)
- [ ] Extend `site/scripts/validate/commune.mjs` — assert VHDV module (covered) / no-estimate note (uncovered) on built commune pages

*Existing infrastructure (pytest, 13-validator Node suite, forbidden-language, figure-registry) covers the rest.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| ENUSC XLSX acquisition from INE JS widget | VL-01 | No stable URL; behind JS "Cuadros Estadísticos" widget; annual/assisted | Drill widget → download VHDV xlsx → drop in `pipeline/cache/enusc_vhdv.xlsx`; fetcher asserts sha256 |
| Visual EN/ES caveat presentation on a covered + an uncovered comuna page | VL-03, VL-04 | Layout/copy legibility is visual | Build site; open one covered (e.g. CUT 13123) + one uncovered comuna page in EN and ES |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
