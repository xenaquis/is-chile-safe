/**
 * ResultPanel.tsx — Commune detail side panel.
 *
 * Fetches /data/cead/comunas/{cut}.json on open (D-13).
 * Shows skeleton while loading; renders full panel on success.
 *
 * Key wiring decisions:
 * - series.by_family is a RECORD (keyed by family name) in comunas/{cut}.json
 * - map-payload.by_family is an ARRAY (indexed by catalog order)
 * - Convert RECORD → catalog-indexed ARRAY here for PanelFamilyBars
 *   using CATALOG_KEY_ORDER (vida=0, robos_violentos=1, vif=2, drogas=3, armas=4, propiedad=5, incivilidades=6)
 *
 * T-03-02-01: No dangerouslySetInnerHTML; all strings via JSX (auto-escaped).
 * T-03-02-02: Fetch only hardcoded same-origin /data/cead/comunas/{cut}.json path.
 */
import { useEffect, useState } from 'react';
import { PanelSparkline } from './PanelSparkline';
import { PanelFamilyBars } from './PanelFamilyBars';
import { IncidentsList, type Incident } from './IncidentsList';

// Catalog family_keys order (catalog.json):
// 0=vida, 1=robos_violentos, 2=vif, 3=drogas, 4=armas, 5=propiedad, 6=incivilidades
const CATALOG_KEY_ORDER = [
  'vida',
  'robos_violentos',
  'vif',
  'drogas',
  'armas',
  'propiedad',
  'incivilidades',
] as const;

// Total communes for national rank display
const TOTAL_COMMUNES = 346;

// Trend arrow symbols and CSS classes
const TREND_ARROW: Record<string, string> = {
  up: '↑',
  down: '↓',
  stable: '→',
};

interface SeriesEntry {
  year: number;
  rate_per_100k: number;
  partial?: boolean;
  by_family: Record<string, number>;
}

interface CommuneData {
  id: string;
  name: string;
  slug: string;
  region_id: string;
  population: number;
  low_population: boolean;
  national_rank: number;
  regional_rank: number;
  trend: 'up' | 'down' | 'stable';
  series: SeriesEntry[];
  last_updated?: string;
  incidents?: Incident[];
}

interface Props {
  cut: string;
  lang: 'en' | 'es';
  year: number;
  onClose: () => void;
}

/** Convert series by_family RECORD → catalog-indexed ARRAY for PanelFamilyBars */
function recordToArray(byFamilyRecord: Record<string, number>): number[] {
  return CATALOG_KEY_ORDER.map((key) => byFamilyRecord[key] ?? 0);
}

/** Get region display name from region_id (fallback to region_id if unknown) */
const REGION_NAMES: Record<string, { es: string; en: string }> = {
  '1':  { es: 'Región de Tarapacá',          en: 'Tarapacá Region' },
  '2':  { es: 'Región de Antofagasta',        en: 'Antofagasta Region' },
  '3':  { es: 'Región de Atacama',            en: 'Atacama Region' },
  '4':  { es: 'Región de Coquimbo',           en: 'Coquimbo Region' },
  '5':  { es: 'Región de Valparaíso',         en: 'Valparaíso Region' },
  '6':  { es: 'Región del Lib. Gral. B. O\'Higgins', en: "O'Higgins Region" },
  '7':  { es: 'Región del Maule',             en: 'Maule Region' },
  '8':  { es: 'Región del Biobío',            en: 'Biobío Region' },
  '9':  { es: 'Región de La Araucanía',       en: 'Araucanía Region' },
  '10': { es: 'Región de Los Lagos',          en: 'Los Lagos Region' },
  '11': { es: 'Región de Aysén',              en: 'Aysén Region' },
  '12': { es: 'Región de Magallanes',         en: 'Magallanes Region' },
  '13': { es: 'Región Metropolitana',         en: 'Metropolitan Region' },
  '14': { es: 'Región de Los Ríos',           en: 'Los Ríos Region' },
  '15': { es: 'Región de Arica y Parinacota', en: 'Arica y Parinacota Region' },
  '16': { es: 'Región de Ñuble',              en: 'Ñuble Region' },
  '56': { es: 'Región de Valparaíso',         en: 'Valparaíso Region' },
};

