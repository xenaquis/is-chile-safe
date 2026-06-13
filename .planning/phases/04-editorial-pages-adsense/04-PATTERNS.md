# Phase 4: Editorial Pages + AdSense — Pattern Map

**Mapped:** 2026-06-13
**Files analyzed:** 38 new/modified files (20 editorial pages EN+ES, 8 legal pages EN+ES, 2 layouts, 5 components, 1 validator, 1 validator registration, 1 footer modification)
**Analogs found:** 38 / 38 (all have a role-match or exact analog)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `site/src/layouts/EditorialLayout.astro` | layout | request-response | `site/src/layouts/BaseLayout.astro` | exact |
| `site/src/layouts/LegalLayout.astro` | layout | request-response | `site/src/layouts/BaseLayout.astro` | exact |
| `site/src/components/DataCallout.astro` | component | request-response | `site/src/components/StatCard.astro` | exact |
| `site/src/components/FAQBlock.astro` | component | request-response | `site/src/layouts/BaseLayout.astro` (jsonLd prop) | role-match |
| `site/src/components/AdSlot.astro` | component | request-response | `site/src/components/MapPlaceholderSlot.astro` | role-match |
| `site/src/components/CookieConsent.astro` | component | event-driven | `site/src/components/PageFooter.astro` (structure) | partial |
| `site/src/components/ContactForm.astro` | component | request-response | `site/src/components/StatCard.astro` (Astro Props + style) | partial |
| `site/src/pages/index.astro` | page | request-response | `site/src/pages/index.astro` (existing — extend) | exact |
| `site/src/pages/is-chile-safe.astro` | page | request-response | `site/src/pages/index.astro` | exact |
| `site/src/pages/chile-crime-map.astro` | page | request-response | `site/src/pages/map.astro` | exact |
| `site/src/pages/is-santiago-safe.astro` | page | request-response | `site/src/pages/index.astro` | exact |
| `site/src/pages/santiago-safety-map.astro` | page | request-response | `site/src/pages/map.astro` | exact |
| `site/src/pages/valparaiso-safety.astro` | page | request-response | `site/src/pages/index.astro` | exact |
| `site/src/pages/vina-del-mar-safety.astro` | page | request-response | `site/src/pages/index.astro` | exact |
| `site/src/pages/concepcion-safety.astro` | page | request-response | `site/src/pages/index.astro` | exact |
| `site/src/pages/safest-cities-in-chile.astro` | page | request-response | `site/src/pages/commune/[slug].astro` (data loading) | role-match |
| `site/src/pages/methodology.astro` | page | request-response | `site/src/pages/index.astro` | exact |
| `site/src/pages/privacy-policy.astro` | page | request-response | `site/src/pages/index.astro` | exact |
| `site/src/pages/terms.astro` | page | request-response | `site/src/pages/index.astro` | exact |
| `site/src/pages/about.astro` | page | request-response | `site/src/pages/index.astro` | exact |
| `site/src/pages/contact.astro` | page | request-response | `site/src/pages/index.astro` | exact |
| `site/src/pages/es/index.astro` | page | request-response | `site/src/pages/es/index.astro` (existing — extend) | exact |
| `site/src/pages/es/mapa-delito-chile.astro` | page | request-response | `site/src/pages/es/mapa.astro` | exact |
| `site/src/pages/es/delitos-por-comuna.astro` | page | request-response | `site/src/pages/es/index.astro` | exact |
| `site/src/pages/es/comunas-mas-seguras-chile.astro` | page | request-response | `site/src/pages/es/index.astro` | exact |
| `site/src/pages/es/mapa-seguridad-santiago.astro` | page | request-response | `site/src/pages/es/mapa.astro` | exact |
| `site/src/pages/es/seguridad-valparaiso.astro` | page | request-response | `site/src/pages/es/index.astro` | exact |
| `site/src/pages/es/seguridad-vina-del-mar.astro` | page | request-response | `site/src/pages/es/index.astro` | exact |
| `site/src/pages/es/seguridad-concepcion.astro` | page | request-response | `site/src/pages/es/index.astro` | exact |
| `site/src/pages/es/metodologia.astro` | page | request-response | `site/src/pages/es/index.astro` | exact |
| `site/src/pages/es/politica-privacidad.astro` | page | request-response | `site/src/pages/es/index.astro` | exact |
| `site/src/pages/es/terminos.astro` | page | request-response | `site/src/pages/es/index.astro` | exact |
| `site/src/pages/es/acerca-de.astro` | page | request-response | `site/src/pages/es/index.astro` | exact |
| `site/src/pages/es/contacto.astro` | page | request-response | `site/src/pages/es/index.astro` | exact |
| `site/scripts/validate/forbidden-language.mjs` | validator | batch | `site/scripts/validate/hreflang.mjs` | exact |
| `site/scripts/validate/all.mjs` (modify) | config | batch | `site/scripts/validate/all.mjs` | exact |
| `site/src/components/PageFooter.astro` (modify) | component | request-response | `site/src/components/PageFooter.astro` | exact |
| `site/src/config/i18n.ts` (modify) | config | — | `site/src/config/i18n.ts` | exact |

