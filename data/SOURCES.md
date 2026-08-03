# Data Sources — Chile Safety Map

Canonical provenance registry for every data class stored under `data/` and displayed on ischilesafe.com.

Last verified: 2026-06-18 (Phase 17 Wave 0 spikes S1–S5).

---

## CEAD — displayed incidence rates

**Full name:** Centro de Estudios y Análisis del Delito (CEAD), Ministerio del Interior y Seguridad Pública.

**Host:** `cead.minsegpublica.gob.cl`

**Primary endpoint (data):**
`POST https://cead.minsegpublica.gob.cl/wp-content/plugins/cead-estadisticas/get_estadisticas_delictuales.php`

**Catalog endpoint (grupo/subgrupo tree):**
`POST https://cead.minsegpublica.gob.cl/wp-content/plugins/cead-estadisticas/ajax_2.php`
with `seleccion=9` — returns all 22 grupos + 45 subgrupos regardless of `familia` param.

**Taxonomy provenance:**
The canonical familia/grupo/subgrupo tree is read at runtime from the catalog endpoint
above (`ajax_2.php seleccion=9`). No separate public taxonomy document was located during
Wave 0 research. The organizational authority for this classification scheme is the
Subsecretaría de Prevención del Delito (SPD) — see `## SPD — institutional authority`
below.

**Measure semantics:**
- `tipoVal=1,2` → **casos policiales** = denuncias (`1`) + detenciones flagrantes (`2`).
  These are strictly additive at the offence level (confirmed: 287+732=1,019 for
  homicide 2024). Never sum across measure types (double-counting risk).
- `tipoVal=3` → aprehendidos (persons arrested). Surfaces as a clearance/enforcement
  signal; do NOT fold into incidence counts.
- `medida=2` → **tasa por 100,000 habitantes** using INE resident-population
  denominators. This is the canonical metric displayed on the site.
- `medida=1` → raw count (used internally for cross-checks; never displayed in rankings).

**Taxonomy — familia encoding:**
The familia is encoded as the first digit of the grupo id:
`1xx` = vida, `2xx` = robos violentos, `3xx` = VIF, `4xx` = drogas,
`5xx` = armas, `6xx` = propiedad, `7xx` = incivilidades, `999` = otros.

**Key grupo mappings (Wave 0 confirmed):**

| Metric | grupos | Note |
|--------|--------|------|
| Homicidios | 101 | "Homicidios y femicidios" combined — cannot isolate via subgrupo (silently ignored); use SPD VHC instead |
| Lesiones | 103, 104, 105 | graves/gravísimas + menos graves + leves; do NOT include 106 (Amenazas) |
| VIF | 3xx | familia 3; VIF-context lesiones (subgrupos 30101/30102) belong HERE, not in lesiones |
| Drogas | 4xx / grupo 401 | **Ley 20.000** offences only (trafficking/possession for supply). Consumption = grupo 702 under incivilidades — a distinct category. Drug rates read low BY DESIGN. |
| Secuestro | — | **Absent from CEAD taxonomy entirely** (S1 spike fully enumerated all 7 familias). Source = Fiscalía (see below). |

**Coverage:** Nacional, regional, comunal. 346 comunas. 2005–present.

**Vintage:** Updated quarterly (approximate); pipeline refreshes on GitHub Actions cron.

**Licence:** Datos públicos del Estado de Chile; non-commercial re-use with attribution
required per CEAD site terms. Not an open-data licence (no explicit CC/OGL).

**Pipeline entry:** `pipeline/cead/client.py` — `POST get_estadisticas_delictuales.php`;
inter-batch sleep in orchestrator; validates 346-commune count after every scrape.

---

## Composite Crime Index — methodology

**Status:** Active (Phase 18). The composite index combines 7 winsorized per-100k metrics into a single
normalised score displayed in the ChoroplethLayer and ResultPanel.

**Formula:** Weighted sum of 7 winsorized metrics (reference year 2024):

