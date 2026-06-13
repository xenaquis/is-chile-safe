# Phase 4: Editorial Pages + AdSense - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning
**Mode:** Autonomous smart-discuss (4 grey areas, all accepted with recommended values)

<domain>
## Phase Boundary

The high-value editorial and legal layer of the site: 10 priority EN + 10 priority ES curated editorial pages, a rich methodology page, four legal pages (Privacy/Terms/About/Contact), a build-time forbidden-language gate, and a deferred-activation AdSense integration. These are hand-curated SEO hero pages (unlike the templated programmatic pages of Phase 2), built on the Phase-2 Astro foundation and reusing its layout/components/i18n.

Requirements: EDIT-01, EDIT-02, EDIT-03, EDIT-04, EDIT-05, MON-01.

**Out of this phase:**
- The programmatic commune/region/crime pages (Phase 2) and the interactive map island (Phase 3) — reused here (some editorial pages embed the map / link to data), not rebuilt.
- Live deploy, GSC submission, and confirming the "first indexing wave" → Phase 6 (this phase builds the AdSense slots + gate but does not flip them on in production).
- The RSS/news layer (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### Editorial content authorship
- **D-01:** Each of the 20 editorial pages = a **templated skeleton + curated editorial prose per page**, injecting real data callouts (rate/ranking/trend from `data/cead/`) so claims are sourced and current. Not pure-manual, not pure-templated.
- **D-02:** Depth **~800–1500 words/page** with proper SEO structure (single H1, H2 sections); the question-style pages ("Is Santiago safe", "Is Chile safe") include an FAQ block with `FAQPage` schema.
- **D-03:** Map-bearing editorial pages (`/chile-crime-map/`, `/santiago-safety-map/`, and ES equivalents) **embed the Phase-3 map island** (`client:only="react"`, reusing the MapIsland) with editorial content around it. Other editorial pages stay static.
- **D-04:** Bilingual via **parallel hand-maintained ES/EN templates** (same approach as Phase 2), sober editorial language throughout.

### Forbidden-language gate (EDIT-05)
- **D-05:** Implemented as a **post-build validator over `dist/` HTML** (extends `site/scripts/validate/`), failing the build with a clear, non-zero error naming the offending page + term. Wired so `npm run build` + validate catches it.
- **D-06:** Term list = the 4 named phrases **plus variants**: "zona/comuna peligrosa(s)/peligroso(s)", "ranking definitivo", "zona segura garantizada", "100% seguro", "garantiza(da) seguridad", and EN equivalents ("dangerous zone/area", "guaranteed safe", "definitive ranking"). Extensible list in the validator.
- **D-07:** Scope = **all pages' visible text** (strip tags/scripts; ignore attributes/URLs).
- **D-08:** Matching is **case- and accent-insensitive**, word-boundary aware (avoid false positives inside larger words).

### AdSense (MON-01)
- **D-09:** Ad slots are **built but gated behind an env flag (`ADSENSE_ENABLED`, default off)** — MON-01 activates only after the first indexing wave (Phase 6). With the flag off, slots render nothing (or a reserved-space placeholder).
- **D-10:** An **`<AdSlot>` component reserves fixed dimensions** to avoid CLS; placed in the page template (content pages + editorial), **never on the map view or legal pages**.
- **D-11:** **Cookie-consent banner + a Privacy page** that discloses AdSense/cookies (AdSense policy + Chile/GDPR-style requirement). Consent gates ad personalization script load.
- **D-12:** AdSense loader script is **async/`client:idle`**, single publisher ID read from env; not inlined per-page.

### Legal pages + structure
- **D-13:** Legal pages (EDIT-04) = **Privacy Policy, Terms, About, Contact** in EN + ES, linked from the site footer.
- **D-14:** Contact = a **static form (mailto or a no-backend form service placeholder)** — no server (MVP is 100% static).
- **D-15:** Methodology (EDIT-03) = **one rich page**: CEAD sources, rate-per-100k calculation, subregistro / cifra negra caveat, comparison criteria, and the trend formula (the % threshold from Phase-1 D-13). Indexed before AdSense application.
- **D-16:** **Reuse Phase-2 `BaseLayout` + components** (header, footer, hreflang/canonical injection, stat callouts) — no new layout system.

### Claude's Discretion
- Exact slug routing for editorial pages (the fixed slugs are in REQUIREMENTS.md EDIT-01/02); how getStaticPaths or individual `.astro` files are organized under `src/pages/`.
- Exact AdSlot dimensions/positions; the consent banner library vs hand-rolled.
- Which data callouts each editorial page surfaces (e.g. "Is Santiago safe" → Santiago commune rate vs national, trend).
- The static contact-form mechanism (mailto link vs a free form endpoint placeholder).
- Exact FAQ questions per question-style page.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/REQUIREMENTS.md` — EDIT-01 (10 EN slugs), EDIT-02 (10 ES slugs), EDIT-03, EDIT-04, EDIT-05, MON-01 — the exact priority page slugs are LOCKED here.
- `.planning/phases/02-astro-site-programmatic-pages/02-CONTEXT.md` + `02-UI-SPEC.md` — Phase-2 layout, palette, components, hreflang/canonical/sitemap pattern, sober-language rule (templates already comply; this phase adds the enforcing gate).
- `.planning/phases/03-leaflet-map-island/03-CONTEXT.md` — the MapIsland to embed in map-bearing editorial pages (`client:only="react"`).
- `.planning/phases/01-data-foundation/01-CONTEXT.md` — rate calc, trend formula, low_population, featured categories — the methodology page documents these.
- `CLAUDE.md` — stack + editorial-language constraints + AdSense as the monetization plan; sober-language list.
- `site/scripts/validate/` — Phase-2/3 validator pattern to extend with the forbidden-language validator.
- `site/src/layouts/BaseLayout.astro` + `site/src/components/` — reuse targets.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `site/src/layouts/BaseLayout.astro` — header/footer/hreflang/canonical/PWA meta (reuse for all editorial + legal pages).
- `site/src/components/` — StatCard, TrendChip, LevelChip, Sparkline, MapPlaceholderSlot, ranking table (data callouts for editorial pages).
- `site/src/components/map/MapIsland.tsx` — embed in map-bearing editorial pages.
- `site/src/lib/data.ts` + `colorScale.ts` — data access for sourced editorial callouts.
- `site/scripts/validate/all.mjs` — register the new forbidden-language validator here.
- `site/src/config/i18n.ts` — bilingual strings/route map to extend.

### Established Patterns
- Parallel ES/EN templates; `prefixDefaultLocale: false` (EN root, ES /es/); manual hreflang via BaseLayout.
- Validators are node `node:test`/assert scripts over `dist/` HTML, chained after `npm run build` (OneDrive: chain build+validate in one command).
- `public/data` served via the Phase-3 `sync-data.mjs` prebuild (relevant if editorial pages fetch data client-side).

### Integration Points
- Editorial pages feed Phase-6 GSC submission + the AdSense activation gate.
- The forbidden-language validator joins the `all.mjs` suite (currently 8/8).
- AdSense env flag (`ADSENSE_ENABLED`) flipped in Phase-6 deploy.

</code_context>

<specifics>
## Specific Ideas

- These 20 pages are the SEO money pages ("Is Santiago safe", "comunas más seguras de Chile", "Chile crime map") — they must read authoritatively and stay editorially sober (legal/reputational reason from PROJECT.md).
- AdSense approval requires substantive content + a methodology page + legal pages indexed FIRST — hence activation is deferred (MON-01) and gated.
- The forbidden-language gate is a structural safety net; templates are already written to comply by design.

</specifics>

<deferred>
## Deferred Ideas

- Flipping `ADSENSE_ENABLED=true` in production after the first GSC indexing wave — Phase 6.
- GSC submission of the editorial pages — Phase 6.
- Newsletter / downloadable reports / lead capture — v2 (REQUIREMENTS.md deferred).
- A real backend contact form — out of scope (static MVP).

</deferred>

---

*Phase: 4 - Editorial Pages + AdSense*
*Context gathered: 2026-06-13 (autonomous smart-discuss)*
