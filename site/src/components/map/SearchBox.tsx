/**
 * SearchBox.tsx — Commune name search with prefix-filter dropdown.
 *
 * Ported from ischilesafe.com/components.jsx SearchBox (lines 63-101).
 * Uses island-internal SearchIcon SVG (no icon lib — UI-SPEC inline SVG only).
 * T-03-02-03: client-side Array.filter over the 346-commune index only; no eval, no server query.
 */
import { useState, useRef, useEffect } from 'react';

// Inline SVG icon (ported from ischilesafe.com/components.jsx lines 41-61)
function SearchIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeWidth="1.8" />
      <line x1="12.2" y1="12.2" x2="16" y2="16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

export interface CommuneIndexEntry {
  cut: string;
  name: string;
  slug: string;
  region_id: string;
}

interface Props {
  index: CommuneIndexEntry[];
  lang: 'en' | 'es';
  onSelect: (cut: string) => void;
  onLocate: () => void;
}

export function SearchBox({ index, lang, onSelect, onLocate }: Props) {
  const [q, setQ] = useState('');
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const results = q.trim()
    ? index.filter((c) => c.name.toLowerCase().startsWith(q.toLowerCase())).slice(0, 8)
    : [];

  function pick(cut: string) {
    setQ('');
    setOpen(false);
    onSelect(cut);
  }

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div className="search-box" ref={containerRef}>
      <div className="search-input-wrap">
        <span className="search-icon"><SearchIcon /></span>
        <input
          type="search"
          className="search-input"
          placeholder={lang === 'es' ? 'Buscar comuna…' : 'Search commune…'}
          value={q}
          aria-label={lang === 'es' ? 'Buscar comuna' : 'Search commune'}
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
          }}
          onFocus={() => { if (q.trim()) setOpen(true); }}
        />
        <button
          className="locate-btn-visible"
          aria-label={lang === 'es' ? 'Mostrar mi ubicación' : 'Show my location'}
          onClick={onLocate}
          type="button"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <circle cx="9" cy="9" r="3" fill="currentColor" />
            <circle cx="9" cy="9" r="6" stroke="currentColor" strokeWidth="1.8" />
            <line x1="9" y1="1" x2="9" y2="3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            <line x1="9" y1="15" x2="9" y2="17" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            <line x1="1" y1="9" x2="3" y2="9" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            <line x1="15" y1="9" x2="17" y2="9" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      {open && results.length > 0 && (
        <ul className="search-dropdown" role="listbox">
          {results.map((c) => (
            <li
              key={c.cut}
              className="search-result"
              role="option"
              aria-selected={false}
              onMouseDown={() => pick(c.cut)}
            >
              <strong className="search-result-name">{c.name}</strong>
            </li>
          ))}
        </ul>
      )}

      {open && q.trim() && results.length === 0 && (
        <div className="search-dropdown search-no-results">
          {lang === 'es' ? 'Sin resultados' : 'No results'}
        </div>
      )}
    </div>
  );
}
