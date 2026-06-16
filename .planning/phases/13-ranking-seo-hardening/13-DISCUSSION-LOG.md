# Phase 13: Ranking SEO Hardening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-15
**Phase:** 13-ranking-seo-hardening
**Areas discussed:** Social image (og:image), ItemList JSON-LD scope, OG/Twitter text + card type, Validation depth

---

## Social image (og:image)

| Option | Description | Selected |
|--------|-------------|----------|
| Per page TYPE | Curated static images (home/comuna/region/ranking/editorial) under `site/public/og/`; $0 build, no new deps; enables `summary_large_image` | ✓ |
| Single site-wide image | One OG image for all pages; simplest but every share looks identical | |
| Per-page generated cards | Build-time satori/@vercel-og cards with comuna name + rate; nicer but adds dependency + build cost over 774 pages | |

**User's choice:** Per page type (recommended).
**Notes:** Per-page generated cards explicitly deferred to a future enhancement. Locks Twitter card = `summary_large_image`.

---

## ItemList JSON-LD scope

| Option | Description | Selected |
|--------|-------------|----------|
| Regional ranking (ficha + region) | Real rankings with position + rate per comuna | ✓ |
| /crime/[family] pages | Crime-type ranking tables; high SEO value | ✓ |
| Home two lead tables | Lowest / highest reported-rate top-6 tables | ✓ |
| /rankings/ index + ficha "similar" | Index is a link list (no rates); "similar" is proximity order, not absolute rank | ✓ |

**User's choice:** All four — full coverage.
**Notes:** Weaker-semantic tables (`/rankings/` index, "similar comunas") to be represented honestly — position = displayed order, never presented as a safety ranking; no rate-as-rank claim.

---

## OG/Twitter text + card type

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse title + description | `og:title` = page `<title>`, `og:description` = existing meta description (per-locale, DRY) | ✓ |
| Distinct social copy | Author separate punchier OG text; more control but double-maintenance per-locale | |

**User's choice:** Reuse title + description (recommended).
**Notes:** Twitter card type already fixed to `summary_large_image` by the og:image decision.

---

## Validation depth

| Option | Description | Selected |
|--------|-------------|----------|
| Sampled per template type | Assert OG + JSON-LD presence/shape on one page per type (home/comuna/region/crime/ranking/editorial) × both locales; fast, catches template regressions | ✓ |
| All 774 pages | Enforce on every dist page; max guarantee but slower and redundant if templates are the only variation | |

**User's choice:** Sampled per template type (recommended).
**Notes:** "Validate against schema.org" = offline JSON-LD shape check (parse + assert @context/@type + required fields), no network call — keeps the ~$0 build.

---

## Claude's Discretion

- Exact `og:type` mapping per template; `og:locale` value form; per-type OG image filenames + dimensions (1200×630) and default fallback.
- `jsonLd` emission as array-of-`<script>` blocks vs schema.org `@graph` (confirm cleanest + valid in research).
- Which exact URLs represent each "template type" in the sampled validator.

## Deferred Ideas

- Dynamically generated per-page OG card images (satori/@vercel-og) → future enhancement.
- Any page copy/content/layout change → out of scope (additive meta/structured-data only).
- `adsense-consent-mode-phase6` todo — reviewed, not folded (unrelated AdSense concern).
