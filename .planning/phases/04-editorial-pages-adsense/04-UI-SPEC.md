---
phase: 4
slug: editorial-pages-adsense
status: draft
shadcn_initialized: false
preset: none
created: 2026-06-13
---

# Phase 4 — UI Design Contract

> Visual and interaction contract for Editorial Pages + AdSense. All Phase-2 design tokens
> (palette, typography, spacing, components, BaseLayout) are LOCKED and inherited verbatim —
> this spec defines ONLY the NEW surfaces this phase introduces:
> (1) editorial page template, (2) AdSlot component, (3) cookie-consent banner,
> (4) map-bearing editorial layout, (5) legal page template.
>
> Source: 04-CONTEXT.md D-01..D-16 (authoritative), 02-UI-SPEC.md (inherited tokens),
> site/src/styles/global.css (confirmed token values), site/src/layouts/BaseLayout.astro.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (CSS custom properties — same as Phase 2; no shadcn, no Tailwind) |
| Preset | not applicable |
| Component library | none — Astro-native components only; reuse Phase-2 inventory |
| Icon library | Inline SVG only — same 3 prototype SVGs (SearchIcon, LocateIcon, PinGlyph) already in codebase |
| Font | Nunito Sans (`wght@400;700`); fallback: "Segoe UI", system-ui, sans-serif — already loaded via global.css |

Source: Phase-2 02-UI-SPEC.md Design System section (confirmed in site/src/styles/global.css).

---

## Spacing Scale

**INHERITED FROM PHASE 2 — DO NOT REDEFINE.** Exact token values from `global.css `:

| Token | Value | CSS Variable |
|-------|-------|-------------|
| xs | 4px | `--xs` |
| sm | 8px | `--sm` |
| md | 16px | `--md` |
| lg | 24px | `--lg` |
| xl | 32px | `--xl` |
| 2xl | 48px | `--2xl` |
| 3xl | 64px | `--3xl` |

Phase-4-specific exceptions:

| Exception | Value | Reason |
|-----------|-------|--------|
| Editorial prose column max-width | 720px | Optimal reading width for 800-1500 word articles (narrower than the 860px page-content container) |
| AdSlot reserved height (leaderboard) | 90px | IAB standard leaderboard (728×90) to prevent CLS; mobile: 50px (320×50 mobile banner) |
| AdSlot reserved height (rectangle) | 250px | IAB medium rectangle (300×250); used in-content |
| AdSlot side margin | 16px (`--md`) auto | Centered with auto margins at all breakpoints |
| FAQ block question row padding | 16px vertical (`--md`) | Adequate tap target height for expand/collapse; no JS needed — static open in Phase 4 |
| Cookie banner bottom offset | 0px | Banner is sticky-bottom, full-width, sits flush with viewport edge |
| Cookie banner padding | 16px 24px (`--md` / `--lg`) | Vertical / horizontal internal padding |
| Data-callout box border-left | 4px solid `--primary` | Visual signal distinguishing sourced data callouts from prose |
| Data-callout box padding | 16px (`--md`) | Internal padding of the callout box |

---

## Typography

**INHERITED FROM PHASE 2 — DO NOT REDEFINE.** Exact values from `global.css`:

| Role | Size | Weight | Line Height | CSS Variable | Usage |
|------|------|--------|-------------|-------------|-------|
| Body | 16px | 400 | 1.5 | `--text-body` / `--weight-body` | Editorial prose paragraphs, legal page body text |
| Label | 14px | 700 | 1.4 | `--text-label` / `--weight-strong` | Source attribution lines, callout labels, FAQ "Q:" prefix, methodology footnotes, cookie banner secondary text |
| Heading | 20px | 700 | 1.25 | `--text-heading` / `--weight-strong` | Editorial H2 sections, FAQ question text, legal page section headings |
| Display | 28px | 700 | 1.15 | `--text-display` / `--weight-strong` | Page H1 on every editorial and legal page |

Phase-4-specific typographic rules (additions, not redefinitions):

