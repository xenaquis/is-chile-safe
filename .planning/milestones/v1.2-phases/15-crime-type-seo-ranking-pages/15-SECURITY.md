---
phase: 15
slug: crime-type-seo-ranking-pages
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-16
---

# Phase 15 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| committed CEAD JSON → Astro build-time read | Only data crossing into the build; pipeline-validated. No user input, no runtime network, no auth. | CEAD denuncia rates (public, non-sensitive) |
| rendered dist/ HTML → public/SEO crawlers | Output is static HTML; the editorial-tone guard is the relevant integrity boundary. | Public crime-ranking pages (no secrets/PII) |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-15-01 | Tampering | familyDefs.ts methodology copy (editorial-guard bypass) | mitigate | `forbidden-language.mjs` FORBIDDEN_TERMS (lines 35–57) + build-time dist/ scan; `RANKING_METHODOLOGY_EN/ES` (familyDefs.ts 66–86) verified term-clean | closed |
| T-15-02 | Information disclosure | seo.mjs sample paths | accept | Validator reads only local dist/ HTML; no secrets, PII, or network | closed |
| T-15-03 | Tampering | ItemList name / H1 / methodology prose (editorial-guard bypass) | mitigate | `assertSafeName()` (jsonld.ts 21–31) called by `buildItemList` (73–75); ItemList names + H1s in both `[crime].astro` pages verified sober (no safe/dangerous/segura/peligrosa) | closed |
| T-15-04 | Tampering | Homicide rate field (wrong-source data integrity) | mitigate | `dataSource:'featured_rates'` branch reads `commune.featured_rates?.homicidios` (EN [crime].astro 29,88–90; ES 37,96–98), never `by_family['homicidios']` | closed |
| T-15-05 | Information disclosure | internal links / sitemap | accept | Links target public static comuna/region pages; coverage.mjs no-orphan guard | closed |
| T-15-SC | Tampering | npm/pip/cargo installs (supply chain) | accept | No new packages this phase; `site/package.json` last modified Phase 13 (e363c7a), confirmed via `git log` | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-15-01 | T-15-02 | seo.mjs reads only local dist/ build output — read-only, no secrets/PII/network; scope fully local and committed. | gsd-security-auditor | 2026-06-16 |
| AR-15-02 | T-15-05 | All linked pages are public static comuna/region pages by design; coverage.mjs prevents orphans. | gsd-security-auditor | 2026-06-16 |
| AR-15-03 | T-15-SC | No new packages installed this phase; existing dependency set audited in prior phases. | gsd-security-auditor | 2026-06-16 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-16 | 6 | 6 | 0 | gsd-security-auditor (sonnet) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-16
