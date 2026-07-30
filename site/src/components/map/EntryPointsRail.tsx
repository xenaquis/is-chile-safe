/**
 * EntryPointsRail.tsx — grouped Año/Tipo de delito/Modo entry points
 * (MAPSH-02/03/05 at >=481px). Each dimension is a native <details> wrapping
 * the Wave-1 FilterFields components, with one-open-at-a-time via a single
 * React `openId` state (never imperative DOM/aria mutation — premortem 7),
 * Escape-closes via a container-scoped React onKeyDown (NO document keyboard
 * listener — F-49 evidence chain), and click-outside-closes via a guarded
 * document mousedown listener (pattern ported from SearchBox.tsx:50-58).
 */

import { useEffect, useRef, useState } from 'react';
import { EN_STRINGS, ES_STRINGS } from '../../config/i18n';
import { CHIP_DEFS } from '../../lib/mapFilterDefs';
import { YearField, FamilyField, ModeField } from './FilterFields';

type EntryId = 'year' | 'family' | 'mode';

interface Props {
  lang: 'en' | 'es';
  year: number;
  onYearChange: (year: number) => void;
  crimeFamily: string | null;
  onFamilyChange: (key: string | null, index: number | null) => void;
  mode: 'composite' | 'family';
  onModeChange: (mode: 'composite' | 'family') => void;
}

function familyLabel(lang: 'en' | 'es', crimeFamily: string | null, short: boolean): string {
  if (crimeFamily === null) {
    if (short) return lang === 'es' ? 'Todos' : 'All';
    return lang === 'es' ? 'Todos los delitos' : 'All crime types';
  }
  const def = CHIP_DEFS.find((c) => c.key === crimeFamily);
  if (!def) return lang === 'es' ? 'Todos' : 'All';
  return lang === 'es' ? def.labelEs : def.labelEn;
}

function modeLabel(lang: 'en' | 'es', mode: 'composite' | 'family'): string {
  if (mode === 'composite') return lang === 'es' ? 'Índice' : 'Index';
  return lang === 'es' ? 'Por delito' : 'By crime';
}

type Band = 'wide' | 'mid' | 'narrow';

function getBand(): Band {
  if (typeof window === 'undefined') return 'wide';
  const w = window.innerWidth;
  if (w >= 640) return 'wide';
  if (w >= 481) return 'mid';
  return 'narrow';
}

export function EntryPointsRail({
  lang,
  year,
  onYearChange,
  crimeFamily,
  onFamilyChange,
  mode,
  onModeChange,
}: Props) {
  const strings = lang === 'es' ? ES_STRINGS : EN_STRINGS;
  const [openId, setOpenId] = useState<EntryId | null>(null);
  const [band, setBand] = useState<Band>(getBand());
  const railRef = useRef<HTMLDivElement>(null);
  const yearSummaryRef = useRef<HTMLElement>(null);
  const familySummaryRef = useRef<HTMLElement>(null);
  const modeSummaryRef = useRef<HTMLElement>(null);

  useEffect(() => {
    function handleResize() {
      setBand(getBand());
    }
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    function handleMouseDown(e: MouseEvent) {
      if (!railRef.current || railRef.current.offsetParent === null) return;
      if (openId !== null && !railRef.current.contains(e.target as Node)) {
        setOpenId(null);
      }
    }
    document.addEventListener('mousedown', handleMouseDown);
    return () => document.removeEventListener('mousedown', handleMouseDown);
  }, [openId]);

  function handleRailKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (e.key === 'Escape' && openId !== null) {
      const closingId = openId;
      setOpenId(null);
      e.stopPropagation();
      const refs: Record<EntryId, React.RefObject<HTMLElement>> = {
        year: yearSummaryRef,
        family: familySummaryRef,
        mode: modeSummaryRef,
      };
      refs[closingId].current?.focus();
    }
  }

  const fLabelLong = familyLabel(lang, crimeFamily, false);
  const fLabelShort = familyLabel(lang, crimeFamily, true);
  const mLabel = modeLabel(lang, mode);

  let stateSummary: string;
  if (band === 'wide') {
    stateSummary = `${mLabel} · ${fLabelLong} · ${year}`;
  } else if (band === 'mid') {
    stateSummary = `${fLabelLong} · ${year}`;
  } else {
    stateSummary = `${fLabelShort} · ${year}`;
  }

  return (
    <div
      data-role="filter-entry"
      className="entry-points-rail"
      ref={railRef}
      onKeyDown={handleRailKeyDown}
    >
      <details
        data-role="entry-point"
        open={openId === 'year'}
        onToggle={(e) =>
          setOpenId(
            (e.currentTarget as HTMLDetailsElement).open
              ? 'year'
              : openId === 'year'
              ? null
              : openId
          )
        }
      >
        <summary
          ref={yearSummaryRef as React.RefObject<HTMLElement>}
          aria-expanded={openId === 'year'}
          aria-controls="entry-panel-year"
        >
          {strings.map_entry_year}: {year}
        </summary>
        <div id="entry-panel-year">
          <YearField lang={lang} year={year} onYearChange={onYearChange} />
        </div>
      </details>

      <details
        data-role="entry-point"
        open={openId === 'family'}
        onToggle={(e) =>
          setOpenId(
            (e.currentTarget as HTMLDetailsElement).open
              ? 'family'
              : openId === 'family'
              ? null
              : openId
          )
        }
      >
        <summary
          ref={familySummaryRef as React.RefObject<HTMLElement>}
          aria-expanded={openId === 'family'}
          aria-controls="entry-panel-family"
        >
          {strings.map_entry_family}: {fLabelLong}
        </summary>
        <div id="entry-panel-family">
          <FamilyField lang={lang} crimeFamily={crimeFamily} onFamilyChange={onFamilyChange} />
        </div>
      </details>

      <details
        data-role="entry-point"
        open={openId === 'mode'}
        onToggle={(e) =>
          setOpenId(
            (e.currentTarget as HTMLDetailsElement).open
              ? 'mode'
              : openId === 'mode'
              ? null
              : openId
          )
        }
      >
        <summary
          ref={modeSummaryRef as React.RefObject<HTMLElement>}
          aria-expanded={openId === 'mode'}
          aria-controls="entry-panel-mode"
        >
          {strings.map_entry_mode}: {mLabel}
        </summary>
        <div id="entry-panel-mode">
          <ModeField lang={lang} mode={mode} onModeChange={onModeChange} />
        </div>
      </details>

      <div className="entry-state-summary" aria-live="polite">
        {stateSummary}
      </div>
    </div>
  );
}
