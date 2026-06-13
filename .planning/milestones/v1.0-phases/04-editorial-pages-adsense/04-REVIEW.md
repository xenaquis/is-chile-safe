---
phase: 04-editorial-pages-adsense
reviewed: 2026-06-13T00:00:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - site/scripts/validate/forbidden-language.mjs
  - site/scripts/validate/all.mjs
  - site/scripts/validate/structure.mjs
  - site/src/components/AdSlot.astro
  - site/src/components/CookieConsent.astro
  - site/src/components/DataCallout.astro
  - site/src/components/FAQBlock.astro
  - site/src/components/ContactForm.astro
  - site/src/layouts/BaseLayout.astro
  - site/src/layouts/EditorialLayout.astro
  - site/src/layouts/LegalLayout.astro
  - site/src/config/i18n.ts
  - site/src/components/PageFooter.astro
  - site/src/pages/is-santiago-safe.astro
  - site/src/pages/safest-cities-in-chile.astro
findings:
  critical: 3
  warning: 5
  info: 4
  total: 12
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-06-13
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

Phase 4 delivers editorial pages, AdSense gating, cookie consent, validation scripts, and
supporting components. The architecture is generally sound — the `ADSENSE_ENABLED` gate is
implemented correctly in both BaseLayout and AdSlot, JSON-LD uses `JSON.stringify` (not raw
interpolation), and the data layer correctly calls `loadNationalAverage()` / `loadCommune()`
rather than the SUM path.

Three critical issues require attention before shipping: (1) the `set:html` injection of
`JSON.stringify(jsonLd)` is not safe — user-controlled string values inside the object can
break out of the `<script>` tag via `</script>` substrings; (2) the forbidden-language
word-boundary regex silently misses terms adjacent to accented letters, producing false
negatives; (3) `is-santiago-safe.astro` sets `esPath="/is-santiago-safe/"` (the English
path) — the ES hreflang alternate will point to an English URL, and the language switcher
will loop back to the same page rather than a Spanish page.

---

## Structural Findings (fallow)

No structural pre-pass provided for this phase.

---

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: JSON-LD `set:html` injection allows `</script>` breakout

**File:** `site/src/layouts/BaseLayout.astro:73`

**Issue:** `JSON.stringify(jsonLd)` is passed to `set:html` inside a `<script>` block.
`JSON.stringify` does NOT escape the forward slash in `</script>` sequences. If any string
value inside `jsonLd` contains the literal text `</script>`, the browser HTML parser will
terminate the script block early, breaking JSON-LD parsing and potentially exposing whatever
text follows as raw HTML. On these pages, `jsonLd` values come from CEAD data
(commune/region names) and from FAQ answer text authored in page files — both are developer-
controlled at build time. However, if CEAD data ever contains a `</` sequence (e.g. a
commune name change or scraped text), this will silently break the page. The pattern is
also structurally unsafe for any future path where user-supplied text reaches `jsonLd`.

**Fix:** Apply a targeted escape of `</` → `<\/` after `JSON.stringify`. This is the
standard mitigation for JSON-LD in HTML `<script>` blocks:

```typescript
// In BaseLayout.astro, replace line 73:
<script is:inline type="application/ld+json" set:html={JSON.stringify(jsonLd)} />

// With:
<script is:inline type="application/ld+json"
  set:html={JSON.stringify(jsonLd).replace(/<\//g, '<\\/')} />
```

---

### CR-02: `is-santiago-safe.astro` — `esPath` points to the English URL, breaking hreflang and the language switcher

**File:** `site/src/pages/is-santiago-safe.astro:71`

**Issue:** The page passes `esPath="/is-santiago-safe/"` (the same as `enPath`). This causes:
1. The `<link rel="alternate" hreflang="es">` tag to resolve to the English page —
   Googlebot will treat the ES alternate as a duplicate of EN, wasting crawl budget and
   potentially triggering a hreflang mismatch warning.
2. `PageFooter`'s language switcher (`altHref`) for EN visitors will send them to
   `/is-santiago-safe/` — the same page they are already on — instead of a Spanish
   equivalent.

The comment in the file says "no ES pair in EDIT-02 — slug_flag", which suggests the ES
page does not exist yet. The correct behaviour in this situation is to either (a) omit the
ES hreflang alternate entirely, or (b) point it to the closest canonical Spanish equivalent
(e.g. `/es/mapa-seguridad-santiago/`). Pointing it to the EN URL is actively wrong.

