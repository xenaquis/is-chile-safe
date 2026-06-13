---
phase: 2
slug: astro-site-programmatic-pages
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-13
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. This is a **build-only static-site** phase: validation is build-output assertion, not interactive testing. No browser, no runtime server — assertions run against `astro build` output in `site/dist/`.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Node.js built-in `assert` + `node:test` (no Jest/Vitest dependency); `@astrojs/check` for .astro typecheck |
| **Config file** | `site/astro.config.mjs` (Wave 0 installs); validation scripts under `site/scripts/validate/` |
| **Quick run command** | `cd site && node scripts/validate/structure.mjs` (asserts dist HTML structure for a sample page set) |
| **Full suite command** | `cd site && npm run build && node scripts/validate/all.mjs` (build + page-count + hreflang reciprocity + file-size + Schema.org assertions) |
| **Estimated runtime** | ~30–60 seconds (full build of batch ~85 files; <10s for assertion scripts) |

---

## Sampling Rate

- **After every task commit:** Run `node scripts/validate/structure.mjs` (or `astro check` for type-only tasks)
- **After every plan wave:** Run `npm run build && node scripts/validate/all.mjs`
- **Before `/gsd:verify-work`:** Full build green + all assertion scripts exit 0
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

> Task IDs are provisional (planner assigns final). This maps each requirement to its build-output validation. `❌ W0` = infrastructure built in Wave 0.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 2-00-01 | 00 | 0 | (infra) | — | N/A | build | `cd site && npm run build` exits 0 | ❌ W0 | ⬜ pending |
| 2-00-02 | 00 | 0 | (infra) | — | N/A | typecheck | `cd site && npx astro check` exits 0 | ❌ W0 | ⬜ pending |
| 2-01-01 | 01 | 1 | PAGES-01 | — | N/A | structure | `node scripts/validate/commune.mjs` asserts each built commune page ≥500 words + 5 data dimensions present (rate-vs-national, rate-vs-regional, trend, dominant-family, comparable-commune) | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 1 | PAGES-04 | — | N/A | count | `node scripts/validate/rollout.mjs` asserts dist contains exactly the rollout-allowlist commune pages (×2 locales) when ROLLOUT_ALL unset; all 346×2 when set | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 1 | PAGES-02 | — | N/A | count | assert 16 region pages × 2 locales built with aggregates + commune ranking | ❌ W0 | ⬜ pending |
| 2-03-01 | 03 | 1 | PAGES-03 | — | N/A | count | assert 7 crime-family pages × 2 locales (14 total) built with national ranking | ❌ W0 | ⬜ pending |
| 2-04-01 | 04 | 2 | SEO-01 | — | N/A | hreflang | `node scripts/validate/hreflang.mjs` asserts every page has reciprocal en/es/x-default alternates pointing at existing dist files | ❌ W0 | ⬜ pending |
| 2-04-02 | 04 | 2 | SEO-02 | — | N/A | structure | assert self-canonical on every page + sitemap-index.xml exists and lists only rollout pages | ❌ W0 | ⬜ pending |
| 2-04-03 | 04 | 2 | SEO-03 | — | N/A | jsonld | `node scripts/validate/schema.mjs` asserts territorial pages embed valid Dataset/Place JSON-LD crediting CEAD | ❌ W0 | ⬜ pending |
| 2-04-04 | 04 | 2 | SEO-04 | — | N/A | structure | assert manifest.webmanifest present + theme-color meta on all pages; no SEO-critical content in client-only islands | ❌ W0 | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `site/` Astro 6.4.x project scaffolded (`astro.config.mjs`, `package.json`, `tsconfig.json`, `.nvmrc`) — installs framework + @astrojs/sitemap + chroma-js
- [ ] `site/src/lib/data.ts` — build-time `node:fs` loader for `../data/cead/` (resolved via `fileURLToPath(import.meta.url)`, NOT `import.meta.glob`)
- [ ] `site/scripts/validate/` — Node assertion scripts (structure, commune, rollout, hreflang, schema, all) — stubs created Wave 0, filled as plans land
- [ ] `site/src/config/rollout.json` — batch allowlist (CUT codes) + CUT→slug resolution helper

*Build-output assertion is new infrastructure — no prior framework exists in `/site/` (greenfield).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Pages visually render with correct teal palette + incidence colors | (UI-SPEC) | Visual fidelity not assertable from HTML structure alone | `cd site && npm run dev`, open `/commune/santiago/` + `/es/comuna/santiago/`, confirm palette + sparkline + family bars render |
| GSC indexing of initial 10–20 batch before full 346 | PAGES-04 (deploy gate) | Requires live deploy + Google — deferred to Phase 6 | Deferred; Phase 2 only verifies the rollout config gate works at build time |
| Prose reads naturally across variation branches | PAGES-01 | Subjective language quality | Spot-read 5 commune pages across trend/rank tiers (e.g. Santiago, Vitacura, a low-pop commune) in both locales |

---

## Validation Sign-Off

- [ ] All tasks have automated build-assertion verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (Astro scaffold + data loader + validate scripts)
- [ ] No watch-mode flags (build is one-shot)
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter (after planner maps final task IDs)

**Approval:** pending
