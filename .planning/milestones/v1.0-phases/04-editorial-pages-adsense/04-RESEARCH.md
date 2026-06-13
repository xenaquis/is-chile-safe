# Phase 4: Editorial Pages + AdSense — Research

**Researched:** 2026-06-13
**Domain:** Astro static editorial pages, forbidden-language validator, AdSense/CMP integration, FAQPage schema
**Confidence:** HIGH (all critical findings derived from the actual codebase; no external library research needed for locked decisions)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Templated skeleton + curated editorial prose per page, injecting real data callouts from `data/cead/`. Not pure-manual, not pure-templated.
- **D-02:** ~800–1500 words/page with single H1, H2 sections. Question-style pages include FAQ block with `FAQPage` schema.
- **D-03:** Map-bearing editorial pages embed Phase-3 MapIsland (`client:only="react"`). Other editorial pages are static.
- **D-04:** Bilingual via parallel hand-maintained ES/EN templates, sober language throughout.
- **D-05:** Forbidden-language gate = post-build validator over `dist/` HTML (extends `site/scripts/validate/`), non-zero exit naming page + term.
- **D-06:** Full term list with variants (both EN and ES), extensible.
- **D-07:** Scope = all pages' visible text (strip tags/scripts; ignore attributes/URLs).
- **D-08:** Case- and accent-insensitive, word-boundary aware.
- **D-09:** Ad slots gated behind `ADSENSE_ENABLED` env flag (default off). With flag off, slots render nothing/placeholder.
- **D-10:** `<AdSlot>` reserves fixed dimensions for CLS prevention. Never on map view or legal pages.
- **D-11:** Cookie-consent banner + Privacy page. Consent gates ad personalization script load.
- **D-12:** AdSense loader = async/`client:idle`, single publisher ID from env, NOT inlined per-page.
- **D-13:** Legal pages = Privacy Policy, Terms, About, Contact in EN + ES, linked from footer.
- **D-14:** Contact = static mailto form. No server (MVP).
- **D-15:** Methodology = one rich page documenting CEAD sources, rate-per-100k, subregistro caveat, trend formula, comparison criteria. Indexed before AdSense application.
- **D-16:** Reuse Phase-2 `BaseLayout` + components. No new layout system.

### Claude's Discretion
- Exact slug routing for editorial pages (slugs are in REQUIREMENTS.md EDIT-01/02).
- Exact AdSlot dimensions/positions (spec is in UI-SPEC.md).
- Consent banner library vs hand-rolled.
- Which data callouts each editorial page surfaces.
- Static contact-form mechanism (mailto link vs free form endpoint placeholder).
- Exact FAQ questions per question-style page.

### Deferred Ideas (OUT OF SCOPE)
- Flipping `ADSENSE_ENABLED=true` in production — Phase 6.
- GSC submission of editorial pages — Phase 6.
- Newsletter / downloadable reports / lead capture — v2.
- A real backend contact form — out of scope (static MVP).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EDIT-01 | 10 EN editorial pages: `/`, `/chile-crime-map/`, `/is-chile-safe/`, `/santiago-safety-map/`, `/is-santiago-safe/`, `/valparaiso-safety/`, `/vina-del-mar-safety/`, `/concepcion-safety/`, `/safest-cities-in-chile/`, `/methodology/` | Individual `.astro` files under `site/src/pages/`; reuse BaseLayout; data from `lib/data.ts` |
| EDIT-02 | 10 ES editorial pages: `/es/`, `/es/mapa-delito-chile/`, `/es/delitos-por-comuna/`, `/es/delitos-por-region/`, `/es/comunas-mas-seguras-chile/`, `/es/mapa-seguridad-santiago/`, `/es/seguridad-valparaiso/`, `/es/seguridad-vina-del-mar/`, `/es/seguridad-concepcion/`, `/es/metodologia/` | Files under `site/src/pages/es/`; parallel to EDIT-01 |
| EDIT-03 | Methodology page documenting sources, limits, rate calculation, underreporting, comparison criteria | `/methodology/` + `/es/metodologia/`; one rich page per locale |
| EDIT-04 | Legal pages: Privacy Policy, Terms, About, Contact (EN + ES) | 4 × 2 = 8 additional `.astro` files; new `LegalLayout.astro` |
| EDIT-05 | Build-time forbidden-language gate failing build on prohibited terms | New `site/scripts/validate/forbidden-language.mjs`; registered in `all.mjs` |
| MON-01 | AdSense integration (deferred activation): slots built but gated behind `ADSENSE_ENABLED` flag | `AdSlot.astro` + `CookieConsent.astro`; AdSense loader in BaseLayout |
</phase_requirements>

---

## Summary

Phase 4 is an Astro content-authoring phase — no new libraries, no new framework decisions. The Phase-2 foundation (BaseLayout, components, validators, lib/data.ts) is mature and well-structured, so this phase layers editorial `.astro` files and a handful of new Astro components on top of proven patterns.

The three genuinely complex engineering problems are: (1) the forbidden-language validator, which must go beyond the partial inline check already in `commune.mjs` to produce a comprehensive dist/-scanning validator with accent normalization and word-boundary awareness; (2) the AdSense/CMP integration, which must be fully flag-gated and CLS-safe without any backend; and (3) the FAQPage JSON-LD composition, which must flow through the existing `BaseLayout` `jsonLd` prop pattern already established in Phase 3.