- **FAQ questions:** 20px/700 (Heading role) — consistent with H2 to signal answer structure without nesting confusion.
- **FAQ answers:** 16px/400 (Body role) — same as prose.
- **Data callout value:** 28px/700 (Display role) — reuse StatCard visual contract for inline data callouts.
- **Data callout label:** 14px/700 (Label role) — source attribution ("Fuente: CEAD {year}" / "Source: CEAD {year}").
- **Cookie banner body text:** 14px/400 (Label size, body weight) — concise notice copy, below body weight to distinguish from main content.
- **AdSlot placeholder text (ADSENSE_ENABLED=off):** 14px/400, color `--muted` — not shown to end users in production; dev/staging only.
- **Legal page H1:** 28px/700 (Display) — same as editorial H1.
- **Contact form labels:** 14px/700 (Label) — form field labels.
- **Contact form input text:** 16px/400 (Body) — input field values.

---

## Color

**INHERITED FROM PHASE 2 — DO NOT REDEFINE.** Exact values from `global.css `:

| Token | Hex | CSS Variable |
|-------|-----|-------------|
| `--primary` | `#0f766e` | Brand teal — accent |
| `--bg` | `#f5f8f8` | Page background |
| `--ink` | `#1c2a2b` | Body text, headings |
| `--muted` | `#5d6c6d` | Secondary text |
| `--line` | `#e2e9e8` | Borders, dividers |
| `--card` | `#ffffff` | Card backgrounds |

### 60/30/10 Distribution (same as Phase 2, inherited)

| Role | Value | Usage in Phase 4 |
|------|-------|-----------------|
| Dominant (60%) | `#f5f8f8` (`--bg`) | Page background for all editorial, legal, methodology pages |
| Secondary (30%) | `#ffffff` (`--card`) | Data-callout boxes, FAQ answer blocks, contact form fields, methodology caveat box |
| Accent (10%) | `#0f766e` (`--primary`) | Same reserved list as Phase 2 PLUS: data-callout left-border, cookie banner "Accept" button fill, "Read our privacy policy" link |

Accent reserved for (Phase-4 additions appended to Phase-2 list):
- Primary CTA button fill (inherited)
- Active nav link (inherited)
- Active lang toggle button (inherited)
- Rank badge background (inherited)
- Featured-family accent dot (inherited)
- Sparkline active-year bar (inherited)
- **Data-callout left border** (new — 4px solid `--primary`)
- **Cookie banner "Accept" / "Acepta" button fill** (new)
- **"About this data" and source attribution links** (already in MethodologyCaveat; confirmed for editorial pages)

Accent is NEVER applied to: body text, decorative borders, `--card` or `--bg` backgrounds, AdSlot placeholder containers, or legal page headings.

### Phase-4 Semantic Additions

| Role | Value | Usage |
|------|-------|-------|
| Cookie banner background | `#1c2a2b` (`--ink`) | Dark overlay bar — contrast with page content; text: `--card` |
| Cookie banner "Reject" / "Rechazar" button | transparent, border `--card`, text `--card` | Outlined style — less prominent than Accept |
| AdSlot placeholder (dev only) | `#f5f8f8` (`--bg`) background, `2px dashed --line` border | Matches MapPlaceholderSlot visual contract; never shown in production |
| Contact form field background | `#ffffff` (`--card`) | Standard input surface |
| Contact form field border | `1px solid --line` | Resting state |
| Contact form field border (focus) | `2px solid --primary` | Focus ring, keyboard-accessible |
| Forbidden-language gate error (build log only) | n/a — terminal output | Not a visual element; not rendered in browser |

---

## Page Templates (New Surfaces)

### Template 1 — Standard Editorial Page

Applies to all 20 editorial pages that do NOT embed the map.

Section order (top to bottom):

