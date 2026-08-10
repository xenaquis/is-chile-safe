/**
 * ComparatorIsland.tsx — React island for commune-to-commune comparison.
 * client:only="react" — prevents SSR; mounted on /compare/ and /es/comparar/ only.
 * No Leaflet dependency — pure React; no double-init guard needed.
 *
 * REDESIGN (proposal 4b): the three parallel number tables collapse into ONE
 * chart — one row per crime family, all selected communes on a shared per-row
 * scale, with the national rate as a fixed dashed line instead of a column at
 * the far right. Distance between dots IS the difference. Numbers stay to the
 * right of every row, and a screen-reader table carries the same figures.
 *
 * Invariants preserved from the previous implementation:
 *   - client:only safety: i18n.ts is NEVER imported here; cmp_* strings arrive
 *     as a prop. New cx_* strings come from config/comparatorStrings.ts, a
 *     dependency-free module (see its header).
 *   - ?a=&b= URL sync + preselect with 4–5 digit CUT validation (adds &c= for
 *     the optional third commune; a/b keep their meaning).
 *   - latestCompleteYear() = max non-partial series year, chosen by VALUE not
 *     array position (WR-01).
 *   - The national reference year is derived independently and always labelled.
 *   - composite_index is indexed by its OWN latest key, not the series year.
 *   - Homicide is gated on the RATE alone; the count is appended only if present
 *     (WR-05, HOM-02 — 0 is a valid rate).
 *   - Homicide never comes from by_family (Pitfall 1) — only featured_rates.
 *   - Accent-insensitive search; combobox ARIA + keyboard nav; 44px targets.
 *   - No commune is ever called "safe" or "dangerous".
 *
 * Props passed from the Astro shell at SSG time:
 *   - lang, communes (index), strings (cmp_* subset), regionNames (id → name)
 */
import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { formatRate, formatDecimal } from '../lib/formatNumber';
import {
  COMPARATOR_STRINGS_EN,
  COMPARATOR_STRINGS_ES,
  SLOT_COLORS,
} from '../config/comparatorStrings';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ComparatorEntry {
  id: string;       // CUT code
  name: string;
  region_id: string;
  low_population?: boolean;
}

interface Props {
  lang: 'en' | 'es';
  communes: ComparatorEntry[];
  strings: Record<string, string>;
  /** region_id → region name. Optional: the island degrades to no region label. */
  regionNames?: Record<string, string>;
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
// Helpers
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

const normalizeForSearch = (s: string) =>
  s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();

function interpolate(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (_, key) =>
    key in vars ? String(vars[key as keyof typeof vars]) : `{${key}}`
  );
}

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

// Display order: descending typical magnitude, so the chart reads top-heavy
// instead of alternating between long and short bars. Same 7 keys as before.
const FAMILY_KEYS = [
  'incivilidades',
  'propiedad',
  'vida',
  'vif',
  'robos_violentos',
  'drogas',
  'armas',
] as const;

const FAMILY_LABELS: Record<string, { en: string; es: string }> = {
  vida: { en: 'Crimes against life', es: 'Delitos contra la vida' },
  robos_violentos: { en: 'Violent robbery', es: 'Robos violentos' },
  vif: { en: 'Domestic violence', es: 'Violencia intrafamiliar' },
  drogas: { en: 'Drug crimes', es: 'Drogas' },
  armas: { en: 'Weapons', es: 'Armas' },
  propiedad: { en: 'Property crimes', es: 'Delitos de propiedad' },
  incivilidades: { en: 'Disorder', es: 'Incivilidades' },
};

const TREND_ARROW: Record<string, string> = { up: '↑', down: '↓', stable: '→' };

const CI_BANDS: Record<number, { en: string; es: string }> = {
  1: { en: 'Very Low', es: 'Muy Bajo' },
  2: { en: 'Low', es: 'Bajo' },
  3: { en: 'Moderate', es: 'Moderado' },
  4: { en: 'High', es: 'Alto' },
  5: { en: 'Very High', es: 'Muy Alto' },
};

const BAND_TOKEN: Record<number, string> = {
  1: 'var(--s1)', 2: 'var(--s2)', 3: 'var(--s3)', 4: 'var(--s4)', 5: 'var(--s5)',
};

const POPULAR_PAIRS: Array<[string, string]> = [
  ['13101', '13114'],
  ['13123', '13120'],
  ['5109', '5101'],
];

