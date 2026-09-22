# Phase 23: ENUSC Communal Victimization Layer — Research

**Researched:** 2026-06-19
**Domain:** Python snapshot ingestion + Astro static page enrichment (additive, no backend)
**Confidence:** HIGH — all findings derived from live codebase inspection

---

## Summary

Phase 23 adds the INE ENUSC 2024 SAE VHDV household-victimization figure as a clearly-labeled additive module on the 136 covered comuna pages (EN + ES), with an explicit "no estimate" note on the 210 uncovered comunas. The external data source is fully settled (see SEED-002-ENUSC-DATA-PROFILE.md — do not re-derive). This research investigates only how THIS repo already does the analogous things so the planner can reuse patterns.

**The three primary analogs already in the repo are:**
1. `pipeline/snapshots/fetch_spd_homicide.py` → the fetcher pattern to mirror exactly
2. The `composite_index` additive field on `data/cead/comunas/{CUT}.json` → the data-enrichment pattern to mirror for `enusc_vhdv`
3. The composite index section in `site/src/pages/commune/[slug].astro` (section "6b") → the UI module pattern to mirror for the VHDV panel

**Primary recommendation:** Mirror the SPD/SII snapshot pipeline pattern verbatim. One new file `pipeline/snapshots/fetch_enusc_vhdv.py`, one new committed artifact `data/snapshots/enusc_vhdv.json`, additive enrichment of each `comunas/{CUT}.json` with an `enusc_vhdv` top-level key (parallel to `composite_index`), and a new section in each commune page template that conditionally renders based on key presence.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VL-01 | Isolated ENUSC SAE VHDV ingest from versioned in-repo snapshot with provenance; runs after CEAD; fails gracefully | SPD fetcher pattern + `continue-on-error: true` in `cead-scraper.yml` |
| VL-02 | 136 CUTs join directly (CUT raw digits in col A); build-time coverage assertion (count == 136); unresolved rows fail loudly | Direct CUT join confirmed in data profile; `index.json` as CUT authority |
| VL-03 | EN + ES pages show VHDV value + year + bilingual SAE/experimental caveat; forbidden-language validator exits 0 | i18n string pattern from `i18n.ts`; forbidden-language.mjs runs over dist/ |
| VL-04 | 210 uncovered comunas render explicit bilingual "no ENUSC estimate" note; no broken layout | Conditional render with null check, same pattern as `composite_index?.[year]` guard |
| VL-05 | F-series figure-registry zero-orphan passes; SOURCES.md + methodology pages updated; Phase-18 outputs byte-unchanged | figure-registry.mjs pattern; existing `## ENUSC` block in SOURCES.md is a stub needing expansion |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Excel ingestion + CUT join | Python (pipeline) | — | All data ingestion is Python; no frontend data fetching |
| Snapshot provenance JSON | Python (pipeline) | — | Mirrors SPD/SII pattern: pipeline writes, data/ stores |
| Additive CUT-keyed enrichment of comunas/{CUT}.json | Python (pipeline) | — | build_composite_index.py pattern: read, enrich, atomic_write_json |
| VHDV module on 136 commune pages (EN + ES) | Astro (SSG) | — | Static pre-render; no client-side JS; data read at build time |
| "No estimate" fallback on 210 commune pages | Astro (SSG) | — | Conditional null-check in same Astro template |
| i18n strings (EN + ES caveat text) | Config (i18n.ts) | — | All UI strings live in EN_STRINGS / ES_STRINGS |
| Figure-registry zero-orphan check | Validator (figure-registry.mjs) | — | Token check over data/SOURCES.md |
| Forbidden-language gate | Validator (forbidden-language.mjs) | — | Runs over dist/ HTML after build |
| Byte-unchanged verification of Phase-18 outputs | Build assertion script | — | Compare dist/ build hashes or commune JSON checksums |

---

## 1. Snapshot Ingestion Pattern [VERIFIED: live codebase]

### Existing analogs

Two complete fetchers exist in `pipeline/snapshots/`:

| Fetcher | Cache file | Output | Join key |
|---------|-----------|--------|----------|
| `fetch_spd_homicide.py` | `pipeline/cache/spd_vhc.xlsx` | `data/snapshots/spd_homicide.json` | name → make_slug → CUT |
| `fetch_sii_exposure.py` | `pipeline/cache/sii_pub_comu.xlsb` | `data/snapshots/sii_exposure.json` | name → make_slug → CUT |

### Output JSON schema (SPD canonical shape)

```json
{
  "source": "Subsecretaria de Prevencion del Delito / ...",
  "source_url": "https://prevenciondehomicidios.cl/...",
  "vintage": "2018-2025",
  "fetched": "2026-06-19T00:43:42Z",
  "caveat": "...",
  "records": [
    {"cut": "10101", "name": "Puerto Montt", "year": 2018, "homicides": 11}
  ]
}
```