---

## Pattern Assignments

### `site/src/layouts/EditorialLayout.astro` and `LegalLayout.astro` (layout, request-response)

**Analog:** `site/src/layouts/BaseLayout.astro`

EditorialLayout wraps BaseLayout (uses `<BaseLayout>` as its inner slot target). LegalLayout is identical but omits AdSlot injection.

**Full BaseLayout pattern** (`site/src/layouts/BaseLayout.astro` lines 1–73 — read above):

```astro
---
import '../styles/global.css';
import PageHeader from '../components/PageHeader.astro';
import PageFooter from '../components/PageFooter.astro';

interface Props {
  lang: 'en' | 'es';
  title: string;
  description: string;
  enPath: string;
  esPath: string;
  jsonLd?: object | null;
  mountType?: string;
}

const {
  lang,
  title,
  description,
  enPath,
  esPath,
  jsonLd = null,
} = Astro.props;

const BASE_URL = 'https://ischilesafe.com';
const canonicalPath = lang === 'en' ? enPath : esPath;
---
<!doctype html>
<html lang={lang}>
  <head>
    ...
    {jsonLd !== null && (
      <script is:inline type="application/ld+json" set:html={JSON.stringify(jsonLd)} />
    )}
  </head>
  <body>
    <PageHeader locale={lang} enPath={enPath} esPath={esPath} />
    <main class="page-content">
      <slot />
    </main>
    <PageFooter locale={lang} enPath={enPath} esPath={esPath} />
  </body>
</html>
```

**How EditorialLayout differs from BaseLayout:** EditorialLayout is NOT a new `<html>` layout — it wraps `<BaseLayout>` and adds a `<div class="editorial-prose">` wrapper (max-width 720px) plus `<AdSlot>` injection positions. It passes all BaseLayout props through including `jsonLd`. LegalLayout is the same wrapper but never renders AdSlot.

**Props interface for EditorialLayout:**
```astro
interface Props {
  lang: 'en' | 'es';
  title: string;
  description: string;
  enPath: string;
  esPath: string;
  jsonLd?: object | null;
}
```

---

### `site/src/components/DataCallout.astro` (component, request-response)

**Analog:** `site/src/components/StatCard.astro`

DataCallout reuses the same CSS variable system and value/label/sublabel pattern as StatCard, but adds a `4px solid var(--primary)` left border and a source attribution line.

**StatCard full source** (`site/src/components/StatCard.astro` lines 1–54):

```astro
---
interface Props {
  label: string;
  value: string | number;
  sublabel?: string;
}
const { label, value, sublabel } = Astro.props;
---
<div class="stat-card">
  <div class="stat-value">{value}</div>
  <div class="stat-label">{label}</div>
  {sublabel && <div class="stat-sublabel">{sublabel}</div>}
</div>
<style>
  .stat-card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: var(--md);
    display: flex;
    flex-direction: column;
    gap: var(--xs);
  }
  .stat-value {
    font-size: var(--text-display); /* 28px/700 */
    font-weight: var(--weight-strong);
    line-height: 1.15;
    color: var(--ink);
  }
  .stat-label {
    font-size: var(--text-label); /* 14px/700 */
    font-weight: var(--weight-strong);
    color: var(--muted);
  }
  .stat-sublabel {
    font-size: var(--text-label);
    font-weight: var(--weight-body);
    color: var(--muted);
  }
</style>
```

