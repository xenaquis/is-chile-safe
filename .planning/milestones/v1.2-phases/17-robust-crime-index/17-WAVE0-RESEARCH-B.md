# Phase 17 — Wave 0 Spike Results (S2 + S3 + S5)

**Run:** 2026-06-18, local Chilean egress (all three gov hosts reachable; the
cloud sandbox would 403). Scripts: `pipeline/experiments/probe_spd_homicide.py`,
`probe_xlsx_sources.py`, `probe_coverage.py`, `probe_sii_links.py`,
`probe_sii_comu.py`. Raw output in `pipeline/cache/*.txt`.

Continuation of `17-WAVE0-RESEARCH-A.md` (S1 + S4).

---

## S2 — SPD homicide source ✅ RESOLVED (comuna-level)

**Source:** Subsecretaría de Prevención del Delito / Centro para la Prevención
de Homicidios (`prevenciondehomicidios.cl`). Consolidated official VHC figure
(Ministerio Público origin).

- **Dataset:** `https://prevenciondehomicidios.cl/wp-content/uploads/2026/03/Base_de_Datos_VHC_2018_2025.xlsx`
  (~547 KB, sheet `Base de Datos` + `Variables` data dictionary).
- **Granularity: COMUNA-LEVEL ✓** — this kills the S2 risk (feared SPD was
  regional-only). Victim-level microdata: **one row per homicide victim**.
- Columns: `SEXO, EDAD_RECOD, CONDENAS, NACION_RECOD, LUG_AGR_RECOD,
  ARMA_RECOD, CONTEXTO_RECOD, COMUN_AGR (comuna), NOM_REG (región), DIA, MES2,
  ID_ANO (year), HORA_RECOD`, plus precomputed `Tasa Nacional/Regional`.
- **Coverage:** 8,669 victims, years **2018–2025**, 315 distinct comunas
  (the ~31 missing communes simply had zero homicides in 7 years — no "otras"
  grouping label exists; granularity is genuine, not bucketed).
- National victims/yr: 2018=845, 2019=924, 2020=1115, 2021=906, 2022=1330,
  2023=1249, **2024=1209**, 2025=1091 (partial). 2024≈1209 matches the known
  ~1,200 consummated-homicide figure → dataset validated.
- **Homicide count per comuna/year = COUNT of rows** filtered by `COMUN_AGR` +
  `ID_ANO`. (No pre-aggregated count column; aggregate at ingest.)

**Caveats for Wave 1/4:**
- `COMUN_AGR` / `NOM_REG` are NAME strings → need name→CUT join (commune
  catalog in `data/cead/meta/catalog.json`; mind the name-normalization pitfall).
- 2025 is partial/unconsolidated — apply the same partial-year guard as CEAD.
- This replaces CEAD grupo-101 for homicide (D-HOM). Bonus: CEAD grupo 101 =
  "Homicidios **y femicidios**" and `subgrupo[]` is ignored, so CEAD cannot
  isolate homicide anyway — SPD is strictly better.

---

## S3 — Exposure proxy (SII empresas + trabajadores) ✅ RESOLVED (2005–2024)

**Source:** SII "Estadísticas de empresas por comuna"
(`https://www.sii.cl/sobre_el_sii/estadisticas_de_empresas.html`).

- **Ingest target:** `https://www.sii.cl/sobre_el_sii/empresas/PUB_COMU.xlsb`
  (~1.2 MB, `.xlsb` → needs `pyxlsb`; sheet `Datos`, header on row index 4).
  (The older `/estadisticas/region/PUB_Reg_Com.xlsx` is a 2005–2015 archive —
  do NOT use it; PUB_COMU.xlsb is the current 2005–2024 vintage, updated
  Oct 2025.)
- **Coverage:** 6,940 rows, **2005–2024**, **347 comunas** in 2024 (346 + a
  `Sin Información` bucket to drop) → full national coverage ✓.
- Relevant columns:
  - `Comuna del domicilio o casa matriz` (name)
  - `Número de empresas`
  - **`Número de trabajadores dependientes informados`** ← primary exposure proxy
  - `Trabajadores ponderados por meses trabajados` (FTE-weighted — better proxy)
  - `Ventas anuales en UF`, gender/honorarios splits also present.