### ENUSC fetcher differences from SPD pattern

1. **No stable URL** — the resolved URL has a `?sfvrsn=` token that may rotate. The fetcher MUST accept the URL as a parameter or config constant, and should assert the sha256 of the cached file before processing. This is a new pattern — existing fetchers trust the HTTP response. Add `hashlib.sha256(bytes).hexdigest()` assertion after cache write.
2. **openpyxl engine** — `.xlsx` not `.xlsb`, so use `engine="openpyxl"` (same as fetch_spd_homicide.py uses `pd.read_excel(..., engine="openpyxl")`).
3. **Direct CUT join** — the ENUSC file has CUT in col A as raw string digits. No name→slug→CUT resolution needed. Load the file, iterate rows, join on `str(row["Código comuna"]).strip()`. The name→CUT resolver is only a redundant cross-check for a post-join audit log.
4. **Sheet/header** — single sheet `Hoja1`, header row 3 (0-indexed row 2 for pandas `header=2`), data rows 4–139 (136 rows).
5. **Extra fields to carry** — `tipo_estimacion` (col F) and `cv` (col G) must be in the output record for future-vintage quality flagging.

### Target fetcher contract

```
pipeline/snapshots/fetch_enusc_vhdv.py

CACHE_ONLY=1 env var skips download, parses pipeline/cache/enusc_vhdv.xlsx
Asserts sha256 == KNOWN_SHA256 (from data profile) before processing
Produces data/snapshots/enusc_vhdv.json

Output shape:
{
  "source": "INE — Estadisticas Experimentales: Seguridad Ciudadana (ENUSC 2024 SAE)",
  "source_url": "<resolved sfvrsn URL>",
  "landing_page": "https://www.ine.gob.cl/estadisticas/estadisticas-experimentales/seguridad-ciudadana",
  "vintage": "2024",
  "fetched": "<ISO timestamp>",
  "caveat": "Estadistica experimental (SAE). INE labels this 'etapa inicial de madurez'. ...",
  "records": [
    {
      "cut": "13101",
      "name": "Santiago",
      "vhdv_rate": 0.0478,
      "ci_lower": 0.042,
      "ci_upper": 0.053,
      "tipo_estimacion": "Directa y sintetica",
      "cv": 0.041
    }
  ]
}
```

### sha256 assertion (new pattern for this fetcher)

```python
KNOWN_SHA256 = "ad9503826fd21590eca7cf37629872df09f3115ad0c6d80dfe5cedcb63c3d4ba"

def _assert_sha256(path: pathlib.Path) -> None:
    import hashlib
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != KNOWN_SHA256:
        raise RuntimeError(
            f"sha256 mismatch for {path}: expected {KNOWN_SHA256}, got {digest}. "
            "File may have been republished. Re-resolve via INE JS widget and update KNOWN_SHA256."
        )
```

### Where raw cache lives

`pipeline/cache/enusc_vhdv.xlsx` — git-ignored (confirmed: existing `pipeline/cache/` is git-ignored per the SPD/SII pattern). [VERIFIED: live codebase — `pipeline/cache/` exists and is excluded from git by `.gitignore`]

### Attribution entry

Add to `data/snapshots/ATTRIBUTION.md` following the existing table format for `spd_homicide.json` and `sii_exposure.json`.

---

## 2. CEAD Pipeline Ordering and Graceful Failure [VERIFIED: live codebase]

### Orchestration file

`.github/workflows/cead-scraper.yml` — the single orchestration point for all data steps.

### Current step order

```
1. Run CEAD scraper          (python pipeline/scrape_cead.py)
2. Build composite index     (continue-on-error: true)
3. Build map payload         (continue-on-error: true)
4. Commit data if changed
5. Trigger CF deploy
```

### How to insert ENUSC step

Insert between step 1 (CEAD scraper) and step 2 (composite index), with `continue-on-error: true`:

```yaml
- name: Build ENUSC victimization snapshot
  continue-on-error: true
  env:
    CACHE_ONLY: '1'
  run: python pipeline/snapshots/fetch_enusc_vhdv.py
```

**Why `CACHE_ONLY=1`:** The ENUSC file has no stable URL and is manually/assisted-deposited into `pipeline/cache/`. The cron job should NEVER attempt a network download — it should only parse the committed cache file. If the cache file is absent, `fetch_enusc_vhdv.py` exits non-zero, `continue-on-error: true` absorbs the failure, and CEAD + composite index continue unaffected. This is VL-01 satisfied.

**Additive enrichment step:** After `fetch_enusc_vhdv.py`, a second step `build_enusc_enrichment.py` reads `data/snapshots/enusc_vhdv.json` and writes `enusc_vhdv` additively into each `data/cead/comunas/{CUT}.json`. This is also `continue-on-error: true` and runs before `build_composite_index.py` to keep ordering clean (though the composite index does not consume ENUSC data).