1. **PageHeader** — reuse from Phase 2; no changes.
2. **EditorialHero** — `<h1>` (28px/700/1.15); optional subtitle `<p>` (16px/400/1.5); max-width 720px.
3. **EditorialBody** — prose content (16px/400/1.5, max-width 720px); H2 sections (20px/700/1.25) with `--xl` (32px) top margin; paragraphs separated by `--md` (16px).
4. **DataCallout** (repeated as needed) — box with `4px solid --primary` left border, `--card` background, `--radius` border-radius, `--md` padding. Contains: value (28px/700, `--primary` color), label (14px/700, `--muted`), source attribution (14px/400, `--muted`). Used for: national rate, Santiago rate vs national, commune trend, etc. DO NOT use CallOuts for claims not directly derivable from `data/cead/`.
5. **FAQBlock** (question-style pages only — "Is Chile safe", "Is Santiago safe") — static open (no JS accordion). Each FAQ item: question as `<h2>` (20px/700), answer as `<p>` (16px/400), separated by `1px solid --line` rule. FAQPage JSON-LD schema (see SEO section below).
6. **AdSlot** (position: after first H2 section AND at page bottom; NEVER in hero or FAQ block) — see AdSlot spec below.
7. **MethodologyCaveat** — reuse Phase-2 component; no changes.
8. **PageFooter** — reuse from Phase 2; no changes.

### Template 2 — Map-Bearing Editorial Page

Applies to: `/chile-crime-map/`, `/santiago-safety-map/`, `/es/mapa-delito-chile/`, `/es/mapa-seguridad-santiago/`.

Section order:

1. **PageHeader**
2. **EditorialHero** — same as Template 1.
3. **EditorialIntro** — 1-3 paragraphs of editorial prose before the map (max-width 720px).
4. **MapIslandBlock** — full-width container (max-width: none; breaks out of the 720px prose column). Minimum height 480px on desktop / 320px on mobile. Contains `<MapIsland client:only="react" />` (Phase-3 component; reuse exactly as wired in map.astro and es/mapa.astro). No editorial text overlaps the map.
5. **EditorialBody** — continues below the map (max-width 720px).
6. **DataCallout** (as needed)
7. **AdSlot** — after first editorial body H2 and at page bottom; NEVER inside or adjacent to the MapIslandBlock (map view is an AdSlot exclusion zone per D-10).
8. **MethodologyCaveat**
9. **PageFooter**

### Template 3 — Methodology Page

Applies to: `/methodology/`, `/es/metodologia/`.

Section order:

1. **PageHeader**
2. **MethodologyHero** — h1 + subtitle. EN: "How this data works" / ES: "Cómo funcionan estos datos".
3. **MethodologyBody** — rich prose (~1200 words target); structured with H2 sections. Required H2 sections (in order):
   - EN: "Data source: CEAD" / ES: "Fuente de datos: CEAD"
   - EN: "How the rate is calculated" / ES: "Cómo se calcula la tasa"
   - EN: "Underreporting (cifra negra)" / ES: "Subregistro (cifra negra)"
   - EN: "Trend formula" / ES: "Fórmula de tendencia"
   - EN: "Comparison criteria" / ES: "Criterios de comparación"
   - EN: "What this site does NOT say" / ES: "Lo que este sitio NO dice"
4. **AdSlot** — at page bottom only (methodology is a credibility page; one slot only, bottom).
5. **PageFooter**

### Template 4 — Legal Page (Privacy, Terms, About)

Applies to: Privacy Policy, Terms of Use, About (both locales).

Section order:

1. **PageHeader**
2. **LegalHero** — h1 (28px/700); last-updated date in Label style (14px/400, `--muted`).
3. **LegalBody** — structured prose; H2 sections (20px/700) for each policy section; body text (16px/400); internal links use `--primary` color.
4. **AdSlot** — NONE. Legal pages are an AdSlot exclusion zone per D-10.
5. **PageFooter**

### Template 5 — Contact Page

Applies to: `/contact/`, `/es/contacto/`.

Section order:

1. **PageHeader**
2. **ContactHero** — h1 (28px/700). EN: "Contact" / ES: "Contacto".
3. **ContactIntro** — 1-2 paragraphs (16px/400) explaining purpose.
4. **ContactForm** — static form; see Contact Form spec below.
5. **AdSlot** — NONE. Contact is a legal/trust page; no ads.
6. **PageFooter**

---

## Component Inventory (Phase 4 Additions)

Reused Phase-2 components (NO changes allowed to their existing API or styles):

| Component | Reused As-Is |
|-----------|-------------|
| `BaseLayout.astro` | Yes — all editorial/legal pages wrap in it |
| `PageHeader.astro` | Yes |
| `PageFooter.astro` | Yes — must add legal page links (Privacy, Terms, About, Contact) |
| `MethodologyCaveat.astro` | Yes — used in editorial + methodology pages |
| `StatCard.astro` | Yes — reused inside DataCallout |
| `TrendChip.astro` | Yes — where editorial pages reference trend |
| `LevelChip.astro` | Yes — where editorial pages reference incidence level |
| `MapIsland.tsx` | Yes — embedded in map-bearing editorial pages (`client:only="react"`) |

New components (Phase 4):

| Component | Type | Notes |
|-----------|------|-------|
| `EditorialLayout.astro` | Astro layout | Extends BaseLayout; adds editorial-prose CSS (max-width 720px column, section spacing); wraps Templates 1-3 |
| `LegalLayout.astro` | Astro layout | Extends BaseLayout; same as EditorialLayout but no AdSlot injection; wraps Templates 4-5 |
| `DataCallout.astro` | Astro | Props: `value: string`, `label: string`, `source: string`, `locale: 'en' \| 'es'`. Server-renders the styled box. |
| `FAQBlock.astro` | Astro | Props: `items: { q: string; a: string }[]`, `locale`. Renders static open Q+A list; outputs FAQPage JSON-LD via BaseLayout `jsonLd` prop. |
| `AdSlot.astro` | Astro | Props: `slot: 'content' \| 'bottom'`, `publisherId: string`. Reads `ADSENSE_ENABLED` env at build time. When off: renders `<div class="ad-placeholder" aria-hidden="true" />` with reserved dimensions. When on: emits `<ins class="adsbygoogle">` with data attributes. Never renders on map pages or legal pages (enforced by template — not by the component itself). |
| `CookieConsent.astro` | Astro | Sticky-bottom banner. Reads a `csm_consent` localStorage key client-side (minimal inline `<script>`). Hides itself if key is set. Buttons: Accept (sets key + loads AdSense personalization) and Reject (sets key, no ad personalization). |
| `ContactForm.astro` | Astro | Static HTML form; `action="mailto:xenaquis@gmail.com"` (Phase-4 MVP contact mechanism per D-14). Fields: Name, Email, Message, Submit button. No server endpoint. |

---

## AdSlot Component Specification

### Reserved Dimensions (CLS Prevention — D-10)

| Position | Width | Height (desktop) | Height (mobile) | Trigger |
|----------|-------|-----------------|-----------------|---------|
| `content` (in-article) | 100% of prose column (max 728px) | 90px | 50px | After first H2 section |
| `bottom` (end of page) | 100% of prose column (max 728px) | 90px | 50px | Before PageFooter |

The `<div>` wrapper always renders with these reserved dimensions regardless of `ADSENSE_ENABLED` state. When `ADSENSE_ENABLED=false` the inner content is an empty `aria-hidden` placeholder. When `ADSENSE_ENABLED=true` the `<ins>` tag fills the same wrapper. No layout shift possible.

### AdSlot Placement Rules (D-10)

| Page Type | `content` slot | `bottom` slot |
|-----------|---------------|--------------|
| Editorial pages (all 20) | Yes | Yes |
| Methodology page | No | Yes (one only) |
| Home / index pages | Yes | Yes |
| Map-bearing editorial (Templates 2) | Yes (prose section only) | Yes |
| Legal pages (Privacy, Terms, About, Contact) | No | No |
| Map view (`/map/`, `/es/mapa/`) | No | No |
| Commune / region / crime-type pages (Phase 2) | No (Phase 2 out of scope) | No |