**DataCallout Props (from UI-SPEC):**
```astro
interface Props {
  value: string;
  label: string;
  source: string;
  locale: 'en' | 'es';
}
```

DataCallout adds `.callout-source` (same style as `.stat-sublabel`) and replaces `border: 1px solid var(--line)` with `border-left: 4px solid var(--primary)` + removes the other three borders. `.stat-value` color changes to `var(--primary)` instead of `var(--ink)`.

---

### `site/src/components/FAQBlock.astro` (component, request-response)

**Analog:** `site/src/layouts/BaseLayout.astro` (jsonLd prop pattern, lines 60–63)

FAQBlock constructs a FAQPage JSON-LD object and passes it to the parent page, which passes it to BaseLayout's `jsonLd` prop. The component also renders static open Q+A HTML.

**JSON-LD injection pattern from BaseLayout** (line 61–63):
```astro
{jsonLd !== null && (
  <script is:inline type="application/ld+json" set:html={JSON.stringify(jsonLd)} />
)}
```

**FAQBlock usage pattern:**
```astro
---
// In the editorial page (e.g. is-chile-safe.astro):
const faqItems = [
  { q: "Is Chile safe for tourists?", a: "Plain text answer, no HTML." },
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
// Pass to BaseLayout via layout: <BaseLayout jsonLd={jsonLd} ...>
---
```

**FAQBlock Props:**
```astro
interface Props {
  items: { q: string; a: string }[];
  locale: 'en' | 'es';
}
```

The component renders static HTML: each item as `<div class="faq-item"><h2 class="faq-q">{item.q}</h2><p class="faq-a">{item.a}</p></div>` separated by `1px solid var(--line)`. It does NOT inject JSON-LD itself — it is the parent page's responsibility to construct the `jsonLd` object and pass it to the layout. This keeps JSON-LD injection at a single point (BaseLayout).

---

### `site/src/components/AdSlot.astro` (component, request-response)

**Analog:** `site/src/components/MapPlaceholderSlot.astro` (env-gated placeholder pattern)

No existing AdSlot. The closest structural analog is MapPlaceholderSlot — a reserved-space `<div>` that renders placeholder content when the real feature is unavailable.

**AdSlot Props and gate pattern:**
```astro
---
interface Props {
  slot: 'content' | 'bottom';
  publisherId?: string;
}
const { slot, publisherId = import.meta.env.PUBLIC_ADSENSE_PUBLISHER_ID ?? '' } = Astro.props;
const enabled = import.meta.env.ADSENSE_ENABLED === 'true';
---
<div class={`ad-slot ad-slot--${slot}`} aria-hidden={!enabled ? 'true' : undefined}>
  {enabled && publisherId ? (
    <ins class="adsbygoogle"
      data-ad-client={publisherId}
      data-ad-slot={slot === 'content' ? 'CONTENT_SLOT_ID' : 'BOTTOM_SLOT_ID'}
      data-ad-format="auto"
      data-full-width-responsive="true">
    </ins>
  ) : (
    <div class="ad-placeholder" aria-hidden="true"></div>
  )}
</div>
<style>
  .ad-slot {
    width: 100%;
    max-width: 728px;
    margin: var(--lg) auto;
  }
  .ad-slot--content { height: 90px; }
  .ad-slot--bottom  { height: 90px; }
  @media (max-width: 639px) {
    .ad-slot--content,
    .ad-slot--bottom { height: 50px; }
  }
  .ad-placeholder {
    width: 100%;
    height: 100%;
    background: var(--bg);
    border: 2px dashed var(--line);
    border-radius: var(--radius);
  }
</style>
```

`ADSENSE_ENABLED` (no `PUBLIC_` prefix) is a build-time-only flag. `PUBLIC_ADSENSE_PUBLISHER_ID` is client-accessible (Astro convention for `PUBLIC_` prefix). Default: both undefined → slot renders placeholder only.

---

### `site/src/components/CookieConsent.astro` (component, event-driven)

**Analog:** `site/src/components/PageFooter.astro` (sticky positioned Astro component with scoped styles)

PageFooter shows the Astro component Props + scoped `<style>` + zero `client:*` directives pattern. CookieConsent uses the same pattern but adds a vanilla `<script>` (not `client:*`) for localStorage interaction.