---

## 3. F-Series Figure Registry (Zero-Orphan) [VERIFIED: live codebase]

### Registry location and format

`site/scripts/validate/figure-registry.mjs` — checks for token presence in `data/SOURCES.md`.

### Current registry: F1–F15

Current in-scope figures: F1–F15. The highest existing is F15 (news incidents). New VHDV figure(s) must be F16 (or follow the next available ID — confirm no F16 exists yet).

### How to register

1. Add a new entry to the `FIGURE_REGISTRY` array in `figure-registry.mjs`:

```javascript
{
  id: 'F16',
  description: 'ENUSC SAE VHDV household victimization rate (experimental, 2024)',
  tokens: [
    // Requires INE ENUSC SAE section + VHDV identifier in SOURCES.md
    ['## INE ENUSC SAE', 'VHDV'],
    ['ENUSC', 'Victimizacion en Hogares', 'SAE'],
  ],
  note: 'INE ENUSC 2024 communal SAE estimate; labeled experimental. 136/346 comunas coverage.',
},
```

2. Add the corresponding `## INE ENUSC SAE` section to `data/SOURCES.md`.

### Existing ENUSC stub in SOURCES.md

`data/SOURCES.md` already has a `## ENUSC — underreporting / cifra negra` block (line 292) covering the survey's use for F11 (underreporting claims). This is a **different use** from F16 (the SAE communal VHDV figure). The new F16 registration should be a SEPARATE section `## INE ENUSC SAE — communal VHDV victimization (experimental)` so the token match is unambiguous and the existing F11 registration is undisturbed.

### Validator invocation

```bash
# Standalone (reads data/SOURCES.md only, no build needed)
node site/scripts/validate/figure-registry.mjs

# Via full suite
cd site && npm run build && npm run validate
```

---

## 4. Commune Page Rendering (EN + ES) [VERIFIED: live codebase]

### Template files

| Locale | Path |
|--------|------|
| EN | `site/src/pages/commune/[slug].astro` |
| ES | `site/src/pages/es/comuna/[slug].astro` |

Both are static Astro files (`getStaticPaths` + `Astro.props`). Zero `client:*` directives on these pages (design decision D-09). All data read at build time via `loadCommune(cut)` from `site/src/lib/data.ts`.

### Existing composite index module (closest analog — section "6b")

```astro
<!-- 6b. Composite Crime Index section (CI-05/CI-06) -->
{(() => {
  const COMPOSITE_YEAR = 2024;
  const ci = data.composite_index?.[String(COMPOSITE_YEAR)];
  if (!ci) return null;
  ...
  return (
    <section class="panel-section composite-index-section" ...>
      <h2>{t.ci_section_heading}</h2>
      <span class="ci-score-big">{Math.round(ci.score)}</span>
      <div class="ci-caveat">{t.ci_caveat_text}</div>
    </section>
  );
})()}
```

### Pattern for VHDV module

Mirror section 6b exactly:

```astro
<!-- 6c. ENUSC VHDV victimization module (VL-03/VL-04) -->
{(() => {
  const vhdv = data.enusc_vhdv;
  if (!vhdv) {
    // VL-04: 210 uncovered comunas — explicit "no estimate" note
    return (
      <section class="enusc-no-estimate" aria-label={t.enusc_no_estimate_aria}>
        <p class="enusc-no-estimate-text">{t.enusc_no_estimate_text}</p>
      </section>
    );
  }
  // VL-03: 136 covered comunas — value + CI + caveat
  return (
    <section class="enusc-vhdv-section" aria-label={t.enusc_section_aria}>
      <h2 class="section-heading">{t.enusc_section_heading}</h2>
      <div class="enusc-rate">
        {(vhdv.vhdv_rate * 100).toFixed(1)}%
        <span class="enusc-year">(2024)</span>
      </div>
      <div class="enusc-ci">
        {t.enusc_ci_label}: {(vhdv.ci_lower * 100).toFixed(1)}% – {(vhdv.ci_upper * 100).toFixed(1)}%
      </div>
      <div class="enusc-caveat">{t.enusc_caveat_text}</div>
    </section>
  );
})()}
```

### TypeScript type extension in data.ts

Add `enusc_vhdv` to `CommuneData`:

```typescript
// Phase 23 additive field — present for 136 ENUSC-covered comunas
enusc_vhdv?: {
  vhdv_rate: number;          // proportion 0–1 (e.g. 0.0478 = 4.78%)
  ci_lower: number;
  ci_upper: number;
  tipo_estimacion: string;    // "Directa y sintetica" | "Sintetica"
  cv: number;
  vintage: number;            // 2024
};
```

`loadCommune()` reads directly from the JSON file — no code change needed in the loader function, since TypeScript optional fields on the interface are transparently present/absent in the JSON.