```
composite_score = sum(w_i * normalized_i)  for i in {M1, M2, M3, M4, M5, M6, M7}
```

**Locked weight vector (C-02):**

| Metric key | Weight |
|------------|--------|
| spd_homicide_rate | 0.30 |
| cead_robos_rate | 0.20 |
| cead_vida_rate | 0.15 |
| cead_propiedad_rate | 0.12 |
| cead_vif_rate | 0.10 |
| cead_drogas_rate | 0.08 |
| cead_armas_rate | 0.05 |

**Normalization method:** Winsorized min-max. Each metric is first winsorized with
`scipy.stats.mstats.winsorize(limits=[0.01, 0.01])` to clip the top and bottom 1 % of values,
then rescaled to [0, 1] via min-max. This prevents extreme outliers (e.g., Sierra Gorda
43,369 per-100k) from collapsing the choropleth colour range.

**M1 — homicide (SPD VHC switch):** M1 (`spd_homicide_rate`) uses the SPD VHC dataset as the
index input rather than CEAD grupo 101 (see `## SPD — homicide reference snapshot` below).
SPD VHC provides authenticated per-commune homicide counts unavailable cleanly in CEAD.
CEAD grupo-101 `featured_rates.homicidios` is preserved unchanged for the per-family display
on commune pages (additive schema migration — no existing consumers broken).

**SII exposure caveat (M7):** The SII exposure metric (`sii_workers`) uses SII `PUB_COMU.xlsb`
`Numero de trabajadores dependientes informados` per commune (reference year 2024). The commune
is the firm's registered domicile / HQ, not the physical establishment. Multi-site firms
attribute all workers to HQ, concentrating counts in business-hub communes. Cap applied:
`sii_workers / ine_population > 5.0` → the metric falls back to the INE resident population as the denominator (5.0 is a fallback trigger threshold, not a multiplier).
Communes without SII data have `available_metrics` decremented by 1.

**Reference year:** 2024 (latest complete year for all 7 input metrics).

**Figure registry tokens (accent-free, required to exist verbatim for F13/F14):**
- F13: "SPD" + "homicidio" (SPD VHC homicide, M1 index input)
- F13: "Subsecretaria de Prevencion" + "homicidio" (institutional provenance)
- F14: "SII" + "trabajadores" (SII worker exposure metric)
- F14: "SII" + "exposicion" (SII daytime exposure proxy — see exposicion caveat above)

The SPD (Subsecretaria de Prevencion del Delito) administers the CEAD and the VHC homicide
database. The SII (Servicio de Impuestos Internos) tracks exposicion econonomica by commune.

---

## SPD — homicide reference snapshot

> **Status: Active (Phase 18). M1 index input = spd_homicide_rate.**
> Previously deferred; now wired to the composite index. Stored in `data/snapshots/` once ingested.

> **Institutional note (SC-07):** SPD (Subsecretaría de Prevención del Delito) is the
> parent body that administers CEAD and owns the crime-classification taxonomy. See
> `## SPD — institutional authority` for the full parent-body entry.

**Full name:** Subsecretaría de Prevención del Delito / Centro para la Prevención de
Homicidios — Base de Datos VHC (Víctimas de Homicidios Consumados).

**Host:** `prevenciondehomicidios.cl`

**Exact dataset URL:**
`https://prevenciondehomicidios.cl/wp-content/uploads/2026/03/Base_de_Datos_VHC_2018_2025.xlsx`
(~547 KB; sheet `Base de Datos`; data dictionary in sheet `Variables`.)

**Measure semantics:**
Victim-level microdata — one row per homicide victim. Homicide count per
comuna/year = COUNT of rows filtered by `COMUN_AGR` + `ID_ANO`. No pre-aggregated
count column; aggregate at ingest.

