---
phase: quick-260620-hrh
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - site/src/lib/familyDefs.ts
  - site/src/components/CrimeFamilyCharts.astro
  - site/src/config/i18n.ts
  - site/src/pages/commune/[slug].astro
  - site/src/pages/es/comuna/[slug].astro
autonomous: true
requirements: [HRH-SEL, HRH-CHARTS]
user_setup: []

must_haves:
  truths:
    - "Each commune page (EN and ES) shows a year selector defaulting to latestCompleteYear, server-rendered in static HTML."
    - "Changing the year via the selector updates the rate StatCard, FamilyBreakdownBars (values + bar widths + heading year), homicide section (rate/count/heading/source year), and the Sparkline active-year highlight — with zero page reload and zero framework island."
    - "Each commune page shows a static SVG longitudinal-evolution chart section: one mini-chart per crime family (7) plus one homicide-per-year chart, all server-rendered with zero JS."
    - "Partial-year data points render at reduced opacity in the charts; charts carry bilingual aria-labels and family labels."
    - "Sections that do not vary by year (ComparisonCallouts, LevelChip/color level, composite index 2024, ENUSC 2024, rankings/comparables) remain unchanged on their fixed year."
  artifacts:
    - path: "site/src/components/CrimeFamilyCharts.astro"
      provides: "Static SVG longitudinal charts for 7 families + homicide-per-year"
      min_lines: 60
    - path: "site/src/lib/familyDefs.ts"
      provides: "Shared FAMILY_LABELS_PAGE (en/es) for charts + breakdown bars"
      contains: "FAMILY_LABELS_PAGE"
  key_links:
    - from: "site/src/pages/commune/[slug].astro"
      to: "year-data JSON island"
      via: "<script type=\"application/json\"> + vanilla <script> data-* lookup"
      pattern: "type=\"application/json\""
    - from: "site/src/pages/commune/[slug].astro"
      to: "CrimeFamilyCharts.astro"
      via: "component import + render"
      pattern: "CrimeFamilyCharts"
---

<objective>
Add a whole-page year selector and a static longitudinal crime-evolution chart section to every commune page (EN `/commune/{slug}/` and ES `/es/comuna/{slug}/`).

Purpose: Let users explore any year 2005–latest and see the multi-year trend per crime family, deepening engagement and SEO content depth — without breaking the zero-island SEO constraint (D-09).

Output:
- New `CrimeFamilyCharts.astro` (static SVG, zero JS) rendering 7 family charts + 1 homicide-per-year chart.
- A vanilla-JS year selector that rewrites the year-bound DOM on change, with the default year fully server-rendered.
- New bilingual i18n strings.
- Both commune pages updated as exact mirrors.

This is pure frontend. All data already exists in `data/cead/comunas/{cut}.json` (`series[]` and `featured_rates.homicidios`/`homicidios_count`). NEVER rescale rates — `by_family`/`featured_rates` are already per-100k (memory: crime-rates-already-per-100k). `vida` family ≠ homicide; homicide is tracked separately (memory: vida-homicide-slug-collision).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/quick/260620-hrh-anio-selector-graficos-longitudinales-po/260620-hrh-CONTEXT.md
@CLAUDE.md

# Pattern to extend (static SVG bar sparkline, partial years at 0.5 opacity):
@site/src/components/Sparkline.astro

# Existing breakdown bars — owns the per-page FAMILY_LABELS (en/es) we will hoist:
@site/src/components/FamilyBreakdownBars.astro

# Shared family constants live here (FAMILY_ORDER already exported):
@site/src/lib/familyDefs.ts

<interfaces>
<!-- Executor: use these directly. No further exploration needed. -->

Each `data/cead/comunas/{cut}.json` (loaded via `loadCommune(cut)` → `data`):
```typescript
data.series: Array<{
  year: number;
  rate_per_100k: number;
  by_family: { vida, propiedad, robos_violentos, incivilidades, vif, drogas, armas: number };
  partial?: boolean;
}>;                                   // 2005–2026
data.featured_rates.homicidios:        Record<string /*year*/, number /*rate per 100k*/>;
data.featured_rates.homicidios_count:  Record<string /*year*/, number /*count*/>;
data.latestCompleteYear: number;       // current server-rendered default
```

FAMILY_ORDER (already exported from site/src/lib/familyDefs.ts):
`['vida','propiedad','robos_violentos','incivilidades','vif','drogas','armas']`

FamilyBreakdownBars.astro currently hard-codes a per-page FAMILY_LABELS map
(en/es) DISTINCT from familyDefs FAMILY_LABELS_EN/ES (different casing/wording,
e.g. 'Life crimes' vs 'Life Crimes'). Preserve the FamilyBreakdownBars wording
exactly — hoist it verbatim, do not swap in the familyDefs variant.

