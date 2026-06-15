# Retrospective — Chile Safety Map (ischilesafe.com)

## Milestone: v1.0 — MVP

**Shipped (code-complete):** 2026-06-13
**Phases:** 6 | **Plans:** 28

### What Was Built

A bilingual (ES/EN) static platform combining a quantitative layer (official CEAD crime stats per commune/region/country as an interactive Leaflet choropleth with year/crime filters, rankings, sparklines, geolocation) and a qualitative layer (recent press incidents classified + geolocated by DeepSeek v4-flash, shown as map pins). 740+ programmatic SEO pages, 20 editorial + 8 legal hero pages, a build-time forbidden-language gate, env-gated AdSense, and a fully automated GitHub Actions → Cloudflare Pages pipeline with a no-rebuild-loop Deploy Hook.

### What Worked

- **Contract-first cross-phase wiring.** Phase 3 defined the `incidents/current.json` TS interface up front; Phase 5's Pydantic model was built to serialize to it field-for-field. The integration checker confirmed 14/14 contracts wired with zero drift.
- **Closed-list + deterministic centroids** for the news pipeline — the LLM picks a CUT from the fixed 346 list (temp 0.0) and never emits coordinates, structurally preventing the headline hallucination risk.
- **Test-first Wave 0** in Phases 1 & 5 (pytest scaffolds + mocked DeepSeek) kept the pipeline fully verifiable in CI without a live API key.
- **Reuse over rebuild** — Phase 4 wrapped the Phase-2 BaseLayout/design system (D-16) instead of a new layout; Phase 6 reused the existing build/validate scripts.
- **Adversarial code review caught real, shipping-blocking bugs** the plan-checker missed: the AdSlot reserved-`slot` prop (CLS break), the JSON-LD `</script>` breakout, the news seen-ledger not recording rejects (API-cost leak), and — most importantly — the Phase-6 deploy gate that would have **never fired** (step-level `env.CF_HOOK` invisible to its own `if:`).

### What Was Inefficient

- **ES hreflang stubs churned** — Phases 4-04/4-05 created placeholder ES pages for hreflang reciprocity that Phase 4-06 then overwrote. A single ES-pages plan ordered before the EN map pages would have avoided the throwaway work.
- **`structure.mjs` sentinel went red mid-wave** (once methodology built but legal pages hadn't), which looked alarming until 04-07 closed it. A clearer "phase-gate validator activates at the end" signal would reduce noise.
- **OneDrive working dir** forced chaining build+validate in one command throughout (known constraint, but a recurring tax).

### Patterns Established

- Phase-3 TS interface as the locked output contract for a downstream Python producer.
- `*-HUMAN-UAT.md` to persist genuinely-human/external verification (live API key, live deploy) without blocking autonomous progress.
- Deterministic ID (SHA-256 of source URL) + committed seen-ledger for idempotent, cost-bounded re-runs.
- Env-gated, default-off integration (AdSense) shipped inert in one phase, activated by a later deploy phase.

### Key Lessons

- **A step's own `env:` is NOT in scope for that step's `if:`** — gate on job-level env. This silently dead-ended the entire deploy path and only a code review caught it. Worth a lint rule.
- **Keep one source of truth for ordered enums** — FAMILY_KEYS is duplicated (pipeline ↔ FiltersRow); add a CI assertion before it silently mis-maps crime families.
- For an infra phase, the honest "done" can be **code-complete with documented human go-live gates** — archiving with a runbook + HUMAN-UAT beats faking a deploy the agent can't perform.

### Cost Observations

- Model mix: planning/architecture on Opus; research/pattern-map/execute/review/verify on Sonnet subagents.
- The four code reviews paid for themselves — each surfaced ≥1 genuinely shipping-blocking defect (CLS, XSS-adjacent, cost leak, dead deploy gate).

## Milestone: v1.1 — Polish & QA

**Shipped:** 2026-06-15
**Phases:** 3 (7–9) | **Plans:** 15

### What Was Built

A QA/polish pass before go-live: a full E2E browser review (Phase 7) feeding a findings ledger, then bug/data-correctness fixes (Phase 8) and UX/readability/a11y polish (Phase 9). Data correctness confirmed (rates = national mean, not sum), console clean, AdSlot CLS removed, bilingual glossary added, sober tone enforced, WCAG-AA contrast verified.

### What Worked

- The findings-ledger pattern (Phase 7 → 8/9) gave a clean, auditable closure trail; ~80% of findings closed within the milestone.
- The milestone audit caught the two real residual defects (F-006, WR-03) and the artifact gap (missing 09-VERIFICATION.md) before close — the audit gate did its job.
- Chained build+validate (OneDrive desync guard) kept dist/ assertions trustworthy.

### What Was Inefficient

- The deferral chain dropped terminal nodes: F-002/F-004 were deferred Ph8→Ph9 but never got a Phase-9 disposition, so they surfaced again only at audit. Deferrals need an explicit owner/phase every time.
- 09-VERIFICATION.md was never produced during the phase (coverage was real via SUMMARY+VALIDATION), forcing a retroactive artifact at close.
- STATE.md milestone pointer drifted (said v1.1/5-phases while v1.2 Phases 10–11 were already executing) — milestone boundaries weren't advanced when v1.2 work started early.

### Patterns Established

- Grammatical region naming centralized in `regionNameEs()` rather than inline templates — a single source for the "de / del / no-preposition" rule.
- Accessible zero-JS disclosure: sr-only-but-focusable checkbox (never `display:none`) keeps a keyboard path under the zero-JS constraint.

### Key Lessons

- A grammar bug found in one template (region page) was symptomatic of a wider one (the whole ES prose engine) — fix the class, grep the blast radius, don't stop at the flagged line.
- Structural validators (region/coverage) check join integrity, not geographic correctness — they passed while Tarapacá comunas were mis-regioned. Geographic correctness needs its own assertion (found as backlog 999.1).

### Cost Observations

- Milestone closed in a single session; gap-closure (F-006 + WR-03) + full archive on Opus inline.
- Two clean build+validate cycles (10/10 validators) bracketed the code fixes — cheap, high-confidence gate.

## Cross-Milestone Trends

| Milestone | Phases | Plans | Shipped | Notable |
|-----------|--------|-------|---------|---------|
| v1.0 MVP | 6 | 28 | 2026-06-13 | Full stack: data → site → map → editorial → news → CI/CD |
| v1.1 Polish & QA | 3 | 15 | 2026-06-15 | E2E review → fixes; audit caught 2 residual defects pre-close |

**Recurring themes:**
- Audits/reviews consistently surface ≥1 real shipping-blocker per milestone — keep the gate.
- Deferral hygiene is the weak spot: deferred items lose their terminal owner. Every deferral should name the closing phase.
- Validators verify structure, not semantics/geography — semantic correctness needs explicit assertions.
