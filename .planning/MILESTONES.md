# Milestones

## v1.0 MVP (Shipped: 2026-06-13)

**Phases completed:** 6 phases, 28 plans, 16 tasks

**Key accomplishments:**

- Pydantic v2 data contracts (7 models, 346-count validation gate, plausibility range checks) plus atomic JSON write utility, pytest infrastructure, and pinned Python dependencies.
- Static INE 2024 communal population JSON (346 entries) with lru_cached lookup and 10,000-threshold low-population filter for DATA-04 ranking exclusions.
- Open Question 3 (confirming `grupo[]/subgrupo[]` parameter values for homicides subgroup ID=101 and the kidnappings subgroup ID) was NOT resolved at this checkpoint. The user chose to defer subgroup ID confirmation to Plan 04.
- 1. [Rule 1 - Bug] make_slug apostrophe handling
- 1. [Rule 3 - Blocker] DATA_ROOT path depth was 3 levels in RESEARCH.md but needs 4
- 1. [Rule 1 - Bug] Unused import in PageFooter.astro
- 1. [Rule 3 - Blocking] import.meta.url breaks in Astro prerender bundles
- 16×2 bilingual region pages with regional-mean aggregates, sorted commune ranking tables, reciprocal hreflang, and Dataset+Place JSON-LD; region and structure validators green.
- 14 bilingual crime-type pages (7 families × 2 locales) with build-time national commune ranking by family rate, translated URL slugs, and Dataset-only JSON-LD.
- Rollout-gated sitemap with ROLLOUT_ALL override, PWA manifest + teal placeholder icons, EN/ES home placeholders, 7-validator suite (hreflang reciprocity + Schema.org), full 346-commune ROLLOUT_ALL build verified at 745 files under the 20K Cloudflare limit.
- Rule: None (planned per PLAN.md critical_finding)
- Rule: Rule 1 (Bug)
- Geolocation via Geolocation API + ray-cast PiP for commune highlight (MAP-05), and graceful NEWS incident-pin layer with HTML-escaped divIcon popups (MAP-04); build and all 8 validators green.
- 1. [Rule 2 - Missing] ES hreflang stub pages
- 1. [Rule 2 - Missing] ES hreflang stub pages (x4)
- 1. [Rule 1 - Bug] Metodologia H2 "Lo que este sitio NO afirma" failed the Task 3 gate
- Pydantic v2 output schema locked to IncidentPinLayer.ts contract, 346-commune centroid lookup generated via Node+Shoelace, 6 test modules + 4 fixtures scaffold Wave-1 implementation with DeepSeek mocked
- feedparser RSS fetch with per-feed graceful fallback, CRIME_KEYWORDS pre-filter, seen-URL ledger, DeepSeek v4-flash closed-list JSON classifier with CUT/confidence anti-hallucination rejection, and deterministic centroid lookup
- stdlib-difflib URL+title dedup and sha256-id idempotent 30-day rolling store with IncidentsFile schema gate before every atomic write.
- RSS news pipeline orchestrator wiring fetch→keyword-filter→seen-ledger→classify→centroid→dedup→merge_and_write with D-17 cost cap, graceful no-key path, and 6 mocked-DeepSeek integration tests (IncidentsFile.model_validate + TS field names confirmed).
- Two GitHub Actions cron workflows with data-change-gated commits and dry-run-safe Cloudflare Pages Deploy Hook curl via `env.CF_HOOK` pattern.
- 3-job parallel CI guard (Astro build+9 validators, pytest, actionlint) triggered on PR and workflow_dispatch, with zero deploy/push capability.
- Human CF-dashboard runbook: CF Pages project + Deploy Hook + auto-build OFF + ischilesafe.com domain + rebuild-loop verification.

---