**Key columns:** `COMUN_AGR` (commune name string), `NOM_REG` (region name),
`ID_ANO` (year), `SEXO`, `EDAD_RECOD`, `ARMA_RECOD`, `CONTEXTO_RECOD`.

**Coverage:** 8,669 victims, 315 distinct comunas, years 2018–2025 (2025 partial).
~31 communes with zero homicides in 7 years simply absent (genuine zeros, not bucketed).

**Granularity:** COMUNA-LEVEL confirmed (Wave 0 S2).

**Caveat:** `COMUN_AGR` is a name string → requires name→CUT join via
`data/cead/meta/catalog.json`; apply name-normalization before join.
2025 is unconsolidated — apply partial-year guard.

**Vintage:** Dataset published March 2026; covers 2018–2025.

**Licence:** Public government data (Ministerio del Interior y Seguridad Pública).

**Why preferred over CEAD grupo 101:** CEAD grupo 101 = "Homicidios y femicidios"
combined; `subgrupo[]` filter is silently ignored by the data endpoint, so CEAD
cannot isolate homicide from femicide. SPD VHC is the authoritative consummated-
homicide figure (origin: Ministerio Público).

---

## SII — exposure proxy reference snapshot

> **Status: reference snapshot — NOT wired to the displayed metric.**
> Deferred to Phase 18 (composite index D-IDX). Stored in `data/snapshots/` once ingested.

**Full name:** Servicio de Impuestos Internos (SII) — Estadísticas de empresas por
comune (`PUB_COMU.xlsb`).

**Host / landing page:** `https://www.sii.cl/sobre_el_sii/estadisticas_de_empresas.html`

**Exact dataset URL:**
`https://www.sii.cl/sobre_el_sii/empresas/PUB_COMU.xlsb`
(~1.2 MB; `.xlsb` format → requires `pyxlsb`; sheet `Datos`, header on row index 4.)

> Do NOT use `/estadisticas/region/PUB_Reg_Com.xlsx` — that is a 2005–2015 archive.

**Measure semantics:**
Primary exposure proxy = `Número de trabajadores dependientes informados` per commune/year.
Secondary (preferred for daytime mass) = `Trabajadores ponderados por meses trabajados`
(FTE-weighted). Also includes `Número de empresas` and sales/gender splits.

**Coverage:** 6,940 rows, 347 communes in 2024 (346 + `Sin Información` bucket → drop).
Years 2005–2024. Full national coverage confirmed (Wave 0 S3).

**Caveat — domicile artifact:** The commune is the firm's registered domicile / casa
matriz, NOT the physical establishment location. Multi-site firms attribute all workers
to HQ → concentrates counts in business-HQ communes (Las Condes, Santiago, Providencia).
Document in methodology; consider capping or log-scaling.

**Vintage:** Updated October 2025 (covers through 2024).

**Licence:** Public government data (SII, Chile).

---

## Fiscalía — secuestro reference snapshot

> **Status: reference snapshot — NOT wired to the displayed metric.**
> Secuestro is absent from CEAD entirely (confirmed Wave 0 S1). Regional-level
> figure available; commune-level NOT confirmed. Deferred to Phase 18 / S5b spike.

**Full name:** Fiscalía de Chile (Ministerio Público) — Boletín Estadístico /
Informe de Fenómenos Criminales: Secuestro.

**Stats portal:** `https://www.fiscaliadechile.cl/persecucion-penal/estadisticas`

**Press downloads:** `http://www.fiscaliadechile.cl/Fiscalia/sala_prensa/descargas.do`

**Measure semantics:**
Count of secuestro cases prosecuted, reported by fiscalía regional.
National 2024 figure: 868 cases (+2.1% vs 850 in 2023; highest since 2014).
Top fiscalías: RM Sur, RM Centro Norte, Valparaíso.

**Granularity:** REGIONAL (fiscalía regional). Fiscalía regions ≠ administrative
regions (RM is split into multiple fiscalías → a mapping step is required).
COMMUNE-LEVEL not confirmed in this pass (PDFs; BED interactive app may export
finer data — not yet probed, see S5b).

