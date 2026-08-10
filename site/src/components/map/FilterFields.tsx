/**
 * FilterFields.tsx — pure, wrapper-less field renderers for the map control
 * shell. MAPV2: FamilyField + ModeField are replaced by a single LayerField
 * (the unified layer list from LAYER_DEFS — composite index and crime
 * families as sibling options, which removes the separate Modo dimension).
 * YearField is unchanged.
 *
 * LayerField keeps the radiogroup/radio ARIA contract and the full
 * roving-tabindex + arrow-key behaviour (H-02): the checked radio is the only
 * tab stop; ArrowRight/Down, ArrowLeft/Up, Home and End move focus AND
 * selection with wraparound. Keydown is scoped to the radiogroup <div> —
 * never `document` (F-49).
 */

import { useRef } from 'react';
import {
  LAYER_DEFS,
  activeLayerId,
  AVAILABLE_YEARS,
  FAMILY_DEFS_EN,
  FAMILY_DEFS_ES,
  type LayerDef,
} from '../../lib/mapFilterDefs';
import { mapV2Strings } from '../../config/mapV2Strings';

interface YearFieldProps {
  lang: 'en' | 'es';
  year: number;
  onYearChange: (year: number) => void;
}

export function YearField({ lang, year, onYearChange }: YearFieldProps) {
  return (
    <select
      className="chip select"
      value={year}
      onChange={(e) => onYearChange(Number(e.target.value))}
      aria-label={lang === 'es' ? 'Filtrar por año' : 'Filter by year'}
    >
      {AVAILABLE_YEARS.map((y) => (
        <option key={y} value={y}>{y}</option>
      ))}
    </select>
  );
}

export interface LayerFieldProps {
  lang: 'en' | 'es';
  mode: 'composite' | 'family';
  crimeFamily: string | null;
  onLayerChange: (def: LayerDef) => void;
}

export function LayerField({ lang, mode, crimeFamily, onLayerChange }: LayerFieldProps) {
  const strings = mapV2Strings(lang);
  const btnRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const activeId = activeLayerId(mode, crimeFamily);

  function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    const count = LAYER_DEFS.length;
    let currentIndex = LAYER_DEFS.findIndex((l) => l.id === activeId);
    if (currentIndex === -1) currentIndex = 0;

    let nextIndex: number | null = null;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      nextIndex = (currentIndex + 1) % count;
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      nextIndex = (currentIndex - 1 + count) % count;
    } else if (e.key === 'Home') {
      nextIndex = 0;
    } else if (e.key === 'End') {
      nextIndex = count - 1;
    } else {
      return; // never preventDefault for Tab/Shift+Tab or any other key
    }

    e.preventDefault();
    const next = LAYER_DEFS[nextIndex];
    onLayerChange(next);
    btnRefs.current[nextIndex]?.focus();
  }

  return (
    <div role="radiogroup" aria-label={strings.layer_group} onKeyDown={handleKeyDown}>
      {LAYER_DEFS.map((def, i) => {
        const isActive = def.id === activeId;
        const hint = def.key
          ? (lang === 'es' ? FAMILY_DEFS_ES[def.key] : FAMILY_DEFS_EN[def.key])
          : undefined;
        return (
          <button
            key={def.id}
            ref={(el) => {
              btnRefs.current[i] = el;
            }}
            type="button"
            role="radio"
            aria-checked={isActive}
            tabIndex={isActive ? 0 : -1}
            className={`chip${isActive ? ' active' : ''}`}
            onClick={() => onLayerChange(def)}
            title={hint}
          >
            {def.featured && !isActive && (
              <span
                className="accent-dot"
                aria-hidden="true"
                style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--primary)', display: 'inline-block', marginRight: 6, flexShrink: 0 }}
              />
            )}
            {lang === 'es' ? def.labelEs : def.labelEn}
          </button>
        );
      })}
    </div>
  );
}
