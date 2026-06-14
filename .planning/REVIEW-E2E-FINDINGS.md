# E2E Review Findings — Phase 7

**Date:** 2026-06-13
**Reviewer:** Claude Code (BrowserOS MCP)
**Dev server:** http://localhost:4322 (port 4321 was occupied; fresh `astro dev` instance used)
**Viewport (desktop):** 1280×800 (effective innerWidth ~1296, devicePixelRatio 1.25)
**Viewport (mobile wave):** 375×812 (Wave 4)
**BrowserOS tool mapping (verified at runtime):** navigate → `navigate_page`; screenshot→disk → `save_screenshot` (written to `C:\temp\ui-reviews\`, then moved into `.planning/ui-reviews/` — the OneDrive path's spaces time the tool out); console → `get_console_logs`; interact → `take_snapshot`+`click`/`fill`; JS → `evaluate_script`.

**Severity legend:** Critical = broken core function / data-integrity / blocks user. Warning = visible defect, degraded UX or SEO. Polish = minor / cosmetic / content gap.

**Screenshot evidence:** `.planning/ui-reviews/` (gitignored binaries). Each finding/URL references its file by relative path.

**Coverage:** REVIEW-01 (30 fixed URLs) · REVIEW-02 (14 programmatic-sample URLs) · REVIEW-03 (7 map interaction groups) · REVIEW-04 (9 mobile pages). Evidence: 61 desktop + 9 mobile + 1 preflight screenshots in `ui-reviews/`.

---

## Severity Summary

| Severity | Count | Finding IDs |
|----------|:-----:|-------------|
| 🔴 Critical | **0** | — |
| 🟠 Warning | **4** | F-001, F-005, F-007, F-009 |
| 🟡 Polish | **5** | F-002, F-003, F-004, F-006, F-008 |
| **Total** | **9** | |

**Informational (PASS, not a defect):** the incident-layer `/data/incidents/current.json` **404 is the expected dev empty state** (no live pipeline) — it produces no app `console.error` and no uncaught exception, so it is **not** a finding (per research Pitfall 4).

**Triage headline for Phase 8:** no Critical defects — the core map, CEAD data, rate methodology, and all reviewed pages render correctly in both locales. The two highest-value fixes are **F-005** (region/crime ranking pages link to thousands of non-rollout commune pages that 404 — biggest SEO/UX impact) and **F-009** (mobile header has no path to the Map). The remaining Warnings (F-001, F-007) are localized i18n leaks; Polish items are content/UX refinements.

---

## Consolidated Findings (by severity)

### 🟠 Warning

#### F-001 — H1 uses English "Commune" on a Spanish page
- **Page:** `/es/delitos-por-comuna/`
- **Locale:** ES
- **Screenshot:** `ui-reviews/r01-es-delitos-por-comuna.png`
- **Observation:** The visible `<h1>` reads "Delitos en Chile por **Commune**…" — English "Commune" on a Spanish money page. Title and slug are correctly "Comuna"; only the H1 is wrong.
- **Recommendation:** Change the H1 to "Comuna". Primary on-page SEO heading; an English word in the ES H1 hurts ranking and credibility.

#### F-005 — Region & crime ranking pages link to non-rollout communes that 404 (systematic)
- **Page:** All `/region/*` + `/es/region/*` and all `/crime/*` + `/es/delito/*`
- **Locale:** Both
- **Screenshot:** `ui-reviews/r02-en-region-metropolitana.png`, `ui-reviews/r02-en-crime-homicide.png`
- **Observation:** Region and crime ranking tables link to every commune in scope, but only the 12 rollout communes have built pages — all others return **404** (confirmed: `/commune/cerrillos/`, `/commune/recoleta/`, `/es/comuna/cerrillos/` → 404). RM region 48/52 links dead; Biobío 32/33; each crime page lists all 346 communes → ~334/346 dead. Repeats across 16 regions + 7 crime families × 2 locales → thousands of broken internal links.
- **Recommendation:** Until rollout expands, render non-rollout communes as plain text (no `<a>`) in region/crime rankings, OR build lightweight pages for all communes, OR gate the linked set to rollout slugs. Highest SEO/UX impact of the phase.

#### F-007 — Map panel close button labeled "Cerrar" (Spanish) on the EN map
- **Page:** `/map/` — ResultPanel close control
- **Locale:** EN
- **Screenshot:** `ui-reviews/r03-04-panel.png`
- **Observation:** Panel close button shows "×" but its accessible name is "Cerrar" (Spanish) on the English map — an i18n leak to assistive tech. All other panel strings are correctly English.
- **Recommendation:** Localize the close button `aria-label`/text (EN → "Close", ES → "Cerrar").

#### F-009 — Mobile header has no nav to Home/Map/Methodology (no hamburger)
- **Page:** Global header at mobile width (all pages)
- **Locale:** Both
- **Screenshot:** `ui-reviews/r04-mobile-home.png`, `ui-reviews/r04-mobile-map.png`
- **Observation:** At ≤ mobile width the header nav links Home/Map/Methodology are `display:none` with **no hamburger/menu toggle** (verified: `offsetParent === null`). Only the logo and EN/ES toggle remain; footer nav has no Map link. On a phone the core **Map** is unreachable from site chrome.
- **Recommendation:** Add a mobile menu (hamburger) exposing Home/Map/Methodology, or a persistent mobile "Map" entry point. High impact — the map is the core product.

### 🟡 Polish

#### F-002 — Missing legal pages (cookie / accessibility)
- **Page:** Legal section (site-wide)
- **Locale:** Both
- **Screenshot:** `ui-reviews/r01-en-terms.png`, `ui-reviews/r01-en-privacy.png`
- **Observation:** Only 4 legal URLs exist (terms + privacy, each locale). REQUIREMENTS.md anticipated 8 — no cookie/consent policy and no accessibility statement.
- **Recommendation:** Before AdSense go-live add a cookie/consent policy (AdSense sets cookies → consent likely required) and consider an accessibility statement. Not blocking for v1.1.

#### F-003 — ES methodology is ~half the EN content
- **Page:** `/es/metodologia/` vs `/methodology/`
- **Locale:** ES
- **Screenshot:** `ui-reviews/r01-es-metodologia.png`, `ui-reviews/r01-en-methodology.png`
- **Observation:** ES methodology ~4.2KB body vs EN ~8.8KB — roughly half. Methodology is an E-E-A-T/trust page; a thinner ES version weakens the Spanish funnel.
- **Recommendation:** Bring ES methodology to content parity with EN.

#### F-004 — Thin contact pages
- **Page:** `/contact/` (826 chars), `/es/contacto/` (975 chars)
- **Locale:** Both
- **Screenshot:** `ui-reviews/r01-en-contact.png`, `ui-reviews/r01-es-contacto.png`
- **Observation:** Contact pages are very thin (<1KB text). Acceptable but minimal.
- **Recommendation:** Optional — add a contact method + response expectation so the page has standalone value.

#### F-006 — ES region name grammar ("Región de Metropolitana")
- **Page:** `/es/region/metropolitana/` (and other ES region pages)
- **Locale:** ES
- **Screenshot:** `ui-reviews/r02-es-region-metropolitana.png`
- **Observation:** ES region H1/title use a generic "Región de {name}" template → "Región de Metropolitana" (should be "Región Metropolitana"; "del Biobío" is conventional for Biobío).
- **Recommendation:** Use the official per-region display name instead of a blanket "Región de {name}".

#### F-008 — Incident empty-state shows no "coming soon" toast
- **Page:** `/map/` — incident layer toggle
- **Locale:** Both
- **Screenshot:** `ui-reviews/r03-08-incidents-empty.png`
- **Observation:** Toggling the incident layer on (404 empty state) shows no user-facing toast across multiple capture windows — only the panel "Recent incidents —". Graceful (no error) but no explicit feedback. The 404 itself is expected and is NOT a defect.
- **Recommendation:** Confirm the empty-state Toast fires (may be mis-wired or auto-dismissing too fast); a brief "Incident data coming soon" toast would make the empty state self-explanatory.

---

## Evidence Appendix (per-review detail)

The sections below are the full per-wave evidence (inventory tables, template checklists, rate-sanity, interaction logs, mobile overflow measurements) that the consolidated findings above are drawn from.

---

## REVIEW-01 — Editorial + Map + Legal Inventory

**Scope walked (30 URLs):** 12 EN editorial + 12 ES editorial + 2 map (`/map/`, `/es/mapa/`) + 4 legal (`/terms/`, `/privacy-policy/`, `/es/terminos/`, `/es/politica-privacidad/`).

**Method:** Each URL navigated at desktop viewport; for each — `evaluate_script` health probe (title, H1, body length, horizontal-overflow, broken-image count, hreflang + canonical presence), `save_screenshot`, `get_console_logs`.

### Inventory evidence table

| URL | Locale | Screenshot | Render | Console | Notes |
|-----|--------|-----------|--------|---------|-------|
| `/` | EN | r01-en-home.png | ✓ | clean | hreflang×3, canonical |
| `/is-chile-safe/` | EN | r01-en-is-chile-safe.png | ✓ | clean | |
| `/is-santiago-safe/` | EN | r01-en-is-santiago-safe.png | ✓ | clean | |
| `/safest-cities-in-chile/` | EN | r01-en-safest-cities.png | ✓ | clean | neutral wording ("Lowest Reported Crime") |
| `/chile-crime-map/` | EN | r01-en-chile-crime-map.png | ✓ | clean | |
| `/santiago-safety-map/` | EN | r01-en-santiago-safety-map.png | ✓ | clean | 18 imgs, 0 broken |
| `/valparaiso-safety/` | EN | r01-en-valparaiso-safety.png | ✓ | clean | |
| `/vina-del-mar-safety/` | EN | r01-en-vina-del-mar-safety.png | ✓ | clean | |
| `/concepcion-safety/` | EN | r01-en-concepcion-safety.png | ✓ | clean | |
| `/about/` | EN | r01-en-about.png | ✓ | clean | |
| `/contact/` | EN | r01-en-contact.png | ✓ | clean | thin content (826 chars) → F-004 |
| `/methodology/` | EN | r01-en-methodology.png | ✓ | clean | 8849 chars |
| `/es/` | ES | r01-es-home.png | ✓ | clean | |
| `/es/mapa-delito-chile/` | ES | r01-es-mapa-delito-chile.png | ✓ | clean | 18 imgs, 0 broken |
| `/es/mapa-seguridad-santiago/` | ES | r01-es-mapa-seguridad-santiago.png | ✓ | clean | |
| `/es/comunas-mas-seguras-chile/` | ES | r01-es-comunas-mas-seguras.png | ✓ | clean | neutral wording |
| `/es/delitos-por-comuna/` | ES | r01-es-delitos-por-comuna.png | ✓ | clean | **H1 says "Commune" (EN) → F-001** |
| `/es/delitos-por-region/` | ES | r01-es-delitos-por-region.png | ✓ | clean | |
| `/es/seguridad-concepcion/` | ES | r01-es-seguridad-concepcion.png | ✓ | clean | |
| `/es/seguridad-valparaiso/` | ES | r01-es-seguridad-valparaiso.png | ✓ | clean | |
| `/es/seguridad-vina-del-mar/` | ES | r01-es-seguridad-vina-del-mar.png | ✓ | clean | |
| `/es/acerca-de/` | ES | r01-es-acerca-de.png | ✓ | clean | |
| `/es/contacto/` | ES | r01-es-contacto.png | ✓ | clean | thin content (975 chars) → F-004 |
| `/es/metodologia/` | ES | r01-es-metodologia.png | ✓ | clean | 4174 chars (vs EN 8849) → F-003 |
| `/map/` | EN | r01-en-map.png | ✓ | clean (error level) | choropleth via canvas; legend + search + chips + zoom present |
| `/es/mapa/` | ES | r01-es-mapa.png | ✓ | clean (error level) | canvas choropleth; legend localized ("Incidencia reportada") |
| `/terms/` | EN | r01-en-terms.png | ✓ | clean | |
| `/privacy-policy/` | EN | r01-en-privacy.png | ✓ | clean | |
| `/es/terminos/` | ES | r01-es-terminos.png | ✓ | clean | |
| `/es/politica-privacidad/` | ES | r01-es-politica-privacidad.png | ✓ | clean | |

**Global health (all 30 URLs):** no horizontal overflow at desktop; every page has `hreflang`×3 (en/es/x-default) + a canonical link; zero broken images; zero console errors or warnings on any page.

**Map console reads (per plan requirement):** `/map/` and `/es/mapa/` both read at `error` level → 0 entries. The incidents layer is OFF by default, so the expected `/data/incidents/current.json` 404 (empty-state, Pitfall 4 — NOT a defect) does not fire on initial load; its graceful empty-state toast is exercised in Wave 3 (REVIEW-03) when the layer is toggled on.

### Findings

#### F-001 — [Severity: Warning]
- **Page:** `/es/delitos-por-comuna/`
- **Locale:** ES
- **Screenshot:** ui-reviews/r01-es-delitos-por-comuna.png
- **Observation:** The visible `<h1>` reads *"Delitos en Chile por **Commune**: una perspectiva basada en datos"* — "Commune" is untranslated English on a Spanish page. Page `<title>` and slug are correctly Spanish ("Delitos en Chile por Comuna"); only the H1 is wrong.
- **Recommendation:** Change the H1 to "Comuna". This is the primary on-page SEO heading for a money/programmatic-index page; an English word in the Spanish H1 hurts ES ranking signal and looks unprofessional.

#### F-002 — [Severity: Polish]
- **Page:** Legal section (site-wide)
- **Locale:** Both
- **Screenshot:** ui-reviews/r01-en-terms.png, ui-reviews/r01-en-privacy.png
- **Observation:** Only 4 legal URLs exist (terms + privacy-policy, each locale). REQUIREMENTS.md anticipated 8 legal pages — no cookie policy and no accessibility statement are shipped. (Verified count, per 07-RESEARCH Pitfall 5 — logged as a single Polish finding, not a blocker.)
- **Recommendation:** Before/with AdSense go-live, add a cookie/consent policy (AdSense uses cookies — likely required for EU/consent compliance) and consider an accessibility statement. Not blocking for v1.1 QA.

#### F-003 — [Severity: Polish]
- **Page:** `/es/metodologia/` vs `/methodology/`
- **Locale:** ES
- **Screenshot:** ui-reviews/r01-es-metodologia.png, ui-reviews/r01-en-methodology.png
- **Observation:** ES methodology rendered ~4,174 chars of body text vs the EN page's ~8,849 — the Spanish methodology page is roughly half the content. Methodology is a trust/E-E-A-T page; a thinner ES version weakens the Spanish funnel.
- **Recommendation:** Bring the ES methodology to content parity with EN (translate the missing sections).

#### F-004 — [Severity: Polish]
- **Page:** `/contact/` (826 chars), `/es/contacto/` (975 chars)
- **Locale:** Both
- **Screenshot:** ui-reviews/r01-en-contact.png, ui-reviews/r01-es-contacto.png
- **Observation:** Contact pages are very thin (under ~1KB of text). Acceptable for a contact page, but minimal.
- **Recommendation:** Optional — add an email/contact method and a one-line response expectation so the page has standalone value.

**REVIEW-01 status:** COMPLETE — full fixed-page inventory (30 URLs) navigated, screenshotted, and console-checked in both locales. 0 Critical, 1 Warning, 3 Polish.

---

## REVIEW-02 — Programmatic Page Sampling

**Declared sample (14 URLs, both locales):**
- **Communes (3 tiers):** Santiago (high pop, CUT 13101), Concepción (mid, 8101), Punta Arenas (low, 12101) — EN `/commune/{slug}/` + ES `/es/comuna/{slug}/`
- **Regions (2):** Metropolitana, Biobío — EN `/region/{slug}/` + ES `/es/region/{slug}/`
- **Crime types (2):** Life crimes (homicide) `/crime/homicide/` ÷ `/es/delito/homicidios/`, Property `/crime/property/` ÷ `/es/delito/propiedad/`

Covers 3 population tiers, 3 distinct regions, both featured crime families, both locales.

### Commune 10-component template checklist

Components (per `site/src/pages/commune/[slug].astro`): breadcrumb hero + LevelChip; 3-card KeyStatsRow (rate + national rank "#N of 346" + regional rank); Sparkline SVG + TrendChip; 2 ComparisonCallouts (national + regional); FamilyBreakdownBars; ComparableCommune; MapPlaceholderSlot→`/map/`; ProseSummary; MethodologyCaveat (CEAD).

| Component | Santiago EN/ES | Concepción EN/ES | Punta Arenas EN/ES |
|-----------|:---:|:---:|:---:|
| Breadcrumb + hero + LevelChip | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ |
| KeyStatsRow (rate + ranks) | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ |
| Sparkline SVG | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ |
| TrendChip | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ |
| 2 ComparisonCallouts | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ |
| FamilyBreakdownBars (36 shapes) | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ |
| ComparableCommune | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ |
| MapPlaceholderSlot→/map/ | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ |
| ProseSummary | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ |
| MethodologyCaveat (CEAD) | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ |
| **10/10 present** | ✓ | ✓ | ✓ |

All 6 commune pages: no horizontal overflow, hreflang×3, console clean. Full ES localization verified (labels "Tasa por 100.000 hab.", "Ranking nacional/regional", "Incidencia alta/baja", "% sobre/bajo el promedio").

### Rate-vs-raw-count sanity (REVIEW-02 requirement)

National mean (from `/`) = 5,808 per 100k. Headline StatCard values:

| Commune | Rate shown | National rank | vs national | Sanity |
|---------|-----------|---------------|-------------|--------|
| Santiago | 9,309 /100k | #11 of 346 | +60% | ✓ rate, not a raw count (raw would be ~50k+ for 544k pop) |
| Concepción | 7,256 /100k | #40 of 346 | +25% | ✓ |
| Punta Arenas | 3,512 /100k | #250 of 346 | −40% | ✓ |

Values are monotonic with tier and consistent with the stated vs-national percentages — the headline figure is a per-100k rate, not a raw sum. **Rate sanity PASS** (Pitfall 1 / methodology MEAN-not-SUM holds on the sampled pages).

### Region & crime page render check

| Page | Locale | Renders | Table | CEAD+year | rate/100k | hreflang | Console |
|------|--------|---------|-------|-----------|-----------|----------|---------|
| `/region/metropolitana/` | EN | ✓ | ✓ | ✓ | ✓ | ×3 | clean |
| `/region/biobio/` | EN | ✓ | ✓ | ✓ | ✓ | ×3 | clean |
| `/es/region/metropolitana/` | ES | ✓ | ✓ | ✓ | ✓ | ×3 | clean |
| `/es/region/biobio/` | ES | ✓ | ✓ | ✓ | ✓ | ×3 | clean |
| `/crime/homicide/` (Life Crimes) | EN | ✓ | ✓ | ✓ | ✓ | ×3 | clean |
| `/crime/property/` | EN | ✓ | ✓ | ✓ | ✓ | ×3 | clean |
| `/es/delito/homicidios/` | ES | ✓ | ✓ | ✓ | ✓ | ×3 | clean |
| `/es/delito/propiedad/` | ES | ✓ | ✓ | ✓ | ✓ | ×3 | clean |

### Findings

#### F-005 — [Severity: Warning] (systematic / high-volume)
- **Page:** All region pages (`/region/*`, `/es/region/*`) and all crime-type pages (`/crime/*`, `/es/delito/*`), both locales
- **Locale:** Both
- **Screenshot:** ui-reviews/r02-en-region-metropolitana.png, ui-reviews/r02-en-crime-homicide.png
- **Observation:** Region and crime ranking pages link to **every commune in scope**, but only the 12 rollout communes have built pages — all non-rollout commune links return **404** (confirmed via fetch: `/commune/cerrillos/`, `/commune/recoleta/`, `/es/comuna/cerrillos/` → 404). Counts: RM region 48/52 links dead; Biobío region 32/33 dead; each crime page lists all 346 communes → ~334/346 dead. This repeats across 16 regions + 7 crime families × 2 locales — thousands of broken internal links.
- **Recommendation:** Until the rollout expands, render non-rollout communes as plain text (no `<a>`) in region/crime rankings, OR build lightweight pages for all communes, OR gate the linked set to rollout slugs. This is the most impactful finding of the phase for SEO crawl health and on-site UX (users clicking a ranked commune hit a dead end). Borderline Critical for SEO; flagged Warning because the core map + data + rollout commune pages are intact.

#### F-006 — [Severity: Polish]
- **Page:** `/es/region/metropolitana/` (and likely other ES region pages)
- **Locale:** ES
- **Screenshot:** ui-reviews/r02-es-region-metropolitana.png
- **Observation:** ES region H1/title use a generic "Región de {name}" template → "Región **de** Metropolitana", which is awkward Spanish (official name is "Región Metropolitana"; "Región del Biobío" is the conventional form for Biobío). Reads as a templated string not tuned per region name.
- **Recommendation:** Use the official region display name per region (special-case Metropolitana → "Región Metropolitana"; consider "del" for masculine region names) rather than a blanket "Región de {name}".

**REVIEW-02 status:** COMPLETE — 14 declared-sample URLs reviewed; 3 commune pages pass the full 10-component template + rate-vs-raw sanity in both locales; region/crime templates render correctly. 0 Critical, 1 Warning (F-005, high-volume), 1 Polish.

---

## REVIEW-03 — Map Dynamic Interactions

**Target:** `/map/` (EN), desktop 1280×800, map island hydrated (canvas choropleth, year select, 8 crime chips + incidents toggle, search, locate). Interactions driven via BrowserOS `select_option` / `take_snapshot`+`click` / `fill`; choropleth recolour confirmed by screenshot (canvas backing store is not pixel-sampleable). Console cleared before the locate and incident steps to isolate their output.

### Per-interaction evidence

| # | Interaction | Method | Result | Console | Screenshot |
|---|-------------|--------|--------|---------|-----------|
| 1 | Year filter → 2010 | `select_option` on "Filter by year" | select value = 2010, choropleth recoloured | clean | r03-01-year-2010.png |
| 2a | Crime chip → Property crimes | click chip | aria-pressed=true, choropleth recoloured (visually confirmed) | clean | r03-02-property.png |
| 2b | Reset → All types | click chip | All types aria-pressed=true, Property=false | clean | r03-03-alltypes.png |
| 3 | Commune panel (Santiago via search) | search→select | ResultPanel opened | clean | r03-04-panel.png |
| 4 | Panel contents | DOM read | rate ~20,258/100k (2010), Trend → Stable, **#11 of 346**, sparkline (2 SVGs, 2005–2026), 7-family bars (Life 1956/Property 5999/Violent 2023/Disorder 9484/Domestic 552/Drug 164/Weapons 80), "View full profile"→/commune/santiago/ | clean | r03-05-panel-detail.png |
| 5 | Search "Temuco" | fill→select | map zoomed to Temuco, panel opened (~9,345/100k, ↑ Increasing, **#52 of 346**), profile→/commune/temuco/ | clean | r03-06-search.png |
| 6 | Geolocation locate | click "Show my location" | no crash; no marker/toast within 2.5s (permission pending/unavailable in automation context — acceptable per plan) | no error | r03-07-locate.png |
| 7 | Incident layer toggle ON | click "Recent incidents" | toggle aria-pressed=true; `/data/incidents/current.json` → 404 (expected empty state); panel "Recent incidents —" | **see note** | r03-08-incidents-empty.png |

### Incident-layer console result (REVIEW-03 explicit requirement)

Toggling the incident layer ON fetches `/data/incidents/current.json`, which returns **404 — this is the expected dev empty state (Pitfall 4), not a defect.** The console entries for it are `source:"browser"` resource-load 404s (the browser auto-logs any failed fetch). There were **0 app-emitted `console.error` calls and 0 uncaught exceptions** — the layer degrades gracefully. **Pitfall-4 criterion (no console.error / no uncaught error): PASS.**

### Findings

#### F-007 — [Severity: Warning]
- **Page:** `/map/` (EN) — ResultPanel close control
- **Locale:** EN
- **Screenshot:** ui-reviews/r03-04-panel.png
- **Observation:** The panel's close button shows "×" visually but its accessible name (button label) is **"Cerrar"** (Spanish) on the English map. This is an i18n leak — a hardcoded Spanish string surfaced to screen-reader/assistive-tech users on EN. (All other panel strings are correctly English: "Metropolitan Region", "Rate per 100,000 inhab.", "National rank", "Annual evolution", "Incidence by category".)
- **Recommendation:** Localize the close button's `aria-label`/text via the locale strings (EN → "Close", ES → "Cerrar").

#### F-008 — [Severity: Polish]
- **Page:** `/map/` — incident layer toggle
- **Locale:** Both (component shared)
- **Screenshot:** ui-reviews/r03-08-incidents-empty.png
- **Observation:** Research/UI-spec anticipated a graceful "coming soon"/empty-state **Toast** when the incident layer is toggled on with no data. Across multiple toggles and capture windows (500ms–2.5s), no toast was observed — the only empty-state signal is the panel's "Recent incidents —" em-dash. Behavior is graceful (no error/crash) but gives no explicit user feedback that incidents are unavailable/coming-soon.
- **Recommendation:** Confirm the Toast actually fires on the 404 empty state (it may be mis-wired or auto-dismissing too fast); a brief "Incident data coming soon" toast would make the empty state self-explanatory. Non-blocking.

**REVIEW-03 status:** COMPLETE — all 7 interaction groups exercised live; year/chip filters recolour, panel shows rate/trend/ranking/sparkline/7-family bars, search zooms+opens panel, locate is graceful, incident empty state is graceful with no app console.error. 0 Critical, 1 Warning (F-007 i18n), 1 Polish (F-008).

---

## REVIEW-04 — Mobile Viewport (375px)

**Tooling note (method transparency):** BrowserOS MCP exposes no device-emulation / `set-viewport` tool (the research-assumed tool does not exist; `window.resizeTo` did not change the render viewport). Mobile was emulated faithfully by rendering each page inside a **same-origin 375×812 `<iframe>`** — an iframe establishes its own CSS viewport, so `@media` breakpoints fire at 375px and overflow was measured via `iframe.contentDocument` (`innerWidth` confirmed = 375 on every page). This is accurate for responsive layout, overflow, and breakpoint behavior; it does not emulate a mobile user-agent string, device-pixel-ratio, or touch input. Screenshots show the 375px page in the left column on a gray host background.

### Per-page overflow check (`scrollWidth > innerWidth` at innerWidth=375)

| Page | Locale | innerW | scrollW | Horizontal overflow | Screenshot |
|------|--------|:------:|:-------:|:-------------------:|-----------|
| `/` | EN | 375 | 360 | **false** ✓ | r04-mobile-home.png |
| `/is-chile-safe/` | EN | 375 | 360 | **false** ✓ | r04-mobile-is-chile-safe.png |
| `/is-santiago-safe/` | EN | 375 | 360 | **false** ✓ | r04-mobile-is-santiago-safe.png |
| `/chile-crime-map/` | EN | 375 | 368 | **false** ✓ | r04-mobile-chile-crime-map.png |
| `/safest-cities-in-chile/` | EN | 375 | 360 | **false** ✓ | r04-mobile-safest-cities.png |
| `/map/` | EN | 375 | 360 | **false** ✓ | r04-mobile-map.png |
| `/es/` | ES | 375 | 360 | **false** ✓ | r04-mobile-es-home.png |
| `/es/mapa-delito-chile/` | ES | 375 | 368 | **false** ✓ | r04-mobile-es-mapa-delito-chile.png |
| `/es/mapa/` | ES | 375 | 360 | **false** ✓ | r04-mobile-es-mapa.png |

**No horizontal overflow on any money page or map at 375px.**

### Map usability at 375px (`/map/` and `/es/mapa/`)

| Check | `/map/` (EN) | `/es/mapa/` (ES) |
|-------|:---:|:---:|
| Choropleth canvas visible | ✓ | ✓ |
| Search reachable (in-viewport) | ✓ | ✓ (present) |
| Locate control reachable | ✓ | — |
| Filter chips reachable (horizontal-scroll row) | ✓ | ✓ |
| Chip touch-target height | 44px ✓ | 44px ✓ |
| Commune panel opens without breaking layout | ✓ (panel opened via search; scrollW stayed 360, no overflow) | — |

Map is usable at mobile width in both locales: full-width search, year selector + scrollable crime-chip row, choropleth fills the column, legend visible, and opening the Santiago panel did not introduce horizontal overflow.

### Findings

#### F-009 — [Severity: Warning]
- **Page:** Global header (all pages) at mobile width
- **Locale:** Both
- **Screenshot:** ui-reviews/r04-mobile-home.png, ui-reviews/r04-mobile-map.png
- **Observation:** At ≤ mobile width the primary header nav links **Home / Map / Methodology are `display:none`** and there is **no hamburger / menu-toggle button** to reveal them (verified in DOM: the three links report `offsetParent === null`; the only interactive header controls remaining are the logo link and the EN/ES toggle). The footer nav (Privacy/Terms/About/Contact) stays visible, but it does **not** include a link to the Map. Net effect: on a phone, a user cannot reach the core **Map** (or Methodology) from the site chrome — only via in-page content links or the logo→home.
- **Recommendation:** Add a mobile menu (hamburger) that exposes Home / Map / Methodology, or surface a persistent mobile "Map" entry point. The map is the product's core value, so a missing mobile nav path to it is high-impact. Borderline Critical for mobile UX; logged Warning because the pages themselves render correctly and an in-content path to the map exists from the homepage.

**Touch-target note (Polish, no separate finding):** map filter chips measure 44px (adequate). The search `<input>`'s inner text box measures ~17px tall, but its padded container is larger and tappable; recommend confirming the search control's hit area is ≥44px on a real device.

**REVIEW-04 status:** COMPLETE — 9 money/map pages checked at a true 375px viewport (via iframe emulation); zero horizontal overflow anywhere; map usable in both locales with 44px chips and a clean panel-open. 0 Critical, 1 Warning (F-009 mobile nav), 0 Polish. Closes the mobile UAT deferred from v1.0 Phase 3.