**Vintage:** 2024 figures from published 2024 boletin estadístico.

**Licence:** Public government data (Ministerio Público, Chile).

---

## chilemapas — map geometry

**Full name:** chilemapas R package / geodata bundle (Chilean commune boundary
polygons derived from INE/SUBDERE/BCN cartography).

**Repository:** `https://github.com/pachadotdev/chilemapas`

**Licence:** GPL-3.0. Use requires attribution and source-code availability of
derivative works under GPL-3 terms.

**What is used:** Commune-level boundary polygons (346 comunas). Pre-processed to
TopoJSON at 87 KB for the interactive choropleth map.

**Coverage:** 346 comunas, nationwide. Geometry only — no statistical data.

**Attribution requirement (displayed in methodology pages):**
> Geometry: chilemapas (GPL-3), derived from INE/SUBDERE/BCN cartography.

**Pipeline entry:** `scripts/build-topojson.mjs` — four-way CUT integrity assertion
(missing/orphan/dup/Santiago vs index.json); srcCodeToCut normalizes zero-padded
`codigo_comuna` to CEAD CUT format.

**Important distinction:** chilemapas provides boundary geometry only. All crime
statistics overlaid on the map are sourced from CEAD (see above), not from chilemapas.

---

## INE — population denominator (per-100k + <10k rule)

**Full name:** Instituto Nacional de Estadísticas (INE) — Proyecciones de Población
(base Censo 2017).

**Official landing:**
`https://www.ine.gob.cl/estadisticas/sociales/demografia-y-vitales/proyecciones-de-poblacion`

**Measure semantics:**
Resident-population projection by commune, year 2024. Used as:
- (a) the per-100k denominator for every displayed rate (matches CEAD `medida=2`);
- (b) the gate for the <10,000-inhabitant low-population exclusion (DATA-04).

**Vintage:** INE Censo 2017 base + projection series; year 2024 slice.

**Fetch provenance:** `pipeline/scripts/fetch_ine_population.py` →
`data/ine/poblacion_comunal.json` (346 communes).

**SUPPLY-CHAIN CAVEAT:** The fetch script currently downloads from a **THIRD-PARTY
MIRROR**, not directly from INE:
`https://github.com/bastianolea/censo_proyecciones_poblacion` (community-maintained,
NOT an official INE distribution channel).

Risk: if the mirror is abandoned, unmaintained, or re-methodologized without notice,
denominators drift silently — affecting every displayed per-100k rate.

Mitigation (P20): CI step spot-checks ≥5 commune populations against the official
INE projection table after each fetch (implemented in plan 20-04). Future work:
switch fetch to pull directly from the official INE endpoint once a stable machine-
readable URL is confirmed.

**Licence:** Datos públicos del Estado de Chile (INE).

---

## ENUSC — underreporting / cifra negra

**Full name:** Encuesta Nacional Urbana de Seguridad Ciudadana (ENUSC).

**Publisher:** Subsecretaría de Prevención del Delito, Ministerio del Interior y
Seguridad Pública / INE (co-executed).

**Official landing:**
`https://www.ine.gob.cl/estadisticas/sociales/seguridad-publica-y-justicia`

**Measure semantics:**
Household victimization survey. Among other indicators, reports the proportion of
incidents reported to police (denuncia) by crime type — the empirical basis for the
three cifra-negra (underreporting) statements on the methodology page (F11).

**Vintage:** Resolved: intentionally generic — no specific ENUSC edition year is
claimed. The three underreporting bullets on the methodology pages cite the ENUSC
programme generically (property-crime, intra-family-violence, and homicide
reporting-rate patterns), not a dated statistic; no code path in this repository
ties those bullets to a specific survey year, and naming one without human
confirmation would replace an honest gap with an unverifiable claim. Distinct from
the dated SAE VHDV snapshot in the section below (`## INE ENUSC SAE — communal VHDV
victimization`), which is code-verified and carries its own explicit vintage.

