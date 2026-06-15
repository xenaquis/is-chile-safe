---
spike: 002
name: comuna-finder
type: standard
validates: "Given 346 comunas, when a user searches or browses, then any comuna is reachable in ≤2 interactions and none feels 'lost'"
verdict: VALIDATED
related: [001, 003]
tags: [ia, directory, search, findability, seo]
---

# Spike 002: Comuna finder / directory (the 346)

## What This Validates
Given all 346 comunas, when the user searches by name or browses by region / A–Z, then any comuna is reachable in ≤2 interactions — the concrete fix for the "material perdido" problem (today 334 comunas exist in data + on the map but have no page and no link → dead clicks / 404s).

## How to Run
Open `finder.html`. Type in the filter; toggle **A–Z** vs **Por región**. Deep-links: `finder.html#region-13` opens the region view scrolled to Metropolitana (this is how 001-b's region grid links in).

## What to Expect
- All **346** comunas listed, each with incidence level dot + rate/100k, linking to its ficha (Spike 003).
- Live filter; **accent-insensitive** ("vina" → Viña del Mar, "nunoa" → Ñuñoa).
- Two organizations: alphabetical (with A–Z jump index) and grouped by the 16 regions (with counts).
- "baja pob." tag on low-population comunas (the ones the site excludes from rankings but still deserve a page).

## Investigation Trail
- Verified in-browser (BrowserOS): 346 items rendered, 22 A–Z sections, region view groups correctly (Tarapacá 7 / Antofagasta 9 / Atacama 9 …), and accent-folded search returns "Viña del Mar" for the query "vina". Reachability confirmed: search = 1 interaction to filter + 1 click = 2.
- Region derived canonically from the CUT code (`cut//1000` → region 1–16), sidestepping the CEAD provincial `region_id` quirk — reliable for grouping.
- Surfacing question that emerged: should low-population comunas appear in the directory? Decided **yes** (they get a page; they're just excluded from *rankings* per DATA-04) — otherwise they stay "lost," which is the whole problem.

## Results
**Verdict: VALIDATED.** A search-first directory with A–Z + region views makes all 346 reachable in ≤2 interactions and is the missing connective tissue. This component should exist regardless of which 001 home framing wins — it is the backbone of the "publicar las 346" decision. SEO bonus: the directory + region indexes are crawlable internal-link hubs that distribute link equity to all 692 comuna pages (ES+EN).
