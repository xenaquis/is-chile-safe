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
