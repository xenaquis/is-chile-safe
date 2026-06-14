# E2E Review Findings — Phase 7

**Date:** 2026-06-13
**Reviewer:** Claude Code (BrowserOS MCP)
**Dev server:** http://localhost:4322 (port 4321 was occupied; fresh `astro dev` instance used)
**Viewport (desktop):** 1280×800 (effective innerWidth ~1296, devicePixelRatio 1.25)
**Viewport (mobile wave):** 375×812 (Wave 4)
**BrowserOS tool mapping (verified at runtime):** navigate → `navigate_page`; screenshot→disk → `save_screenshot` (written to `C:\temp\ui-reviews\`, then moved into `.planning/ui-reviews/` — the OneDrive path's spaces time the tool out); console → `get_console_logs`; interact → `take_snapshot`+`click`/`fill`; JS → `evaluate_script`.

**Severity legend:** Critical = broken core function / data-integrity / blocks user. Warning = visible defect, degraded UX or SEO. Polish = minor / cosmetic / content gap.

**Screenshot evidence:** `.planning/ui-reviews/` (gitignored binaries). Each finding/URL references its file by relative path.

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