// ---------------------------------------------------------------------------
// ComparatorIsland
// ---------------------------------------------------------------------------
export default function ComparatorIsland({ lang, communes, strings, regionNames }: Props) {
  const s = strings;
  const t = lang === 'es' ? COMPARATOR_STRINGS_ES : COMPARATOR_STRINGS_EN;
  const regionName = (id: string) => (regionNames ? regionNames[id] ?? '' : '');

  const searchIndex = useRef(
    communes.map(c => ({ ...c, _norm: normalizeForSearch(c.name) }))
  );

  const [selected, setSelected] = useState<ComparatorEntry[]>([]);
  const [communeData, setCommuneData] = useState<Record<string, CommuneData | null>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [query, setQuery] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [nationalData, setNationalData] = useState<NationalData | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const maxReached = selected.length >= 3;

  const suggestions = useMemo(() => {
    const q = normalizeForSearch(query);
    if (!q) return [] as ComparatorEntry[];
    return searchIndex.current
      .filter(c => c._norm.includes(q) && !selected.some(x => x.id === c.id))
      .slice(0, 8);
  }, [query, selected]);

  // ---------------------------------------------------------------------------
  // Data fetching
  // ---------------------------------------------------------------------------
  // Requested ids — a ref, not state, so a re-render (or StrictMode double
  // invoke) can never fire the same fetch twice.
  const requested = useRef<Set<string>>(new Set());

  const fetchCommune = useCallback(async (entry: ComparatorEntry) => {
    const { id } = entry;
    if (requested.current.has(id)) return;
    requested.current.add(id);
    setLoading(prev => ({ ...prev, [id]: true }));
    const data = await safeFetch<CommuneData>(`/data/cead/comunas/${id}.json`);
    if (data === null) requested.current.delete(id);
    setCommuneData(prev => ({ ...prev, [id]: data }));
    setLoading(prev => ({ ...prev, [id]: false }));
  }, []);

  const ensureCommune = useCallback((entry: ComparatorEntry) => {
    void fetchCommune(entry);
  }, [fetchCommune]);

  useEffect(() => {
    if (nationalData) return;
    void safeFetch<NationalData>('/data/cead/national.json').then(d => {
      if (d) setNationalData(d);
    });
  }, [nationalData]);

  // ---------------------------------------------------------------------------
  // URL sync — ?a=&b=&c=
  // ---------------------------------------------------------------------------
  const initializedRef = useRef(false);
  useEffect(() => {
    if (!initializedRef.current) return;
    if (typeof window === 'undefined') return;
    const [a, b, c] = [selected[0]?.id ?? '', selected[1]?.id ?? '', selected[2]?.id ?? ''];
    const u = new URL(window.location.href);
    u.searchParams.delete('a');
    u.searchParams.delete('b');
    u.searchParams.delete('c');
    if (a) u.searchParams.set('a', a);
    if (b) u.searchParams.set('b', b);
    if (c) u.searchParams.set('c', c);
    window.history.replaceState(null, '', u.pathname + u.search);
  }, [selected]);

  const didMountRef = useRef(false);
  useEffect(() => {
    if (didMountRef.current) return;
    didMountRef.current = true;
    if (typeof window === 'undefined') { initializedRef.current = true; return; }
    const params = new URLSearchParams(window.location.search);
    const cutRe = /^\d{4,5}$/;
    const picked: ComparatorEntry[] = [];
    for (const key of ['a', 'b', 'c']) {
      const raw = params.get(key) ?? '';
      if (!cutRe.test(raw)) continue;
      if (picked.some(p => p.id === raw)) continue;
      const found = communes.find(x => x.id === raw);
      if (found) picked.push(found);
    }
    if (picked.length > 0) {
      setSelected(picked.slice(0, 3));
      picked.slice(0, 3).forEach(e => { void fetchCommune(e); });
    }
    initializedRef.current = true;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---------------------------------------------------------------------------
  // Selection
  // ---------------------------------------------------------------------------
  function selectCommune(entry: ComparatorEntry) {
    if (selected.length >= 3 || selected.some(c => c.id === entry.id)) return;
    setSelected(prev => [...prev, entry]);
    ensureCommune(entry);
    setQuery('');
    setDropdownOpen(false);
    setActiveIndex(-1);
  }

  function selectPair(a: ComparatorEntry, b: ComparatorEntry) {
    setSelected([a, b]);
    ensureCommune(a);
    ensureCommune(b);
    setQuery('');
  }

  function removeCommune(id: string) {
    setSelected(prev => prev.filter(c => c.id !== id));
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setDropdownOpen(true);
      setActiveIndex(i => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(i => Math.max(i - 1, -1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && suggestions[activeIndex]) selectCommune(suggestions[activeIndex]);
    } else if (e.key === 'Escape') {
      setDropdownOpen(false);
      setActiveIndex(-1);
    }
  }

  // ---------------------------------------------------------------------------
  // Year selection (WR-01 — always by value, never array position)
  // ---------------------------------------------------------------------------
  const completeYears = (series: SeriesEntry[]) =>
    series.filter(x => !x.partial).map(x => x.year);

  const latestCompleteYear = (data: CommuneData): number | null => {
    const ys = completeYears(data.series);
    return ys.length ? Math.max(...ys) : null;
  };

  const natYear: number | null = nationalData
    ? (completeYears(nationalData.series).length ? Math.max(...completeYears(nationalData.series)) : null)
    : null;

  const loadedRows = selected
    .map(e => ({ entry: e, data: communeData[e.id] }))
    .filter((r): r is { entry: ComparatorEntry; data: CommuneData } => !!r.data);

  // The chart year is the newest complete year shared by every loaded commune AND
  // by the national series. If there is none, each commune falls back to its own
  // latest complete year and the mismatch is stated in words (cx_mixed_years).
  const sharedYear: number | null = (() => {
    if (!loadedRows.length || natYear === null) return null;
    let candidates = new Set(completeYears(loadedRows[0].data.series));
    for (const r of loadedRows.slice(1)) {
      const ys = new Set(completeYears(r.data.series));
      candidates = new Set([...candidates].filter(y => ys.has(y)));
    }
    const natYears = new Set(completeYears(nationalData!.series));
    const common = [...candidates].filter(y => natYears.has(y));
    return common.length ? Math.max(...common) : null;
  })();

  const yearFor = (data: CommuneData): number | null => sharedYear ?? latestCompleteYear(data);

  const seriesAt = (data: CommuneData, year: number | null): SeriesEntry | null =>
    year === null ? null : data.series.find(x => x.year === year && !x.partial) ?? null;

  const natSeries: SeriesEntry | null =
    nationalData && (sharedYear ?? natYear) !== null
      ? nationalData.series.find(x => x.year === (sharedYear ?? natYear) && !x.partial) ?? null
      : null;

  const colorOf = (i: number) => SLOT_COLORS[i % SLOT_COLORS.length];
  const colorFor = (id: string) => colorOf(selected.findIndex(c => c.id === id));

  // ---------------------------------------------------------------------------
  // Chart model
  // ---------------------------------------------------------------------------
  const chartRows = FAMILY_KEYS.map(family => {
    const cells = loadedRows.map(r => {
      const entry = seriesAt(r.data, yearFor(r.data));
      const raw = entry ? entry.by_family[family] : undefined;
      return {
        id: r.entry.id,
        name: r.data.name,
        color: colorFor(r.entry.id),
        value: raw !== undefined ? raw : null,
        year: yearFor(r.data),
      };
    });
    const mean = natSeries ? natSeries.by_family[family] ?? null : null;
    const nums = cells.map(c => c.value).filter((v): v is number => v !== null);
    const top = Math.max(...nums, mean ?? 0, 1) * 1.15;
    const pos = (v: number) => clamp((v / top) * 100, 2, 98);
    const ps = nums.map(pos);
    const lowest = nums.length ? Math.min(...nums) : null;
    return {
      family,
      label: FAMILY_LABELS[family]?.[lang] ?? family,
      cells: cells.map(c => ({ ...c, pos: c.value !== null ? pos(c.value) : null })),
      mean,
      meanPos: mean !== null ? pos(mean) : null,
      linkLeft: ps.length ? Math.min(...ps) : 0,
      linkWidth: ps.length ? Math.max(...ps) - Math.min(...ps) : 0,
      lowest,
    };
  });

  const natMissing = nationalData === null || natYear === null;
  const mixedYears = !natMissing && sharedYear === null && loadedRows.length > 0;
  const mixedYearLabel = loadedRows
    .map(r => `${r.data.name} ${yearFor(r.data) ?? '—'}`)
    .join(' · ');

  // Plain-language summary — only when two or more communes have loaded.
  let summary: string | null = null;
  if (loadedRows.length >= 2) {
    const [A, B] = loadedRows;
    const va = (f: string) => {
      const e = seriesAt(A.data, yearFor(A.data));
      const v = e ? e.by_family[f] : undefined;
      return v === undefined ? null : v;
    };
    const vb = (f: string) => {
      const e = seriesAt(B.data, yearFor(B.data));
      const v = e ? e.by_family[f] : undefined;
      return v === undefined ? null : v;
    };
    const comparable = FAMILY_KEYS.filter(f => va(f) !== null && vb(f) !== null);
    if (comparable.length) {
      const lower = comparable.filter(f => (va(f) as number) < (vb(f) as number)).length;
      const widest = comparable
        .slice()
        .sort((x, y) => Math.abs((vb(y) as number) - (va(y) as number)) - Math.abs((vb(x) as number) - (va(x) as number)))[0];
      summary = interpolate(t.cx_summary, {
        a: A.data.name,
        b: B.data.name,
        n: lower,
        total: comparable.length,
        family: (FAMILY_LABELS[widest]?.[lang] ?? widest).toLowerCase(),
        va: formatRate(va(widest) as number, lang),
        vb: formatRate(vb(widest) as number, lang),
      });
      if (loadedRows.length === 3) {
        summary += ' ' + interpolate(t.cx_summary_third, { c: loadedRows[2].data.name });
      }
    }
  }

  const listboxId = 'cmp-listbox';
  const activeOptionId = activeIndex >= 0 ? `cmp-option-${activeIndex}` : undefined;

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="comparator-island">

      {/* ---------- Selection bar: one pill per commune + one add slot ---------- */}
      <div className="cmp-slotbar">
        {selected.map((c, i) => (
          <span key={c.id} className="cmp-tag" style={{ borderColor: colorOf(i) }}>
            <span className="cmp-tag-dot" style={{ background: colorOf(i) }} aria-hidden="true" />
            <span className="cmp-tag-name">{c.name}</span>
            {regionName(c.region_id) && (
              <span className="cmp-tag-region">{regionName(c.region_id)}</span>
            )}
            <button
              type="button"
              className="cmp-tag-x"
              onClick={() => removeCommune(c.id)}
              aria-label={interpolate(s.cmp_remove_aria ?? 'Remove {name}', { name: c.name })}
            >
              ×
            </button>
          </span>
        ))}

        {!maxReached && (
          <div className="cmp-addslot">
            <span className="cmp-addslot-icon" aria-hidden="true">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.6" />
                <path d="M11 11l3.5 3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
            </span>
            <input
              ref={inputRef}
              type="text"
              role="combobox"
              aria-autocomplete="list"
              aria-expanded={dropdownOpen && suggestions.length > 0}
              aria-controls={listboxId}
              aria-activedescendant={activeOptionId}
              aria-label={selected.length === 0 ? (s.cmp_input_placeholder ?? t.cx_add_slot) : t.cx_add_slot}
              placeholder={selected.length === 0 ? (s.cmp_input_placeholder ?? t.cx_add_slot) : t.cx_add_slot}
              value={query}
              onChange={e => { setQuery(e.target.value); setDropdownOpen(true); setActiveIndex(-1); }}
              onKeyDown={handleKeyDown}
              onFocus={() => { if (query) setDropdownOpen(true); }}
              onBlur={() => setTimeout(() => setDropdownOpen(false), 150)}
            />
            {dropdownOpen && query && (
              <ul id={listboxId} role="listbox" className="cmp-listbox">
                {suggestions.length === 0 ? (
                  <li className="cmp-option cmp-option--empty">{s.cmp_no_match}</li>
                ) : (
                  suggestions.map((c, i) => (
                    <li
                      key={c.id}
                      id={`cmp-option-${i}`}
                      role="option"
                      aria-selected={i === activeIndex}
                      className={'cmp-option' + (i === activeIndex ? ' is-active' : '')}
                      onMouseDown={e => { e.preventDefault(); selectCommune(c); }}
                    >
                      <span className="cmp-option-name">{c.name}</span>
                      <span className="cmp-option-region">{regionName(c.region_id)}</span>
                      {c.low_population && (
                        <span className="cmp-option-lowpop" title={s.low_pop_footnote}>{t.cx_lowpop_tag}</span>
                      )}
                    </li>
                  ))
                )}
              </ul>
            )}
          </div>
        )}

        {maxReached && <span className="cmp-maxnote">{s.cmp_max_reached}</span>}

        {loadedRows.length > 1 && (
          <button
            type="button"
            className="cmp-sort"
            onClick={() => {
              const loadedIds = new Set(loadedRows.map(r => r.entry.id));
              const loadedOrder = loadedRows
                .slice()
                .sort((x, y) => {
                  const ex = seriesAt(x.data, yearFor(x.data));
                  const ey = seriesAt(y.data, yearFor(y.data));
                  return (ey?.rate_per_100k ?? 0) - (ex?.rate_per_100k ?? 0);
                })
                .map(r => r.entry);
              const unloadedOrder = selected.filter(c => !loadedIds.has(c.id));
              setSelected([...loadedOrder, ...unloadedOrder]);
            }}
          >
            {t.cx_sort_button}
          </button>
        )}
      </div>

      {/* ---------- Empty state ---------- */}
      {selected.length === 0 && (
        <div className="cmp-empty">
          <p className="cmp-empty-h">{s.cmp_empty_heading}</p>
          <p className="cmp-empty-b">{s.cmp_empty_body}</p>
          <div className="cmp-chips">
            <span className="cmp-chips-label">{s.cmp_chips_label}</span>
            {POPULAR_PAIRS.map(([aId, bId]) => {
              const a = communes.find(c => c.id === aId);
              const b = communes.find(c => c.id === bId);
              if (!a || !b) return null;
              return (
                <button key={aId + '-' + bId} type="button" className="cmp-chip" onClick={() => selectPair(a, b)}>
                  {a.name} vs {b.name}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {selected.length === 1 && <p className="cmp-hint">{s.cmp_add_prompt}</p>}

      {/* ---------- Loading / error notes per commune ---------- */}
      {selected.map(c =>
        loading[c.id] ? (
          <p key={'l' + c.id} className="cmp-hint" aria-live="polite">{c.name}…</p>
        ) : communeData[c.id] === null ? (
          <p key={'e' + c.id} className="cmp-error">
            {interpolate(s.cmp_data_error ?? 'Could not load data for {name}.', { name: c.name })}
          </p>
        ) : null
      )}

      {/* ---------- Headline cards ---------- */}
      {loadedRows.length > 0 && (
        <div className="cmp-cards">
          {loadedRows.map(r => {
            const year = yearFor(r.data);
            const entry = seriesAt(r.data, year);
            const ciYears = r.data.composite_index
              ? Object.keys(r.data.composite_index).map(Number).filter(n => !Number.isNaN(n))
              : [];
            const ciYear = ciYears.length ? Math.max(...ciYears) : null;
            const ci = ciYear !== null ? r.data.composite_index?.[String(ciYear)] : undefined;
            const natTotal = natSeries?.rate_per_100k ?? null;
            const diff =
              entry && natTotal && !mixedYears && !natMissing
                ? Math.round(((entry.rate_per_100k - natTotal) / natTotal) * 100)
                : null;
            return (
              <div key={r.entry.id} className="cmp-card" style={{ borderLeftColor: colorFor(r.entry.id) }}>
                <div className="cmp-card-head">
                  <span className="cmp-card-name">{r.data.name}</span>
                  <span className="cmp-card-region">{regionName(r.data.region_id)}</span>
                </div>
                <div className="cmp-card-rate">
                  <span className="cmp-card-num">
                    {entry ? formatRate(entry.rate_per_100k, lang) : '—'}
                  </span>
                  <span className="cmp-card-cap">{t.cx_total_rate}</span>
                </div>
                <div className="cmp-card-meta">
                  {ci && (
                    <span className="cmp-band" style={{ background: BAND_TOKEN[ci.level] }}>
                      {s.cmp_composite_label} {ci.score.toFixed(1)} · {CI_BANDS[ci.level]?.[lang] ?? ''} ({ciYear})
                    </span>
                  )}
                  {ci && (
                    <a className="cmp-what" href={lang === 'es' ? '/es/metodologia/' : '/methodology/'}>
                      {s.cmp_what_is_this}
                    </a>
                  )}
                  {ci && <span className="cmp-rank">{interpolate(t.cx_rank_line, { rank: ci.rank })}</span>}
                  {r.data.trend ? (
                    <span
                      className="cmp-trend"
                      style={{ color: `var(--trend-${r.data.trend})` }}
                      role="img"
                      aria-label={
                        lang === 'es'
                          ? r.data.trend === 'up' ? 'Al alza' : r.data.trend === 'down' ? 'A la baja' : 'Estable'
                          : r.data.trend === 'up' ? 'Rising' : r.data.trend === 'down' ? 'Declining' : 'Stable'
                      }
                    >
                      {TREND_ARROW[r.data.trend]}
                    </span>
                  ) : (
                    <span className="cmp-rank" title={s.cmp_trend_unavailable}>—</span>
                  )}
                  {diff !== null && (
                    <span className={'cmp-diff' + (diff > 0 ? ' is-up' : diff < 0 ? ' is-down' : '')}>
                      {diff === 0
                        ? t.cx_at_mean
                        : interpolate(diff > 0 ? t.cx_above_mean : t.cx_below_mean, { pct: Math.abs(diff) })}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ---------- The chart ---------- */}
      {loadedRows.length > 0 && (
        <section className="cmp-chart" aria-labelledby="cmp-chart-h">
          <header className="cmp-chart-head">
            <h2 id="cmp-chart-h" className="cmp-chart-h">{t.cx_profile_heading}</h2>
            {!mixedYears && sharedYear !== null && (
              <span className="cmp-chart-year">
                {interpolate(t.cx_reference_year, { year: sharedYear })}
              </span>
            )}
            {!natMissing && (
              <span className="cmp-legend">
                <span className="cmp-legend-line" aria-hidden="true" />
                {t.cx_national_line}
              </span>
            )}
          </header>

          {!natMissing && mixedYears && (
            <p className="cmp-warn">{interpolate(t.cx_mixed_years, { years: mixedYearLabel })}</p>
          )}

          {chartRows.map(row => (
            <div key={row.family} className="cmpx-row">
              <span className="cmpx-label">{row.label}</span>
              <span
                className="cmpx-track"
                role="img"
                aria-label={interpolate(t.cx_row_aria, {
                  family: row.label,
                  values: row.cells
                    .map(c => `${c.name} ${c.value !== null ? formatRate(c.value, lang) : '—'}`)
                    .concat(row.mean !== null ? [`${t.cx_national_line} ${formatRate(row.mean, lang)}`] : [])
                    .join(', '),
                })}
              >
                <span className="cmpx-base" aria-hidden="true" />
                {row.linkWidth > 0 && (
                  <span
                    className="cmpx-link"
                    aria-hidden="true"
                    style={{ left: `${row.linkLeft}%`, width: `${row.linkWidth}%` }}
                  />
                )}
                {row.meanPos !== null && (
                  <span className="cmpx-mean" aria-hidden="true" style={{ left: `${row.meanPos}%` }} />
                )}
                {row.cells.map(c =>
                  c.pos === null ? null : (
                    <span
                      key={c.id}
                      className="cmpx-dot"
                      aria-hidden="true"
                      title={`${c.name} · ${formatRate(c.value as number, lang)}`}
                      style={{ left: `${c.pos}%`, background: c.color }}
                    />
                  )
                )}
              </span>
              <span className="cmpx-values">
                {row.cells.map(c => (
                  <span key={c.id} className="cmpx-val">
                    <span className="cmpx-val-dot" style={{ background: c.color }} aria-hidden="true" />
                    <span className={'cmpx-val-num' + (row.lowest !== null && c.value === row.lowest ? ' is-low' : '')}>
                      {c.value !== null ? formatRate(c.value, lang) : '—'}
                    </span>
                  </span>
                ))}
              </span>
            </div>
          ))}

          <p className="cmp-scale-note">{t.cx_scale_note}</p>

          {/* Homicide — kept off the shared scale (different order of magnitude)
              and always sourced from featured_rates, never by_family (Pitfall 1). */}
          <div className="cmp-hom">
            <span className="cmp-hom-h">{t.cx_homicide_heading}</span>
            {loadedRows.map(r => {
              const year = yearFor(r.data);
              const homRate = year !== null ? r.data.featured_rates?.homicidios?.[String(year)] : undefined;
              const homCount = year !== null ? r.data.featured_rates?.homicidios_count?.[String(year)] : undefined;
              return (
                <span key={r.entry.id} className="cmp-hom-item">
                  <span className="cmpx-val-dot" style={{ background: colorFor(r.entry.id) }} aria-hidden="true" />
                  <span className="cmp-hom-name">
                    {mixedYears ? `${r.data.name} · ${year ?? '—'}` : r.data.name}
                  </span>
                  <span className="cmp-hom-val">
                    {homRate !== undefined
                      ? `${formatDecimal(homRate, lang)}${
                          homCount !== undefined
                            ? ` (${homCount} ${
                                homCount === 1
                                  ? s.cmp_case_singular ?? (lang === 'es' ? 'caso' : 'case')
                                  : s.cmp_case_plural ?? (lang === 'es' ? 'casos' : 'cases')
                              })`
                            : ''
                        }`
                      : interpolate(s.cmp_homicide_no_data ?? 'No reported cases — CEAD {year}', { year: year ?? '—' })}
                  </span>
                </span>
              );
            })}
            {!mixedYears && (
              <span className="cmp-hom-note">
                {interpolate(s.cmp_homicide_row ?? 'Homicide (per 100k, {year})', { year: sharedYear ?? natYear ?? '—' })}
              </span>
            )}
          </div>
        </section>
      )}

      {/* ---------- Plain-language summary ---------- */}
      {summary && <p className="cmp-summary">{summary}</p>}

      {/* ---------- Same figures as a table, for screen readers and copy/paste ---------- */}
      {loadedRows.length > 0 && (
        <table className="cmp-sr-table">
          <caption>{t.cx_table_caption}</caption>
          <thead>
            <tr>
              <th scope="col">{t.cx_th_family}</th>
              {loadedRows.map(r => (
                <th key={r.entry.id} scope="col">
                  {mixedYears ? `${r.data.name} (${yearFor(r.data) ?? '—'})` : r.data.name}
                </th>
              ))}
              <th scope="col">{t.cx_national_line}</th>
            </tr>
          </thead>
          <tbody>
            {chartRows.map(row => (
              <tr key={row.family}>
                <th scope="row">{row.label}</th>
                {row.cells.map(c => (
                  <td key={c.id}>{c.value !== null ? formatRate(c.value, lang) : '—'}</td>
                ))}
                <td>{row.mean !== null ? formatRate(row.mean, lang) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* ---------- Component styles ----------
          Scoped by the .comparator-island / .cmp*-prefixed class names. Only the
          three dynamic values (slot color, dot position, band token) are inline. */}
      <style>{`
        .comparator-island { padding: var(--md) 0; }

        .cmp-slotbar { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sm); margin-bottom: var(--md); }
        .cmp-tag { display: inline-flex; align-items: center; gap: 9px; height: 44px; padding: 0 var(--sm) 0 var(--md);
          border: 1.5px solid var(--line); border-radius: 999px; background: var(--card); }
        .cmp-tag-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; background: #8892a0; }
        .cmp-tag-name { font-size: var(--text-body); font-weight: var(--weight-strong); color: var(--ink); }
        .cmp-tag-region { font-size: var(--text-label); color: var(--muted); }
        .cmp-tag-x { width: 44px; height: 44px; margin: -7px 0; display: inline-flex; align-items: center; justify-content: center;
          border: none; border-radius: 50%; background: var(--bg); color: var(--muted); font-size: 16px; line-height: 1;
          cursor: pointer; font-family: var(--font); }
        .cmp-tag-x:hover { background: var(--line); color: var(--ink); }

        .cmp-addslot { position: relative; display: flex; align-items: center; gap: var(--sm); width: 300px; height: 44px;
          padding: 0 var(--md); border: 1.5px dashed var(--line); border-radius: 999px; background: var(--card); }
        .cmp-addslot:focus-within { border-color: var(--primary); border-style: solid; }
        .cmp-addslot-icon { color: var(--muted); display: inline-flex; flex-shrink: 0; }
        .cmp-addslot input { flex: 1; min-width: 0; border: none; outline: none; background: transparent;
          font-family: var(--font); font-size: var(--text-body); color: var(--ink); }

        .cmp-listbox { position: absolute; top: calc(100% + 6px); left: 0; width: 420px; max-width: 90vw; z-index: 50;
          margin: 0; padding: 0; list-style: none; background: var(--card); border: 1px solid var(--line);
          border-radius: var(--radius); overflow: hidden; box-shadow: 0 10px 24px rgba(28,42,43,0.12); }
        .cmp-option { display: flex; align-items: center; gap: var(--sm); min-height: 46px; padding: 0 var(--md);
          border-bottom: 1px solid var(--line); cursor: pointer; font-size: var(--text-label); }
        .cmp-option:last-child { border-bottom: none; }
        .cmp-option.is-active, .cmp-option:hover { background: var(--bg); }
        .cmp-option--empty { color: var(--muted); cursor: default; }
        .cmp-option-name { font-weight: var(--weight-strong); color: var(--ink); }
        .cmp-option-region { color: var(--muted); margin-left: auto; }
        .cmp-option-lowpop { font-size: 12px; color: var(--muted); background: var(--bg); border-radius: 4px; padding: 1px 6px; }

        .cmp-maxnote { font-size: var(--text-label); color: var(--muted); }
        .cmp-sort { margin-left: auto; min-height: 44px; padding: 0 var(--md); border: 1.5px solid var(--line);
          border-radius: 999px; background: var(--card); color: var(--muted); font-family: var(--font);
          font-size: var(--text-label); font-weight: var(--weight-strong); cursor: pointer; }
        .cmp-sort:hover { color: var(--ink); border-color: var(--muted); }

        .cmp-empty { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius);
          padding: var(--xl) var(--lg); text-align: center; }
        .cmp-empty-h { font-size: var(--text-heading); font-weight: var(--weight-strong); color: var(--ink); margin: 0 0 var(--xs); }
        .cmp-empty-b { font-size: var(--text-label); color: var(--muted); margin: 0 0 var(--lg); }
        .cmp-chips { display: flex; flex-wrap: wrap; gap: var(--sm); justify-content: center; align-items: center; }
        .cmp-chips-label { font-size: var(--text-label); color: var(--muted); }
        .cmp-chip { min-height: 44px; padding: 0 var(--md); border: 1.5px solid var(--line); border-radius: 999px;
          background: var(--card); color: var(--ink); font-family: var(--font); font-size: var(--text-label);
          font-weight: var(--weight-strong); cursor: pointer; white-space: nowrap; }
        .cmp-chip:hover { border-color: var(--primary); color: var(--primary); }

        .cmp-hint { font-size: var(--text-label); color: var(--muted); margin: 0 0 var(--sm); }
        .cmp-error { font-size: var(--text-label); color: var(--trend-up); margin: 0 0 var(--sm); }

        .cmp-cards { display: flex; flex-wrap: wrap; gap: var(--sm); margin-bottom: var(--md); }
        .cmp-card { flex: 1 1 260px; background: var(--card); border: 1px solid var(--line); border-left: 4px solid var(--line);
          border-radius: var(--radius); padding: var(--md); }
        .cmp-card-head { display: flex; align-items: baseline; gap: var(--sm); flex-wrap: wrap; }
        .cmp-card-name { font-size: var(--text-heading); font-weight: var(--weight-strong); color: var(--ink); }
        .cmp-card-region { font-size: var(--text-label); color: var(--muted); }
        .cmp-card-rate { display: flex; align-items: baseline; gap: var(--sm); margin-top: var(--xs); flex-wrap: wrap; }
        .cmp-card-num { font-size: var(--text-display); font-weight: var(--weight-strong); color: var(--ink);
          font-variant-numeric: tabular-nums; line-height: 1.1; }
        .cmp-card-cap { font-size: var(--text-label); color: var(--muted); }
        .cmp-card-meta { display: flex; align-items: center; flex-wrap: wrap; gap: var(--sm); margin-top: var(--sm); }
        .cmp-band { display: inline-flex; align-items: center; min-height: 26px; padding: 2px var(--sm); border-radius: 999px;
          font-size: 12px; font-weight: var(--weight-strong); color: var(--ink); }
        .cmp-what { font-size: var(--text-label); color: var(--muted); text-decoration: underline; }
        .cmp-what:hover { color: var(--ink); }
        .cmp-rank, .cmp-trend { font-size: var(--text-label); color: var(--muted); }
        .cmp-diff { font-size: var(--text-label); font-weight: var(--weight-strong); color: var(--muted); }
        .cmp-diff.is-up { color: var(--trend-up); }
        .cmp-diff.is-down { color: var(--trend-down); }

        .cmp-chart { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius);
          padding: var(--md) var(--lg) var(--lg); }
        .cmp-chart-head { display: flex; align-items: baseline; flex-wrap: wrap; gap: var(--sm) var(--md);
          padding-bottom: var(--sm); border-bottom: 1px solid var(--line); }
        .cmp-chart-h { font-size: var(--text-heading); font-weight: var(--weight-strong); color: var(--ink); margin: 0; }
        .cmp-chart-year { font-size: var(--text-label); color: var(--muted); }
        .cmp-legend { margin-left: auto; display: inline-flex; align-items: center; gap: 7px;
          font-size: var(--text-label); color: var(--muted); }
        .cmp-legend-line { display: inline-block; width: 0; height: 14px; border-left: 2px dashed var(--ink); }
        .cmp-warn { font-size: var(--text-label); color: var(--muted); margin: var(--sm) 0 0; }

        .cmpx-row { display: grid; grid-template-columns: 190px 1fr 200px; align-items: center; gap: var(--md);
          padding: 11px 0; border-bottom: 1px solid var(--bg); }
        .cmpx-label { font-size: var(--text-label); font-weight: var(--weight-strong); color: var(--ink); line-height: 1.3; }
        .cmpx-track { position: relative; display: block; height: 26px; }
        .cmpx-base { position: absolute; left: 0; right: 0; top: 11px; height: 4px; border-radius: 2px; background: var(--bg); }
        .cmpx-link { position: absolute; top: 11px; height: 4px; border-radius: 2px; background: var(--line); }
        .cmpx-mean { position: absolute; top: 0; bottom: 0; border-left: 2px dashed var(--ink); }
        .cmpx-dot { position: absolute; top: 5px; width: 16px; height: 16px; margin-left: -8px; border-radius: 50%;
          background: #8892a0; border: 2px solid var(--card); box-shadow: 0 1px 3px rgba(28,42,43,0.25); }
        .cmpx-values { display: flex; align-items: center; justify-content: flex-end; gap: var(--md); }
        .cmpx-val { display: inline-flex; align-items: baseline; gap: 5px; }
        .cmpx-val-dot { width: 8px; height: 8px; border-radius: 50%; background: #8892a0; }
        .cmpx-val-num { font-size: var(--text-body); font-weight: var(--weight-strong); color: var(--muted);
          font-variant-numeric: tabular-nums; }
        .cmpx-val-num.is-low { color: var(--ink); }

        .cmp-scale-note { font-size: 12px; color: var(--muted); margin: var(--sm) 0 0; }

        .cmp-hom { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sm) var(--md);
          margin-top: var(--md); padding-top: var(--md); border-top: 1px solid var(--line); }
        .cmp-hom-h { font-size: var(--text-label); font-weight: var(--weight-strong); color: var(--ink); }
        .cmp-hom-item { display: inline-flex; align-items: baseline; gap: 6px; font-size: var(--text-label); }
        .cmp-hom-name { color: var(--muted); }
        .cmp-hom-val { color: var(--ink); font-weight: var(--weight-strong); font-variant-numeric: tabular-nums; }
        .cmp-hom-note { margin-left: auto; font-size: 12px; color: var(--muted); }

        .cmp-summary { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius);
          padding: var(--md) var(--lg); margin: var(--md) 0 0; font-size: var(--text-body); line-height: 1.6; color: var(--ink); }

        .cmp-sr-table { position: absolute; width: 1px; height: 1px; margin: -1px; padding: 0; overflow: hidden;
          clip: rect(0 0 0 0); white-space: nowrap; border: 0; }

        @media (max-width: 860px) {
          .cmpx-row { grid-template-columns: 150px 1fr 150px; gap: var(--sm); }
          .cmp-addslot { width: 100%; }
          .cmp-sort { margin-left: 0; }
        }
        @media (max-width: 640px) {
          .cmpx-row { grid-template-columns: 1fr; gap: var(--xs); padding: var(--sm) 0; }
          .cmpx-values { justify-content: flex-start; }
          .cmp-chart { padding: var(--md); }
          .cmp-hom-note { margin-left: 0; }
        }
      `}</style>
    </div>
  );
}
