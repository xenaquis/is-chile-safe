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

## Cross-Milestone Trends

_(First milestone — trends accumulate from v1.1 onward.)_