**Used by:** `src/pages/methodology.astro` and `src/pages/es/metodologia.astro`
(underreporting H2 section). These pages MUST carry an inline citation link to the
ENUSC landing page (wired in plan 20-03).

**Licence:** Datos públicos del Estado de Chile.

---

## INE ENUSC SAE — communal VHDV victimization (experimental)

**Full name:** ENUSC 2024 — Victimización en Hogares por Delitos Violentos (VHDV), modelo de Estimación en Áreas Pequeñas (SAE).

**Publisher:** Instituto Nacional de Estadísticas (INE) — Estadísticas Experimentales: Seguridad Ciudadana.

**Official landing:**
`https://www.ine.gob.cl/estadisticas/estadisticas-experimentales/seguridad-ciudadana`

**File URL (sfvrsn may rotate on republish):**
`https://www.ine.gob.cl/docs/default-source/estadisticas-experimentales-seguridad-ciudadana/cuadros-estadisticos/2024/tabulados-sae--enusc-2024-vhdv.xlsx?sfvrsn=671c099f_4`

**Measure semantics:**
Proportion of households reporting at least one violent crime (VHDV). Value is 0–1 (proportion), NOT per-100k. Do not rescale. Communal SAE estimates cover 136 of 346 comunas; the remaining 210 have no estimate.

