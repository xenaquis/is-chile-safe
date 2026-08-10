/**
 * LayerRail.tsx — MAPV2 replacement for EntryPointsRail (>=481px).
 *
 * The three <details> disclosures (Año / Tipo de delito / Modo) become ONE
 * always-visible row: the layer chips (LayerField) plus the year select.
 * The current state no longer needs a prose summary to be readable — the
 * active chip IS the state — but StateSummary is kept as an aria-live
 * region for screen readers (spec §6), rendered by MapTopbar as a sibling.
 *
 * data-role="filter-entry" is preserved on the rail (map-pages validator
 * picks it as the filter entry point). No document-scoped listeners (F-49):
 * there is nothing to open or close anymore.
 */

import { LayerField } from './FilterFields';
import { YearField } from './FilterFields';
import { EN_STRINGS, ES_STRINGS } from '../../config/i18n';
import { layerLabel, MODE_LABELS, type LayerDef } from '../../lib/mapFilterDefs';
import { useEffect, useState } from 'react';

interface Props {
  lang: 'en' | 'es';
  year: number;
  onYearChange: (year: number) => void;
  mode: 'composite' | 'family';
  crimeFamily: string | null;
  onLayerChange: (def: LayerDef) => void;
}

export function LayerRail({ lang, year, onYearChange, mode, crimeFamily, onLayerChange }: Props) {
  // MPX-C7: year_label duplicated map_entry_year — read the shared i18n
  // source (already used by FilterSheet) instead of a second copy in
  // mapV2Strings.ts. i18n.ts itself is NOT edited.
  const strings = lang === 'es' ? ES_STRINGS : EN_STRINGS;
  return (
    <div data-role="filter-entry" className="layer-rail">
      <div className="layer-rail-chips">
        <LayerField lang={lang} mode={mode} crimeFamily={crimeFamily} onLayerChange={onLayerChange} />
      </div>
      <div className="layer-rail-year">
        <span className="layer-rail-year-label" aria-hidden="true">{strings.map_entry_year}</span>
        <YearField lang={lang} year={year} onYearChange={onYearChange} />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// StateSummary — persistent selection summary, ported from EntryPointsRail
// (aria-live per spec §6). Rendered by MapTopbar as a SIBLING of the rail so
// the announcement survives the rail being display:none at <=480px.
// ---------------------------------------------------------------------------

type Band = 'wide' | 'mid' | 'narrow';

function getBand(): Band {
  if (typeof window === 'undefined') return 'wide';
  const w = window.innerWidth;
  if (w >= 640) return 'wide';
  if (w >= 481) return 'mid';
  return 'narrow';
}

export function StateSummary({ lang, year, crimeFamily, mode }: { lang: 'en' | 'es'; year: number; crimeFamily: string | null; mode: 'composite' | 'family' }) {
  const [band, setBand] = useState<Band>(getBand());
  useEffect(() => {
    function onResize() { setBand(getBand()); }
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);
  // MPX-B7/C6: in composite mode the layer chip already says "Crime Index" /
  // "Índice Delictivo" — prefixing mLabel duplicates that. Omit the mode
  // prefix in composite mode at every band; keep it in family mode at
  // `wide` only. `narrow` uses the short CHIP_DEFS label so the string
  // never truncates (F-46).
  const fLabel = layerLabel(lang, mode, crimeFamily);
  const mLabel = MODE_LABELS[lang][mode];
  const text = band === 'wide'
    ? (mode === 'composite' ? fLabel : mLabel + ' · ' + fLabel) + ' · ' + year
    : fLabel + ' · ' + year;
  return (
    <div className="entry-state-summary" aria-live="polite">{text}</div>
  );
}
