/**
 * ComparatorIsland.tsx — React island for commune-to-commune comparison.
 * client:only="react" — prevents SSR; mounted on /compare/ and /es/comparar/ only.
 * No Leaflet dependency — pure React table/form; no double-init guard needed.
 *
 * Props passed from Astro shell at SSG time:
 *   - lang: locale ('en'|'es')
 *   - communes: 346-item index from loadIndex()
 *   - strings: i18n strings object (do NOT import EN/ES_STRINGS here — client:only safety)
 */
import { useState, useRef, useCallback, useEffect } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ComparatorEntry {
  id: string;       // CUT code
  name: string;
  region_id: string;
}

interface Props {
  lang: 'en' | 'es';
  communes: ComparatorEntry[];
  strings: Record<string, string>;
}

interface SeriesEntry {
  year: number;
  rate_per_100k: number;
  by_family: Record<string, number>;
  partial?: boolean;
}

interface CompositeIndexEntry {
  score: number;
  rank: number;
  regional_rank: number;
  level: 1 | 2 | 3 | 4 | 5;
  available_metrics: number;
}

interface CommuneData {
  id: string;
  name: string;
  slug: string;
  region_id: string;
  national_rank: number;
  regional_rank: number;
  trend: 'up' | 'down' | 'stable';
  featured_rates?: {
    propiedad?: Record<string, number>;
    homicidios?: Record<string, number>;
    homicidios_count?: Record<string, number>;
    secuestros?: Record<string, number>;
  };
  series: SeriesEntry[];
  composite_index?: Record<string, CompositeIndexEntry>;
}

interface NationalData {
  series: SeriesEntry[];
}

// ---------------------------------------------------------------------------
// Graceful fetch helper (mirrors MapIsland.tsx)
// ---------------------------------------------------------------------------
async function safeFetch<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Accent-insensitive normalization (port of pipeline/news/resolver.py _norm)
// ---------------------------------------------------------------------------
const normalizeForSearch = (s: string) =>
  s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();

// ---------------------------------------------------------------------------
// Helper: interpolate {key} in string template
// ---------------------------------------------------------------------------
function interpolate(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (_, key) =>
    key in vars ? String(vars[key as keyof typeof vars]) : `{${key}}`
  );
}

// ---------------------------------------------------------------------------
// Crime family display order and labels (matches FAMILY_SLUGS in i18n.ts)
// ---------------------------------------------------------------------------
const FAMILY_KEYS = ['vida', 'robos_violentos', 'vif', 'drogas', 'armas', 'propiedad', 'incivilidades'] as const;

const FAMILY_LABELS: Record<string, { en: string; es: string }> = {
  vida: { en: 'Crimes against life', es: 'Delitos contra la vida' },
  robos_violentos: { en: 'Violent robbery', es: 'Robos violentos' },
  vif: { en: 'Domestic violence', es: 'Violencia intrafamiliar' },
  drogas: { en: 'Drug crimes', es: 'Drogas' },
  armas: { en: 'Weapons', es: 'Armas' },
  propiedad: { en: 'Property crimes', es: 'Delitos de propiedad' },
  incivilidades: { en: 'Disorder', es: 'Incivilidades' },
};

const TREND_ARROW: Record<string, string> = {
  up: '↑',
  down: '↓',
  stable: '→',
};

// ---------------------------------------------------------------------------
// CI band labels
// ---------------------------------------------------------------------------
const CI_BANDS: Record<number, { en: string; es: string }> = {
  1: { en: 'Very Low', es: 'Muy Bajo' },
  2: { en: 'Low', es: 'Bajo' },
  3: { en: 'Moderate', es: 'Moderado' },
  4: { en: 'High', es: 'Alto' },
  5: { en: 'Very High', es: 'Muy Alto' },
};