**Fix (option A — no ES page):** Supply a `null`/empty `esPath` and conditionally omit the
ES hreflang in BaseLayout when esPath is empty. Alternatively, omit the `<link hreflang="es">`
when `esPath === enPath`.

**Fix (option B — redirect to closest ES editorial page):** Set
`esPath="/es/mapa-seguridad-santiago/"` if that page exists, so the switcher is useful.

At minimum, change BaseLayout to guard against self-referential duplicates:

```astro
{esPath && esPath !== enPath && (
  <link rel="alternate" hreflang="es" href={`${BASE_URL}${esPath}`} />
)}
```

---

### CR-03: `forbidden-language.mjs` — word-boundary lookahead/lookbehind only checks `[a-z0-9]`, so accented letters are transparent boundaries, producing false negatives

**File:** `site/scripts/validate/forbidden-language.mjs:103`

**Issue:** The boundary pattern `(?<![a-z0-9])...(?![a-z0-9])` intentionally avoids `\b`
because `\b` breaks on accented chars. However the replacement only covers ASCII lowercase
letters and digits. After NFD normalisation and accent removal (`normalizeAccents`), the
input text is already ASCII — so `[a-z0-9]` is actually sufficient in the normalised text
for most cases. The real gap is in the allow-list regex on line 64:

```js
/en este per[io]+do seg[u]+n datos cead/i,
```

This allow-list regex uses `[io]+` and `[u]+` to tolerate accent normalisation, but the
`según` → `segun` conversion is already performed by `normalizeAccents` on `normalizedVisible`
before the match. More importantly, the allow-list window is checked **after** the match
position, spanning only 100 characters forward (line 151). If the qualifying phrase appears
**before** the forbidden term (e.g. "según datos CEAD ... la más segura"), the allow-list
will miss it and the validator will incorrectly fail the page.

Specifically: `safest-cities-in-chile.astro` contains the text "the lowest reported crime
incidence" and other qualified phrases, but also contains the word-sequence "the safest" in
the is-santiago-safe.astro FAQ answer text on line 35 (`"the safest" places to live`). That
text is inside a JavaScript string that will end up in `jsonLd` JSON-LD, which is inside a
`<script>` block. The `extractVisibleText` function strips `<script>` blocks first, so
`"the safest"` in FAQ answer text embedded in a `<script type="application/ld+json">` block
**will be stripped** and will not be checked. However the same text also appears verbatim in
the rendered `<FAQBlock>` HTML — line 35 of the FAQ answer contains the phrase `"the 'objectively
safest' places to live"` which renders as visible text. The single-quote wrapping prevents a
literal match of `the safest` only if the quote is adjacent with no space — but it is
`"the "objectively safest" places` — so `the safest` as a bare substring does exist in the
visible text, separated only by the inner quoted word. After normalisation the pattern would
match `safest` preceded by a space (not `[a-z0-9]`), so the boundary passes. There is no
qualifying CEAD phrase within 100 chars after this occurrence in the prose, so **this page
will trip the forbidden-language gate at runtime** when the validator actually scans dist/.

**Fix (two parts):**

Part 1 — extend the allow-list window to also look backward (50 chars before the match),
since qualifying phrases often precede the superlative in Spanish editorial prose:

```js
// line 151 — replace window definition:
const preWindow = normalizedVisible.slice(Math.max(0, matchIndex - 150), matchIndex);
const postWindow = normalizedVisible.slice(matchIndex, matchIndex + match[0].length + 100);
const window = preWindow + postWindow;
const allowed = ALLOW_LIST.some((re) => re.test(window));
```

Part 2 — the phrase `"objectively safest"` in `safest-cities-in-chile.astro` line 93 will
match the term `the safest` because the word `the` is in the preceding sentence and the
boundary check passes on a space character. Reword to avoid the literal substring:

```astro
// line 93 — replace:
— it represents a snapshot of official reported data

// The specific phrase "objectively safest" already breaks the term match but "the safest"
// appears adjacent: change "the 'objectively safest' places to live"
// → "the communes with objectively lowest reported incidence"
```

---

## Warnings

### WR-01: `EditorialLayout.astro` — `<AdSlot slot="bottom" />` passes wrong `slot` prop value

