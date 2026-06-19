---
phase: 11
slug: publish-346-comunas-finder
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-15
---

# Phase 11 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Verified retroactively via `/gsd:secure-phase 11`. Register authored at plan time (all 4 PLAN files carry `<threat_model>` blocks).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| repo data → build | Only trusted, version-controlled CEAD JSON feeds the loaders. | Public crime statistics (no PII) |
| repo data → static HTML | Comuna names/slugs rendered server-side as text/links. | Trusted CEAD index strings |
| user query → DOM (directory search) | Search input is client-side only, never sent to a server; interpolated into the DOM by highlight logic. | Untrusted user keystrokes (client-only) |
| npm registry → devDeps | `cross-env` install pulls a third-party package into the build toolchain. | Build-time tooling code |
| build output → dist/ → CI gate | Validator suite is the trust gate proving 0 dead-links + full coverage before publish. | Generated static HTML |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-11-01 | Tampering | data.ts memoization caches | accept | Module-level caches (`_indexCache`, `_communeCache`, `_regionCache`, `_natAvg`, `_regAvg`) hold only build-time-derived values from trusted repo JSON; single-pass build, no concurrency or invalidation surface. `data.ts:114–118`. | closed |
| T-11-02 | Denial of Service | CI/Cloudflare 20-min build budget | mitigate | Memoization removes O(n²) re-reads (`data.ts:114–118`); coverage/rollout validators are dist-only (no rebuild). Build wall-clock ~90 s, well within budget (11-04-SUMMARY.md). | closed |
| T-11-03 | Tampering | crime/region templates emitting comuna links | accept | href emitted as static `` `/commune/${row.slug}/` `` from build-time CEAD slugs; no user input reaches the template. `crime/[family].astro:215`. | closed |
| T-11-04 | Information Disclosure | newly-published 334 comuna pages | accept | All content is already-public CEAD official statistics; no PII; publishing is the explicit phase goal. | closed |
| T-11-05 | Tampering/XSS | directory search-highlight `<mark>` injection | mitigate | `highlight()` slices the trusted `data-name` attribute around the match index and concatenates only literal `<mark>` tags; `innerHTML` receives only `name.slice()` output — raw query `q` never enters the DOM string. `communes/index.astro:201–221`, `es/comunas/index.astro:201–221`. (ASVS V5) | closed |
| T-11-06 | Information Disclosure | directory exposes all 346 comuna links | accept | Intended findability hub; public CEAD data; SEO is a stated project goal; no PII. | closed |
| T-11-07 | Spoofing/Integrity | orphan internal links (dead clicks) | mitigate | `coverage.mjs:101–163` Assertion B scans all `dist/**/*.html`, extracts every `/commune/{slug}/` and `/es/comuna/{slug}/` href, asserts each has a generated `index.html`; registered in `all.mjs:40`. Confirmed PASS (0 dead links across 772 HTML files, 11-04-SUMMARY.md). | closed |
| T-11-SC | Tampering | cross-env devDependency install (supply chain) | mitigate | `package.json:10` build script `cross-env ROLLOUT_ALL=true astro build`; `package-lock.json:2775` pins `cross-env@10.1.0` (established MIT build tool) to `registry.npmjs.org` with integrity hash. | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-11-01 | T-11-01 | Build-time memoization caches hold derived values with no invalidation; single-pass Astro build over immutable version-controlled repo JSON; no concurrency or cache-poisoning surface. | gsd-security-auditor | 2026-06-15 |
| AR-11-03 | T-11-03 | Static `<a href>` links use build-time slugs derived from trusted CEAD JSON; no user-controlled input reaches template rendering. | gsd-security-auditor | 2026-06-15 |
| AR-11-04 | T-11-04 | All 346 comuna pages publish officially-published CEAD crime statistics; no PII; no confidentiality obligation. | gsd-security-auditor | 2026-06-15 |
| AR-11-06 | T-11-06 | Directory exposes an index of all 346 public CEAD localities as an intended findability hub; SEO is a stated project goal. | gsd-security-auditor | 2026-06-15 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-15 | 8 | 8 | 0 | gsd-security-auditor (claude-sonnet-4-6) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-15