// ---------------------------------------------------------------------------
// ComparatorIsland
// ---------------------------------------------------------------------------
export default function ComparatorIsland({ lang, communes, strings }: Props) {
  const s = strings;

  // Build accent-insensitive search index once
  const searchIndex = useRef(
    communes.map(c => ({ ...c, _norm: normalizeForSearch(c.name) }))
  );

  function searchCommunes(query: string): ComparatorEntry[] {
    const q = normalizeForSearch(query);
    if (!q) return [];
    return searchIndex.current.filter(c => c._norm.includes(q)).slice(0, 20);
  }

  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  const [selected, setSelected] = useState<ComparatorEntry[]>([]);
  const [communeData, setCommuneData] = useState<Record<string, CommuneData | null>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [query, setQuery] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [nationalData, setNationalData] = useState<NationalData | null>(null);
  const [regionalData, setRegionalData] = useState<Record<string, NationalData>>({});

  const inputRef = useRef<HTMLInputElement>(null);
  const listboxRef = useRef<HTMLUListElement>(null);

  const suggestions = searchCommunes(query);
  const maxReached = selected.length >= 3;

  // ---------------------------------------------------------------------------
  // Fetch commune data on selection
  // ---------------------------------------------------------------------------
  const fetchCommune = useCallback(async (entry: ComparatorEntry) => {
    const { id } = entry;
    if (communeData[id] !== undefined) return; // already fetched or errored

    setLoading(prev => ({ ...prev, [id]: true }));
    const data = await safeFetch<CommuneData>(`/data/cead/comunas/${id}.json`);
    setCommuneData(prev => ({ ...prev, [id]: data }));
    setLoading(prev => ({ ...prev, [id]: false }));
  }, [communeData]);

  // Fetch national data once
  useEffect(() => {
    if (nationalData) return;
    void safeFetch<NationalData>('/data/cead/national.json').then(d => {
      if (d) setNationalData(d);
    });
  }, [nationalData]);

  // Fetch regional data when a new region appears
  useEffect(() => {
    const regionIds = [...new Set(selected.map(c => c.region_id))];
    for (const rid of regionIds) {
      if (!regionalData[rid]) {
        void safeFetch<NationalData>(`/data/cead/regions/${rid}.json`).then(d => {
          if (d) setRegionalData(prev => ({ ...prev, [rid]: d }));
        });
      }
    }
  }, [selected, regionalData]);

  // ---------------------------------------------------------------------------
  // Select / remove commune
  // ---------------------------------------------------------------------------
  function selectCommune(entry: ComparatorEntry) {
    if (maxReached) return;
    if (selected.find(c => c.id === entry.id)) return;
    const next = [...selected, entry];
    setSelected(next);
    void fetchCommune(entry);
    setQuery('');
    setDropdownOpen(false);
    setActiveIndex(-1);
  }

  function removeCommune(id: string) {
    setSelected(prev => prev.filter(c => c.id !== id));
  }

  // ---------------------------------------------------------------------------
  // Keyboard nav
  // ---------------------------------------------------------------------------
  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(i => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(i => Math.max(i - 1, -1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && suggestions[activeIndex]) {
        selectCommune(suggestions[activeIndex]);
      }
    } else if (e.key === 'Escape') {
      setDropdownOpen(false);
      setActiveIndex(-1);
    }
  }

  // ---------------------------------------------------------------------------
  // Derive latestCompleteYear
  // ---------------------------------------------------------------------------
  function latestCompleteYear(data: CommuneData): number {
    const years = data.series.filter(s => !s.partial).map(s => s.year);
    if (years.length === 0) return 2024;
    return Math.max(...years);
  }

  // ---------------------------------------------------------------------------
  // Get per-family rate for a commune at its latestCompleteYear
  // ---------------------------------------------------------------------------
  function getFamilyRate(data: CommuneData, family: string): number | null {
    const year = latestCompleteYear(data);
    const entry = data.series.find(s => s.year === year);
    if (!entry) return null;
    const val = entry.by_family[family];
    return val !== undefined ? val : null;
  }

  // ---------------------------------------------------------------------------
  // Get national/regional avg for a family
  // ---------------------------------------------------------------------------
  function getNationalFamilyRate(family: string): number | null {
    if (!nationalData) return null;
    const latestSeries = nationalData.series.filter(s => !(s as SeriesEntry & { partial?: boolean }).partial);
    if (!latestSeries.length) return null;
    const last = latestSeries[latestSeries.length - 1];
    const val = last.by_family[family];
    return val !== undefined ? val : null;
  }

  // ---------------------------------------------------------------------------
  // Trend arrow color
  // ---------------------------------------------------------------------------
  function trendColor(trend: string): string {
    if (trend === 'up') return 'var(--trend-up)';
    if (trend === 'down') return 'var(--trend-down)';
    return 'var(--trend-stable)';
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  const listboxId = 'cmp-listbox';
  const activeOptionId = activeIndex >= 0 ? `cmp-option-${activeIndex}` : undefined;

  return (
    <div className="comparator-island" style={{ padding: 'var(--md)' }}>

      {/* Search + selected tags */}
      <div className="cmp-search-area" style={{ marginBottom: 'var(--md)' }}>
        {/* Selected commune tags */}
        {selected.length > 0 && (
          <div className="cmp-tags" style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--xs)', marginBottom: 'var(--sm)' }}>
            {selected.map(c => (
              <span
                key={c.id}
                className="cmp-tag"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 'var(--xs)',
                  padding: 'var(--xs) var(--sm)',
                  border: '1px solid var(--primary)',
                  borderRadius: 'var(--radius)',
                  background: 'var(--card)',
                  fontSize: 'var(--text-label)',
                }}
              >
                {c.name}
                <button
                  onClick={() => removeCommune(c.id)}
                  aria-label={interpolate(s.cmp_remove_aria ?? 'Remove {name}', { name: c.name })}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'var(--primary)',
                    padding: '0 2px',
                    minHeight: '44px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    fontSize: '16px',
                  }}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Autocomplete input */}
        <div style={{ position: 'relative' }}>
          <input
            ref={inputRef}
            type="text"
            role="combobox"
            aria-autocomplete="list"
            aria-expanded={dropdownOpen && suggestions.length > 0}
            aria-controls={listboxId}
            aria-activedescendant={activeOptionId}
            aria-disabled={maxReached}
            disabled={maxReached}
            placeholder={maxReached ? s.cmp_max_reached : s.cmp_input_placeholder}
            value={query}
            onChange={e => {
              setQuery(e.target.value);
              setDropdownOpen(true);
              setActiveIndex(-1);
            }}
            onKeyDown={handleKeyDown}
            onFocus={() => { if (query) setDropdownOpen(true); }}
            onBlur={() => setTimeout(() => setDropdownOpen(false), 150)}
            style={{
              width: '100%',
              padding: 'var(--sm) var(--md)',
              fontSize: 'var(--text-body)',
              border: '1px solid var(--line)',
              borderRadius: 'var(--radius)',
              background: maxReached ? 'var(--bg)' : 'var(--card)',
              color: 'var(--ink)',
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />

          {/* Dropdown */}
          {dropdownOpen && query && (
            <ul
              id={listboxId}
              ref={listboxRef}
              role="listbox"
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                background: 'var(--card)',
                border: '1px solid var(--line)',
                borderTop: 'none',
                borderRadius: '0 0 var(--radius) var(--radius)',
                maxHeight: '264px',
                overflowY: 'auto',
                margin: 0,
                padding: 0,
                listStyle: 'none',
                zIndex: 50,
              }}
            >
              {suggestions.length === 0 ? (
                <li
                  style={{
                    padding: 'var(--sm) var(--md)',
                    color: 'var(--muted)',
                    fontSize: 'var(--text-label)',
                    minHeight: '44px',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  {s.cmp_no_match}
                </li>
              ) : (
                suggestions.map((c, i) => {
                  const isSelected = !!selected.find(x => x.id === c.id);
                  const isActive = i === activeIndex;
                  return (
                    <li
                      key={c.id}
                      id={`cmp-option-${i}`}
                      role="option"
                      aria-selected={isSelected}
                      aria-disabled={isSelected || maxReached}
                      onMouseDown={e => {
                        e.preventDefault();
                        if (!isSelected && !maxReached) selectCommune(c);
                      }}
                      style={{
                        padding: 'var(--sm) var(--md)',
                        minHeight: '44px',
                        display: 'flex',
                        alignItems: 'center',
                        cursor: isSelected || maxReached ? 'default' : 'pointer',
                        background: isActive ? 'var(--bg)' : 'var(--card)',
                        color: isSelected ? 'var(--muted)' : 'var(--ink)',
                        fontSize: 'var(--text-label)',
                        borderBottom: '1px solid var(--line)',
                      }}
                    >
                      {c.name}
                      {isSelected && (
                        <span style={{ marginLeft: 'var(--xs)', color: 'var(--muted)', fontSize: '12px' }}>
                          {' '}✓
                        </span>
                      )}
                    </li>
                  );
                })
              )}
            </ul>
          )}
        </div>

        {/* State prompt */}
        {selected.length === 0 && (
          <p style={{ color: 'var(--muted)', fontSize: 'var(--text-label)', marginTop: 'var(--sm)' }}>
            {s.cmp_empty_heading}
          </p>
        )}
        {selected.length === 1 && (
          <p style={{ color: 'var(--muted)', fontSize: 'var(--text-label)', marginTop: 'var(--sm)' }}>
            {s.cmp_add_prompt}
          </p>
        )}
      </div>

      {/* Side-by-side columns + avg column */}
      {selected.length > 0 && (
        <div
          className="cmp-columns-wrapper"
          style={{
            overflowX: 'auto',
          }}
        >
          <div
            className="cmp-columns"
            style={{
              display: 'flex',
              gap: 'var(--lg)',
              alignItems: 'flex-start',
              minWidth: 0,
            }}
          >
            {/* Commune columns */}
            {selected.map(entry => {
              const data = communeData[entry.id];
              const isLoading = loading[entry.id];

              if (isLoading) {
                return (
                  <div
                    key={entry.id}
                    className="cmp-column cmp-column--loading"
                    style={{
                      flex: '1 1 200px',
                      minWidth: '180px',
                      background: 'var(--card)',
                      borderRadius: 'var(--radius)',
                      border: '1px solid var(--line)',
                      padding: 'var(--md)',
                    }}
                  >
                    <div style={{ background: 'var(--line)', height: '24px', borderRadius: '4px', marginBottom: 'var(--sm)', animation: 'pulse 1.5s infinite' }} />
                    <div style={{ background: 'var(--line)', height: '40px', borderRadius: '4px', marginBottom: 'var(--sm)', animation: 'pulse 1.5s infinite' }} />
                    <div style={{ background: 'var(--line)', height: '200px', borderRadius: '4px', animation: 'pulse 1.5s infinite' }} />
                  </div>
                );
              }

              if (data === null) {
                return (
                  <div
                    key={entry.id}
                    className="cmp-column cmp-column--error"
                    style={{
                      flex: '1 1 200px',
                      minWidth: '180px',
                      background: 'var(--card)',
                      borderRadius: 'var(--radius)',
                      border: '1px solid var(--line)',
                      padding: 'var(--md)',
                    }}
                  >
                    <h2 style={{ fontSize: 'var(--text-heading)', marginBottom: 'var(--sm)' }}>{entry.name}</h2>
                    <p style={{ color: 'var(--muted)', fontSize: 'var(--text-label)' }}>
                      {interpolate(s.cmp_data_error ?? 'Could not load data for {name}. Try refreshing.', { name: entry.name })}
                    </p>
                  </div>
                );
              }

              if (!data) return null; // not yet fetched (shouldn't happen)

              const year = latestCompleteYear(data);
              const ci = data.composite_index?.[String(year)];
              const bandLabel = ci ? (CI_BANDS[ci.level]?.[lang] ?? '') : '';

              // Homicide row (HOM-02 — !== undefined, 0 is valid)
              const homRate = data.featured_rates?.homicidios?.[String(year)];
              const homCount = data.featured_rates?.homicidios_count?.[String(year)];
              const hasHom = homRate !== undefined && homCount !== undefined;

              return (
                <div
                  key={entry.id}
                  className="cmp-column"
                  style={{
                    flex: '1 1 200px',
                    minWidth: '180px',
                    background: 'var(--card)',
                    borderRadius: 'var(--radius)',
                    border: '1px solid var(--line)',
                    padding: 'var(--md)',
                  }}
                >
                  <h2 style={{ fontSize: 'var(--text-heading)', fontWeight: 'var(--weight-strong)', marginBottom: 'var(--sm)', color: 'var(--ink)' }}>
                    {data.name}
                  </h2>

                  {/* Composite index headline */}
                  {ci ? (
                    <div style={{ marginBottom: 'var(--md)' }}>
                      <div style={{ fontSize: 'var(--text-display)', fontWeight: 'var(--weight-strong)', color: 'var(--ink)' }}>
                        {ci.score.toFixed(1)}
                      </div>
                      <div style={{ fontSize: 'var(--text-label)', fontWeight: 'var(--weight-strong)', color: 'var(--muted)' }}>
                        {bandLabel}
                      </div>
                      <div style={{ fontSize: 'var(--text-label)', color: 'var(--muted)' }}>
                        #{ci.rank} {lang === 'es' ? 'de 346 a nivel nacional' : 'of 346 nationally'}
                      </div>
                    </div>
                  ) : (
                    <div style={{ marginBottom: 'var(--md)', color: 'var(--muted)', fontSize: 'var(--text-label)' }}>
                      {lang === 'es' ? 'Sin índice compuesto' : 'No composite index'}
                    </div>
                  )}

                  {/* Per-family breakdown */}
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--text-label)' }}>
                    <thead>
                      <tr>
                        <th scope="col" style={{ textAlign: 'left', padding: '2px 4px', color: 'var(--muted)', fontWeight: 'var(--weight-strong)' }}>
                          {lang === 'es' ? 'Delito' : 'Crime type'}
                        </th>
                        <th scope="col" style={{ textAlign: 'right', padding: '2px 4px', color: 'var(--muted)', fontWeight: 'var(--weight-strong)' }}>
                          {lang === 'es' ? 'Tasa/100k' : 'Rate/100k'}
                        </th>
                        <th scope="col" style={{ textAlign: 'center', padding: '2px 4px', color: 'var(--muted)', fontWeight: 'var(--weight-strong)' }}>
                          {lang === 'es' ? 'Tend.' : 'Trend'}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {FAMILY_KEYS.map(family => {
                        const rate = getFamilyRate(data, family);
                        const label = FAMILY_LABELS[family]?.[lang] ?? family;
                        return (
                          <tr key={family} style={{ borderTop: '1px solid var(--line)' }}>
                            <th scope="row" style={{ textAlign: 'left', padding: '4px', fontWeight: 'normal', color: 'var(--ink)' }}>
                              {label}
                            </th>
                            <td style={{ textAlign: 'right', padding: '4px', color: 'var(--ink)' }}>
                              {rate !== null ? rate.toFixed(1) : '—'}
                            </td>
                            <td style={{ textAlign: 'center', padding: '4px' }}>
                              <span
                                role="img"
                                aria-label={lang === 'es'
                                  ? (data.trend === 'up' ? 'Al alza' : data.trend === 'down' ? 'A la baja' : 'Estable')
                                  : (data.trend === 'up' ? 'Rising' : data.trend === 'down' ? 'Declining' : 'Stable')}
                                style={{ color: trendColor(data.trend) }}
                              >
                                {TREND_ARROW[data.trend] ?? '→'}
                              </span>
                            </td>
                          </tr>
                        );
                      })}

                      {/* Homicide sub-row (HOM-02) */}
                      <tr style={{ borderTop: '2px solid var(--line)', background: 'var(--bg)' }}>
                        <th scope="row" style={{ textAlign: 'left', padding: '4px', fontWeight: 'var(--weight-strong)', color: 'var(--ink)', fontSize: '12px' }}>
                          {interpolate(s.cmp_homicide_row ?? 'Homicide (per 100k, {year})', { year })}
                        </th>
                        <td style={{ textAlign: 'right', padding: '4px', color: 'var(--ink)' }}>
                          {hasHom
                            ? homRate!.toFixed(2)
                            : <span style={{ color: 'var(--muted)', fontSize: '11px' }}>
                                {interpolate(s.cmp_homicide_no_data ?? 'No reported cases — CEAD {year}', { year })}
                              </span>
                          }
                        </td>
                        <td />
                      </tr>
                    </tbody>
                  </table>
                </div>
              );
            })}

            {/* Average column */}
            <div
              className="cmp-column cmp-column--avg"
              style={{
                flex: '1 1 160px',
                minWidth: '140px',
                background: 'var(--bg)',
                borderRadius: 'var(--radius)',
                border: '2px solid var(--primary)',
                padding: 'var(--md)',
              }}
            >
              <h2 style={{ fontSize: 'var(--text-heading)', fontWeight: 'var(--weight-strong)', marginBottom: 'var(--sm)', color: 'var(--primary)' }}>
                {s.cmp_avg_column ?? (lang === 'es' ? 'Prom. Chile' : 'Chile avg.')}
              </h2>
              {nationalData ? (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--text-label)' }}>
                  <thead>
                    <tr>
                      <th scope="col" style={{ textAlign: 'left', padding: '2px 4px', color: 'var(--muted)', fontWeight: 'var(--weight-strong)' }}>
                        {lang === 'es' ? 'Delito' : 'Crime type'}
                      </th>
                      <th scope="col" style={{ textAlign: 'right', padding: '2px 4px', color: 'var(--muted)', fontWeight: 'var(--weight-strong)' }}>
                        {lang === 'es' ? 'Tasa/100k' : 'Rate/100k'}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {FAMILY_KEYS.map(family => {
                      const rate = getNationalFamilyRate(family);
                      const label = FAMILY_LABELS[family]?.[lang] ?? family;
                      return (
                        <tr key={family} style={{ borderTop: '1px solid var(--line)' }}>
                          <th scope="row" style={{ textAlign: 'left', padding: '4px', fontWeight: 'normal', color: 'var(--ink)' }}>
                            {label}
                          </th>
                          <td style={{ textAlign: 'right', padding: '4px', color: 'var(--ink)' }}>
                            {rate !== null ? rate.toFixed(1) : '—'}
                          </td>
                        </tr>
                      );
                    })}
                    {/* Homicide row placeholder in avg column */}
                    <tr style={{ borderTop: '2px solid var(--line)', background: 'var(--bg)' }}>
                      <th scope="row" colSpan={2} style={{ textAlign: 'left', padding: '4px', fontSize: '11px', color: 'var(--muted)', fontWeight: 'normal' }}>
                        {lang === 'es' ? 'Homicidios: CEAD/SPD' : 'Homicide: CEAD/SPD'}
                      </th>
                    </tr>
                  </tbody>
                </table>
              ) : (
                <p style={{ color: 'var(--muted)', fontSize: 'var(--text-label)' }}>
                  {lang === 'es' ? 'Cargando…' : 'Loading…'}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Skeleton pulse animation */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @media (max-width: 640px) {
          .cmp-columns { flex-direction: column !important; }
        }
      `}</style>
    </div>
  );
}