Everything else is prose authoring + Astro template work reusing existing patterns. The planner should allocate separate waves for (Wave 0) new shared components, (Wave 1) layout extensions + validator, (Wave 2) EN editorial pages, (Wave 3) ES editorial pages + legal pages, and (Wave 4) integration/validator wiring.

**Primary recommendation:** Follow the existing codebase patterns exactly. The validator extension pattern from `commune.mjs`/`hreflang.mjs`, the `jsonLd` prop injection from `BaseLayout.astro`, and the `lib/data.ts` build-time loaders are all proven and documented. No new npm packages needed.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Editorial prose content | Frontend Server (SSR/prerender) | — | Astro pre-renders `.astro` files to static HTML; all content is build-time |
| Data callouts (rate/rank/trend) | Frontend Server (SSR/prerender) | — | `lib/data.ts` is a build-time Node.js loader; called at prerender time, zero client JS |
| FAQPage JSON-LD | Frontend Server (SSR/prerender) | — | BaseLayout `jsonLd` prop injected at build; no client runtime |
| Map embedding in editorial pages | Browser / Client | Frontend Server (shell HTML) | MapIsland is `client:only="react"` — Astro pre-renders the shell, React/Leaflet hydrate in browser |
| Forbidden-language gate | Build pipeline | — | Post-build Node.js script scanning `dist/`; never touches the browser |
| AdSlot placeholder/dimensions | Frontend Server (SSR/prerender) | — | `<div>` with fixed CSS dimensions is static HTML; no JS when ADSENSE_ENABLED=false |
| AdSense loader script | Browser / Client | — | `<script async>` tag in `<head>` only when ADSENSE_ENABLED=true; loads from Google CDN |
| Cookie consent banner | Browser / Client | Frontend Server (shell HTML) | Banner HTML is static; the LocalStorage read + hide logic is a minimal inline `<script>` |
| Legal pages | Frontend Server (SSR/prerender) | — | Pure static HTML, no interactivity |
| Contact form | Browser / Client | — | `mailto:` form submission handled entirely by the browser's mail client |

---

## Standard Stack

### Core (all inherited from Phase 2 — no new packages)

| Library | Version | Purpose | Source |
|---------|---------|---------|--------|
| astro | 6.4.6 | Static page generation | [VERIFIED: site/package.json] |
| @astrojs/react | ^5.0.7 | React island for MapIsland embed | [VERIFIED: site/package.json] |
| react / react-dom | ^19.2.7 | MapIsland dependency | [VERIFIED: site/package.json] |
| @astrojs/sitemap | 3.7.3 | Auto-generate sitemap (i18n-aware) | [VERIFIED: site/package.json] |

### Supporting (existing — no new installs)

| Library | Version | Purpose |
|---------|---------|---------|
| node:fs, node:path | built-in | Validator file I/O (same as all other validators) |
| `lib/data.ts` | project | Build-time data access for editorial callouts |

**No new npm packages are required for Phase 4.** The accent normalization needed for the forbidden-language validator is implemented using the built-in `String.prototype.normalize('NFD')` + regex strip — no external library needed. [VERIFIED: Node.js built-in]

**Installation:** None required. All dependencies are already installed.

---

## Package Legitimacy Audit

> No new packages are introduced in Phase 4. This section is intentionally empty.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### Recommended Project Structure

```
site/
  src/
    layouts/
      EditorialLayout.astro   # extends BaseLayout; 720px prose column; AdSlot injection
      LegalLayout.astro       # extends BaseLayout; no AdSlot; legal-page styling
    components/
      DataCallout.astro       # sourced data box (value + label + source attr)
      FAQBlock.astro          # static Q+A list; outputs FAQPage JSON-LD
      AdSlot.astro            # reserved CLS-safe dims; ADSENSE_ENABLED gate
      CookieConsent.astro     # sticky-bottom consent banner; localStorage gate
      ContactForm.astro       # static mailto form
    pages/
      index.astro             # extend existing (EN home)
      is-chile-safe.astro
      chile-crime-map.astro
      is-santiago-safe.astro
      santiago-safety-map.astro
      valparaiso-safety.astro
      vina-del-mar-safety.astro
      concepcion-safety.astro
      safest-cities-in-chile.astro
      methodology.astro
      privacy-policy.astro
      terms.astro
      about.astro
      contact.astro
      es/
        index.astro
        mapa-delito-chile.astro
        delitos-por-comuna.astro
        delitos-por-region.astro
        comunas-mas-seguras-chile.astro
        mapa-seguridad-santiago.astro
        seguridad-valparaiso.astro
        seguridad-vina-del-mar.astro
        seguridad-concepcion.astro
        metodologia.astro
        politica-privacidad.astro
        terminos.astro
        acerca-de.astro
        contacto.astro
  scripts/validate/
    forbidden-language.mjs    # new validator; registered in all.mjs
```

NOTE on `index.astro`: The EN home page (`/`) almost certainly already exists from Phase 2 as the root `pages/index.astro`. The task is to extend it with editorial content, not create it from scratch. Verify before touching.

### Pattern 1: Build-time data injection into editorial pages

Editorial pages call `lib/data.ts` functions at the top of the Astro component script block. This is identical to how commune/region pages work.