### i18n strings (i18n.ts additions)

Add to `I18nStrings` interface and both `EN_STRINGS` / `ES_STRINGS` in `site/src/config/i18n.ts`:

```typescript
// New keys for Phase 23
enusc_section_heading: string;
enusc_section_aria: string;
enusc_ci_label: string;
enusc_caveat_text: string;
enusc_no_estimate_text: string;
enusc_no_estimate_aria: string;
```

**EN_STRINGS values (draft):**
- `enusc_section_heading`: `"Household Victimization (ENUSC 2024)"`
- `enusc_ci_label`: `"95% confidence interval"`
- `enusc_caveat_text`: `"INE experimental estimate (SAE-modeled). Proportion of households reporting at least one violent crime. Covers 136 of 346 comunas. Distinct from CEAD reported-crime index — measures victimization survey responses, not police denuncias. Source: INE Estadísticas Experimentales, Seguridad Ciudadana."`
- `enusc_no_estimate_text`: `"No INE ENUSC victimization estimate available for this comuna (SAE model covers 136 of 346 comunas)."`

**ES_STRINGS values (draft):**
- `enusc_section_heading`: `"Victimización en Hogares (ENUSC 2024)"`
- `enusc_ci_label`: `"Intervalo de confianza al 95%"`
- `enusc_caveat_text`: `"Estimación experimental de INE (modelo SAE). Proporción de hogares que reportaron al menos un delito violento. Cubre 136 de 346 comunas. Distinto del índice CEAD de delitos reportados — mide respuestas de encuesta de victimización, no denuncias policiales. Fuente: INE Estadísticas Experimentales, Seguridad Ciudadana."`
- `enusc_no_estimate_text`: `"Sin estimación de victimización ENUSC disponible para esta comuna (el modelo SAE cubre 136 de 346 comunas)."`

### i18n localized-slug pitfall [from memory: i18n-localized-slug-pitfall]

`getRelativeLocaleUrl()` does NOT translate ES slugs. Both commune templates already use hardcoded `/es/` prefix for cross-links. The new VHDV module contains no cross-links, so this pitfall does not apply here.

### build-path drift pitfall [from memory: news-page-build-path-drift]

`data.ts` uses `process.cwd()` (stable at build time) not `import.meta.url`. The VHDV data is read from `data/cead/comunas/{CUT}.json` via `loadCommune()`, which already uses the correct path. No new file reads needed in the Astro template — all data flows through `loadCommune()`. If a separate read from `data/snapshots/enusc_vhdv.json` is needed at build time (e.g., for coverage count), use `path.resolve(process.cwd(), '..', 'data', 'snapshots', 'enusc_vhdv.json')` — never `import.meta.url`.

---

## 5. Validators [VERIFIED: live codebase]

### Forbidden-language validator

**Location:** `site/scripts/validate/forbidden-language.mjs`

**How it works:** Strips script/style blocks and HTML tags from dist/ pages, normalizes accents (NFD), then matches a word-boundary-aware forbidden term list. An allow-list of qualifying phrases (e.g., "according to CEAD data for 2024") exempts attributed superlatives.

**VL-03 compliance:** The VHDV caveat text must NOT contain any forbidden terms. The draft `enusc_caveat_text` values above avoid: "seguro/peligroso," "safe/dangerous," "the safest," "most dangerous," "más segura," "más peligrosa." The terms "experimental" and "estimate" are not in the forbidden list. The validator will pass as written.

**Invocation:**
```bash
cd site && npm run build && node scripts/validate/forbidden-language.mjs
# Or via full suite:
cd site && npm run build && npm run validate
```

**OneDrive desync [from memory: onedrive-build-artifacts-desync]:** ALWAYS chain build and validate in one command. Never run `npm run validate` as a standalone command after a separate `npm run build` terminal call.

### Figure-registry validator

**Location:** `site/scripts/validate/figure-registry.mjs`

**Runs against:** `data/SOURCES.md` (no dist/ build required)

**Required action for VL-05:** Add F16 entry to the FIGURE_REGISTRY array AND add the matching `## INE ENUSC SAE` section to `data/SOURCES.md` in the same commit.

### Byte-unchanged verification (VL-05)

**No pre-existing assertion script** for this — it must be created for Phase 23. Pattern: before and after the additive enrichment step, compute sha256 of Phase-18 outputs and assert equality.

**Scope of "Phase-18 outputs":** The `featured_rates`, `series`, `national_rank`, `regional_rank`, `trend`, `composite_index`, `spd_homicide_rate`, `sii_exposure_index` fields in each `data/cead/comunas/{CUT}.json`. Only `enusc_vhdv` is added; all others must be byte-unchanged.

