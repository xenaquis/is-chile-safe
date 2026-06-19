---
phase: 19-tech-debt-sweep
reviewed: 2026-06-19T06:00:00Z
depth: standard
files_reviewed: 35
files_reviewed_list:
  - pipeline/news/store.py
  - pipeline/scrape_cead.py
  - pipeline/shared/schema.py
  - pipeline/tests/conftest.py
  - pipeline/tests/test_centroids.py
  - pipeline/tests/test_classifier.py
  - pipeline/tests/test_dedup.py
  - pipeline/tests/test_feeds.py
  - pipeline/tests/test_schema.py
  - pipeline/tests/test_store.py
  - site/src/components/CookieConsent.astro
  - site/src/components/MapPlaceholderSlot.astro
  - site/src/components/PageFooter.astro
  - site/src/components/PageHeader.astro
  - site/src/components/map/FiltersRow.tsx
  - site/src/config/i18n.ts
  - site/src/pages/commune/[slug].astro
  - site/src/pages/crime-ranking/[crime].astro
  - site/src/pages/crime/[family].astro
  - site/src/pages/crimes-by-region.astro
  - site/src/pages/es/comuna/[slug].astro
  - site/src/pages/es/comunas-mas-seguras-chile.astro
  - site/src/pages/es/delito/[family].astro
  - site/src/pages/es/delitos-por-region.astro
  - site/src/pages/es/mapa-delito-chile.astro
  - site/src/pages/es/mapa-seguridad-santiago.astro
  - site/src/pages/es/metodologia.astro
  - site/src/pages/es/noticias.astro
  - site/src/pages/es/ranking-delito/[crime].astro
  - site/src/pages/es/seguridad-concepcion.astro
  - site/src/pages/es/seguridad-valparaiso.astro
  - site/src/pages/es/seguridad-vina-del-mar.astro
  - site/src/pages/is-santiago-safe.astro
  - site/src/pages/methodology.astro
  - site/src/pages/news.astro
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: clean
---

# Phase 19: Code Review Report

**Reviewed:** 2026-06-19
**Depth:** standard
**Files Reviewed:** 35
**Status:** findings

## Summary

Phase 19 delivers: methodology wording fix (TD-01), MapPlaceholder CTA (TD-02),
news sort + safeUrl (TD-03/TD-05), vida redirect (TD-04), pipeline URL guard
(TD-05), partial_year flag (TD-06), FAMILY_KEYS CI assertion + ByFamily TypedDict
+ dynamic AVAILABLE_YEARS (TD-07), BIL-01/02/03 bilingual fixes, new
/crimes-by-region/ page, i18n extraction of headings/table-headers (BIL-04), and
SEO spine (SEO-01/02/03).

No BLOCKER-level issues found. The three warnings below should be addressed before
the next milestone. The info items are minor quality observations.

---

## Warnings

### WR-01: `build_incident` return type lie — callers must null-check

**File:** `pipeline/news/store.py:68-72`
**Issue:** `build_incident()` is annotated `-> dict` but returns `None` when the
URL fails the scheme check (line 72: `return None  # type: ignore[return-value]`).
The `# type: ignore` suppresses mypy on the function definition, but every call
site that doesn't null-check the return value will fail at runtime with an
`AttributeError` (e.g. `inc["id"]` on None).

`merge_and_write` defensively filters None at line 145, so the store itself is
safe. However, any future caller of `build_incident` outside `merge_and_write`
that forgets the null-check will produce a runtime crash, and the type system
won't catch it because the signature promises `dict`.

**Fix:** Change the return type to `dict | None` and remove the `# type: ignore`:
```python
def build_incident(
    *,
    url: str,
    ...
) -> dict | None:
```
This makes the `None` path visible to every caller at type-check time.

---

### WR-02: `CommuneRankingTable` bypasses the new BIL-04 i18n keys — ES renders hardcoded EN-biased strings