i18n (site/src/config/i18n.ts): EN_STRINGS / ES_STRINGS, with a TS interface
above EN_STRINGS. Existing `{year}`-placeholder strings: `rate_label`,
`family_breakdown_heading`. Pattern for use: `t.rate_label.replace('{year}', String(year))`.

Astro pitfall (memory: astro-script-no-expr-interpolation): `{expr}` is rendered
LITERALLY inside `<script>`/`<style>`. Pass server→client data ONLY via
`<script type="application/json" set:html={JSON.stringify(...)}>` or `data-*`
attributes — NEVER by interpolating `{expr}` inside an executable `<script>`.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Hoist shared family labels + build CrimeFamilyCharts.astro (static SVG, zero JS)</name>
  <files>site/src/lib/familyDefs.ts, site/src/components/CrimeFamilyCharts.astro, site/src/components/FamilyBreakdownBars.astro</files>
  <action>
First, hoist the page-style family labels into familyDefs.ts. In `site/src/lib/familyDefs.ts`, add a new exported const `FAMILY_LABELS_PAGE: Record<string, { en: string; es: string }>` containing EXACTLY the entries currently in `FamilyBreakdownBars.astro`'s local `FAMILY_LABELS` (vida 'Life crimes'/'Delitos contra la vida', propiedad 'Property crimes'/'Delitos contra la propiedad', robos_violentos 'Violent robbery'/'Robos violentos', incivilidades 'Disorder'/'Incivilidades', vif 'Domestic violence'/'Violencia intrafamiliar', drogas 'Drug crimes'/'Drogas', armas 'Weapons'/'Armas'). Add a `homicidios: { en: 'Homicide', es: 'Homicidios' }` entry too (needed by the charts). Do NOT alter existing exports.

Then in `FamilyBreakdownBars.astro`: delete the local `FAMILY_LABELS` const and import `FAMILY_LABELS_PAGE` from `../lib/familyDefs`, replacing the lookup `FAMILY_LABELS[key]?.[locale]` with `FAMILY_LABELS_PAGE[key]?.[locale]`. Behavior must be byte-identical to before.