### AdSense Loader (D-12)

A single async script tag in `<head>` gated behind `ADSENSE_ENABLED`:

```html
<!-- Injected by BaseLayout.astro when ADSENSE_ENABLED=true -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={publisherId}"
  crossorigin="anonymous"></script>
```

The script is NOT inlined per-page. Publisher ID comes from `import.meta.env.PUBLIC_ADSENSE_PUBLISHER_ID`. Default value: empty string (renders nothing).

---

## Cookie-Consent Banner Specification

### Layout

- Position: `fixed; bottom: 0; left: 0; right: 0; z-index: 200` — above header (`z-index: 100`).
- Background: `var(--ink)` (`#1c2a2b`) — dark bar.
- Padding: `var(--md) var(--lg)` (16px vertical, 24px horizontal).
- Content layout: `display: flex; flex-wrap: wrap; align-items: center; gap: var(--md)`.
- Max-width: none — full viewport width.

### Copy

| Element | EN Copy | ES Copy |
|---------|---------|---------|
| Banner body | "We use cookies to serve ads and analyze traffic. See our [Privacy Policy]." | "Usamos cookies para mostrar anuncios y analizar el tráfico. Ver nuestra [Política de Privacidad]." |
| Accept button | "Accept" | "Aceptar" |
| Reject button | "Reject" | "Rechazar" |
| "Privacy Policy" link | links to `/privacy-policy/` | links to `/es/politica-privacidad/` |

### Interaction

- On **Accept**: set `localStorage.setItem('csm_consent', 'accepted')`, hide banner, call `googletag.pubads().setPrivacySettings({nonPersonalizedAds: false})` if AdSense is enabled.
- On **Reject**: set `localStorage.setItem('csm_consent', 'rejected')`, hide banner, call `googletag.pubads().setPrivacySettings({nonPersonalizedAds: true})` if AdSense is enabled (serves non-personalized ads).
- On **page load**: if `csm_consent` key exists, banner is hidden before first paint (inline script in `<head>`).
- Banner is ONLY injected when `ADSENSE_ENABLED=true` (no consent needed when no ads).

### Button Styles

| Button | Background | Border | Text color | Hover |
|--------|-----------|--------|-----------|-------|
| Accept | `var(--primary)` (`#0f766e`) | none | `var(--card)` (`#ffffff`) | darken 10% (`#0d6460`) |
| Reject | transparent | `1px solid var(--card)` | `var(--card)` | `background: rgba(255,255,255,0.1)` |

Both buttons: font 14px/700 (Label), padding `8px 16px`, border-radius `calc(var(--radius)/2)` (7px), min-height 44px (touch target).

---

## Contact Form Specification

### Fields

| Field | Type | Label EN | Label ES | Required |
|-------|------|---------|---------|---------|
| Name | `<input type="text">` | "Your name" | "Tu nombre" | Yes |
| Email | `<input type="email">` | "Email address" | "Correo electrónico" | Yes |
| Message | `<textarea rows="5">` | "Message" | "Mensaje" | Yes |
| Submit | `<button type="submit">` | "Send message" | "Enviar mensaje" | — |

### Form Styles

- Field container margin-bottom: `var(--md)` (16px).
- Label: 14px/700 (`--text-label` / `--weight-strong`), color `--ink`, display block, margin-bottom `var(--xs)` (4px).
- Input/textarea: 16px/400, color `--ink`, background `var(--card)`, border `1px solid var(--line)`, border-radius `calc(var(--radius)/2)`, padding `var(--sm) var(--md)` (8px 16px), width 100%, max-width 480px.
- Focus ring: `border: 2px solid var(--primary)`, `outline: none`.
- Submit button: same style as primary CTA in Phase 2 — background `var(--primary)`, color `var(--card)`, 16px/700, padding `var(--sm) var(--xl)` (8px 32px), border-radius `calc(var(--radius)/2)`, border none, min-height 44px.

