# Spike Manifest

## Idea
Determine the best way to **offer / present** the Chile Safety Map's content to users — resolving the "desordenado con material perdido" problem. The site has rich material (346 comunas of CEAD data, rankings, an interactive map, a built-but-dark news layer) but it feels scattered: only 12/346 comunas have reachable pages, rankings list comunas without linking them, the map's clicks dead-end for 334 comunas, and the news layer isn't surfaced. These spikes prototype the **information architecture** — home/hub framing, a comuna directory, and a cross-linked comuna page — with real CEAD 2025 data and the site's design tokens, so the right structure can be *felt* before the real build (v1.2).

## Requirements
Design decisions emerging from this spike session (non-negotiable for the real build unless revisited):

- **Publish all 346 comunas** (decision taken this session) — every comuna gets a reachable page; the directory + region indexes are the internal-link hubs that distribute SEO equity.
- **A comuna directory/finder must exist** (Spike 002) — search-first, accent-insensitive, with A–Z and by-region views; includes low-population comunas (they get a page, just not a ranking slot).
- **Comuna pages are hubs, not dead-ends** (Spike 003) — each cross-links to map / regional ranking / similar comunas / crime-type rankings / its geolocated news.
- **News↔comuna linking** — incidents link both to the source article AND back to the comuna ficha; depends on geolocation accuracy (see news/model decision — fix name→CUT before shipping real incidents).
- **Home framing = Hybrid C+B** (Spike 001, approved 2026-06-15): editorial/SEO-led above the fold, a prominent "busca tu comuna" search hero, and the national map as a first-class CTA — no single sole entry point.

## Spikes

| # | Name | Type | Validates | Verdict | Tags |
|---|------|------|-----------|---------|------|
| 001 | home-hub-framing | comparison | Cold visitor reaches their comuna in ≤2 clicks; site feels organized | ✓ VALIDATED → **Hybrid C+B** | ia, navigation, home, seo |
| 002 | comuna-finder | standard | Any of 346 comunas reachable in ≤2 interactions; none "lost" | ✓ VALIDATED | ia, directory, search, findability |
| 003 | comuna-page-spokes | standard | Ficha cross-links coherently to map/ranking/similar/news | ✓ VALIDATED | ia, cross-linking, hub-and-spoke, news |

## How to view
Open `.planning/spikes/001-home-hub-framing/index.html` in a browser (file://). It tabs across A/B/C and links onward to the finder (002) and ficha (003). All mockups share `_shared/spike-data.js` (real CEAD 2025) + `_shared/spike.css` (site tokens).