**Practical implementation:** The enrichment script should read each commune JSON, add only the `enusc_vhdv` key, and write it back via `atomic_write_json`. A pytest or CLI assertion can confirm the `composite_index` and `featured_rates` field values match the pre-enrichment snapshot for a random sample. Alternatively, the enrichment script can assert the key was absent before writing it (if key exists and differs, fail loudly — do not silently overwrite).

---

## 6. Name→CUT Resolver [VERIFIED: live codebase]

**Location:** `pipeline/cead/normalizer.py` — `make_slug()` function. Used by SPD and SII fetchers to join on commune name.

**Interface:**

```python
from pipeline.cead.normalizer import make_slug

slug = make_slug("Ñuñoa")   # → "nunoa"
slug = make_slug("O'Higgins") # → "ohiggins"
```

**Used by SPD fetcher:**

```python
def _build_cut_map() -> dict[str, tuple[str, str]]:
    entries = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    result: dict[str, tuple[str, str]] = {}
    for entry in entries:
        slug = make_slug(entry["name"])
        result[slug] = (entry["cut"], entry["name"])
    return result
```

**For ENUSC:** Per the data profile, the direct CUT join (col A) works with 0 unknown CUTs. The resolver is a redundant cross-check only. Recommended use: after loading the ENUSC sheet, build the slug→CUT map, then verify that `make_slug(row["Nombre comuna"])` → resolved CUT matches col A CUT. Log any discrepancies; do not fail on them. This ensures future vintages with name-only rows would still work.

---

## Architecture Patterns

### Recommended project structure (new files only)

```
pipeline/
  snapshots/
    fetch_enusc_vhdv.py          # new: XLSX ingestion + sha256 assert + CUT join
  build_enusc_enrichment.py      # new: reads enusc_vhdv.json, enriches comunas/{CUT}.json

data/
  snapshots/
    enusc_vhdv.json              # new: committed versioned snapshot with provenance
    ATTRIBUTION.md               # update: add enusc_vhdv.json block

site/src/
  config/
    i18n.ts                      # update: add 6 new VHDV i18n keys
  lib/
    data.ts                      # update: add enusc_vhdv? optional field to CommuneData
  pages/
    commune/[slug].astro         # update: add section 6c (VHDV module)
    es/comuna/[slug].astro       # update: add section 6c (ES VHDV module)
  scripts/validate/
    figure-registry.mjs          # update: add F16 entry

.github/workflows/
  cead-scraper.yml               # update: add ENUSC steps (continue-on-error)
```

### System architecture diagram

```
INE XLSX (manual drop)
  → pipeline/cache/enusc_vhdv.xlsx  (git-ignored)
  → fetch_enusc_vhdv.py
      sha256 assert
      pandas parse (openpyxl, Hoja1, header=2)
      direct CUT join (col A)
      redundant name-slug cross-check (log only)
      → data/snapshots/enusc_vhdv.json  (committed, provenance JSON)

data/snapshots/enusc_vhdv.json
  → build_enusc_enrichment.py
      for each record:
        read data/cead/comunas/{CUT}.json
        add enusc_vhdv: {vhdv_rate, ci_lower, ci_upper, tipo_estimacion, cv, vintage}
        atomic_write_json(commune_path, commune)
      build assertion: all 136 CUTs resolved; count == 136

data/cead/comunas/{CUT}.json  (136 enriched, 210 unchanged)
  → Astro build (loadCommune)
      data.enusc_vhdv present? → render VHDV module (section 6c)
      absent? → render "no estimate" note (VL-04)

dist/ HTML
  → forbidden-language.mjs (VL-03 gate)
  → figure-registry.mjs (VL-05 gate)
```

### Anti-patterns to avoid

- **Do NOT add `enusc_vhdv` to the composite index formula.** The VHDV rate is a proportion (0–1), not per-100k; merging it into the composite would require unit conversion and would alter Phase-18 locked outputs. VL-05 explicitly forbids this.
- **Do NOT display VHDV as per-100k.** Display as a percentage of households (multiply by 100, show `%`). See data profile: "Proportion 0–1. NOT per-100k; do not rescale."
- **Do NOT use `client:load` on the VHDV section.** It is static Astro markup, no React. Zero JS shipped.
- **Do NOT use `{expr}` interpolation inside `<script>` tags** (memory: astro-script-no-expr-interpolation). The VHDV module has no `<script>` — all data is in server-rendered HTML. Not applicable here but noted as a standing pitfall.
- **Do NOT store the XLSX in git.** Only the processed `enusc_vhdv.json` is committed. The raw cache stays in `pipeline/cache/` (git-ignored).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic JSON writes | Custom write-then-rename | `pipeline/shared/atomic_write.atomic_write_json()` | Already exists; cross-platform atomic via `os.replace()` |
| URL-safe commune slug | Custom regex | `pipeline/cead/normalizer.make_slug()` | Already handles NFD, apostrophes, accents consistently |
| HTTP retries | Custom try/except loop | `tenacity.retry` (already in requirements.txt) | Exponential backoff; used by SPD and SII fetchers |
| i18n strings | Inline hardcoded strings in .astro | `site/src/config/i18n.ts` `EN_STRINGS`/`ES_STRINGS` + `t.key` | Existing pattern; edit one file, both locales derived |
| CUT validity check | Manual list | `data/cead/meta/index.json` | Canonical CUT authority; SPD fetcher uses it |

