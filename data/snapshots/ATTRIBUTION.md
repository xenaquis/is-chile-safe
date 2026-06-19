# Data Snapshots — Attribution

> All snapshots in this directory are **REFERENCE-ONLY** and are NOT wired to
> any displayed metric on the site. They are committed as reproducible research
> artifacts for Phase 18 composite index work.

---

## spd_homicide.json

| Field        | Value |
|--------------|-------|
| Source       | Subsecretaria de Prevencion del Delito / Centro para la Prevencion de Homicidios |
| Full URL     | https://prevenciondehomicidios.cl/wp-content/uploads/2026/03/Base_de_Datos_VHC_2018_2025.xlsx |
| Dataset name | Base de Datos VHC 2018–2025 (Victimas de Homicidio Consumado) |
| Licence      | Datos Abiertos Gobierno de Chile |
| Vintage      | 2018–2025 (2025 partial/unconsolidated) |
| Granularity  | Victim-level microdata aggregated to commune + year |
| Script       | pipeline/snapshots/fetch_spd_homicide.py |
| Note         | REFERENCE-ONLY — not wired to any displayed metric. Intended as the authoritative homicide source for Phase 18 composite index (replaces CEAD grupo-101 which conflates homicides+femicides and cannot be isolated by subgrupo). |

---

## sii_exposure.json

| Field        | Value |
|--------------|-------|
| Source       | Servicio de Impuestos Internos (SII) — Estadisticas de empresas por comuna |
| Full URL     | https://www.sii.cl/sobre_el_sii/empresas/PUB_COMU.xlsb |
| Dataset name | PUB_COMU.xlsb — Estadisticas de empresas por comuna |
| Licence      | Datos Abiertos Gobierno de Chile |
| Vintage      | 2005–2024 (updated Oct 2025) |
| Granularity  | Commune + year; 346 real communes + 1 "Sin Informacion" bucket (dropped) |
| Script       | pipeline/snapshots/fetch_sii_exposure.py |
| Note         | REFERENCE-ONLY — not wired to any displayed metric. Intended as the daytime economic-activity exposure proxy for Phase 18 composite index. Caveat: the commune is the firm's registered domicile/casa matriz, not the physical establishment — multi-site firms attribute all workers to HQ, concentrating counts in business-district communes. |

---

## enusc_vhdv.json

| Field        | Value |
|--------------|-------|
| Source       | INE — Estadisticas Experimentales: Seguridad Ciudadana |
| Full URL     | https://www.ine.gob.cl/docs/default-source/estadisticas-experimentales-seguridad-ciudadana/cuadros-estadisticos/2024/tabulados-sae--enusc-2024-vhdv.xlsx?sfvrsn=671c099f_4 |
| Dataset name | ENUSC 2024 — VHDV (Victimizacion en Hogares por Delitos Violentos), modelo SAE |
| Licence      | Datos publicos del Estado de Chile (INE terms) |
| Vintage      | 2024 (SAE first published 2026-01-21) |
| Granularity  | 136 comunas (SAE communal model); 210 comunas have no estimate |
| Script       | pipeline/snapshots/fetch_enusc_vhdv.py |
| sha256       | ad9503826fd21590eca7cf37629872df09f3115ad0c6d80dfe5cedcb63c3d4ba |
| Note         | **WIRED to commune pages (section 6c)** — distinct from other snapshots in this directory which are REFERENCE-ONLY. The vhdv_rate is a proportion 0-1 (NOT per-100k). INE labels this "estadistica experimental, etapa inicial de madurez." The sfvrsn URL parameter may rotate on INE republish; acquisition is manual via INE JS widget. |

---

## fiscalia_secuestro.json

| Field        | Value |
|--------------|-------|
| Source       | Fiscalia de Chile — Boletin Estadistico / Informe de Fenomenos Criminales: Secuestro |
| Full URL     | https://www.fiscaliadechile.cl/persecucion-penal/estadisticas |
| Dataset name | Boletin Estadistico de la Fiscalia (PDF reports) |
| Licence      | Public institutional statistics (Chile) — no explicit open-data licence; cite source |
| Vintage      | 2023–2024 (national totals confirmed; per-region breakdown partial) |
| Granularity  | Fiscalia-regional and national (commune-level NOT available from PDF sources) |
| Script       | pipeline/snapshots/fetch_fiscalia_secuestro.py |
| Note         | REFERENCE-ONLY — not wired to any displayed metric. Static figures embedded from Wave 0 S5 spike (2026-06-18). No machine-readable download found; data extracted manually from PDFs. Fiscalia regions do NOT map 1:1 to administrative regions (RM split into RM Sur, RM Centro Norte, RM Oriente etc.). Commune-level secuestro data deferred to S5b / Phase 18. |