### Mechanism

`action="mailto:xenaquis@gmail.com" method="POST" enctype="text/plain"` — opens the user's mail client. No backend. MVP per D-14. A comment above the form element: `<!-- Phase-4 MVP: mailto link. Replace with a form service endpoint in v2. -->`.

---

## Forbidden-Language Gate Specification (EDIT-05)

This is a build-time validator, not a visual element. Included here for completeness as it directly governs what may appear on-screen.

### Scope

All pages in `dist/` after `astro build`. Strip HTML tags and script content before matching. Ignore URL strings and HTML attributes (src, href, alt, data-*).

### Term List (D-06)

Matching is case-insensitive, accent-insensitive, word-boundary-aware.

| EN Forbidden Term | ES Forbidden Term |
|------------------|-----------------|
| dangerous zone | zona peligrosa |
| dangerous area | área peligrosa |
| dangerous commune | comuna peligrosa |
| dangerous neighborhood | barrio peligroso |
| definitive ranking | ranking definitivo |
| guaranteed safe | zona segura garantizada |
| 100% safe | 100% seguro |
| guaranteed safety | seguridad garantizada |
| the safest (without qualifying phrase) | la más segura (sin calificador) |

Qualifying phrase exception: "la más segura en este período según datos CEAD" passes the gate (accent-normalized comparison). The bare phrase "la más segura" without this qualifier fails.

### Validator Output

On failure: non-zero exit, stderr output in format:
```
[forbidden-language] FAIL: /path/to/page.html
  Line 42: "zona peligrosa" — forbidden term detected
  Term matched: "zona peligrosa" (pattern: zona\s+peligrosa)
```

---

## SEO + Schema.org (Phase 4 Additions)

### Meta Tags — Editorial Pages

| Tag | EN Value | ES Value |
|-----|---------|---------|
| `<title>` (home) | "Chile Safety Map — Official Crime Data" | "Mapa de Seguridad Chile — Datos Oficiales de Incidencia" |
| `<title>` (is-chile-safe) | "Is Chile Safe? — Crime Data & Safety Guide" | n/a (ES equivalent: /es/delitos-por-comuna/) |
| `<title>` (is-santiago-safe) | "Is Santiago Safe? — Crime Statistics & Safety Tips" | "¿Es seguro Santiago? — Estadísticas de Incidencia" |
| `<title>` (methodology) | "Methodology — How We Calculate Crime Rates" | "Metodología — Cómo Calculamos las Tasas" |
| `<title>` (privacy) | "Privacy Policy — Chile Safety Map" | "Política de Privacidad — Chile Safety Map" |
| `<title>` (about) | "About — Chile Safety Map" | "Acerca de — Chile Safety Map" |
| `<title>` (contact) | "Contact — Chile Safety Map" | "Contacto — Chile Safety Map" |
| `<meta name="description">` | Per-page; 150-160 chars; must include primary keyword + "CEAD data" attribution | Per-page; 150-160 chars; includes "datos CEAD" |
| `<meta name="robots">` | `index, follow` | `index, follow` |

### Schema.org — FAQPage (D-02)