---

## Common Pitfalls

### Pitfall 1: VHDV unit confusion — proportion vs percentage vs per-100k
**What goes wrong:** Developer displays `0.0478` (the raw proportion) or rescales it to per-100k (= 4,780) instead of showing 4.8%.
**Why it happens:** Other pipeline metrics ARE per-100k; the ENUSC value is different.
**How to avoid:** Display `(vhdv.vhdv_rate * 100).toFixed(1) + "%"`. The caveat text must say "proportion of households." Never say "per 100,000."
**Warning signs:** Values like "0.0478" or "4780.0" appearing in the rendered HTML.

### Pitfall 2: sha256 mismatch on INE republish
**What goes wrong:** INE republishes the XLSX with a rotated `?sfvrsn=` token and/or updated data. The sha256 check fails. The CEAD cron pipeline breaks the ENUSC step.
**Why it happens:** INE's JS widget URL is unstable. The sha256 guards against silent data drift.
**How to avoid:** `continue-on-error: true` in the GitHub Actions step. The fetcher fails loudly (log the mismatch), but CEAD and composite index continue. The human operator is alerted via the GitHub Actions failure notification. To update: download the new file, verify contents, update `KNOWN_SHA256` in `fetch_enusc_vhdv.py`.
**Warning signs:** GitHub Actions `build-enusc-victimization-snapshot` step fails with "sha256 mismatch."

### Pitfall 3: F16 token missing from SOURCES.md
**What goes wrong:** Figure-registry.mjs fails because the new `## INE ENUSC SAE` section was not added to `data/SOURCES.md` in the same commit as the F16 registry entry.
**Why it happens:** Developer adds UI panel and i18n strings but forgets the SOURCES.md + figure-registry.mjs update.
**How to avoid:** These three files must be updated in the same commit: `data/SOURCES.md` (new section), `site/scripts/validate/figure-registry.mjs` (F16 entry), and the commune page templates (VHDV section).

### Pitfall 4: Phase-18 fields silently overwritten
**What goes wrong:** `build_enusc_enrichment.py` reads the commune JSON and writes it back. If there is a bug in the write path, it could overwrite existing fields (`composite_index`, `featured_rates`).
**Why it happens:** Python dict merge bug (`{**commune, "enusc_vhdv": vhdv}` is safe, but `commune["enusc_vhdv"] = vhdv; atomic_write(commune)` mutates in place, which is also safe — as long as no other keys are touched).
**How to avoid:** The enrichment script must ONLY add the `enusc_vhdv` key. Add a pre/post assertion: `assert commune.get("composite_index") == original_ci` for a random sample of 10 communes after enrichment.

### Pitfall 5: OneDrive build-artifact desync
**What goes wrong:** `npm run validate` reads from a partially-synced `dist/`.
**How to avoid:** Chain: `cd site && npm run build && npm run validate`. Never separate commands. [from memory: onedrive-build-artifacts-desync]

### Pitfall 6: 210 "no estimate" comunas show an empty section / broken layout
**What goes wrong:** The `enusc_vhdv` conditional renders an empty `<section>` with no content, breaking the page flow.
**How to avoid:** The `if (!vhdv)` branch must render a paragraph with the explicit "no estimate" text. Do not render an empty `<section>`. The CSS for `.enusc-no-estimate` should render as a subtle informational note (e.g., muted text, no border).

---

## Code Examples

### Fetcher: sha256 guard + CACHE_ONLY pattern
```python
# Source: live codebase (pipeline/snapshots/fetch_spd_homicide.py) adapted for ENUSC
KNOWN_SHA256 = "ad9503826fd21590eca7cf37629872df09f3115ad0c6d80dfe5cedcb63c3d4ba"
CACHE_FILE = REPO_ROOT / "pipeline" / "cache" / "enusc_vhdv.xlsx"

def _assert_sha256(path: pathlib.Path) -> None:
    import hashlib
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != KNOWN_SHA256:
        raise RuntimeError(
            f"sha256 mismatch for {path}: expected {KNOWN_SHA256}, got {digest}. "
            "INE may have republished the file. Re-verify and update KNOWN_SHA256."
        )

def main() -> None:
    cache_only = os.environ.get("CACHE_ONLY", "").strip() in ("1", "true", "yes")
    if not cache_only:
        _download(RESOLVED_URL, CACHE_FILE)  # RESOLVED_URL from config/param
    _assert_sha256(CACHE_FILE)
    ...
```