```typescript
// Source: site/src/lib/data.ts (verified)
import { loadNationalAverage, loadCommune, latestCompleteYearRate } from '../lib/data.ts';

// At build time (Astro script block):
const nationalAvg = loadNationalAverage();
const santiago = loadCommune('13101');   // CUT for Santiago
const santiagoRate = latestCompleteYearRate(santiago);
const santiagoYear = santiago.latestCompleteYear;
```

Key pitfall: `loadNational().series[].rate_per_100k` is a SUM not a per-capita average — always use `loadNationalAverage()` for the displayed national rate. This is documented in `lib/data.ts` header. [VERIFIED: site/src/lib/data.ts line 183]

### Pattern 2: BaseLayout jsonLd prop for FAQPage schema

BaseLayout already accepts a `jsonLd?: object | null` prop and injects it safely via `JSON.stringify` + `set:html`. FAQBlock should construct the JSON-LD object and pass it up to the page, which passes it to BaseLayout.

```typescript
// Source: site/src/layouts/BaseLayout.astro (verified)
// BaseLayout renders:
// {jsonLd !== null && (
//   <script is:inline type="application/ld+json" set:html={JSON.stringify(jsonLd)} />
// )}

// In an editorial page:
const faqItems = [
  { q: "Is Chile safe for tourists?", a: "..." },
  { q: "Which cities in Chile are safest?", a: "..." },
];
const jsonLd = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": faqItems.map(item => ({
    "@type": "Question",
    "name": item.q,
    "acceptedAnswer": { "@type": "Answer", "text": item.a }
  }))
};
// Pass to BaseLayout: <BaseLayout jsonLd={jsonLd} ...>
```

Note: `JSON.stringify` via `set:html` is the XSS-safe injection method per the BaseLayout comment. Never use raw string interpolation for JSON-LD. [VERIFIED: site/src/layouts/BaseLayout.astro line 61]

### Pattern 3: The validator pattern (for forbidden-language.mjs)

All validators follow the same structural pattern established in `hreflang.mjs` and `schema.mjs`:

```javascript
// Source: site/scripts/validate/hreflang.mjs (verified pattern)
import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

// Guard: dist/ must exist
if (!existsSync(DIST_DIR)) {
  console.error('FAIL: dist/ directory not found — run npm run build first');
  process.exit(1);
}

// Recursive file collector (same helper used in hreflang.mjs):
function findIndexFiles(dir, results = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) findIndexFiles(full, results);
    else if (entry.name === 'index.html') results.push(full);
  }
  return results;
}

let failures = 0;
// ... scan, check, report, then:
if (failures > 0) process.exit(1);
```

The `all.mjs` registration is a one-line addition to the `VALIDATORS` array. [VERIFIED: site/scripts/validate/all.mjs]

### Pattern 4: Accent-insensitive visible text extraction for the forbidden-language validator

The existing `commune.mjs` `stripTags()` function is a simple regex that strips tags but does NOT handle: `<script>` block content, HTML attributes, or accent normalization. The new forbidden-language validator needs a stricter extractor.

```javascript
// [ASSUMED] pattern — adapt for forbidden-language.mjs
function extractVisibleText(html) {
  // 1. Remove <script>...</script> blocks (inline JS)
  let text = html.replace(/<script[\s\S]*?<\/script>/gi, ' ');
  // 2. Remove <style>...</style> blocks
  text = text.replace(/<style[\s\S]*?<\/style>/gi, ' ');
  // 3. Remove all remaining tags (leaves only text nodes + attr values)
  //    Attributes are stripped because tag removal strips the whole <...> including attrs.
  text = text.replace(/<[^>]*>/g, ' ');
  // 4. Decode common HTML entities
  text = text.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&nbsp;/g, ' ');
  // 5. Normalize whitespace
  return text.replace(/\s+/g, ' ').trim();
}

// Accent-insensitive normalization (Node.js built-in):
function normalizeAccents(str) {
  return str.normalize('NFD').replace(/[̀-ͯ]/g, '');
}
```

### Pattern 5: Word-boundary matching for forbidden terms

The D-08 requirement is word-boundary aware to avoid false positives (e.g. "peligroso" inside "no es peligroso" should match, but "peligrosidad" should not). JavaScript `\b` word-boundary does NOT work with accented characters. The correct approach for multilingual text:

```javascript
// [ASSUMED] word-boundary pattern for Spanish accent-stripped text
// After normalizing text and term to NFD-stripped lowercase:
// Use lookahead/lookbehind for non-word chars instead of \b
function buildTermPattern(term) {
  // Normalize term (accent-strip, lowercase)
  const normalized = normalizeAccents(term).toLowerCase();
  // Escape regex special chars
  const escaped = normalized.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  // Boundary: term must be preceded and followed by non-word char or start/end
  return new RegExp(`(?<![a-z0-9])${escaped}(?![a-z0-9])`, 'gi');
}
```

The qualifying-phrase exception for "la más segura" (allowed only when followed by "en este período según datos CEAD") requires a separate allow-list regex that checks the match context before reporting a failure.

### Pattern 6: AdSlot component with ADSENSE_ENABLED gate

