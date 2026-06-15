---
phase: 10
slug: high-resolution-commune-geometry
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-15
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> This phase produces a **data/build artifact**, not feature code — validation is build-assertion + structural-validator based, with two intrinsic manual gates (visual recognizability + mobile perf).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Repo structural validators (`site/scripts/validate/*.mjs`) + in-script build assertions (`scripts/build-topojson.mjs`). No unit-test runner needed for a data artifact. |
| **Config file** | none — standalone Node scripts run in CI |
| **Quick run command** | `node scripts/build-topojson.mjs` (asserts 346 / integrity / size budget during regeneration) |
| **Full suite command** | `cd site && node scripts/sync-data.mjs && node scripts/validate/map.mjs` (chained — OneDrive desync mitigation) |
| **Estimated runtime** | ~10–30 seconds (build + validate) |

---

## Sampling Rate

- **After every task commit:** Run `node scripts/build-topojson.mjs` (fails fast on integrity/budget)
- **After every plan wave:** Run `cd site && node scripts/sync-data.mjs && node scripts/validate/map.mjs`
- **Before `/gsd:verify-work`:** `cd site && npm run build` green + manual browser visual+perf check on `/map/` and `/es/mapa/`
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-xx | 01 | 1 | GEO-01 | — / Tampering | Source GeoJSON validated as well-formed before re-key | structural | `node scripts/build-topojson.mjs` | ✅ extend | ⬜ pending |
| 10-01-xx | 01 | 1 | GEO-01 | — | 346 features, 0 missing/orphan/dup CUT vs index.json, 13101 present | structural | `node scripts/build-topojson.mjs` | ✅ extend | ⬜ pending |
| 10-0x-xx | 0x | x | GEO-02 | — | Asset ≤140 KB gzip AND ≤420 KB raw | structural | `node scripts/validate/map.mjs` | ✅ modify | ⬜ pending |
| 10-0x-xx | 0x | x | GEO-02 | — | Reproducible: `build-topojson.mjs` runs clean, re-emits integrity-clean asset | structural | `node scripts/build-topojson.mjs` | ✅ exists | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky. Task IDs finalize when PLAN.md task numbers are assigned.*

---

## Wave 0 Requirements

- [ ] `scripts/build-topojson.mjs` — extend Step-5 assertion to explicitly check **missing + orphan + duplicate** CUTs (currently only count + Santiago) — covers GEO-01 join integrity.
- [ ] `scripts/build-topojson.mjs` + `site/scripts/validate/map.mjs` — raise the 100 KB raw gate to the new budget and add a **gzip-size assertion** — covers GEO-02.
- [ ] No new test framework needed — existing validators + build assertions cover the automatable requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Polygons recognizable as real comuna shapes (coastline/borders) vs blocky | GEO-01 | Visual judgment — no automatable "looks like a real comuna" assertion | Open `/map/` + `/es/mapa/` in a real browser; compare to the pre-change blocky render; confirm coastlines and inter-commune borders read as real shapes |
| Smooth pan/zoom/hover, no new console errors | GEO-02 | Perceptual perf on real device class | Throttled-mobile profile (Moto G4 + Fast 3G, per Phase-3 gate); pan/zoom/hover the map; confirm no jank and clean console on map pages |

---

## Validation Sign-Off

- [ ] All tasks have automated verify (build/validate assertion) or are listed as intrinsic manual gates above
- [ ] Sampling continuity: every build-touching task runs `build-topojson.mjs`
- [ ] Wave 0 covers the assertion extensions (integrity + gzip budget) before the source swap lands
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter (after Wave 0 assertions exist)

**Approval:** pending