**PageFooter Props + structure** (`site/src/components/PageFooter.astro` lines 1–30):
```astro
---
interface Props {
  locale: 'en' | 'es';
  enPath: string;
  esPath: string;
}
const { locale, enPath, esPath } = Astro.props;
---
<footer class="csm-footer">
  <div class="footer-inner page-content">
    ...
  </div>
</footer>
<style>
  .csm-footer {
    border-top: 1px solid var(--line);
    background: var(--card);
    padding: var(--lg) 0;
    margin-top: var(--2xl);
  }
  ...
</style>
```

**CookieConsent structure (adapted):**
```astro
---
interface Props {
  locale: 'en' | 'es';
}
const { locale } = Astro.props;
---
<!-- Inline script: hide synchronously before first paint if already consented -->
<script is:inline>
  if (typeof localStorage !== 'undefined' && localStorage.getItem('csm_consent')) {
    document.currentScript.parentElement.style.display = 'none';
  }
</script>

<div id="csm-consent-banner" class="consent-banner" role="dialog" aria-label="Cookie consent">
  <!-- copy + buttons per UI-SPEC -->
</div>

<script>
  document.getElementById('csm-consent-accept')?.addEventListener('click', () => {
    localStorage.setItem('csm_consent', 'accepted');
    document.getElementById('csm-consent-banner').style.display = 'none';
  });
  document.getElementById('csm-consent-reject')?.addEventListener('click', () => {
    localStorage.setItem('csm_consent', 'rejected');
    document.getElementById('csm-consent-banner').style.display = 'none';
  });
</script>
<style>
  .consent-banner {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    z-index: 200;
    background: var(--ink);
    padding: var(--md) var(--lg);
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--md);
    color: var(--card);
  }
  ...
</style>
```

CookieConsent is injected by EditorialLayout only when `ADSENSE_ENABLED === 'true'`.

---

### `site/src/components/ContactForm.astro` (component, request-response)

**Analog:** `site/src/components/StatCard.astro` (Astro Props interface + scoped CSS variables)

No form component exists; ContactForm is hand-rolled. Uses the same CSS variable system as all other components.

**Props:**
```astro
interface Props {
  locale: 'en' | 'es';
}
```

**Form mechanism (from UI-SPEC + D-14):**
```astro
<!-- Phase-4 MVP: mailto link. Replace with a form service endpoint in v2. -->
<form action="mailto:xenaquis@gmail.com" method="POST" enctype="text/plain">
  <!-- Name, Email, Message fields per UI-SPEC -->
  <button type="submit">Send message</button>
</form>
```

Field styles: `background: var(--card); border: 1px solid var(--line); border-radius: calc(var(--radius)/2); padding: var(--sm) var(--md)`. Focus: `border: 2px solid var(--primary); outline: none`. Submit button: `background: var(--primary); color: var(--card)`.

---

### Standard editorial pages — EN static (is-chile-safe.astro, valparaiso-safety.astro, methodology.astro, etc.)

**Analog:** `site/src/pages/index.astro`

**Full index.astro pattern** (lines 1–40):
```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
---
<BaseLayout
  lang="en"
  title="Is Chile Safe — Chile Safety Map"
  description="Official CEAD crime statistics..."
  enPath="/"
  esPath="/es/"
>
  <section class="home-hero">
    <h1>Is Chile Safe?</h1>
    ...
  </section>
</BaseLayout>
```

**All non-map editorial EN pages follow this exact pattern**, substituting `BaseLayout` with `EditorialLayout` (which wraps BaseLayout), providing their own `title`, `description`, `enPath`, `esPath` and `jsonLd` (for FAQ pages).

**For pages with data callouts** (is-santiago-safe, safest-cities-in-chile, etc.), add the data loading pattern from `commune/[slug].astro` lines 50–58:
```astro
const nationalAvg = loadNationalAverage();
const santiago = loadCommune('13101');
const year = santiago.latestCompleteYear;
const rate = latestCompleteYearRate(santiago);
```

---

### Map-bearing editorial pages (chile-crime-map.astro, santiago-safety-map.astro)

**Analog:** `site/src/pages/map.astro` (lines 1–38)