```astro
---
// Source: site/src/components/AdSlot.astro (to be created)
// Reads env at build time — Astro exposes import.meta.env
interface Props {
  slot: 'content' | 'bottom';
  publisherId?: string;
}
const { slot, publisherId = import.meta.env.PUBLIC_ADSENSE_PUBLISHER_ID ?? '' } = Astro.props;
const enabled = import.meta.env.ADSENSE_ENABLED === 'true';
const isContent = slot === 'content';
// Dimensions from UI-SPEC: content=90px desktop/50px mobile, bottom same
---

<div class={`ad-slot ad-slot--${slot}`} aria-hidden={!enabled ? 'true' : undefined}>
  {enabled && publisherId ? (
    <ins class="adsbygoogle"
      data-ad-client={publisherId}
      data-ad-slot={isContent ? 'CONTENT_SLOT_ID' : 'BOTTOM_SLOT_ID'}
      data-ad-format="auto"
      data-full-width-responsive="true">
    </ins>
  ) : (
    <div class="ad-placeholder" aria-hidden="true"></div>
  )}
</div>
```

The `PUBLIC_` prefix makes the env var available in client-side code (Astro convention). `ADSENSE_ENABLED` without `PUBLIC_` is a build-time-only flag. [ASSUMED — Astro env var convention from training data; verify against Astro 6.x docs if needed]

### Pattern 7: CookieConsent banner — hand-rolled, no library

