---
phase: 7
slug: e2e-review-pass
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-13
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
>
> **Nature of this phase:** Phase 7 is an observational, browser-driven QA review. It writes
> NO production code — only `.planning/REVIEW-E2E-FINDINGS.md` plus screenshot evidence. There
> is therefore no unit/integration test suite to sample. The "tests" are the BrowserOS MCP
> interaction sequences themselves: each task drives the real browser, captures evidence, and
> the evidence (screenshot + clean console + checklist) IS the verification. See RESEARCH.md
> § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | BrowserOS MCP (external browser automation) — no code test framework applies |
| **Config file** | `.mcp.json` (BrowserOS endpoint `http://127.0.0.1:9200/mcp`) |
| **Quick run command** | `cd site && npm run dev` (target under review) + BrowserOS navigate/screenshot/console per URL |
| **Full suite command** | Full review wave sequence (REVIEW-01 → REVIEW-05) producing `.planning/REVIEW-E2E-FINDINGS.md` |
| **Estimated runtime** | Manual/semi-auto; minutes per wave, not seconds |

---

## Sampling Rate

- **After every task commit:** Evidence captured (screenshot in `.planning/ui-reviews/` + console excerpt) for each reviewed URL/interaction.
- **After every plan wave:** Corresponding REVIEW-0x section of `REVIEW-E2E-FINDINGS.md` is appended/updated.
- **Before sign-off:** `REVIEW-E2E-FINDINGS.md` exists, is non-empty, and every finding is tagged Critical/Warning/Polish with page + screenshot + recommendation (REVIEW-05).
- **Max feedback latency:** Per-URL (navigate → screenshot → console read); no deferred batch.

---

## Per-Task Verification Map

> Verification here is browser-evidence, not an automated assert command. "Automated Command"
> column records the BrowserOS-driven check that produces evidence.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-pre | preflight | 0 | — | — | N/A | manual | List `mcp__browseros__*` tools; confirm dev server port from `npm run dev` | n/a | ⬜ pending |
| 07-r01 | review | 1 | REVIEW-01 | — | N/A | observational | BrowserOS navigate+screenshot+console for 12 EN + 12 ES editorial + map(2) + legal(4) URLs | `.planning/ui-reviews/*.png` | ⬜ pending |
| 07-r02 | review | 2 | REVIEW-02 | — | N/A | observational | Template checklist for declared sample (Santiago/Concepción/Punta Arenas, Metropolitana/Biobío, homicide/property, both locales) | `.planning/ui-reviews/*.png` | ⬜ pending |
| 07-r03 | review | 3 | REVIEW-03 | — | N/A | observational | Map interaction sequence (year/chip/panel/sparkline/family/search/geo/incident-empty) — clean console | `.planning/ui-reviews/*.png` | ⬜ pending |
| 07-r04 | review | 4 | REVIEW-04 | — | N/A | observational | set-viewport 375×812 → money pages + map → `document.body.scrollWidth > window.innerWidth` is false | `.planning/ui-reviews/*.png` | ⬜ pending |
| 07-r05 | review | 5 | REVIEW-05 | — | N/A | artifact | `.planning/REVIEW-E2E-FINDINGS.md` exists, non-empty, schema-conformant | `.planning/REVIEW-E2E-FINDINGS.md` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Pre-flight: confirm BrowserOS MCP tools surface as `mcp__browseros__*` (Claude Code restart may be required — see RESEARCH.md Pitfall 2).
- [ ] Pre-flight: confirm Astro dev server running and capture actual port (default 4321; may be 4322 if occupied).
- [ ] No code test framework to install — phase writes no production code.

*Browser/MCP infrastructure is external and already configured; the only Wave 0 work is availability confirmation.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual layout correctness (no overflow, readable) | REVIEW-01, REVIEW-04 | Visual judgment not assertable in code | Inspect each screenshot; flag visual defects in FINDINGS |
| Touch targets ≥44px on mobile | REVIEW-04 | Visual adequacy; spot-check via `evaluate` element dimensions | At 375px, eyeball nav/buttons; JS-measure where ambiguous |
| Map interaction "feels correct" (recolour, panel data) | REVIEW-03 | Behavior observed in live browser | Drive each interaction; screenshot before/after; confirm console clean |
| Template completeness (10 components present) | REVIEW-02 | Compare rendered page to template checklist | Tick each component on sampled commune pages |

*This phase is observational by nature — manual/visual verification is expected and primary, not a gap.*

---

## Validation Sign-Off

- [ ] Every URL in the declared inventory has screenshot + console evidence
- [ ] Sampling continuity: no reviewed category left without evidence
- [ ] Wave 0 availability confirmations passed (BrowserOS + dev server)
- [ ] No watch-mode flags
- [ ] `REVIEW-E2E-FINDINGS.md` complete per REVIEW-05 schema
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