**Full map.astro pattern:**
```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
import MapIsland from '../components/map/MapIsland';
---
<BaseLayout
  lang="en"
  title="Chile Crime Map — Interactive"
  description="..."
  enPath="/map/"
  esPath="/es/mapa/"
>
  <span
    style="position:absolute;width:1px;height:1px;..."
    aria-label="Show my location"
    data-map-locate-label="en"
  />
  <MapIsland client:only="react" lang="en" />
</BaseLayout>
```

**Map-bearing editorial pages** use `EditorialLayout` (not raw BaseLayout), embed `<MapIsland client:only="react" lang={lang} />` inside a full-width block that breaks out of the 720px prose column, and add editorial prose before and after the map block.

---

### ES editorial pages (es/index.astro, es/mapa-delito-chile.astro, etc.)

**Analog:** `site/src/pages/es/index.astro` (lines 1–40)

**Full es/index.astro pattern:**
```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
---
<BaseLayout
  lang="es"
  title="¿Es seguro Chile? — Chile Safety Map"
  description="..."
  enPath="/"
  esPath="/es/"
>
  <section class="home-hero">
    <h1>¿Es seguro Chile?</h1>
    ...
  </section>
</BaseLayout>
```

**All ES pages follow this pattern**, using `../../layouts/EditorialLayout.astro` or `../../layouts/LegalLayout.astro` relative import (two levels up from `pages/es/`). ES equivalents of map-bearing pages use `../../components/map/MapIsland` (same relative depth pattern as `es/mapa.astro`).

---

### `site/scripts/validate/forbidden-language.mjs` (validator, batch)

**Analog:** `site/scripts/validate/hreflang.mjs` (exact structural match)

**Full hreflang.mjs scaffold** (lines 19–48 and 87–163):

```javascript
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

// Recursive file collector (lines 32–42):
function findIndexFiles(dir, results = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      findIndexFiles(full, results);
    } else if (entry.name === 'index.html') {
      results.push(full);
    }
  }
  return results;
}

let failures = 0;
// ... scan, check, report ...
if (failures > 0) {
  console.error(`\nhreflang.mjs: FAILED (${failures} issue(s) ...)`);
  process.exit(1);
}
console.log(`hreflang.mjs: PASSED — ${htmlFiles.length} pages checked`);
```

**Additional functions needed in forbidden-language.mjs** (no analog — constructed from D-06/D-07/D-08 spec):

```javascript
// Accent-insensitive normalization (Node.js built-in):
function normalizeAccents(str) {
  return str.normalize('NFD').replace(/[̀-ͯ]/g, '');
}

// Visible text extraction (strips script/style blocks BEFORE tag stripping):
function extractVisibleText(html) {
  let text = html.replace(/<script[\s\S]*?<\/script>/gi, ' ');
  text = text.replace(/<style[\s\S]*?<\/style>/gi, ' ');
  text = text.replace(/<[^>]*>/g, ' ');
  text = text.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&nbsp;/g, ' ');
  return text.replace(/\s+/g, ' ').trim();
}

// Word-boundary pattern (JS \b does not work with accented chars):
function buildTermPattern(normalizedTerm) {
  const escaped = normalizedTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`(?<![a-z0-9])${escaped}(?![a-z0-9])`, 'g');
}

// Allow-list for qualifying phrases (D-06 exception):
const ALLOW_LIST = [
  /en este per[io]+do seg[u]+n datos cead/i,
  /according to cead data for \d{4}/i,
];
```

**commune.mjs FORBIDDEN_TERMS list** to incorporate into forbidden-language.mjs (lines 24–35 — the existing partial list that this validator supersedes for dist/ scanning):
```javascript
const FORBIDDEN_TERMS = [
  'zona peligrosa', 'comuna peligrosa', 'ranking definitivo',
  'zona segura garantizada', 'la más segura', 'the safest',
  'dangerous zone', 'dangerous commune', 'definitive ranking', 'guaranteed safe',
  // D-06 additions:
  'area peligrosa', 'barrio peligroso', '100% seguro', 'seguridad garantizada',
  'dangerous area', 'dangerous neighborhood', '100% safe', 'guaranteed safety',
  'zona segura', 'definitive ranking',
];
```

---

### `site/scripts/validate/all.mjs` (modify — add one entry)