**Proxy choice + caveat (feeds D-IDX methodology):**
- Recommended denominator signal = **trabajadores dependientes (or FTE-weighted)**
  per comuna as the daytime/economic-activity mass, blended with resident
  population (formula TBD in Wave 2; must stay explainable per D-IDX).
- ⚠️ **Domicile artifact:** the comuna is the firm's *registered domicile / casa
  matriz*, not the establishment where work physically happens. Multi-site firms
  attribute all workers to HQ → concentrates counts in business-HQ communes
  (Las Condes, Santiago, Providencia). This partly *aligns* with daytime
  concentration but overstates pure-HQ communes. Document in methodology;
  consider capping/log-scaling. (A cleaner establishment-level source would be
  ideal but none is national+free; SII is the pragmatic choice.)

---

## S5 — Secuestro source ⚠️ PARTIAL (regional only so far)

Opened because S1 found **secuestro is absent from CEAD's entire taxonomy**
(7 familias / 22 grupos / 45 subgrupos). It is tracked by the **Ministerio
Público / Fiscalía**.

- **Source:** Fiscalía de Chile — Boletín Estadístico / Informe de Fenómenos
  Criminales: Secuestro. Stats portal:
  `https://www.fiscaliadechile.cl/persecucion-penal/estadisticas`;
  press downloads: `http://www.fiscaliadechile.cl/Fiscalia/sala_prensa/descargas.do`.
- **Figures:** 868 secuestros nationally in 2024 (+2.1% vs 850 in 2023; highest
  since 2014). Reported by **fiscalía regional** (top: RM Sur, RM Centro Norte,
  Valparaíso).
- **Granularity: REGIONAL (fiscalía regional), comuna-level NOT confirmed.**
  Fiscalía regions ≠ administrative regions exactly (RM split into multiple
  fiscalías) → a mapping step is needed even for regional use.
- **No clean downloadable comuna dataset found** in this pass (reports are PDFs;
  the BED interactive app may export finer data — not yet probed).

**Decision needed (D-TAX):** secuestro cannot drive a 346-comuna choropleth from
any source found. Options:
1. Keep secuestro as a **region/national-only** metric (display at region level,
   absent on the commune map) — analogous to SPD fallback handling.
2. Source comuna detail from the Fiscalía BED interactive app (needs a new
   spike S5b to test export/API).
3. **Demote secuestro** from the headline 7-metric taxonomy to a
   region-level callout.
→ Recommend **option 1** for v1 (region-level secuestro), revisit S5b later.

---

## Wave 0 — consolidated status

| Spike | Status | Source / key value |
|-------|--------|--------------------|
| S1 lesiones | ✅ | CEAD grupos 103+104+105 |
| S1 secuestros (in CEAD) | ⛔→S5 | absent from CEAD taxonomy |
| S4 tipoVal | ✅ | additive; 1=denuncias 2=detenciones 3=aprehendidos; casos pol.=1,2 |
| S2 SPD homicide | ✅ | VHC xlsx, comuna-level, 2018–2025 |
| S3 exposure proxy | ✅ | SII PUB_COMU.xlsb, comuna, 2005–2024, trabajadores dependientes |
| S5 secuestro source | ⚠️ partial | Fiscalía, regional only; comuna TBD (S5b) |

**Wave 0 is effectively COMPLETE** for the index build. Only open item: S5
comuna-granularity for secuestro — non-blocking if v1 ships secuestro at region
level (recommended). Ready to plan **Wave 1 (pipeline)**:
- extend CEAD client: lesiones (103/104/105), 3 measures (`medida=1`,
  tipoVal 1 / 2 / 3 + casos policiales) normalized per offence (D-AGG);
- new SPD module: download VHC xlsx → aggregate homicides per comuna/year;
- new SII module: download `PUB_COMU.xlsb` (pyxlsb) → empresas + trabajadores
  per comuna/year as the exposure table; commit a static snapshot to `data/`;
- Fiscalía secuestro (region-level) ingest or deferral per D-TAX decision.

Deps added to `pipeline/requirements.txt`: `pyxlsb`, `pandas`.