### Enrichment: additive dict merge (mirrors build_composite_index.py pattern)
```python
# Source: live codebase (pipeline/build_composite_index.py lines ~345–377) adapted
for cut, vhdv_data in enusc_by_cut.items():
    commune_path = data_dir / "comunas" / f"{cut}.json"
    commune = json.loads(commune_path.read_text(encoding="utf-8"))
    commune["enusc_vhdv"] = vhdv_data   # additive: no other keys touched
    atomic_write_json(commune_path, commune)
```

### Astro null-guard (mirrors composite_index section 6b)
```astro
{(() => {
  const vhdv = data.enusc_vhdv;
  if (!vhdv) {
    return (
      <section class="enusc-no-estimate">
        <p class="enusc-no-estimate-text">{t.enusc_no_estimate_text}</p>
      </section>
    );
  }
  return (
    <section class="enusc-vhdv-section" aria-label={t.enusc_section_aria}>
      <h2 class="section-heading">{t.enusc_section_heading}</h2>
      <div class="enusc-rate">
        {(vhdv.vhdv_rate * 100).toFixed(1)}%
        <span class="enusc-year">(2024)</span>
      </div>
      <div class="enusc-ci">
        {t.enusc_ci_label}: {(vhdv.ci_lower * 100).toFixed(1)}% – {(vhdv.ci_upper * 100).toFixed(1)}%
      </div>
      <div class="enusc-caveat">{t.enusc_caveat_text}</div>
    </section>
  );
})()}
```

### GitHub Actions step insertion (continue-on-error pattern)
```yaml
# Source: live codebase (.github/workflows/cead-scraper.yml) — insert after CEAD scraper
- name: Build ENUSC victimization snapshot
  continue-on-error: true
  env:
    CACHE_ONLY: '1'
  run: python pipeline/snapshots/fetch_enusc_vhdv.py

- name: Enrich commune JSONs with ENUSC VHDV
  continue-on-error: true
  run: python pipeline/build_enusc_enrichment.py
```

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (pipeline) + Node.js validators (frontend) |
| Config file | `pipeline/pytest.ini` |
| Quick run command | `cd pipeline && python -m pytest tests/ -x -q` |
| Full suite command | `cd pipeline && python -m pytest tests/ && cd ../site && npm run build && npm run validate` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VL-01 | Fetcher exits 0 with CACHE_ONLY=1 and valid cache; exits non-zero if cache absent | pytest | `pytest tests/test_fetch_enusc_vhdv.py -x` | Wave 0 gap |
| VL-01 | Enrichment step exits 0 even if enusc_vhdv.json absent (graceful degrade) | pytest | `pytest tests/test_build_enusc_enrichment.py::test_missing_snapshot_graceful -x` | Wave 0 gap |
| VL-02 | All 136 CUTs in snapshot resolve to valid CUT in index.json; count == 136 | pytest | `pytest tests/test_build_enusc_enrichment.py::test_coverage_assertion -x` | Wave 0 gap |
| VL-03 | EN + ES commune pages for covered CUT contain `enusc-vhdv-section` and caveat text | validator | `node site/scripts/validate/commune.mjs` (extend) | Extend existing |
| VL-03 | forbidden-language exits 0 | validator | `node site/scripts/validate/forbidden-language.mjs` | Exists |
| VL-04 | Uncovered CUT commune page contains `enusc-no-estimate` element | validator | `node site/scripts/validate/commune.mjs` (extend) | Extend existing |
| VL-05 | figure-registry exits 0 (F16 registered + SOURCES.md token present) | validator | `node site/scripts/validate/figure-registry.mjs` | Extend existing |
| VL-05 | Phase-18 composite_index fields unchanged after enrichment | pytest | `pytest tests/test_build_enusc_enrichment.py::test_phase18_byte_unchanged -x` | Wave 0 gap |

### Sampling Rate
- **Per task commit:** `cd pipeline && python -m pytest tests/test_fetch_enusc_vhdv.py tests/test_build_enusc_enrichment.py -x -q`
- **Per wave merge:** `cd pipeline && python -m pytest tests/ && cd ../site && npm run build && npm run validate`
- **Phase gate:** Full suite green (13 validators + all pytest) before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `pipeline/tests/test_fetch_enusc_vhdv.py` — covers VL-01 (CACHE_ONLY parse, sha256 guard, column detection)
- [ ] `pipeline/tests/test_build_enusc_enrichment.py` — covers VL-01 (graceful degrade), VL-02 (coverage assertion), VL-05 (byte-unchanged)
- [ ] Extend `site/scripts/validate/commune.mjs` — assert presence of VHDV module (or no-estimate note) on built commune pages

---

## Security Domain