**Analog:** `site/scripts/validate/all.mjs` itself (lines 28–37)

**Current VALIDATORS array** (lines 28–37 — confirmed in source):
```javascript
const VALIDATORS = [
  'structure.mjs',
  'commune.mjs',
  'rollout.mjs',
  'region.mjs',
  'crime.mjs',
  'hreflang.mjs',
  'schema.mjs',
  'map.mjs',
];
```

**Required modification:** append `'forbidden-language.mjs'` as the 9th entry. The `spawnSync` loop (lines 41–63) runs it automatically. No other changes to all.mjs.

---

### `site/src/components/PageFooter.astro` (modify — add legal nav links)

**Analog:** `site/src/components/PageFooter.astro` itself (lines 1–70 — read above)

**Current footer-inner structure** (lines 22–30):
```astro
<footer class="csm-footer">
  <div class="footer-inner page-content">
    <span class="footer-wordmark">Chile Safety Map</span>
    <span class="footer-attribution">{attribution}</span>
    <a href={altHref} class="footer-lang" lang={locale === 'en' ? 'es' : 'en'}>
      {altLocaleLabel}
    </a>
  </div>
</footer>
```

**Required addition:** a second `<nav>` row of links below the existing flex row. Do not alter the existing `.footer-inner` flex row. Links use `font-size: var(--text-label); font-weight: var(--weight-body); color: var(--muted)` (same as `.footer-attribution`). Links:
- EN: Privacy Policy → `/privacy-policy/`, Terms of Use → `/terms/`, About → `/about/`, Contact → `/contact/`
- ES: Política de Privacidad → `/es/politica-privacidad/`, Términos de Uso → `/es/terminos/`, Acerca de → `/es/acerca-de/`, Contacto → `/es/contacto/`

---

### `site/src/config/i18n.ts` (modify — add new strings)

**Analog:** `site/src/config/i18n.ts` itself (lines 7–70 interface, lines 72–137 EN_STRINGS, lines 139–204 ES_STRINGS)

**Extension pattern:** add new keys to the `I18nStrings` interface, then provide values in both `EN_STRINGS` and `ES_STRINGS`. Follow the existing naming convention (`noun_verb` or `context_role`).

**New keys needed (from UI-SPEC page templates):**
```typescript
// Add to I18nStrings interface:
footer_privacy: string;
footer_terms: string;
footer_about: string;
footer_contact: string;
nav_is_chile_safe: string;
nav_crime_map: string;
nav_safest_cities: string;
cookie_banner_text: string;
cookie_banner_accept: string;
cookie_banner_reject: string;
data_callout_source_prefix: string;  // "Source: CEAD" / "Fuente: CEAD"
```

---

## Shared Patterns

### Pattern 1: BaseLayout wrapper (applies to ALL new pages)

**Source:** `site/src/layouts/BaseLayout.astro` lines 1–73
**Apply to:** Every new `.astro` page file

Every page must pass `lang`, `title`, `description`, `enPath`, `esPath` to the layout. `jsonLd` is optional (only FAQ pages + non-FAQ editorial pages that emit WebPage schema). `mountType` prop exists but is not used — do not pass it.

```astro
<BaseLayout
  lang="en"
  title="..."
  description="..."
  enPath="/slug/"
  esPath="/es/slug-es/"
  jsonLd={jsonLd}
>
  ...content...
</BaseLayout>
```

### Pattern 2: JSON-LD injection via set:html (XSS safe)

**Source:** `site/src/layouts/BaseLayout.astro` line 61–63
**Apply to:** All pages that emit structured data (FAQ pages, WebPage schema)

```astro
{jsonLd !== null && (
  <script is:inline type="application/ld+json" set:html={JSON.stringify(jsonLd)} />
)}
```

Never use raw string interpolation for JSON-LD. Always construct a plain JS object and pass it as `jsonLd` prop to the layout.

### Pattern 3: Build-time data loading (applies to pages with data callouts)

**Source:** `site/src/pages/commune/[slug].astro` lines 50–65
**Apply to:** is-santiago-safe.astro, safest-cities-in-chile.astro, valparaiso-safety.astro, vina-del-mar-safety.astro, concepcion-safety.astro and their ES equivalents