The decision (D-11 / Claude's Discretion) is between hand-rolled and a library. The recommendation is **hand-rolled** based on:
- The entire consent logic is 15 lines of JS (localStorage read/write + class toggle)
- No library passes the legitimacy gate without slopcheck verification
- The UI-SPEC fully specifies every visual detail already
- No third-party cookie banner library is needed for GDPR "soft" compliance on a static site

The CookieConsent component uses a minimal inline `<script>` (not `client:*`) to hide the banner synchronously before first paint, avoiding a flash:

```astro
---
// site/src/components/CookieConsent.astro
// Only injected when ADSENSE_ENABLED=true (checked in EditorialLayout)
const { locale } = Astro.props;
---

<!-- Inline script: hide banner synchronously if consent already given -->
<script is:inline>
  if (localStorage.getItem('csm_consent')) {
    document.currentScript.parentElement.style.display = 'none';
  }
</script>

<div id="csm-consent-banner" class="consent-banner" role="dialog" aria-label="Cookie consent">
  <!-- copy + buttons per UI-SPEC -->
</div>

<script>
  // Accept / Reject handlers
  document.getElementById('csm-consent-accept')?.addEventListener('click', () => {
    localStorage.setItem('csm_consent', 'accepted');
    document.getElementById('csm-consent-banner').style.display = 'none';
  });
  // ... reject handler analogous
</script>
```

### Pattern 8: PageFooter extension

PageFooter.astro currently has 3 items (wordmark, attribution, lang toggle). The D-13 requirement adds 4 legal-page links. The component must be extended — **not replaced** — by adding a `<nav>` row of links below the existing flex row. The existing layout and styles should not be disrupted.

### Anti-Patterns to Avoid

- **Using `loadNational().series[].rate_per_100k` as the display rate:** It's a SUM across all communes, not per-capita. Always use `loadNationalAverage()` for the mean rate. [VERIFIED: lib/data.ts header comment]
- **Injecting JSON-LD via string interpolation:** BaseLayout uses `JSON.stringify(jsonLd)` + `set:html` specifically to prevent XSS. Never write `<script>{"@context": ...}</script>` with raw template literals. [VERIFIED: BaseLayout.astro line 61]
- **Putting AdSense `<ins>` outside the fixed-dimension wrapper:** The CLS fix requires the wrapper `<div>` to always render with reserved height, even when the slot is empty. The `<ins>` is inside, not replacing, the wrapper.
- **Using `client:load` on the CookieConsent or AdSlot components:** These are Astro components (`.astro`), not React components — they render server-side. The interactive bits use vanilla `<script>` tags.
- **Using `\b` word-boundary in the forbidden-language regex:** `\b` does not work with non-ASCII characters. Use explicit `(?<![a-z0-9])...(? ![a-z0-9])` negative lookbehind/lookahead after accent normalization.
- **Running the forbidden-language validator before `astro build`:** It scans `dist/`; it must run post-build only. The `all.mjs` runner already guards against missing `dist/`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Accent normalization | Custom Unicode table | `String.prototype.normalize('NFD')` + regex strip `[̀-ͯ]` | Node.js built-in, no deps |
| HTML entity decoding | Custom entity map | Minimal set of 4 entities inline (`&amp;`, `&lt;`, `&gt;`, `&nbsp;`) is sufficient for dist/ HTML; the rest are numeric refs | Astro output HTML uses named entities only for these 4 in text |
| sitemap generation | Custom sitemap | `@astrojs/sitemap` already installed and configured | Already handles i18n routes |
| Schema.org JSON | Custom serializer | Plain JS object passed to `BaseLayout jsonLd` prop | BaseLayout already handles `JSON.stringify` safely |

---

## Common Pitfalls

### Pitfall 1: `la más segura` false-positive and false-negative in the forbidden-language gate

**What goes wrong:** The term "la más segura" is forbidden _bare_ but allowed when followed by the qualifying phrase "en este período según datos CEAD". A naive substring match will either flag all comparatives (too strict) or require an exact match (fragile to whitespace variations).

**How to avoid:** Two-pass approach: first find the bare term, then check a context window (next 80 chars) against a normalized allow-list pattern. If the allow-list pattern matches, skip the failure.

**Warning signs:** Any editorial page about "safest cities" will legitimately use qualifying comparatives. The validator must not break the build for valid prose.

### Pitfall 2: Accent normalization applies to BOTH text and terms

**What goes wrong:** The HTML text is normalized (NFD → strip diacritics), but the term list is not. "peligrosa" matches, but "peligrósa" (hypothetical malformed term) would not.

**How to avoid:** Normalize both the extracted text AND each term in `FORBIDDEN_TERMS` before matching.

### Pitfall 3: `<script>` content appears in visible text extraction

**What goes wrong:** The simple `stripTags()` in `commune.mjs` replaces `<tag>` patterns but does not remove the content between `<script>...</script>` tags. If Astro inlines any JS that contains forbidden-term substrings (e.g. a comment or variable name), the validator will produce false positives.

**How to avoid:** In `forbidden-language.mjs`, remove `<script>` block content BEFORE stripping tags. Same for `<style>` blocks. The order is: remove script blocks → remove style blocks → strip remaining tags → decode entities.

### Pitfall 4: `import.meta.env.ADSENSE_ENABLED` evaluated at build time, not runtime

**What goes wrong:** Since Astro pre-renders to static HTML, `import.meta.env.ADSENSE_ENABLED` is evaluated once at build time. If the env var is not set in the CI/CD environment, `import.meta.env.ADSENSE_ENABLED` is `undefined`, which is falsy — the slot renders the placeholder. This is the desired default behavior.

**How to avoid:** Default the check to `false` explicitly: `const enabled = import.meta.env.ADSENSE_ENABLED === 'true'`. Do not use `!!import.meta.env.ADSENSE_ENABLED` — undefined and empty string are both falsy, which is correct, but the explicit string comparison is more readable and catches the case where a CI runner sets it to the string "false".

### Pitfall 5: BaseLayout `mountType` prop (unused but present)

**What goes wrong:** BaseLayout.astro declares a `mountType?: string` prop in its Props interface but does not use it in the template. Phase-4 editorial pages should not pass this prop; it is legacy from Phase 3 development. No action needed, but don't confuse it for a required prop.

### Pitfall 6: OneDrive desync — chain build + validate in one npm command

**What goes wrong:** Running `npm run build` and then separately `npm run validate` on this OneDrive-hosted repo risks `dist/` vanishing between commands due to OneDrive sync. [VERIFIED: project MEMORY.md]

**How to avoid:** Always invoke as a single chained command: `npm run build && node scripts/validate/all.mjs`. The `validate` script alias already does this when invoked after build in one shell session, but the plan must document this as the required invocation pattern.

### Pitfall 7: `index.astro` at EN root — verify if it already exists

**What goes wrong:** Phase 2 likely created `site/src/pages/index.astro` as the EN home page. Creating a new file would overwrite it.

**How to avoid:** Before creating `index.astro`, verify the file exists and read its content. The Phase-4 task extends it with editorial content, not replaces it.

### Pitfall 8: FAQPage JSON-LD answer text must be plain text, no HTML

**What goes wrong:** Google's FAQ rich result spec requires the `acceptedAnswer.text` value to be plain text. If editorial prose contains HTML tags (links, emphasis), the JSON-LD will fail validation.

**How to avoid:** FAQ answer text in the `items` array passed to FAQBlock must be plain-text strings. Any links in the displayed prose should be in the rendered HTML only, not in the JSON-LD `text` field.

---

## Code Examples

### Forbidden-language validator structure (complete skeleton)

```javascript
// site/scripts/validate/forbidden-language.mjs
// Source: pattern from site/scripts/validate/hreflang.mjs (verified)

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

// Term list (D-06) — accent-stripped, lowercase at match time
const FORBIDDEN_TERMS = [
  // EN
  'dangerous zone', 'dangerous area', 'dangerous commune', 'dangerous neighborhood',
  'definitive ranking', 'guaranteed safe', '100% safe', 'guaranteed safety',
  // ES
  'zona peligrosa', 'area peligrosa', 'comuna peligrosa', 'barrio peligroso',
  'ranking definitivo', 'zona segura garantizada', '100% seguro', 'seguridad garantizada',
  // Bare superlative (see allow-list exception below)
  'the safest', 'la mas segura',  // note: will be matched after accent normalization
];

// Allow-list: contexts that follow a forbidden term and make it acceptable
const ALLOW_LIST = [
  // "la más segura en este período según datos CEAD"
  /en este per[io]+do seg[u]+n datos cead/i,
  // English equivalent: "the safest ... according to CEAD data for {year}"
  /according to cead data for \d{4}/i,
];

function normalizeAccents(str) {
  return str.normalize('NFD').replace(/[̀-ͯ]/g, '');
}

function extractVisibleText(html) {
  let text = html.replace(/<script[\s\S]*?<\/script>/gi, ' ');
  text = text.replace(/<style[\s\S]*?<\/style>/gi, ' ');
  text = text.replace(/<[^>]*>/g, ' ');
  text = text.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&nbsp;/g, ' ');
  return text.replace(/\s+/g, ' ').trim();
}

function checkPage(htmlPath) {
  const html = readFileSync(htmlPath, 'utf-8');
  const label = htmlPath.replace(DIST_DIR, '').replace(/\\/g, '/');
  const visible = extractVisibleText(html);
  const normalized = normalizeAccents(visible).toLowerCase();
  const failures = [];

  for (const term of FORBIDDEN_TERMS) {
    const normTerm = normalizeAccents(term).toLowerCase();
    const pattern = new RegExp(`(?<![a-z0-9])${normTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![a-z0-9])`, 'g');
    let match;
    while ((match = pattern.exec(normalized)) !== null) {
      const context = normalized.slice(match.index + normTerm.length, match.index + normTerm.length + 100);
      const isAllowed = ALLOW_LIST.some(re => re.test(context));
      if (!isAllowed) {
        failures.push({ term, index: match.index, excerpt: normalized.slice(Math.max(0, match.index - 20), match.index + normTerm.length + 40) });
      }
    }
  }
  return { label, failures };
}

function findIndexFiles(dir, acc = []) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) findIndexFiles(full, acc);
    else if (e.name === 'index.html') acc.push(full);
  }
  return acc;
}

if (!existsSync(DIST_DIR)) {
  console.error('FAIL: dist/ directory not found — run npm run build first');
  process.exit(1);
}

const files = findIndexFiles(DIST_DIR);
console.log(`forbidden-language: scanning ${files.length} pages in dist/`);
let totalFailures = 0;

for (const f of files) {
  const { label, failures } = checkPage(f);
  if (failures.length > 0) {
    totalFailures += failures.length;
    for (const { term, excerpt } of failures) {
      process.stderr.write(`[forbidden-language] FAIL: ${label}\n  Term: "${term}"\n  Context: "...${excerpt}..."\n`);
    }
  }
}

if (totalFailures > 0) {
  console.error(`\nforbidden-language: ${totalFailures} forbidden term(s) detected. Fix before deploying.`);
  process.exit(1);
}
console.log('forbidden-language: PASS — no forbidden terms detected.');
```

### Registering in all.mjs

```javascript
// Source: site/scripts/validate/all.mjs (verified)
// Add 'forbidden-language.mjs' to the VALIDATORS array:
const VALIDATORS = [
  'structure.mjs',
  'commune.mjs',
  'rollout.mjs',
  'region.mjs',
  'crime.mjs',
  'hreflang.mjs',
  'schema.mjs',
  'map.mjs',
  'forbidden-language.mjs',  // Phase 4 addition
];
```

### DataCallout component

```astro
---
// site/src/components/DataCallout.astro
interface Props {
  value: string;
  label: string;
  source: string;
  locale: 'en' | 'es';
}
const { value, label, source } = Astro.props;
---
<div class="data-callout">
  <div class="callout-value">{value}</div>
  <div class="callout-label">{label}</div>
  <div class="callout-source">{source}</div>
</div>
<style>
  .data-callout {
    border-left: 4px solid var(--primary);
    background: var(--card);
    border-radius: var(--radius);
    padding: var(--md);
    margin: var(--lg) 0;
  }
  .callout-value { font-size: var(--text-display); font-weight: var(--weight-strong); color: var(--primary); }
  .callout-label { font-size: var(--text-label); font-weight: var(--weight-strong); color: var(--muted); }
  .callout-source { font-size: var(--text-label); font-weight: var(--weight-body); color: var(--muted); }
</style>
```

---

## FAQPage Schema: 2025/2026 Eligibility Notes

Google's FAQ rich results have had eligibility restrictions since August 2023. [ASSUMED — from training data; verify against Google Search Central docs before Phase 6 GSC submission]

Key known rules as of research:
- FAQ rich results are shown only for **authoritative government and health sites** in most contexts. General informational sites may not get the FAQ carousel in SERPs, but the JSON-LD is still valid structured data and eligible for other rich result treatments.
- The `FAQPage` schema is still recommended for question-style pages because: (1) it helps Google understand page structure even without a rich result; (2) eligibility policies may change; (3) it is zero-cost to implement via the existing `jsonLd` prop.
- Answer text must be 2,500 characters or fewer. [ASSUMED]
- No HTML in `acceptedAnswer.text`. [ASSUMED — consistent with schema.org spec]

**Recommendation:** Implement FAQPage JSON-LD as specified in CONTEXT.md D-02 and UI-SPEC. Do not gate it behind any check — the implementation cost is negligible.

---

## AdSense Approval Requirements (context for deferred activation)

AdSense approval for a new site requires: [ASSUMED — from training data; verify against Google AdSense help before Phase 6]

1. **Substantial original content** — the editorial + methodology + legal pages built in Phase 4 fulfill this requirement.
2. **Privacy Policy** — explicitly required. Phase 4 builds this.
3. **About page** — not formally required but strongly recommended. Phase 4 builds this.
4. **No paid traffic** — not applicable (organic SEO only).
5. **Content must be indexed** — AdSense activation is correctly deferred to Phase 6 after first GSC indexing wave.
6. **Site must be on a custom domain** — ischilesafe.com is already the target domain.

The Phase-4 build + Phase-6 activation sequence correctly satisfies the "content first, monetization second" requirement.

---

## Static Contact Form: mailto Recommendation

The decision (D-14 / Claude's Discretion) is `mailto:` form vs a free no-backend endpoint. The recommendation is **`mailto:` form** because:

- Zero external service dependency (no Formspree/Netlify Forms API key to manage)
- 100% static — no CI/CD secret needed
- Appropriate for MVP volume (low traffic, few submissions expected)
- Consistent with the "no server" constraint

Mechanism: `<form action="mailto:xenaquis@gmail.com" method="POST" enctype="text/plain">`. The form opens the user's mail client. Behavior varies by browser/OS but is universally supported. A comment in the HTML documents the v2 upgrade path. [VERIFIED: from UI-SPEC.md — this is already the locked mechanism per D-14]

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Separate `client:load` consent library (e.g. cookieconsent npm) | Inline 15-line vanilla JS in `.astro` component | No bundle overhead; no external dependency; works identically |
| FAQ accordion (JS-powered expand/collapse) | Static open Q+A list (D-02 per UI-SPEC) | Zero JS on editorial pages; Google can read all FAQ content in the raw HTML |
| Per-page AdSense script tag | Single async script in `<head>` gated by env flag (D-12) | Correct Google AdSense pattern; avoids duplicate script loads |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `\b` word boundary does not work with accented Spanish chars in JS regex | Code Examples (Pattern 5) | If wrong: validator may miss terms or produce false positives; mitigated by testing validator with accented terms |
| A2 | Google FAQ rich result eligibility is restricted to government/health sites as of 2026 | FAQPage Schema section | If wrong: implementation is already correct either way; no code impact |
| A3 | AdSense requires about + privacy + substantial content before approval | AdSense Requirements section | If wrong: Phase 6 activation plan may need adjustment; zero code impact in Phase 4 |
| A4 | `import.meta.env.PUBLIC_ADSENSE_PUBLISHER_ID` is the correct Astro convention for client-accessible env vars | Pattern 6 (AdSlot) | If wrong: publisher ID may not render in the `<ins>` tag; easy to fix at implementation |
| A5 | FAQPage `acceptedAnswer.text` must be 2,500 chars or fewer | FAQPage section | If wrong: no enforcement code needed; editorial prose should stay well under this limit anyway |

---

## Open Questions

1. **Does `site/src/pages/index.astro` already exist from Phase 2?**
   - What we know: Phase 2 built 740 pre-rendered pages; the root index almost certainly exists.
   - What's unclear: The exact content and structure of the current `index.astro`.
   - Recommendation: Executor reads `site/src/pages/index.astro` before any edits and extends rather than replaces.

2. **Exact ES slug for the "Is Santiago safe" equivalent**
   - What we know: UI-SPEC shows `/es/seguridad-santiago/` as illustrative; REQUIREMENTS.md EDIT-02 does NOT list this slug — it lists `/es/delitos-por-region/` instead.
   - What's unclear: The ES equivalent of `/is-santiago-safe/` is not clearly mapped in REQUIREMENTS.md.
   - Recommendation: Planner maps EN `/is-santiago-safe/` to the closest REQUIREMENTS.md EDIT-02 entry and notes the gap. If no ES equivalent exists in EDIT-02, the EN page has no hreflang ES pair for that slug (use `x-default` only pointing to EN).

3. **`nav_methodology` in i18n.ts already points to `/methodology/` — verify path matches**
   - What we know: `i18n.ts` has `nav_methodology: 'Methodology'` but the path is not stored there (only labels).
   - Recommendation: PageHeader.astro uses a hardcoded `/methodology/` path or derives it from the locale; verify and extend for the new editorial pages' nav links if needed.

---

## Environment Availability

> Step 2.6: SKIPPED — Phase 4 has no new external tool dependencies. All required tools (Node.js, npm, Astro, Python) were verified operational in Phases 1–3.

---

## Validation Architecture

> `workflow.nyquist_validation` is `true` in `.planning/config.json` — this section is required.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Node.js built-in `node:test` + `node:assert/strict` + custom dist/ scanners |
| Config file | none — validators are standalone `node scripts/validate/all.mjs` |
| Quick run command | `npm run build && node scripts/validate/all.mjs` |
| Full suite command | `npm run build && node scripts/validate/all.mjs` (same; all validators run) |

Note: The project has no Jest/Vitest/pytest for frontend tests. All validation is via the custom validator suite over `dist/`. The Nyquist sampling contract is: run the full suite after each wave merge.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | Coverage |
|--------|----------|-----------|-------------------|---------|
| EDIT-01 | 10 EN editorial pages exist and render HTML | Smoke | `node scripts/validate/forbidden-language.mjs` (all pages scanned) + `node scripts/validate/hreflang.mjs` | Wave 2 |
| EDIT-01 | Each editorial page has title, canonical, hreflang | Integration | `node scripts/validate/hreflang.mjs` | Existing validator; passes for new pages automatically |
| EDIT-02 | 10 ES editorial pages exist and render HTML | Smoke | `node scripts/validate/hreflang.mjs` (reciprocal links checked) | Wave 3 |
| EDIT-03 | Methodology page has required H2 sections | Manual | Human inspection of `dist/methodology/index.html` — automated word-count not feasible without topic-aware parser | Wave 3 |
| EDIT-04 | Legal pages exist: privacy, terms, about, contact | Smoke | New `structure.mjs` assertions for REQUIRED_FILES + `hreflang.mjs` reciprocal check | Wave 3 — structure.mjs additions |
| EDIT-05 | Forbidden-language gate fails on prohibited terms | Unit | `node scripts/validate/forbidden-language.mjs` (in all.mjs suite) | Wave 1 |
| EDIT-05 | Gate passes on valid qualifying phrases | Unit | Same validator with test fixture | Wave 1 |
| MON-01 | AdSlot renders placeholder (ADSENSE_ENABLED=false) | Smoke | `grep -r "ad-slot" dist/` — verify presence of reserved dims; verify NO `<ins class="adsbygoogle">` | Wave 2 |
| MON-01 | AdSense loader NOT injected when disabled | Smoke | `grep -r "pagead2.googlesyndication" dist/` — must return no matches | Wave 2 |
| MON-01 | No AdSlot on legal pages | Smoke | `grep "ad-slot" dist/privacy-policy/index.html` — must return empty | Wave 3 |

### Wave 0 Gaps (new test infrastructure needed)

- [ ] `site/scripts/validate/forbidden-language.mjs` — the primary new validator for EDIT-05 (Wave 1, before any editorial content)
- [ ] `structure.mjs` additions: assert `dist/privacy-policy/index.html`, `dist/terms/index.html`, `dist/about/index.html`, `dist/contact/index.html` exist (Wave 3)
- [ ] `structure.mjs` additions: assert all 10 EN editorial slugs exist in `dist/` (Wave 2 completion check)

### Sampling Rate

- **Per task commit:** Run `node scripts/validate/forbidden-language.mjs` alone (fast — scans visible text only)
- **Per wave merge:** `npm run build && node scripts/validate/all.mjs` (full suite, all 9 validators)
- **Phase gate:** Full suite green + human spot-check of 3 editorial pages (prose quality, data accuracy) before `/gsd:verify-work`

---

## Security Domain

> `security_enforcement: true`, `security_asvs_level: 1` in config.json.

### Applicable ASVS Categories (Level 1)

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No login, no auth |
| V3 Session Management | No | No server sessions; localStorage consent key is non-sensitive |
| V4 Access Control | No | All pages public |
| V5 Input Validation | Yes (contact form) | mailto form — no server-side processing; browser handles validation. `required` attributes on fields. No injection risk (no backend). |
| V6 Cryptography | No | No secrets stored or transmitted by the site itself |
| V7 Error Handling | No | Static site; no server-side error paths |
| V8 Data Protection | Yes (AdSense/cookies) | Privacy Policy (EDIT-04) + CookieConsent banner (D-11) fulfills disclosure requirement. No PII collected server-side. |
| V13 API/Web Service | No | No API endpoints |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| JSON-LD XSS via unsafe string interpolation | Tampering | Already mitigated: `JSON.stringify(jsonLd)` + `set:html` in BaseLayout (verified) |
| AdSense publisher ID exposure | Info Disclosure | Not a secret — it's in every page's HTML by design; `PUBLIC_` env prefix is correct |
| Contact form email harvesting | Info Disclosure | `mailto:` makes the email visible in HTML source. Acceptable for MVP; future mitigation: obfuscation or form service. Document in About/Contact page. |
| Cookie consent bypass | Repudiation | localStorage can be cleared. Not a legal issue for a static site without EU-established operations. Soft-compliance is appropriate. |

---

## Sources

### Primary (HIGH confidence — verified from codebase)

- `site/scripts/validate/all.mjs` — validator runner pattern, VALIDATORS array, registration mechanism
- `site/scripts/validate/hreflang.mjs` — dist/ scanner pattern, `findIndexFiles()` helper, path resolution
- `site/scripts/validate/commune.mjs` — `stripTags()`, forbidden term matching pattern, `spawnSync` for TS execution
- `site/scripts/validate/schema.mjs` — `extractJsonLd()` pattern, failure counting/exit
- `site/scripts/validate/structure.mjs` — REQUIRED_FILES pattern, DIST_DIR guard
- `site/src/layouts/BaseLayout.astro` — `jsonLd` prop, `JSON.stringify` + `set:html`, hreflang injection
- `site/src/lib/data.ts` — all loader functions, pitfall on SUM vs MEAN, `loadNationalAverage()`
- `site/src/components/StatCard.astro` — component API and CSS variables
- `site/src/components/PageFooter.astro` — footer structure to extend
- `site/src/config/i18n.ts` — I18nStrings interface, EN_STRINGS/ES_STRINGS, extension pattern
- `site/package.json` — exact dependency versions, `validate` script alias
- `.planning/phases/04-editorial-pages-adsense/04-CONTEXT.md` — all locked decisions
- `.planning/phases/04-editorial-pages-adsense/04-UI-SPEC.md` — component specs, dimensions, templates
- `.planning/REQUIREMENTS.md` — locked slug lists EDIT-01/02

### Secondary (MEDIUM confidence)

- `.planning/STATE.md` — OneDrive build desync issue (build + validate must chain)

### Tertiary (LOW confidence — training data)

- Google FAQ rich result eligibility restrictions (A2)
- AdSense approval requirements (A3)
- Astro `PUBLIC_` env var convention (A4) — should verify against Astro 6.x docs

---

## Metadata

**Confidence breakdown:**
- Validator pattern: HIGH — read 5 existing validators, derived pattern from source
- Data access pattern: HIGH — read `lib/data.ts` in full, pitfalls documented in source
- AdSlot/consent implementation: MEDIUM — pattern derived from spec + Astro conventions; env var naming ASSUMED
- FAQPage JSON-LD eligibility: LOW — Google policy details are training data only

**Research date:** 2026-06-13
**Valid until:** 2026-07-13 (stable stack; AdSense/FAQ policy could change sooner)