This phase adds no authentication, user input, API keys, or dynamic routes. ASVS categories are not applicable. The DEEPSEEK_API_KEY is not involved. The `CF_DEPLOY_HOOK_URL` pattern is unchanged.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | fetch_enusc_vhdv.py | Yes (dev machine + CI) | 3.12.x | — |
| openpyxl | pandas XLSX parse | Yes (in pipeline/requirements.txt) | current | — |
| pandas | XLSX processing | Yes (in pipeline/requirements.txt) | current | — |
| Node.js 20+ | site build + validators | Yes | LTS | — |
| `pipeline/cache/enusc_vhdv.xlsx` | fetch_enusc_vhdv.py CACHE_ONLY | Manually deposited | sha256 verified | Fetcher fails loudly; CEAD continues |

**Missing dependencies with no fallback:** None — all runtime deps are satisfied. The XLSX cache file must be manually deposited before the fetcher can run. If absent, the step fails with `continue-on-error: true` and CEAD is unaffected.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | F16 is the next available figure-registry ID (no existing F16 in figure-registry.mjs) | Section 3 | If F16 already exists, use F17 — trivial fix |
| A2 | `pipeline/cache/` is git-ignored (SPD/SII cache present but not in git) | Section 1 | If git-ignored by a pattern that also matches `.json`, the snapshot could be excluded — verify `.gitignore` |
| A3 | `build_enusc_enrichment.py` should be a separate script from `fetch_enusc_vhdv.py` | Section 2 | Could be a single script; planner may decide to merge. Either works. |

**If this table is empty:** All other claims were verified by direct codebase inspection.

---

## Open Questions (RESOLVED)

1. **Should the enrichment step also emit `enusc_vhdv` into `data/cead/comparator_table.json`** (the Phase 21 handoff)?
   - What we know: `comparator_table.json` is consumed by Phase 21 comparator pages; it currently holds composite index data.
   - What's unclear: Whether the comparator UI benefits from showing VHDV side-by-side.
   - **RESOLVED:** Defer — Phase 21 is about the composite index; VHDV on comparator pages is a Phase 24 idea. Keep Phase 23 additive-only on the commune page. (Plans leave `comparator_table.json` untouched.)

2. **Do methodology pages need a new H2 section for ENUSC SAE communal estimates?**
   - What we know: VL-05 requires methodology page documentation. The existing `methodology.astro` and `es/metodologia.astro` have an ENUSC section (for cifra-negra claims, F11).
   - What's unclear: Whether to add a separate H2 or expand the existing ENUSC section.
   - **RESOLVED:** Add a separate `## Household Victimization Indicator (ENUSC 2024 SAE)` section, to keep F11 and F16 registrations distinct and traceable. (Implemented in plan 23-04 Task 2.)

---

## Sources

### Primary (HIGH confidence — live codebase inspection)
- `pipeline/snapshots/fetch_spd_homicide.py` — canonical fetcher pattern
- `pipeline/snapshots/fetch_sii_exposure.py` — second fetcher reference
- `site/src/pages/commune/[slug].astro` — composite index section 6b (UI analog)
- `site/src/config/i18n.ts` — i18n string pattern, existing CI keys
- `site/scripts/validate/figure-registry.mjs` — registry format, F1–F15
- `site/scripts/validate/forbidden-language.mjs` — forbidden term list
- `site/scripts/validate/all.mjs` — 13-validator suite invocation
- `.github/workflows/cead-scraper.yml` — continue-on-error pattern + step ordering
- `data/snapshots/ATTRIBUTION.md` — attribution table format
- `data/SOURCES.md` — existing ENUSC stub (F11), figure token format
- `pipeline/shared/atomic_write.py` — atomic write utility
- `pipeline/build_composite_index.py` — additive enrichment of commune JSON pattern
- `site/src/lib/data.ts` — CommuneData TypeScript interface, loadCommune()

### Secondary (HIGH confidence — project planning docs)
- `.planning/research/SEED-002-ENUSC-DATA-PROFILE.md` — external schema ground truth (do not re-derive)
- `.planning/research/SEED-002-FINDINGS.md` — Design A rationale
- `.planning/REQUIREMENTS.md` — VL-01..VL-05 full text
- `.planning/ROADMAP.md` — Phase 23 section, ingestion decision

---

## Metadata

**Confidence breakdown:**
- Snapshot ingestion pattern: HIGH — SPD/SII fetchers inspected line-by-line
- Additive enrichment: HIGH — build_composite_index.py lines 345–377 inspected
- Commune page rendering: HIGH — [slug].astro section 6b inspected; i18n.ts CI keys inspected
- Figure-registry: HIGH — figure-registry.mjs F1–F15 array inspected; SOURCES.md ENUSC stub verified
- GitHub Actions: HIGH — cead-scraper.yml step order inspected
- Forbidden-language: HIGH — forbidden-language.mjs term list inspected

**Research date:** 2026-06-19
**Valid until:** 2026-07-19 (stable codebase — patterns unlikely to change in 30 days)