```typescript
import { loadCommune, loadNationalAverage, latestCompleteYearRate } from '../../lib/data.ts';

const nationalAvg = loadNationalAverage(); // MEAN of commune rates — use this
const commune = loadCommune('13101');       // CUT code for Santiago
const year = commune.latestCompleteYear;
const rate = latestCompleteYearRate(commune);
const vsNationalPct = ((rate - nationalAvg) / nationalAvg) * 100;
```

**Critical pitfall:** `loadNationalAverage()` returns the mean per-capita rate. `loadNational().series[].rate_per_100k` is a SUM — never use the SUM for display. This is verified in `site/src/lib/data.ts` header comment.

### Pattern 4: Validator scaffold (applies to forbidden-language.mjs)

**Source:** `site/scripts/validate/hreflang.mjs` lines 19–48
**Apply to:** `site/scripts/validate/forbidden-language.mjs`

```javascript
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

if (!existsSync(DIST_DIR)) {
  console.error('FAIL: dist/ directory not found — run npm run build first');
  process.exit(1);
}

function findIndexFiles(dir, results = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) findIndexFiles(full, results);
    else if (entry.name === 'index.html') results.push(full);
  }
  return results;
}

let failures = 0;
// ... scan loop ...
if (failures > 0) process.exit(1);
console.log('forbidden-language: PASS');
```

### Pattern 5: CSS custom properties (applies to ALL new components)

**Source:** `site/src/components/StatCard.astro` lines 26–54 and `site/src/components/PageFooter.astro` lines 32–70
**Apply to:** DataCallout.astro, AdSlot.astro, CookieConsent.astro, ContactForm.astro, EditorialLayout.astro, LegalLayout.astro

Use only these tokens — no hardcoded hex values or px outside the two exceptions noted in UI-SPEC:
- `var(--bg)`, `var(--card)`, `var(--ink)`, `var(--muted)`, `var(--line)`, `var(--primary)`
- `var(--xs)` 4px, `var(--sm)` 8px, `var(--md)` 16px, `var(--lg)` 24px, `var(--xl)` 32px, `var(--2xl)` 48px
- `var(--text-body)`, `var(--text-label)`, `var(--text-heading)`, `var(--text-display)`
- `var(--weight-body)`, `var(--weight-strong)`
- `var(--radius)`, `var(--page-content)` (860px max-width)

Exceptions: AdSlot reserved heights (90px / 50px), editorial prose column (720px) — use literal values for these CLS-critical dimensions.

### Pattern 6: Astro component zero-client-directive rule

**Source:** All existing `.astro` components (StatCard, PageFooter, BaseLayout, etc.)
**Apply to:** DataCallout.astro, FAQBlock.astro, AdSlot.astro, EditorialLayout.astro, LegalLayout.astro, ContactForm.astro

None of these are React components. No `client:*` directives. Interactive bits (CookieConsent buttons) use vanilla `<script>` tags (not `client:*`). The MapIsland is the only `client:only="react"` component and it already exists.

### Pattern 7: Reciprocal hreflang pair on every page

**Source:** `site/src/layouts/BaseLayout.astro` lines 51–54
**Apply to:** Every new page

Every page must provide both `enPath` and `esPath` to BaseLayout. The 20-slug mapping is in UI-SPEC lines 447–458. Legal pages map 1:1 between locales (e.g. `enPath="/privacy-policy/"`, `esPath="/es/politica-privacidad/"`).

---

## No Analog Found

All files have at least a role-match analog. No files required external research patterns.

| File | Role | Data Flow | Note |
|------|------|-----------|------|
| `site/src/components/AdSlot.astro` | component | request-response | No ad-slot component exists; pattern constructed from env-gate convention + MapPlaceholderSlot visual contract |
| `site/src/components/CookieConsent.astro` | component | event-driven | No consent component exists; pattern constructed from PageFooter structure + vanilla script convention |
| `site/src/components/ContactForm.astro` | component | request-response | No form component exists; fully hand-rolled per UI-SPEC + D-14 |

---

## Metadata

**Analog search scope:** `site/src/layouts/`, `site/src/components/`, `site/src/pages/`, `site/scripts/validate/`, `site/src/config/`, `site/src/lib/`
**Files scanned:** 11 source files read in full
**Pattern extraction date:** 2026-06-13
