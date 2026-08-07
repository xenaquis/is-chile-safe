# Milestones

## v2.1 News Intelligence, Map UX & Ops Hardening (Shipped: 2026-08-05)

**Phases completed:** 8 phases (26–33), 27 plans. Executed as an **unattended autonomous run**
under `v2.1-AUTONOMOUS-DIRECTIVE.md`; 129 binding decisions recorded as F-01..F-129.

**Key accomplishments:**

- **News faceting** on `/news/` + `/es/noticias/` — filter by window, region and crime family with per-option counts and an accent-insensitive comuna typeahead, query-param only, **zero new indexable URLs** and zero hydration (the full card superset is pre-rendered).
- **Map control shell reworked** — the news toggle had been the last chip in a scrolling row with its only affordance suppressed, sitting **507 px offscreen** at desktop and 991 px at 375 px. It is now standalone and labeled, with three `<details>` entry points and a `<dialog>` bottom sheet below 480 px. Zero map-owned touch-target violations at every width.
- **Event clustering: NO-GO, measured and documented** — precision 0.667 (fp=11, tp=22 over 86 hand-labeled pairs) against a locked 100 %/zero-false-merge gate. No clustering shipped; the gate is quarantined as `xfail(strict=True)` so a future model that passes re-opens the decision instead of silently hiding a GO.
- **A live factual error corrected** — the methodology page told readers `Rank 1 = lowest reported rate` while the code sorts descending. Found five times in five phrasings across four sweeps; the guard now matches the semantic shape over all of `site/src`.
- **The cron surface made self-diagnosing** — five shared bash scripts, a heartbeat workflow, per-pipeline alert labels, and a documented answer to "if a cron stops firing, what goes red and when". Two of the phase's own new guards would have broken live crons and were caught before shipping.
- **Security posture** — 13 action refs SHA-pinned, per-job `permissions:` on 8/8 jobs, dependabot across three ecosystems, zizmor in CI, and two new canary-armed gates. 11 of 12 security alerts closed without a major framework upgrade.

---

## v2.0 Composite Index, Comparators & Launch (Shipped: 2026-07, production live)

**Phases completed:** 6 phases (18, 21, 22, 23, 24, 25), 30 plans.

**Key accomplishments:**

- **The site went live** at ischilesafe.com on Cloudflare Pages, with auto-build off and deploys driven by a data-change-gated deploy hook.
- **Composite crime index** — a 0–100 score with 5 bands and national/regional rank, computed from 7 hardened metrics, surfaced on the map, commune pages and popup, always with its caveat block.
- **Commune comparator + A-vs-B programmatic SEO** — side-by-side comparison plus pair pages built from a curated allowlist, each with ≥300 words of non-swappable prose, rolled out in staged batches.
- **ENUSC communal victimization layer** for the 136 communes the survey covers, added additively without disturbing the CEAD spine.
- **Sortable ranking tables** and a UI/UX 360 remediation pass, including the soft-404 fix that a diagnostic found serving 200s for missing pages.

---

## v1.3 v1.3 (Shipped: 2026-06-19)

**Phases completed:** 2 phases, 10 plans, 7 tasks

**Key accomplishments:**

- Fixed unweighted/weighted contradiction in EN+ES methodology prose (two locations each) and added partial_year boolean to build_map_payload output.
- `cd site && npm run build && npm run validate` — 12/12 validators passed.
- Replaced 25+ user-visible "commune" occurrences with "comuna" across 7 ES files, fixed "adjacent"→"vecina" in Valparaíso prose, and created the reciprocal EN /crimes-by-region/ page with correct bidirectional hreflang — eliminating the /es/delitos-por-region/ orphan.
- 1. [Rule 2 - Missing critical functionality] Updated validators to skip static redirect pages
- Retired stale map placeholder with neutral live-map CTA; added FAMILY_KEYS CI assertion + ByFamily TypedDict; cleaned Wave-1 skipif cruft; reconciled nyquist flags.
- Extracted commune section headings, crime/ranking table headers, footnotes, and cookie-consent strings from per-locale inline literals to i18n.ts as single source of truth.
- Adds per-family mean (F3), per-region mean (F4), LevelChip relative tier (F6), F2/F5 weighting distinction, #trend-formula anchor (F7), and Ley 20.000 drogas scope note (F10) across methodology pages, ranking pages, and FamilyBreakdownBars — EN/ES parity maintained, 12/12 validators pass.
- INE population spot-check pytest (9 tests, 7 communes) + figure-registry zero-orphan validator registered as 13th — full suite 13/13 PASS, pipeline 179/179 PASS.

---

## v1.2 Map Fidelity, Findability & News (Shipped: 2026-06-19)

**Phases completed:** 8 phases, 34 plans, 29 tasks

**Key accomplishments:**

