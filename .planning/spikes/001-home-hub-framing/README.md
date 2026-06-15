---
spike: 001
name: home-hub-framing
type: comparison
validates: "Given a cold visitor, when they want to reach their comuna's data, then the path is ≤2 clicks and the site feels organized, not scattered"
verdict: VALIDATED
decision: "Hybrid C+B — editorial/SEO-led above the fold, prominent 'busca tu comuna' search hero, map as first-class CTA (approved 2026-06-15)"
related: [002, 003]
tags: [ia, navigation, home, product-framing, seo]
---

# Spike 001: Home / Hub framing (A / B / C)

## What This Validates
Given a user landing cold on ischilesafe.com, when they want to reach the data for *their* comuna (or a ranking, or the map), then the path should be ≤2 clicks and the site should feel organized — directly addressing the "desordenado con material perdido" complaint. Three competing framings of the landing + primary navigation, compared head-to-head with **real CEAD 2025 data**.

## How to Run
Open `index.html` — a comparator with tabs **A / B / C** and a desktop / 375px-mobile toggle. Each tab loads a full standalone hub mockup; you can also open each directly:
- `001-a-map-first.html`
- `001-b-finder-first.html`
- `001-c-ranking-led.html`

## The three framings

| Variant | Core idea | Entry point | Best for | Risk |
|---------|-----------|-------------|----------|------|
| **A · Map-first** | The national map *is* the home; everything hangs off it | Big map + search overlay | "Show me spatially / explore visually" | Map-first home is weak SEO (thin text above fold); mobile map-as-hero is heavy |
| **B · Finder-first** | "Find your comuna" search + region directory front and center | Prominent search box + region grid | "I know my comuna, take me there" — kills orphan-page feeling fastest | Less editorial surface for long-tail SEO; map demoted |
| **C · Ranking / editorial-led** | SEO landing: headline + lead rankings + guides; map & finder one click away | Rankings + editorial cards + inline search | Google traffic capture (the project's stated core value) | Risk of feeling "listy"; the user's own comuna is one extra step |

## Research / Grounding
- Project core value (CLAUDE.md): *"páginas estáticas bilingües que Google indexa"* — SEO is the monetization engine (AdSense). That pulls toward **C**.
- The "material perdido" complaint is fundamentally a **findability** problem → pulls toward **B** (directory/search front-and-center).
- The map is the product's signature asset (Phase 3 + the Phase 10 geometry work) → pulls toward **A**.
- Real data wired from `data/cead/meta/index.json` + `map-payload.json` (346 comunas, rate/100k, level 1–5) via `_shared/spike-data.js`.

## Investigation Trail
- Built all three on a shared header/nav + design tokens lifted from `site/src/styles/global.css`, so the comparison is about **structure**, not styling noise.
- Verified in-browser (BrowserOS, file://): 001-a renders 346 comunas, live comuna search, 6-row safest/highest tables, 16 region tiles — data layer confirmed working.
- Observation while building: A and C both *include* a search and rankings; the real differentiator is **what occupies the first screen** and therefore what the site signals it is "for." This reframes the choice as: spatial tool (A) vs. personal lookup (B) vs. SEO content hub (C).
- Likely answer is a **hybrid**: C's SEO-led above-the-fold + B's prominent comuna search as the hero input + A's map as a strong secondary CTA. The variants exist to let the user feel which *emphasis* wins.

## Results
**Verdict: VALIDATED — decision: Hybrid C+B (approved 2026-06-15).** The chosen home framing is editorial/SEO-led above the fold (headline + lead "más seguras / mayor incidencia" rankings + guide cards) with the single most prominent interactive element being a **"busca tu comuna" search hero**, and the **national map as a first-class CTA**. This satisfies the SEO core value (C), kills the findability/"material perdido" feeling (B's search + the 002 directory), and keeps the signature map prominent (A) — without making any one of them the sole entry point. Carries into the v1.2 home/IA phase.