**INE status:** Estadística experimental, "etapa inicial de madurez" (INE's own label).

**Vintage:** Reference year 2024; first published 2026-01-21.

**sha256 of ingested file:** `ad9503826fd21590eca7cf37629872df09f3115ad0c6d80dfe5cedcb63c3d4ba`

**Used by:** `data/snapshots/enusc_vhdv.json` → `data/cead/comunas/{CUT}.json` (enusc_vhdv field) → `site/src/pages/commune/[slug].astro` section 6c (F16). See also `data/snapshots/ATTRIBUTION.md`.

**Licence:** Datos públicos del Estado de Chile (INE terms).

**Distinct from:** `## ENUSC — underreporting / cifra negra` (F11 above) which references the ENUSC national survey for underreporting statistics, not the SAE communal estimates.

---

## SPD — institutional authority (parent of CEAD + taxonomy)

**Full name:** Subsecretaría de Prevención del Delito (SPD), Ministerio del Interior
y Seguridad Pública.

**Portal:** `https://www.seguridadpublica.gov.cl`

**Role:** Parent body that administers CEAD and publishes/owns the crime-classification
scheme (grupo/subgrupo taxonomy). Chain of authority for both the CEAD taxonomy and
the VHC homicide dataset.

**Taxonomy provenance:** The canonical familia/grupo/subgrupo tree is read at runtime
from the CEAD catalog endpoint (`ajax_2.php seleccion=9`). No separate public taxonomy
document was located during Wave 0 research. SPD is the organizational authority for
this classification.

**Licence:** Datos públicos del Estado de Chile.

---

## Methodology parameters (editorial decisions)

These are editorial decisions made by the site — not external sources. Documented here
so every displayed rule has a named registry entry with its rationale.

- **Trend window:** 3 years (year N vs N-3). Editorial.
- **Trend threshold:** ±5% to label rising / falling / stable; chosen to avoid flagging
  statistically marginal change. Editorial — no external standard claimed.
- **Low-population exclusion:** Communes with fewer than 10,000 inhabitants are excluded
  from rankings (DATA-04). Editorial; approximates the lower bound INE uses for small-
  area reporting. Communes below threshold are **RETAINED** in the data and flagged —
  never silently dropped.
- **National aggregate figure:** **UNWEIGHTED** mean of non-low-population commune rates
  ("typical-commune" statistic). Distinct from the population-weighted means used in the
  national and regional time-series (F5). The methodology pages and FAQ must not describe
  this figure as "population-weighted" (MC-01/MC-07 — corrected in plan 19).

---

## News feeds — qualitative incident layer (Google News RSS)

**Role:** Qualitative layer of recent incidents extracted from Chilean news media,
sourced via Google News RSS search plus a small set of direct-outlet RSS feeds.
Not a statistical source — complements the quantitative CEAD layer.

**Ingestion mechanism:**
Incidents are primarily sourced via Google News RSS search queries against
`https://news.google.com/rss/search` (`pipeline/news/feeds.py`, `google_news_url()`),
driven by a named query registry
(`_GOOGLE_NEWS_QUERIES`, e.g. `GoogleNews-Nacional`, `GoogleNews-Antofagasta`), not
fixed per-outlet feeds. `pipeline/news/gnews_decoder.py` resolves each Google News
redirect URL back to the real publishing outlet's article URL before full-text fetch.
A handful of direct-outlet RSS feeds (BioBioChile, Cooperativa, LaTercera, LaCuarta)
are also ingested alongside the Google News search feeds.

**Outlet attribution:**
For Google News items, the true outlet name is extracted per item from the RSS
`<source>` tag (`resolve_outlet()` in `pipeline/news/feeds.py`), falling back to the
literal label "Google News" when that tag is empty or absent — readers may
occasionally see "Google News" cited as the source for that honest reason. For
direct-outlet feeds, the feed name itself is used as the outlet.

**Classification:**
Items are classified (crime family, severity) and a commune *name* is proposed by
`ibm-granite/granite-4.1-8b` via OpenRouter (`pipeline/news/classifier.py`), the
default model for this milestone (spike 008: 100% commune accuracy, ~6x cheaper,
~2.5x faster than the prior default). DeepSeek v4-flash is retained as a selectable
fallback provider only (`NEWS_PROVIDER=deepseek`).

**Geolocation:**
The LLM never emits a CUT code. Every LLM-proposed commune name is resolved through
`pipeline/news/resolver.py`, a deterministic name→(cut, slug) dict lookup built from
`data/cead/meta/index.json` — no network calls, no LLM. This is the pipeline's
anti-hallucination control: `resolve_cut()` returns `None` for any name outside the
closed 346-commune set (or an unresolved ambiguity), and the incident is dropped
rather than guessed.

**Full-text research archive (internal, not reader-displayed):**
A daily-cron R2-backed archive (bucket `ischilesafe`) stores full incident text, APA
citations, and a provenance ledger for audit/research purposes
(`pipeline/tests/test_archive_r2.py`). This corpus is internal and is never surfaced
to site readers; it is not part of the reader-facing qualitative incident layer.

**Storage:**
`data/incidents/current.json` (rolling window) plus `data/incidents/archive/`
(monthly archives).

**Attribution requirement (displayed on news pages):**
Every news pin cites its source outlet name and links to the original article URL.
No incident is displayed without a source link.

**Measure semantics:**
Qualitative, not statistical. Incident counts are NOT comparable to CEAD per-100k rates.
Coverage is subject to Google News' indexing of Chilean press coverage and the
direct-outlet feeds' own editorial selection.

**Vintage:** Refreshed via GitHub Actions cron (daily).

**Licence:** News item attribution via inline source links; no reproduction of article bodies.

---

## Cross-source notes

- **Population denominator for rates:** INE resident-population projections (2024).
  These are the denominators CEAD uses for `medida=2` (tasa/100k). Spot-checked
  against official INE projections — assumption A6 closed.
- **CUT code format:** Raw string digits without zero-padding throughout (matches CEAD catalog).
- **Partial-year guard:** Both CEAD and SPD VHC may include the current calendar year
  as an incomplete series. Pipeline applies a `latestCompleteYear` filter.
- **Never displayed:** Raw counts (`medida=1`) and individual `tipoVal` breakdowns
  are used internally for validation only; the site always displays rates per 100,000.
