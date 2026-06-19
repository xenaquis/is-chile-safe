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

## SPD — homicide reference snapshot

> **Status: reference snapshot — NOT wired to the displayed metric.**
> Deferred to Phase 18 (D-HOM metric switch). Stored in `data/snapshots/` once ingested.

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
[verify URL]

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
`https://www.ine.gob.cl/enusc` [verify URL — also published via
`https://www.seguridadpublica.gov.cl` — confirm canonical before publish]

**Measure semantics:**
Household victimization survey. Among other indicators, reports the proportion of
incidents reported to police (denuncia) by crime type — the empirical basis for the
three cifra-negra (underreporting) statements on the methodology page (F11).

**Vintage:** Cite the exact ENUSC edition year used for the on-page claims.
[verify edition]

**Used by:** `src/pages/methodology.astro` and `src/pages/es/metodologia.astro`
(underreporting H2 section). These pages MUST carry an inline citation link to the
ENUSC landing page (wired in plan 20-03).

**Licence:** Datos públicos del Estado de Chile.

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

## Cross-source notes

- **Population denominator for rates:** INE resident-population projections (2024).
  These are the denominators CEAD uses for `medida=2` (tasa/100k). Spot-checked
  against official INE projections — assumption A6 closed.
- **CUT code format:** Raw string digits without zero-padding throughout (matches CEAD catalog).
- **Partial-year guard:** Both CEAD and SPD VHC may include the current calendar year
  as an incomplete series. Pipeline applies a `latestCompleteYear` filter.
- **Never displayed:** Raw counts (`medida=1`) and individual `tipoVal` breakdowns
  are used internally for validation only; the site always displays rates per 100,000.
