---
phase: 21
slug: commune-comparator-a-vs-b-seo
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-20
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from 21-RESEARCH.md "## Validation Architecture". The planner refines the
> Per-Task Verification Map once PLAN.md task IDs are assigned.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Node ESM build-time validators (`site/scripts/validate/*.mjs`) + Astro build assertions; no unit-test runner in repo |
| **Config file** | none — validators are standalone Node scripts run via `npm run validate` |
| **Quick run command** | `node site/scripts/validate/avs-b-budget.mjs` (after build) |
| **Full suite command** | `cd site && npm run build && npm run validate` |
| **Estimated runtime** | ~60–120 seconds (full static build + validators) |

---

## Sampling Rate

- **After every task commit:** Run the relevant single validator (`node site/scripts/validate/<name>.mjs`) or `npx astro check` for island/page tasks
- **After every plan wave:** Run `cd site && npm run build && npm run validate`
- **Before `/gsd:verify-work`:** Full build + all validators must exit 0 (13/13+)
- **Max feedback latency:** ~120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| (assigned by planner) | — | 0 | CMP-02/03 | — | pair allowlist + budget computed from real data | build-assert | `node site/scripts/validate/avs-b-budget.mjs` | ❌ W0 | ⬜ pending |
| (assigned by planner) | — | 0 | CMP-02 | — | ≥300 words non-swappable prose per pair | build-assert | thin-content assertion in build | ❌ W0 | ⬜ pending |
| (assigned by planner) | — | 1 | CMP-01 | — | comparator island hydrates over static shell | manual+astro check | `cd site && npx astro check` | ✅ | ⬜ pending |
| (assigned by planner) | — | 2 | CMP-04 | — | hreflang reciprocity covers A-vs-B | build-assert | `node site/scripts/validate/hreflang.mjs` | ✅ | ⬜ pending |
| (assigned by planner) | — | 2 | CMP-04 | — | every commune page links 3–5 pairs | build-assert | `node site/scripts/validate/spine.mjs` | ✅ | ⬜ pending |
| (assigned by planner) | — | 2 | CI-09 | — | no forbidden absolute-verdict language | build-assert | forbidden-language validator | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/generate-pairs.mjs` — generates `data/comparator-pairs.json` (priority-pair allowlist from real commune data)
- [ ] `site/scripts/validate/avs-b-budget.mjs` — new validator: total files < 18,000 + pair-count assertion
- [ ] `site/src/lib/comparisonProse.ts` — bilingual ≥300-word non-swappable prose engine + thin-content guard

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Accent-insensitive autocomplete UX across 346 communes | CMP-01 | Interactive island behavior; no DOM test runner in repo | Load `/compare/`, type "nunoa" → "Ñuñoa" appears; select 2–3 communes; verify side-by-side panel |
| Prose quality of ≥10 sampled A-vs-B pairs | CMP-06 | Subjective readability/quality of generated prose | Inspect 10 random `/compare/<a>-vs-<b>/` pages EN+ES before deploy |
| GSC URL Inspection of first ~20-pair batch | CMP-07 | Requires Google Search Console access | Submit batch, verify indexable in GSC before expanding |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
