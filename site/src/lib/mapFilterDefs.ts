/**
 * mapFilterDefs.ts — shared crime-type and year option data for the map
 * control shell (Phase 30). Ported verbatim from FiltersRow.tsx:20-52 so
 * every later component imports from ONE shared module.
 *
 * MAPV2: adds LAYER_DEFS — the unified "layer" model that merges the old
 * Modo (composite|family) + Tipo de delito dimensions into one visible list.
 * CHIP_DEFS is kept verbatim as the data source so labels/order never drift.
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

// M-04: single source of truth for the mode-toggle option labels. Retained for
// StateSummary (aria-live) even though the visible Modo control is gone.
export const MODE_LABELS = {
  es: { composite: 'Índice', family: 'Por delito' },
  en: { composite: 'Index', family: 'By crime' },
} as const;

// ---------------------------------------------------------------------------
// MAPV2: unified layer list.
// One flat list where the composite index and each crime family are sibling
// options. Selecting a layer implies the mode — the separate Modo control
// disappears from the UI, but MapIsland's state machine (mode + crimeFamily +
// crimeFamilyIndex + crimeIsHomicide) is preserved untouched.
// ---------------------------------------------------------------------------

export interface LayerDef {
  /** Stable id: 'ci', 'total', or the family key ('vida', …, 'homicidios'). */
  id: string;
  mode: 'composite' | 'family';
  /** Value passed to onFamilyChange(key, index). */
  key: string | null;
  familyIndex: number | null;
  labelEs: string;
  labelEn: string;
  featured: boolean;
}

export const LAYER_DEFS: LayerDef[] = [
  { id: 'ci',    mode: 'composite', key: null, familyIndex: null, labelEs: 'Índice general', labelEn: 'Overall index', featured: true },
  { id: 'total', mode: 'family',    key: null, familyIndex: null, labelEs: 'Tasa total',     labelEn: 'Total rate',    featured: false },
  ...CHIP_DEFS.filter((c) => c.key !== null).map((c) => ({
    id: c.key as string,
    mode: 'family' as const,
    key: c.key,
    familyIndex: c.familyIndex,
    labelEs: c.labelEs,
    labelEn: c.labelEn,
    featured: c.featured,
  })),
];

/** Which LAYER_DEFS id is active for a given (mode, crimeFamily) state pair. */
export function activeLayerId(mode: 'composite' | 'family', crimeFamily: string | null): string {
  if (mode === 'composite') return 'ci';
  return crimeFamily ?? 'total';
}

export function layerLabel(lang: 'en' | 'es', mode: 'composite' | 'family', crimeFamily: string | null): string {
  const def = LAYER_DEFS.find((l) => l.id === activeLayerId(mode, crimeFamily));
  if (!def) return '';
  return lang === 'es' ? def.labelEs : def.labelEn;
}

// Available years: current year → 2005, newest first.
const CEAD_EARLIEST_YEAR = 2005;
export const AVAILABLE_YEARS: number[] = Array.from(
  { length: new Date().getFullYear() - CEAD_EARLIEST_YEAR + 1 },
  (_, i) => new Date().getFullYear() - i
);
