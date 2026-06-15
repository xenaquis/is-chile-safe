---
spike: 003
name: comuna-page-spokes
type: standard
validates: "Given a single comuna ficha, when the user wants context, then it cross-links coherently to map / regional ranking / similar comunas / crime-type rankings / news"
verdict: VALIDATED
related: [001, 002]
tags: [ia, cross-linking, hub-and-spoke, comuna-page, news, internal-links]
---

# Spike 003: Comuna page — hub & spokes

## What This Validates
Given a single comuna's page, when the user lands there (from search, map, or Google), then the page is a **hub** that spokes out coherently to: the national map (centered on it), its regional ranking, similar/neighboring comunas, the per-crime-type rankings, and recent news geolocated to it. This is the interconnection the audit found missing — today incident pins link only to the article, comuna pages don't appear for 334 comunas, and rankings list comunas without linking them.

## How to Run
Open `comuna-page.html` (defaults to Santiago) or deep-link `comuna-page.html#nunoa`, `#valparaiso`, `#vitacura`. Use the "ver otra" picker to switch among all 346.

## What to Expect
- Header stats from real CEAD 2025: rate/100k, national rank (of 256 ranked, non-low-pop), incidence level, population.
- A generated lede sentence (mirrors the site's `proseEngine` style).
- **Incidence-by-crime-family** bar breakdown (7 families, real `by_family` values).
- Four **spokes** (map / regional ranking / similar comunas / crime-type rankings) + a **recent-incidents** news section where each item links to source ↗ AND back to the comuna — the missing news↔comuna link.
- Breadcrumb: Inicio › Comunas › Región › Comuna (the navigational spine connecting 001 ↔ 002 ↔ 003).

## Investigation Trail
- Verified in-browser (BrowserOS) on `#nunoa`: title "Ñuñoa", rate 4.984, rank 88/256, level 2, 7 family bars, regional spoke computed live ("#26 de 52 en su región"), breadcrumb "Región Metropolitana", 3 news items. All from real data.
- The regional-rank spoke ("#26 of 52 in its region") emerged as a strong engagement + internal-link device — it gives every comuna page a reason to link to its region page and vice-versa.
- News integration insight (ties to the DeepSeek/MiniMax finding): the ficha is where geolocated incidents *pay off* — but only if geolocation lands the right comuna. A wrong CUT here puts an incident on the wrong ficha. Reinforces that the news phase must fix geolocation (name→CUT) before this section ships with real data.

## Results
**Verdict: VALIDATED.** The hub-and-spoke ficha turns isolated pages into a connected graph (comuna ↔ region ↔ map ↔ crime-type ↔ news), which is what makes the site stop feeling "scattered." Combined with Spike 002 it resolves the orphan-page problem end to end. Cross-links are also the SEO internal-linking structure the ranking audit flagged as missing.
