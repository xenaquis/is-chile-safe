/**
 * mapFilterDefs.ts — shared crime-type and year option data for the map
 * control shell (Phase 30). Ported verbatim from FiltersRow.tsx:20-52 so
 * every later component (EntryPointsRail, FilterSheet, FilterFields) imports
 * from ONE shared module instead of re-deriving this data per component.
 * FiltersRow.tsx is deleted in Wave 4 — this module is its data survivor.
 *
 * Catalog family_keys order (data/cead/meta/catalog.json):
 *   0=vida, 1=robos_violentos, 2=vif, 3=drogas, 4=armas, 5=propiedad, 6=incivilidades
 */

import { FAMILY_DEFS_EN, FAMILY_DEFS_ES } from './familyDefs';

export { FAMILY_DEFS_EN, FAMILY_DEFS_ES };

// Display order per UI-SPEC: Todos, vida, propiedad, robos_violentos,
// incivilidades, vif, drogas, armas, homicidios. 9 entries.
export const CHIP_DEFS = [
  { key: null,              familyIndex: null, labelEs: 'Todos',                      labelEn: 'All types',         featured: false },
  { key: 'vida',            familyIndex: 0,    labelEs: 'Vida y convivencia',          labelEn: 'Life crimes',       featured: true  },
  { key: 'propiedad',       familyIndex: 5,    labelEs: 'Propiedad',                   labelEn: 'Property crimes',   featured: true  },
  { key: 'robos_violentos', familyIndex: 1,    labelEs: 'Robos violentos',             labelEn: 'Violent robbery',   featured: false },
  { key: 'incivilidades',   familyIndex: 6,    labelEs: 'Incivilidades',               labelEn: 'Disorder',          featured: false },
  { key: 'vif',             familyIndex: 2,    labelEs: 'VIF',                         labelEn: 'Domestic violence', featured: false },
  { key: 'drogas',          familyIndex: 3,    labelEs: 'Drogas',                      labelEn: 'Drug crimes',       featured: false },
  { key: 'armas',           familyIndex: 4,    labelEs: 'Armas',                       labelEn: 'Weapons',           featured: false },
  // 9th chip: homicide as a first-class layer (D-04/HOM-01). A null index here
  // signals MapIsland to use the independent homicide scale
  // (buildStyleMapFromHomicide), NOT by_family. key === 'homicidios' is the ONLY
  // thing distinguishing it from "Todos" — never key options on the index alone.
  { key: 'homicidios',     familyIndex: null, labelEs: 'Homicidios',                  labelEn: 'Homicide',          featured: true  },
];

export type ChipDef = (typeof CHIP_DEFS)[number];

// M-04: single source of truth for the mode-toggle option labels, consumed by
// both ModeField (FilterFields.tsx) and EntryPointsRail's modeLabel() so the
// selected option and the persistent state summary can never show two
// different names for the same state again. Base-SHA labels restored.
export const MODE_LABELS = {
  es: { composite: 'Índice', family: 'Por delito' },
  en: { composite: 'Index', family: 'By crime' },
} as const;

// Available years: current year → 2005, newest first.
const CEAD_EARLIEST_YEAR = 2005;
export const AVAILABLE_YEARS: number[] = Array.from(
  { length: new Date().getFullYear() - CEAD_EARLIEST_YEAR + 1 },
  (_, i) => new Date().getFullYear() - i
);