**File:** `site/src/layouts/EditorialLayout.astro:47`

**Issue:** The line is:

```astro
<AdSlot slot="bottom" />
```

In Astro, `slot="bottom"` is the **Astro slot directive** — it tells Astro which named slot
of the *parent component* to place this element into, not a prop passed to `AdSlot`. The
`AdSlot` component receives `slot` as a prop (line 10 of AdSlot.astro: `slot: 'content' | 'bottom'`),
but here the attribute `slot="bottom"` is interpreted by Astro as the slot directive before
`AdSlot` even receives it. The result is that `AdSlot` is rendered with `slot` prop
`undefined`, which falls outside the `'content' | 'bottom'` union — `adSlotId` will be
`'BOTTOM_SLOT_ID'` only by the falsy branch of the ternary (which happens to produce the
right value), but the `ad-slot--${slot}` class will be `ad-slot--undefined` rather than
`ad-slot--bottom`, breaking the CSS height reservation and therefore the CLS-safe dimensions.

**Fix:** Pass the prop explicitly with a different attribute name, or rename the AdSlot prop:

```astro
<!-- EditorialLayout.astro line 47 — change to: -->
<AdSlot slotType="bottom" />
```

And update `AdSlot.astro` interface and internal references to use `slotType` instead of `slot`.

---

### WR-02: `CookieConsent.astro` — inline script `document.currentScript` is unreliable in module scripts and may not hide the banner on repeat visits

**File:** `site/src/components/CookieConsent.astro:25`

**Issue:** The `is:inline` script at line 24–28 uses `document.currentScript` to access
the parent element and set `display: none`. This pattern is fragile:

1. `document.currentScript` is `null` inside any deferred, async, or module context. The
   `is:inline` directive in Astro renders inline (not async/deferred), so it works — but
   only because of this specific directive. If the surrounding context changes, it silently
   breaks.
2. More importantly, the check `localStorage.getItem('csm_consent')` is truthy for both
   `'accepted'` AND `'rejected'` — but the intent is presumably to hide the banner on any
   prior consent action. This is actually correct for the hide-on-repeat-visit goal, but
   hides the banner even for users who previously rejected cookies, preventing them from
   changing their mind. There is no mechanism to revoke consent.

**Fix:** Use a stable DOM selector instead of `currentScript`, and expose a visible
"manage cookies" link in the footer for consent revocation:

```html
<script is:inline>
  if (typeof localStorage !== 'undefined' && localStorage.getItem('csm_consent')) {
    // Use id instead of currentScript for safety
    document.getElementById('csm-consent-banner')?.style.setProperty('display', 'none');
  }
</script>
```

---

### WR-03: `safest-cities-in-chile.astro` — `topCommunes[0]` accessed without guard when `communeRates` could be empty

**File:** `site/src/pages/safest-cities-in-chile.astro:56`

**Issue:**

```js
const dataYear = topCommunes[0]?.year ?? communeRates[0]?.year ?? 0;
```

The fallback chain handles `topCommunes[0]` being undefined, but if `communeRates` is also
empty (all rollout communes are `low_population`, or `loadRolloutCuts()` returns an empty
array), `dataYear` becomes `0`. The page then renders `CEAD 0 data` in the title, description,
and body text without any build-time error or warning. Additionally, line 160:

```js
Math.round(topCommunes[0]?.rate ?? 0)
```

will silently render `0 incidents` in the prose if `topCommunes` is empty, producing
misleading editorial content.

**Fix:** Add a build-time guard:

```js
if (communeRates.length === 0) {
  throw new Error(
    'safest-cities-in-chile: no eligible communes found — check rollout.json and low_population flags'
  );
}
```

---

### WR-04: `forbidden-language.mjs` — RegExp objects with `g` flag are mutated across pages due to shared `TERM_PATTERNS` array

**File:** `site/scripts/validate/forbidden-language.mjs:107-111`

**Issue:** `TERM_PATTERNS` is built once at module load time (line 107). Each entry holds
a compiled `RegExp` with the `g` (global) flag. The inner loop resets `pattern.lastIndex = 0`
before and after each page (lines 144, 169), which is correct. However if an exception is
thrown inside the `while` loop (e.g. from a malformed file), `lastIndex` will not be reset,
and the next page will start matching mid-string. This is a latent correctness bug — it does
not cause incorrect results in the happy path but makes the validator unreliable on error.