export function ResultPanel({ cut, lang, year, onClose }: Props) {
  const [data, setData] = useState<CommuneData | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);

  // Fetch commune data on open (D-13 — fetch-on-open, not bundled)
  useEffect(() => {
    setLoading(true);
    setData(null);
    setFetchError(false);

    // T-03-02-02: only hardcoded same-origin path; cut is a numeric CUT string
    fetch(`/data/cead/comunas/${cut}.json`)
      .then((r) => {
        if (!r.ok) throw new Error('fetch failed');
        return r.json() as Promise<CommuneData>;
      })
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => {
        setFetchError(true);
        setLoading(false);
      });
  }, [cut]);

  // Skeleton loading state
  if (loading) {
    return (
      <aside
        className="result-panel"
        aria-busy="true"
        aria-label={lang === 'es' ? 'Cargando datos de la comuna' : 'Loading commune data'}
      >
        <div className="panel-head">
          <div>
            <div className="skeleton" style={{ height: 28, width: '60%' }} />
            <div className="skeleton" style={{ height: 14, width: '40%' }} />
          </div>
          <button className="panel-close" onClick={onClose} aria-label={lang === 'es' ? 'Cerrar' : 'Close'}>×</button>
        </div>
        <div className="skeleton" style={{ height: 44 }} />
        <div className="skeleton" style={{ height: 14, width: '70%' }} />
        <div className="skeleton" style={{ height: 44 }} />
      </aside>
    );
  }

  // Error state
  if (fetchError || !data) {
    return (
      <aside className="result-panel">
        <div className="panel-head">
          <h2>{lang === 'es' ? 'Error al cargar' : 'Load error'}</h2>
          <button className="panel-close" onClick={onClose} aria-label={lang === 'es' ? 'Cerrar' : 'Close'}>×</button>
        </div>
        <p style={{ color: 'var(--muted)' }}>
          {lang === 'es' ? 'No se pudo cargar la información.' : 'Could not load commune data.'}
        </p>
      </aside>
    );
  }

  // Find series entry for the selected year
  const seriesEntry = data.series.find((s) => s.year === year)
    ?? data.series[data.series.length - 1]; // fallback to latest

  const rate = seriesEntry?.rate_per_100k ?? null;
  const displayRate = rate !== null ? Math.round(rate).toLocaleString('es-CL') : '—';

  // Build sparkline series (all years, no filtering)
  const sparklineSeries = data.series.map((s) => ({
    year: s.year,
    rate_per_100k: s.rate_per_100k,
    partial: s.partial,
  }));
  const seriesYears = sparklineSeries.map((s) => s.year);
  const firstYear = seriesYears.length > 0 ? Math.min(...seriesYears) : 2005;
  const lastYear = seriesYears.length > 0 ? Math.max(...seriesYears) : year;

  // Convert series by_family RECORD → catalog-indexed ARRAY for PanelFamilyBars
  const byFamilyArray: number[] = seriesEntry?.by_family
    ? recordToArray(seriesEntry.by_family)
    : new Array(7).fill(0);

  // Determine commune level from rate (approximate — use median level 3 if unknown)
  // For display: map rate to level via 5-quintile approximation
  // (exact level not in comunas JSON — derive from rate position in series)
  const maxRate = Math.max(...data.series.map((s) => s.rate_per_100k), 1);
  const pct = rate !== null ? rate / maxRate : 0;
  const level: 1 | 2 | 3 | 4 | 5 =
    pct > 0.8 ? 5 : pct > 0.6 ? 4 : pct > 0.4 ? 3 : pct > 0.2 ? 2 : 1;

  const regionName = REGION_NAMES[data.region_id]?.[lang] ?? `Región ${data.region_id}`;
  const trend = data.trend;
  const trendArrow = TREND_ARROW[trend] ?? '→';
  const trendClass = trend === 'up' ? 'up' : trend === 'down' ? 'down' : 'stable';

  const trendLabel = {
    up:     lang === 'es' ? 'En aumento' : 'Increasing',
    down:   lang === 'es' ? 'En descenso' : 'Decreasing',
    stable: lang === 'es' ? 'Estable' : 'Stable',
  }[trend] ?? 'Stable';

  const ctaHref = lang === 'es'
    ? `/es/comuna/${data.slug}/`
    : `/commune/${data.slug}/`;

  return (
    <aside className="result-panel">
      {/* 1. Panel head: name + region + close */}
      <div className="panel-head">
        <div>
          <h2>{data.name}</h2>
          <div className="panel-region">{regionName}</div>
        </div>
        <button className="panel-close" onClick={onClose} aria-label={lang === 'es' ? 'Cerrar' : 'Close'}>×</button>
      </div>

      {/* 2. Level chip + CEAD attribution */}
      <div className="panel-badge-row">
        <span className="level-chip">
          <span
            aria-hidden="true"
            style={{ width: 8, height: 8, borderRadius: '50%', background: `var(--s${level})`, display: 'inline-block', flexShrink: 0 }}
          />
          {lang === 'es' ? `Nivel ${level}` : `Level ${level}`}
        </span>
        <span className="cead-badge">
          {lang === 'es' ? 'Datos CEAD' : 'CEAD data'}
        </span>
      </div>

      {/* 3. Stat card: rate */}
      <div className="stat-card">
        <div className="stat-big">~{displayRate}</div>
        <div className="stat-unit">
          {lang === 'es'
            ? `Tasa por 100.000 hab. (${year})`
            : `Rate per 100,000 inhab. (${year})`}
        </div>
      </div>

      {/* 4. Mini-stats row: trend + national rank */}
      <div className="mini-stats-row">
        <div className="mini-stat">
          <div className="mini-stat-label">{lang === 'es' ? 'Tendencia' : 'Trend'}</div>
          <span className={`trend-chip ${trendClass}`}>
            {trendArrow} {trendLabel}
          </span>
        </div>
        <div className="mini-stat">
          <div className="mini-stat-label">{lang === 'es' ? 'Posición nacional' : 'National rank'}</div>
          <span>
            #{data.national_rank} {lang === 'es' ? 'de' : 'of'} {TOTAL_COMMUNES}
          </span>
        </div>
      </div>

      {/* 5. Sparkline section */}
      <div className="panel-section">
        <h4>
          {lang === 'es'
            ? `Evolución anual (${firstYear}–${lastYear})`
            : `Annual evolution (${firstYear}–${lastYear})`}
        </h4>
        <PanelSparkline series={sparklineSeries} activeYear={year} />
        <div className="sparkline-axis">
          <span>{firstYear}</span>
          <span>{lastYear}</span>
        </div>
      </div>

      {/* 6. Family breakdown */}
      <div className="panel-section">
        <h4>
          {lang === 'es'
            ? `Incidencia por categoría (${year})`
            : `Incidence by category (${year})`}
        </h4>
        <PanelFamilyBars byFamily={byFamilyArray} locale={lang} level={level} />
      </div>

      {/* 7. Incidents section */}
      <div className="panel-section">
        <h4>{lang === 'es' ? 'Incidentes recientes' : 'Recent incidents'}</h4>
        <IncidentsList incidents={data.incidents} lang={lang} />
      </div>

      {/* 8. CTA button */}
      <a href={ctaHref} className="panel-cta">
        {lang === 'es' ? 'Ver ficha completa' : 'View full profile'}
      </a>

      {/* 9. Official source row */}
      <div className="official-row">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" className="official-check">
          <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
          <path d="M4.5 8l2.5 2.5 4.5-4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span>{lang === 'es' ? 'Fuente: CEAD' : 'Source: CEAD'}</span>
      </div>
    </aside>
  );
}
