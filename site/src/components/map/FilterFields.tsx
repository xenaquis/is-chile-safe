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
 */

import { CHIP_DEFS, AVAILABLE_YEARS, FAMILY_DEFS_EN, FAMILY_DEFS_ES } from '../../lib/mapFilterDefs';

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
  return (
    <div
      role="radiogroup"
      aria-label={lang === 'es' ? 'Tipo de delito' : 'Crime type'}
    >
      {CHIP_DEFS.map(({ key, familyIndex, labelEs, labelEn, featured }) => {
        const isActive = crimeFamily === key;
        const def = key ? (lang === 'es' ? FAMILY_DEFS_ES[key] : FAMILY_DEFS_EN[key]) : undefined;
        return (
          <button
            key={key ?? '__todos__'}
            type="button"
            role="radio"
            aria-checked={isActive}
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

export function ModeField({ lang, mode, onModeChange }: ModeFieldProps) {
  return (
    <div
      role="radiogroup"
      aria-label={lang === 'es' ? 'Modo' : 'Map mode'}
    >
      <button
        type="button"
        role="radio"
        aria-checked={mode === 'composite'}
        className={`chip${mode === 'composite' ? ' active' : ''}`}
        onClick={() => onModeChange('composite')}
      >
        {lang === 'es' ? 'Índice compuesto' : 'Composite index'}
      </button>
      <button
        type="button"
        role="radio"
        aria-checked={mode === 'family'}
        className={`chip${mode === 'family' ? ' active' : ''}`}
        onClick={() => onModeChange('family')}
      >
        {lang === 'es' ? 'Por familia' : 'By family'}
      </button>
    </div>
  );
}