- Registered coverage.mjs in the 10-validator suite and ran the committed full ROLLOUT_ALL=true build; 10/10 validators green; build under 2 minutes; awaiting human reachability checkpoint.
- Build-time plural similar-communes helper + 5 i18n keys per locale + URL ?q= pre-filter on both directory finders, establishing contracts for all Wave-2 hub-and-spoke pages.
- Added `?cut=<CUT>` deep-link focus to Leaflet MapIsland by reading URLSearchParams inside `loadData()` after `mountChoroplethLayer()` completes, calling `selectCommune` via `setTimeout(100ms)`.
- Rankings nav node + global footer-spine row + /rankings/ + /es/rankings/ static index pages closing IA-03 gap.
- spine.mjs validator enforcing IA-01/02/03 cross-link reciprocity (assertions F-L) registered in all.mjs; 11/11 validators green against 774-page ROLLOUT_ALL build.
- Seven branded 1200×630 OG placeholder PNGs generated by a zero-dep Node script, shared buildItemList/buildBreadcrumb JSON-LD helpers with rate excluded and editorial guard, and a new seo.mjs validator registered as the 12th entry in the suite — all green 12/12.
- 1. [Rule 1 - Bug] Experiment script fallback never fired despite subgrupo[] being wrong
- 1. [Rule 1 - Bug] build_map_payload int/str year key lookup mismatch
- 1. [Upstream Fact] Check 8 asserts 'hr' not 'homicide_rate'
- Commune detail panel now shows a separate homicide figure (rate per 100k + absolute case count + CEAD year) reading `featured_rates.homicidios` / `homicidios_count`, bilingual + CEAD-cited, with an explicit non-alarmist zero state, distinct from the 7 family bars (HOM-02).
- SEO validator extended with guarded crime-ranking namespace samples; bilingual 8-key methodology records added to familyDefs.ts citing CEAD subgroup 101, denuncias framing, and full family aggregates.
- Bilingual crime-ranking SSG pages (8 types x 2 locales = 16 new pages) with homicide via featured_rates branch, ItemList+BreadcrumbList+Dataset JSON-LD, sober H1, reciprocal hreflang, and homicide-ranking spoke added to all 346 EN+ES comuna pages.
- resolver.py
- dc9a786
- `IncidentRecord.slug: str | None = None` added to `pipeline/news/schema.py`. `build_incident` in `store.py` gains a `slug=None` keyword param that is included in the returned dict. Back-compat preserved: any existing `current.json` without `slug` still validates (Pydantic optional with default). Three new tests added.
- Bilingual /news/ + /es/noticias/ pages with freshness indicator, incident→source + incident→comuna links in popup/list/page, nav_news i18n string, News nav link, and sitemap rule.
- Complete · **Tasks:** 2/2 (run inline by orchestrator — BrowserOS checkpoint) · **Executed:** 2026-06-18
- Canonical 5-class source registry at data/SOURCES.md (CEAD/SPD/SII/Fiscalia/chilemapas) plus wrong CEAD host corrected in both EN/ES terms pages (ministeriointerior → minsegpublica).
- EN page (`/methodology/`)
- Complete · **Tasks:** 3/3 · **Executed:** 2026-06-18 (inline by orchestrator — plan carries a BrowserOS human-verify checkpoint that gsd-executor cannot run)

---

## v1.1 Polish & QA (Shipped: 2026-06-15)

**Phases completed:** 3 phases (7–9), 15 plans

**Delivered:** A QA/polish pass over the whole rendered site (ES/EN) before go-live — bugs hunted in a real browser, data correctness verified, cognitive load reduced, accessibility and SEO signals tightened. No new features.

**Key accomplishments:**

- Phase 7 — Full E2E browser review (ES/EN) via BrowserOS MCP: editorial/map/legal inventory walk, programmatic-page sampling vs template, map dynamic interactions, mobile 375px viewport, all findings consolidated into REVIEW-E2E-FINDINGS.md (severity/page/screenshot/recommendation). Closed the deferred Phase-3 visual/mobile UAT.
- Phase 8 — Data correctness + bug fixes: rates use the national MEAN (not sum) ranked by rate/100k (spot-checked vs `data/cead/`); 0 console errors on money pages; rollout-row gating fixes dead ranking links; AdSlot reserves height with 0 `adsbygoogle` in the disabled DOM.
- Phase 9 — UX/readability/a11y: single-H1 scannable hierarchy, 720px prose rhythm, bilingual glossary pages, sober tone (forbidden-language validator clean), WCAG-AA contrast (axe PASS), map-control aria, valid meta/canonical/hreflang + FAQPage JSON-LD.
- Milestone-close gap-closure (commit d9593a3): **F-006** ES region grammar fixed via `regionNameEs()` across region pages + the ES prose engine ("Región Metropolitana" / "Región del Biobío" / "Región de Tarapacá"); **WR-03** mobile hamburger made keyboard-operable (sr-only-but-focusable checkbox + focus ring). 09-VERIFICATION.md produced; build clean, 10/10 validators pass.

**Accepted tech debt / known gaps:** F-002 (cookie/accessibility legal pages absent) and F-004 (thin contact pages) — pre-acknowledged Polish non-blockers. 08-VALIDATION.md absent (bug-fix phase; coverage evidenced by 08-VERIFICATION.md).

**Newly found (logged to v1.2 backlog 999.1):** Tarapacá comunas mis-assigned to Aysén/Los Ríos via ambiguous 2-digit `region_id` province codes (collide with region numbers 11/14). Pre-existing Phase-1 data issue; fix deferred to v1.2.

Full detail: `milestones/v1.1-ROADMAP.md` · `milestones/v1.1-REQUIREMENTS.md` · audit `milestones/v1.1-MILESTONE-AUDIT.md`.

---

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