**File:** `site/src/components/CommuneRankingTable.astro:35-38`
**Issue:** BIL-04 extracted table-header strings to `i18n.ts` as `th_commune`,
`th_rate_per_100k`, `th_rank`, and `th_trend`. The EN/ES crime-family pages and
crime-ranking pages were updated to use these keys. However
`CommuneRankingTable.astro` (used by the commune page similar-communes section)
still builds its column labels from *independent* hardcoded strings:

```js
const communeColLabel = locale === 'en' ? 'Commune' : 'Comuna';
const rateColLabel    = locale === 'en' ? 'Rate per 100k' : 'Tasa por 100k';
const rankColLabel    = t.national_rank_label;
const trendColLabel   = t.trend_label;
```

The EN column header "Commune" diverges from `t.th_commune = 'Commune'` today,
but "Rate per 100k" diverges from `t.th_rate_per_100k = 'Rate per 100k'` and will
silently drift on any future wording update to `i18n.ts`. The extraction is
incomplete: this component wasn't updated.

**Fix:** Replace the hardcoded strings with the new keys:
```ts
const t = locale === 'en' ? EN_STRINGS : ES_STRINGS;
// replace:
const communeColLabel = locale === 'en' ? 'Commune' : 'Comuna';
const rateColLabel    = locale === 'en' ? 'Rate per 100k' : 'Tasa por 100k';
// with:
const communeColLabel = t.th_commune;
const rateColLabel    = t.th_rate_per_100k;
```
`t` is already imported and used in this component for `national_rank_label` and
`trend_label`.

---

### WR-03: `partial_year` map-payload flag is produced but never consumed in the frontend

**File:** `pipeline/scrape_cead.py:191-202` (producer) / `site/src/` (no consumer found)
**Issue:** TD-06 correctly adds `partial_year: bool` to the map-payload JSON via
`build_map_payload`. The `partial_year_badge` i18n key exists in both EN and ES
strings (`i18n.ts:183/333`). However, no frontend file reads `payload.partial_year`
or renders `t.partial_year_badge`. The flag reaches the JSON file and stops there.
The REQUIREMENTS acceptance criterion for TD-06 specifies the flag *and* a UI
indicator; the UI half is unimplemented.

**Fix:** In the map island (or wherever map-payload is loaded), read
`payload.partial_year` and, when true, render a visible badge using
`t.partial_year_badge.replace('{year}', String(payload.year))`. This is a
one-component change; the data is already correct.

---

## Info

### IN-01: `new Date().getFullYear()` called twice per render in `FiltersRow.tsx`

**File:** `site/src/components/map/FiltersRow.tsx:49-52`
**Issue:** `new Date().getFullYear()` is called twice at module initialisation to
build `AVAILABLE_YEARS`. Since this is module-level (not inside a component
function), the two calls will always return the same value and there is no
correctness issue. But extracting to a constant removes the redundancy:
```ts
const _currentYear = new Date().getFullYear();
const AVAILABLE_YEARS: number[] = Array.from(
  { length: _currentYear - CEAD_EARLIEST_YEAR + 1 },
  (_, i) => _currentYear - i
);
```

---

### IN-02: `safeUrl()` defined identically in two files with no shared import

**File:** `site/src/pages/news.astro:61-71` and `site/src/pages/es/noticias.astro:62-72`
**Issue:** The function is identical in both files. The context comment says it
"mirrors IncidentPinLayer.ts safeUrl()", implying three copies exist. A utility
module (e.g. `site/src/lib/safeUrl.ts`) would let all three share a single
implementation. This is low-risk duplication today (two copies, simple logic), but
any future change to the whitelist must be applied in three places.

---

### IN-03: `th_commune` i18n key renders "Commune" in EN — consistent with the rest of the EN site but diverges from BIL-01 intent

**File:** `site/src/config/i18n.ts:290` (`th_commune: 'Commune'`)
**Issue:** BIL-01 was specifically about replacing user-visible "commune" with
"comuna" in ES pages. The EN key `th_commune = 'Commune'` is correct for EN. This
is not a bug — just a note that if the EN UI ever shifts to "municipality" or
"city" for a different audience, the key is the single place to change.
No action required.

---

_Reviewed: 2026-06-19_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