**Fix:** Construct a fresh RegExp per page rather than sharing stateful objects, or wrap the
inner loop in a try/finally:

```js
try {
  let match;
  while ((match = pattern.exec(normalizedVisible)) !== null) { ... }
} finally {
  pattern.lastIndex = 0;
}
```

---

### WR-05: `ContactForm.astro` — developer email address hardcoded and exposed in built HTML

**File:** `site/src/components/ContactForm.astro:42`

**Issue:** The form action `mailto:xenaquis@gmail.com` embeds the developer's personal Gmail
address in plain text in every built HTML page. This is acknowledged in the inline comment,
but the comment describes this as a "tradeoff accepted for MVP volume" — however, the email
is also included in a public GitHub repository (visible in git history), which means it is
already public. The risk is spam harvesting at scale once the site is indexed.

This is a WARNING (not Info) because the CLAUDE.md calls out AdSense revenue as the
monetisation model, and inbox spam affecting the developer email directly impairs the
project's operational capability.

**Fix (short term):** Obfuscate with CSS rotation or JS assembly — not foolproof but raises
the harvesting bar. Replace with a form service (Formspree / Netlify Forms) before launch
as documented in the component comment.

---

## Info

### IN-01: `all.mjs` — no timeout on child validator processes

**File:** `site/scripts/validate/all.mjs:51`

**Issue:** `spawnSync` has no `timeout` option. A hung validator (e.g. if `dist/` is on a
network path or an HTML file is extremely large) will block the suite indefinitely with no
output.

**Fix:** Add a reasonable timeout:

```js
const result = spawnSync(process.execPath, [scriptPath], {
  stdio: 'inherit',
  env: { ...process.env },
  timeout: 120_000, // 2 minutes per validator
});
```

---

### IN-02: `AdSlot.astro` — placeholder `CONTENT_SLOT_ID` / `BOTTOM_SLOT_ID` are hardcoded strings, not env vars

**File:** `site/src/components/AdSlot.astro:17`

**Issue:** The AdSense slot IDs are placeholder strings rather than environment variables.
When AdSense is enabled (`ADSENSE_ENABLED=true`), the real slot IDs must be substituted —
but there is no env var for them and no build-time validation that they have been set.

**Fix:** Read slot IDs from env vars and guard:

```js
const adSlotId = slot === 'content'
  ? (import.meta.env.PUBLIC_ADSENSE_SLOT_CONTENT ?? 'MISSING_SLOT_ID')
  : (import.meta.env.PUBLIC_ADSENSE_SLOT_BOTTOM ?? 'MISSING_SLOT_ID');
```

Add a build step warning when `ADSENSE_ENABLED=true` but slot IDs are missing.

---

### IN-03: `structure.mjs` — Phase-4 sentinel only checks file existence, not page validity

**File:** `site/scripts/validate/structure.mjs:186-192`

**Issue:** The Phase-4 block checks only `existsSync(abs)` — it does not call `checkPage()`
(which validates `<title>`, `<link rel="canonical">`, hreflang, and non-empty body). A page
could exist as an empty file or with a broken head and still pass the Phase-4 check.

**Fix:** Replace the existence-only check with `checkPage()` calls (accumulating failures
the same way the top-level sampler does), or at minimum assert that the file is non-zero size.

---

### IN-04: `FAQBlock.astro` — all FAQ items use `<h2>` regardless of document outline position

**File:** `site/src/components/FAQBlock.astro:44`

**Issue:** FAQ question headings are always `<h2>`. In `is-santiago-safe.astro`, the FAQ
section is wrapped in a `<section>` with its own `<h2>` ("Frequently Asked Questions"),
making the FAQ question `<h2>`s siblings of the section heading rather than children — the
heading outline is flat rather than nested. Screen readers navigating by heading will present
all section headings and all FAQ questions at the same level.

**Fix:** Add an `headingLevel?: 'h2' | 'h3'` prop to `FAQBlock` and use `<h3>` when the
FAQ is inside a section that already has an `<h2>`:

```astro
// FAQBlock.astro — use dynamic heading tag
const { items, headingLevel = 'h2' } = Astro.props;
const H = headingLevel;
// In template:
<H class="faq-q">{item.q}</H>
```

---

_Reviewed: 2026-06-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
