---
phase: 17
slug: robust-crime-index
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-18
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `17-RESEARCH.md` § Validation Architecture. Scope is FOCUSED
> (data-quality + traceability + methodology); no displayed-metric or schema change.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (`pipeline/pytest.ini`) + Node validators (`site/scripts/validate/all.mjs`) |
| **Config file** | `pipeline/pytest.ini` |
| **Quick run command** | `cd site && npm run build && npm run validate` (OneDrive-safe: chained) |
| **Full suite command** | `cd pipeline && pytest tests/ ; cd ../site && npm run build && npm run validate` |
| **Estimated runtime** | ~60–120 seconds (build dominates) |

---

## Sampling Rate

- **After every task commit:** Run `cd site && npm run build && npm run validate`
- **After every plan wave:** Full pytest + build + validate
- **Before `/gsd:verify-work`:** Build green + all validators pass + BrowserOS visual check of EN/ES methodology pages
- **Max feedback latency:** ~120 seconds

---

## Per-Task Verification Map

> Provisional (pre-plan): keyed by requirement → observable signal. Planner maps task IDs onto these signals.

| Req | Behavior | Test Type | Automated Command / Signal | File Exists |
|-----|----------|-----------|----------------------------|-------------|
| DQ-01 | `17-DATA-QUALITY.md` exists; each check PASS or documented | script output | `test -f .planning/phases/17-robust-crime-index/17-DATA-QUALITY.md` + grep PASS/FAIL rows | ❌ W0 (new script) |
| DQ-01 | Partial-year flag present on 2026 across 346 commune JSONs | python assert | inline assert over `data/cead/comunas/*.json` series | ✅ existing data |
| DQ-01 | 4 anomalies (Providencia, Lo Barnechea, San Joaquín, Recoleta) re-verified + explained | python assert | values re-derived from `pipeline/cache/` vs surfaced figures | ✅ existing data/cache |
| DQ-02 | Wrong host `ministeriointerior.gob.cl` absent from built HTML | grep dist | `grep -r "ministeriointerior.gob.cl" site/dist/ && echo FOUND || echo CLEAN` | ✅ after build |
| DQ-02 | `data/SOURCES.md` exists with CEAD/SPD/SII/Fiscalía entries | file + grep | `test -f data/SOURCES.md && grep -c "minsegpublica" data/SOURCES.md` | ❌ W0 (new file) |
| DQ-03 | Methodology EN+ES contain clickable links to all 4 sources | grep source | `grep -c "prevenciondehomicidios.cl" site/src/pages/methodology.astro` (+ ES) | ❌ W0 (new content) |
| DQ-03 | No forbidden/absolute-safety language (validator #9) | validator | `cd site && npm run build && npm run validate` | ✅ existing validator |
| DQ-03 | Pages render with correct host + working links in real browser | BrowserOS | navigate + screenshot `methodology/` and `es/metodologia/` | ❌ W0 (manual) |
| DQ-04 | `data/snapshots/spd_homicide.json` non-empty (>200 records) | file + schema | python len(records) assert | ❌ W0 (new file) |
| DQ-04 | `data/snapshots/sii_exposure.json` non-empty (>200 records) | file + schema | python len(records) assert | ❌ W0 (new file) |
| DQ-04 | `data/snapshots/fiscalia_secuestro.json` exists (regional series) | file | `test -f data/snapshots/fiscalia_secuestro.json` | ❌ W0 (new file) |
| DQ-04 | Build + validate chain passes after snapshots committed | validator | `cd site && npm run build && npm run validate` | ✅ existing validators |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pipeline/scripts/verify_data_quality.py` — offline cross-check → emits `17-DATA-QUALITY.md`
- [ ] `pipeline/snapshots/fetch_spd_homicide.py`, `fetch_sii_exposure.py`, `fetch_fiscalia_secuestro.py` (each with `CACHE_ONLY=1` flag re-parsing `pipeline/cache/`)
- [ ] `data/snapshots/` dir + 3 normalized JSON files
- [ ] `data/SOURCES.md` — canonical source registry
- [ ] `.planning/phases/17-robust-crime-index/17-DATA-QUALITY.md` — evidence report

*All packages present (`pandas`, `pyxlsb`, `openpyxl`, `requests`, `tenacity`) — no new deps. Cache files `spd_vhc.xlsx` + `sii_pub_comu.xlsb` already downloaded (Wave 0) → DQ-04 runs fully offline.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| EN+ES methodology render with working clickable source links | DQ-03 | Visual/render correctness not assertable in build | BrowserOS (port 9200): navigate `/methodology/` and `/es/metodologia/`, screenshot, click each source link, confirm correct host + caveats visible |
| Sampled commune/ranking figures still cite source + year | DQ-01/DQ-03 | Cross-page spot check | BrowserOS: open 2–3 commune pages, confirm source attribution + year present |

---

## Validation Sign-Off

- [ ] All tasks have an automated verify or a Wave-0 dependency
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (scripts + snapshot dir)
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