Question-style editorial pages (`/is-chile-safe/`, `/is-santiago-safe/`, ES equivalents) emit `FAQPage` JSON-LD via the BaseLayout `jsonLd` prop:

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "{question text}",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "{answer text — plain text, no HTML}"
      }
    }
  ]
}
```

### Schema.org — WebPage (editorial non-FAQ pages)

Non-FAQ editorial pages emit `WebPage` JSON-LD:

```json
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "{page title}",
  "description": "{meta description}",
  "url": "https://ischilesafe.com/{slug}/",
  "inLanguage": "{en|es}",
  "about": {
    "@type": "Dataset",
    "name": "CEAD Crime Statistics Chile",
    "creator": { "@type": "Organization", "name": "CEAD — Centro de Estudios y Análisis del Delito" }
  }
}
```

### hreflang — Editorial Pages

Same BaseLayout pattern as Phase 2 (already handles it via `enPath`/`esPath` props). Each editorial page passes its reciprocal path pair. The 20-page slug mapping:

| EN Slug | ES Slug |
|---------|---------|
| `/` | `/es/` |
| `/chile-crime-map/` | `/es/mapa-delito-chile/` |
| `/is-chile-safe/` | `/es/delitos-por-comuna/` |
| `/santiago-safety-map/` | `/es/mapa-seguridad-santiago/` |
| `/is-santiago-safe/` | `/es/seguridad-santiago/` (see note) |
| `/valparaiso-safety/` | `/es/seguridad-valparaiso/` |
| `/vina-del-mar-safety/` | `/es/seguridad-vina-del-mar/` |
| `/concepcion-safety/` | `/es/seguridad-concepcion/` |
| `/safest-cities-in-chile/` | `/es/comunas-mas-seguras-chile/` |
| `/methodology/` | `/es/metodologia/` |

Note: REQUIREMENTS.md EDIT-02 does not list `/es/seguridad-santiago/` — executor must use the exact REQUIREMENTS.md EDIT-01/02 slug list as authoritative. This mapping is illustrative; the locked list is in REQUIREMENTS.md.

---

## Responsive Breakpoints (Inherited + Phase 4 Notes)

Breakpoints unchanged from Phase 2:

| Breakpoint | Width | Phase-4 behavior |
|------------|-------|-----------------|
| Mobile | `< 640px` | Editorial prose full-width (no 720px cap, padding `--md` each side); AdSlot switches to 320×50; MapIsland block min-height 320px; cookie banner stacks buttons below text |
| Tablet | `640px – 1024px` | Editorial prose max-width 720px centered; AdSlot 728×90; FAQBlock full-width |
| Desktop | `> 1024px` | Same as tablet; page-content container max-width 860px (`--page-content`) centers everything |

Map-bearing editorial: MapIsland block breaks out of the 720px prose column at all breakpoints (`width: 100%; max-width: none; margin: 0 calc(-1 * var(--md))`). On tablet+ the negative margin breaks out to the 860px container edge.

---

## Copywriting Contract

### Voice Rules (Inherited + Phase 4 Additions)

Same sober-editorial rules as Phase 2 plus the EDIT-05 gate enforces them at build time. Phase-4 additions:

- **Editorial pages never claim absolute safety**: any superlative ("most", "least", "safest") must be qualified with "according to CEAD data for {year}" / "según datos CEAD de {año}".
- **Data callouts always cite the source year**: "Rate: 1,234 per 100k — CEAD {year}" / "Tasa: 1.234 por 100k — CEAD {año}".
- **Methodology page uses first-person institutional "we"** to explain calculations — not passive voice.
- **Legal pages use plain language** — no legalese, no ALL CAPS headings.

### Primary CTAs

| Context | EN Copy | ES Copy |
|---------|---------|---------|
| Home page hero | "Explore the map" | "Explorar el mapa" |
| Editorial pages (after intro) | "View interactive map" | "Ver mapa interactivo" |
| Safety-city editorial pages | "See {City} on the map" | "Ver {Ciudad} en el mapa" |
| Methodology page footer | "Back to map" | "Volver al mapa" |
| Contact page submit | "Send message" | "Enviar mensaje" |

### Empty States

| Context | EN Copy | ES Copy |
|---------|---------|---------|
| DataCallout when rate unavailable | "Rate data not available for this period." | "Datos de tasa no disponibles para este período." |
| MapIsland in editorial page (before load) | "Loading map…" | "Cargando mapa…" |
| Contact form after submit (mailto fallback) | (browser handles mail client open — no custom state) | — |

### Error States

| Context | EN Copy | ES Copy |
|---------|---------|---------|
| Editorial page 404 | "This page hasn't been published yet. Check back soon." | "Esta página aún no está publicada. Vuelve pronto." |
| DataCallout load error (client-side — not applicable; all data injected at build) | n/a | n/a |

### Destructive Actions

No destructive actions in Phase 4. The forbidden-language gate is a build failure (developer-facing), not a user-facing destructive action. No confirmation dialogs required.

---

## Footer Extension (Phase 4 Requirement)

The existing `PageFooter.astro` (Phase 2) must be extended to include legal page links. No visual redesign — add links to the existing footer pattern.

Footer link additions:

| EN Label | EN Path | ES Label | ES Path |
|---------|---------|---------|---------|
| "Privacy Policy" | `/privacy-policy/` | "Política de Privacidad" | `/es/politica-privacidad/` |
| "Terms of Use" | `/terms/` | "Términos de Uso" | `/es/terminos/` |
| "About" | `/about/` | "Acerca de" | `/es/acerca-de/` |
| "Contact" | `/contact/` | "Contacto" | `/es/contacto/` |

These links render in the same Label style (14px/700, `--muted` color) as existing footer copy. No new design tokens.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none — shadcn not initialized | not applicable |
| Third-party | none | not applicable |

No third-party component registries. All new components (AdSlot, CookieConsent, DataCallout, FAQBlock, ContactForm, EditorialLayout, LegalLayout) are hand-rolled Astro-native. chroma-js used at build time only (inherited from Phase 2).

---

## Astro File Structure (Phase 4 Additions)

```
/site/
  src/
    layouts/
      EditorialLayout.astro   — extends BaseLayout; 720px prose column; AdSlot injection
      LegalLayout.astro       — extends BaseLayout; no AdSlot; legal styling
    components/
      DataCallout.astro       — sourced data box (value + label + source)
      FAQBlock.astro          — static FAQ list; outputs FAQPage JSON-LD
      AdSlot.astro            — reserved dimensions; ADSENSE_ENABLED gate
      CookieConsent.astro     — sticky-bottom consent banner; localStorage gate
      ContactForm.astro       — static mailto form
    pages/
      index.astro             — EN home (/) — extend existing with editorial content
      is-chile-safe.astro     — /is-chile-safe/
      chile-crime-map.astro   — /chile-crime-map/
      is-santiago-safe.astro  — /is-santiago-safe/
      santiago-safety-map.astro — /santiago-safety-map/
      valparaiso-safety.astro — /valparaiso-safety/
      vina-del-mar-safety.astro — /vina-del-mar-safety/
      concepcion-safety.astro — /concepcion-safety/
      safest-cities-in-chile.astro — /safest-cities-in-chile/
      methodology.astro       — /methodology/
      privacy-policy.astro    — /privacy-policy/
      terms.astro             — /terms/
      about.astro             — /about/
      contact.astro           — /contact/
      es/
        index.astro           — /es/
        mapa-delito-chile.astro — /es/mapa-delito-chile/
        delitos-por-comuna.astro — /es/delitos-por-comuna/
        seguridad-santiago.astro — (per REQUIREMENTS.md EDIT-02 exact slug)
        mapa-seguridad-santiago.astro — /es/mapa-seguridad-santiago/
        seguridad-valparaiso.astro — /es/seguridad-valparaiso/
        seguridad-vina-del-mar.astro — /es/seguridad-vina-del-mar/
        seguridad-concepcion.astro — /es/seguridad-concepcion/
        comunas-mas-seguras-chile.astro — /es/comunas-mas-seguras-chile/
        metodologia.astro     — /es/metodologia/
        politica-privacidad.astro — /es/politica-privacidad/
        terminos.astro        — /es/terminos/
        acerca-de.astro       — /es/acerca-de/
        contacto.astro        — /es/contacto/
    styles/
      global.css              — NO CHANGES (Phase 2 locked; AdSlot + consent styles scoped to components)
  scripts/validate/
    forbidden-language.mjs   — new validator; registered in all.mjs
```

Note: Exact ES slugs for EDIT-02 must be taken verbatim from REQUIREMENTS.md lines EDIT-02 — the file structure above is illustrative where slugs differ from REQUIREMENTS.md; REQUIREMENTS.md is authoritative.

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
