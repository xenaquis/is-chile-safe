/**
 * FilterFields.tsx — pure, wrapper-less field renderers for the map control
 * shell (Phase 30). None of these components render a disclosure or modal
 * wrapper element — they render only the interactive controls themselves, so
 * they can be reused unwrapped inside FilterSheet's modal body (Plan 30-04)
 * and wrapped in a disclosure panel inside EntryPointsRail (Plan 30-03).
 *
 * FamilyField / ModeField use the radiogroup/radio ARIA roles plus
 * aria-checked (never the plain group role — spec section 5 explicitly calls
 * that invalid as a parent of radio-role children).
 *
 * H-02: both radiogroups implement the full roving-tabindex + arrow-key
 * contract the roles announce (WAI-ARIA APG) — the checked radio is the only
 * tab stop, and ArrowRight/Down, ArrowLeft/Up, Home and End move focus AND
 * selection within the group, with wraparound. The keydown handler is scoped
 * to the radiogroup <div> (never `document`), matching EntryPointsRail's
 * Escape handler pattern — F-49's "no document-scoped keyboard listener"
 * still holds.
 */

import { useRef } from 'react';
import { CHIP_DEFS, AVAILABLE_YEARS, FAMILY_DEFS_EN, FAMILY_DEFS_ES, MODE_LABELS } from '../../lib/mapFilterDefs';
import { EN_STRINGS, ES_STRINGS } from '../../config/i18n';

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

interface FamilyFieldProps {
  lang: 'en' | 'es';
  crimeFamily: string | null;
  onFamilyChange: (key: string | null, index: number | null) => void;
}

export function FamilyField({ lang, crimeFamily, onFamilyChange }: FamilyFieldProps) {
  const btnRefs = useRef<Array<HTMLButtonElement | null>>([]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    const count = CHIP_DEFS.length;
    let currentIndex = CHIP_DEFS.findIndex((c) => c.key === crimeFamily);
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
    const next = CHIP_DEFS[nextIndex];
    onFamilyChange(next.key, next.familyIndex);
    btnRefs.current[nextIndex]?.focus();
  }

  return (
    <div
      role="radiogroup"
      aria-label={lang === 'es' ? 'Tipo de delito' : 'Crime type'}
      onKeyDown={handleKeyDown}
    >
      {CHIP_DEFS.map(({ key, familyIndex, labelEs, labelEn, featured }, i) => {
        const isActive = crimeFamily === key;
        const def = key ? (lang === 'es' ? FAMILY_DEFS_ES[key] : FAMILY_DEFS_EN[key]) : undefined;
        return (
          <button
            key={key ?? '__todos__'}
            ref={(el) => {
              btnRefs.current[i] = el;
            }}
            type="button"
            role="radio"
            aria-checked={isActive}
            tabIndex={isActive ? 0 : -1}
            className={`chip${isActive ? ' active' : ''}`}
            onClick={() => onFamilyChange(key, familyIndex)}
            title={def}
          >
            {featured && !isActive && (
              <span
                className="accent-dot"
                aria-hidden="true"
                style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--primary)', display: 'inline-block', marginRight: 6, flexShrink: 0 }}
              />
            )}
            {lang === 'es' ? labelEs : labelEn}
          </button>
        );
      })}
    </div>
  );
}

interface ModeFieldProps {
  lang: 'en' | 'es';
  mode: 'composite' | 'family';
  onModeChange: (mode: 'composite' | 'family') => void;
}

const MODE_OPTIONS: Array<'composite' | 'family'> = ['composite', 'family'];

export function ModeField({ lang, mode, onModeChange }: ModeFieldProps) {
  const strings = lang === 'es' ? ES_STRINGS : EN_STRINGS;
  const labels = MODE_LABELS[lang];
  const btnRefs = useRef<Array<HTMLButtonElement | null>>([]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    const count = MODE_OPTIONS.length;
    let currentIndex = MODE_OPTIONS.indexOf(mode);
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
      return;
    }

    e.preventDefault();
    const next = MODE_OPTIONS[nextIndex];
    onModeChange(next);
    btnRefs.current[nextIndex]?.focus();
  }

  return (
    <div role="radiogroup" aria-label={strings.map_entry_mode} onKeyDown={handleKeyDown}>
      {MODE_OPTIONS.map((opt, i) => (
        <button
          key={opt}
          ref={(el) => {
            btnRefs.current[i] = el;
          }}
          type="button"
          role="radio"
          aria-checked={mode === opt}
          tabIndex={mode === opt ? 0 : -1}
          className={`chip${mode === opt ? ' active' : ''}`}
          onClick={() => onModeChange(opt)}
        >
          {labels[opt]}
        </button>
      ))}
    </div>
  );
}