Then create `site/src/components/CrimeFamilyCharts.astro` — a static, server-rendered, ZERO-JS component (no client:* — D-09). Model the SVG approach on `Sparkline.astro` (viewBox, scale to series max, partial points at 0.5 opacity), but render LINE/area mini-charts (Claude's discretion: a polyline over per-year points reads better than bars for trend). Props:
  - `series: Array<{ year:number; by_family:Record<string,number>; partial?:boolean }>`
  - `homicidios: Record<string, number>` (year→rate)
  - `locale: 'en' | 'es'`
  - `heading: string` (passed from page i18n)
Render one labelled mini-chart per family in FAMILY_ORDER (7), then one for homicide built from the `homicidios` dict (sort year keys ascending). Each mini-chart: small heading = `FAMILY_LABELS_PAGE[key][locale]`, an inline SVG polyline (each year a point, y scaled to that chart's own max so low-volume families stay readable), partial years marked at 0.5 opacity, and a wrapping element with a descriptive bilingual `aria-label` (e.g. EN `${label} reported incidence per 100,000, ${firstYear}–${lastYear}` / ES `${label}, incidencia reportada por 100.000, ${firstYear}–${lastYear}`). The SVG itself stays `aria-hidden="true"` (decorative; aria-label on the wrapper conveys meaning), matching Sparkline's pattern. NEVER rescale values — plot raw per-100k numbers. Use CSS vars (`var(--primary)`, `var(--muted)`, `var(--line)`) and the project spacing vars in a scoped `<style>`; lay out the 8 mini-charts in a responsive grid.
  </action>
  <verify>
    <automated>cd "site" &amp;&amp; npx astro check 2>&amp;1 | Select-String -Pattern "CrimeFamilyCharts|FamilyBreakdownBars|familyDefs|error" </automated>
  </verify>
  <done>familyDefs.ts exports FAMILY_LABELS_PAGE incl. homicidios; FamilyBreakdownBars imports it (no local FAMILY_LABELS) and type-checks; CrimeFamilyCharts.astro exists, has no client:* directive, renders 8 mini-charts with bilingual aria-labels and partial-year opacity, and astro check reports no new errors.</done>
</task>

<task type="auto">
  <name>Task 2: Add bilingual i18n strings for selector + charts</name>
  <files>site/src/config/i18n.ts</files>
  <action>
In the TS interface above EN_STRINGS, add three fields: `year_selector_label: string;`, `charts_heading: string;`, and `chart_partial_note: string;`.

In EN_STRINGS add:
  - `year_selector_label: 'Analysis year'`
  - `charts_heading: 'Crime evolution by category (2005–present)'`
  - `chart_partial_note: 'Faded points indicate partial-year data.'`
In ES_STRINGS add:
  - `year_selector_label: 'Año de análisis'`
  - `charts_heading: 'Evolución de delitos por categoría (2005–presente)'`
  - `chart_partial_note: 'Los puntos atenuados indican datos de año parcial.'`
Keep ordering/style consistent with neighbouring entries (e.g. near `sparkline_heading` / `family_breakdown_heading`). Do not touch unrelated strings.
  </action>
  <verify>
    <automated>cd "site" &amp;&amp; npx astro check 2>&amp;1 | Select-String -Pattern "year_selector_label|charts_heading|chart_partial_note|error"</automated>
  </verify>
  <done>Both EN_STRINGS and ES_STRINGS contain year_selector_label, charts_heading, chart_partial_note; the interface declares all three; astro check reports no missing-property errors.</done>
</task>

<task type="auto">
  <name>Task 3: Wire year selector (vanilla JS) + charts section into both commune pages</name>
  <files>site/src/pages/commune/[slug].astro, site/src/pages/es/comuna/[slug].astro</files>
  <action>
Apply identical changes to BOTH pages (exact mirrors; EN uses locale 'en'/`toLocaleString('en-US')`/English literal strings already present, ES uses 'es'/`toLocaleString('es-CL')`/Spanish literals already present). Keep `const year = data.latestCompleteYear` as the server-rendered DEFAULT — the static HTML must still render the default year (SEO / progressive enhancement).

(a) Build a per-year data map in frontmatter. Construct `const yearData: Record<string, {...}>` keyed by year string, where each entry holds everything the selector must update: `rate` (the series rate_per_100k for that year), `byFamily` (that year's by_family), `homRate` (featured_rates.homicidios[year] ?? null — 0 is valid, use `!== undefined`), `homCount` (featured_rates.homicidios_count[year] ?? null). Include ALL years present in `data.series` (both complete and partial). Also derive `const availableYears` = the sorted list of those year numbers (descending) for the selector options.

(b) Add the year selector UI. Place a `<label>` + `<select id="year-select">` near the KeyStatsRow (Claude's discretion on exact position). Populate `<option>`s from `availableYears`, marking the default `year` as `selected`. Label text = `t.year_selector_label`. Each option value = the year string.

(c) Embed the year-data map as a JSON island (NOT interpolated into executable JS — memory: astro-script-no-expr-interpolation):
`<script type="application/json" id="year-data" set:html={JSON.stringify(yearData)}></script>`

(d) Add data hooks to the year-bound DOM so vanilla JS can find and rewrite it WITHOUT re-rendering components:
  - Rate StatCard value: wrap/target with `id="rate-value"`; its label (which contains the year) target with `id="rate-label"`.
  - FamilyBreakdownBars heading: the existing `<h2>` already shows the year — give it `id="family-heading"`.
  - FamilyBreakdownBars rows: the component renders `.family-bar-fill` (width) and `.family-bar-val` (number) per family in FAMILY_ORDER. Add `data-family={key}` attributes to the fill and val spans so JS can address each family. (Edit FamilyBreakdownBars.astro to emit `data-family` on `.family-bar-fill` and `.family-bar-val`; this is a shared edit — make it once, it affects both pages identically and is backward-compatible.)
  - Homicide section: give the heading `id="hom-heading"`, the rate span `id="hom-rate"`, the count span `id="hom-count"`, the empty-state `<p>` `id="hom-empty"`, the source `<p>` `id="hom-source"`.
  - Sparkline active-year highlight: the Sparkline is server-rendered with `activeYear={year}`. Updating its highlight in pure JS is awkward (it has no per-bar year hooks). Add `data-year={s.year}` to each `<rect>` in `Sparkline.astro` (shared, backward-compatible edit) so JS can toggle the active fill: on change, set every rect fill to `var(--muted)` then the matching `data-year` rect to `var(--primary)`.

(e) Add ONE vanilla `<script>` (no client:*, plain module script) at the end of each page that:
  1. Parses `#year-data` JSON.
  2. On `#year-select` `change`, reads the selected year and the matching record.
  3. Rewrites: `#rate-value` (Math.round + localized toLocaleString matching the page locale), `#rate-label`/`#family-heading`/`#hom-heading`/`#hom-source` (replace the year substring — recompute from the i18n template by passing the raw `t.rate_label`/`t.family_breakdown_heading` templates AND the localized homicide-heading/source literal strings via `data-*` attributes or a second JSON block, since `t.*` is server-only and must not be interpolated into the script).
  4. Updates family bars: for each family key, set `[data-family="key"].family-bar-val` text and the paired `.family-bar-fill` width % (recompute width as `Math.round(val/max*100)+'%'` using that year's own max across FAMILY_ORDER). Do NOT change bar color (level stays fixed — per CONTEXT).
  5. Updates homicide block: if homRate !== null show `#hom-rate`/`#hom-count` and hide `#hom-empty`; else show `#hom-empty` and hide the figure. Respect 0-as-valid.
  6. Updates Sparkline active rect via `data-year`.
For the year-bound TEMPLATE strings the script needs (rate_label, family_breakdown_heading, homicide heading text, homicide source text, "cases/case" or "casos/caso", unit text), emit them once into a second `<script type="application/json" id="year-i18n" set:html={JSON.stringify({...})}>` block built in frontmatter from the locale's `t.*` values + the page's existing homicide literals. This keeps ALL server data out of executable `<script>` bodies.

(f) Insert the charts section after the FamilyBreakdownBars section (Claude's discretion on exact slot; before composite index reads well). Import `CrimeFamilyCharts` and render:
`<CrimeFamilyCharts series={data.series} homicidios={data.featured_rates?.homicidios ?? {}} locale="en" heading={t.charts_heading} />` (ES: locale="es"). Add a small note paragraph using `t.chart_partial_note`. The charts are static and span ALL years — they do NOT react to the selector.

Do not modify the year-independent sections (ComparisonCallouts, LevelChip, composite index, ENUSC, rankings/comparables).
  </action>
  <verify>
    <automated>cd "site" &amp;&amp; npm run build 2>&amp;1 | Select-String -Pattern "error|fail" ; if (Test-Path "dist\commune") { Get-ChildItem -Recurse "dist\commune" -Filter index.html | Select-Object -First 1 | Get-Content | Select-String -Pattern "year-select|year-data|CrimeFamilyCharts|crime-family-charts|year-i18n" } else { Write-Output "NO_DIST" }</automated>
  </verify>
  <done>Both pages build with no errors; a built EN commune index.html contains the year-select element, the year-data + year-i18n JSON islands, and the charts section markup; the default year is present in static HTML (rate/family/homicide); no client:* directive appears on the commune pages. ES mirror builds identically.</done>
</task>

</tasks>

<verification>
Run ONE chained build+validate command (memory: onedrive-build-artifacts-desync — separate processes lose dist/):

```powershell
cd "site"; npx astro check 2>&1 | Select-String error; npm run build 2>&1 | Select-String -Pattern "error|fail"; npm run validate 2>&1 | Select-String -Pattern "FAIL|error|PASS" | Select-Object -Last 5
```

Manual spot checks (single session, do not relaunch between steps):
- A built EN `dist/commune/{slug}/index.html` and ES `dist/es/comuna/{slug}/index.html` each contain: `<select id="year-select"`, `<script type="application/json" id="year-data"`, `id="year-i18n"`, and the charts section with 8 mini-charts.
- The static HTML shows the default `latestCompleteYear` in the rate card, family heading, and homicide heading (SEO intact, no JS required).
- `grep` confirms NO `client:` directive on either commune page.
- Charts render polylines for all 7 families + homicide; partial years at 0.5 opacity; bilingual aria-labels present.
- Functional (preview server per memory serve-build-for-e2e-review: `npx astro preview --port 4321 --host`): changing the selector updates rate card, family bar values+widths, family heading year, homicide figure/count/heading/source, and Sparkline active bar — with no reload.
</verification>

<success_criteria>
- Year selector present and defaulting to latestCompleteYear, server-rendered, on both EN and ES commune pages.
- Selector is vanilla JS only — zero `client:*` islands (D-09 honored); all server→client data passed via `<script type="application/json">` blocks (no `{expr}` in executable scripts).
- Changing the year updates: rate StatCard, FamilyBreakdownBars (values + widths + heading year), homicide section (rate/count/heading/source year), Sparkline active-year highlight. Color/level stays fixed.
- Static SVG longitudinal charts: 7 family charts + 1 homicide-per-year chart, zero JS, partial years dimmed, bilingual labels, indexable.
- Year-independent sections unchanged (ComparisonCallouts, level color, composite 2024, ENUSC 2024, rankings/comparables).
- New i18n strings added to both EN_STRINGS and ES_STRINGS.
- `astro check`, `npm run build`, and `npm run validate` all pass.
</success_criteria>

<output>
Create `.planning/quick/260620-hrh-anio-selector-graficos-longitudinales-po/260620-hrh-SUMMARY.md` when done.
</output>
