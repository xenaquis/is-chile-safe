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

## Cross-source notes

- **Population denominator for rates:** INE resident-population projections (2024).
  These are the denominators CEAD uses for `medida=2` (tasa/100k). Spot-checked
  against official INE projections — assumption A6 closed.
- **CUT code format:** Raw string digits without zero-padding throughout (matches CEAD catalog).
- **Partial-year guard:** Both CEAD and SPD VHC may include the current calendar year
  as an incomplete series. Pipeline applies a `latestCompleteYear` filter.
- **Never displayed:** Raw counts (`medida=1`) and individual `tipoVal` breakdowns
  are used internally for validation only; the site always displays rates per 100,000.
