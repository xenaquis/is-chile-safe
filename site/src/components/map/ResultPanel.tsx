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
import { RateTooltip } from './RateTooltipReact';
import { EN_STRINGS, ES_STRINGS } from '../../config/i18n';
import { formatRate, formatDecimal } from '../../lib/formatNumber';

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

// Composite index data year — commune JSON stores composite_index only under "2024".
// This constant mirrors commune/[slug].astro:COMPOSITE_YEAR and must be updated
// together when new index vintages are published.
const COMPOSITE_YEAR = 2024;

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
  population: number;
  low_population: boolean;
  national_rank: number;
  regional_rank: number;
  trend: 'up' | 'down' | 'stable';
  series: SeriesEntry[];
  last_updated?: string;
  incidents?: Incident[];
  featured_rates?: {
    homicidios?: Record<string, number>;
    homicidios_count?: Record<string, number>;
    propiedad?: Record<string, number>;
    secuestros?: Record<string, number>;
  };
  // Phase 18-04 additive fields (D-12)
  composite_index?: Record<string, CompositeIndexEntry>;
  spd_homicide_rate?: Record<string, number>;
  sii_exposure_index?: Record<string, number | null>;
}

interface Props {
  cut: string;
  lang: 'en' | 'es';
  year: number;
  nationalAvg: number;
  onClose: () => void;
  /** Current choropleth mode — 'composite' when index mode is active, 'family' for per-family rate mode.
   *  Plan 04 uses this prop to gate the composite score block (D-06). */
  mode?: 'composite' | 'family';
}

/** Convert series by_family RECORD → catalog-indexed ARRAY for PanelFamilyBars */
function recordToArray(byFamilyRecord: Record<string, number>): number[] {
  return CATALOG_KEY_ORDER.map((key) => byFamilyRecord[key] ?? 0);
}

/** Region display name from region_id (clean 1–16 since 999.1 / quick-260616-ldi).
 *  Fallback to `Región {id}` only if an unknown id ever appears. */
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
};

// Band label arrays (D-08) — index 0 = level 1 (Very Low), index 4 = level 5 (Very High)
const BAND_EN = ['Very Low', 'Low', 'Moderate', 'High', 'Very High'] as const;
const BAND_ES = ['Muy Bajo', 'Bajo', 'Moderado', 'Alto', 'Muy Alto'] as const;

export function ResultPanel({ cut, lang, year, nationalAvg, onClose, mode = 'family' }: Props) {
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
  const displayRate = rate !== null ? formatRate(rate, lang) : '—';

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

      {/* 2b. Composite index section (D-06 — rendered ONLY when mode === 'composite') */}
      {mode === 'composite' && (() => {
        const ci = data.composite_index?.[String(COMPOSITE_YEAR)];
        if (!ci) return null;
        const bandLabel = lang === 'es' ? BAND_ES[ci.level - 1] : BAND_EN[ci.level - 1];
        const regionName2 = REGION_NAMES[data.region_id]?.[lang] ?? `Región ${data.region_id}`;
        const rankRegional = lang === 'es'
          ? ES_STRINGS.ci_rank_regional
              .replace('#{rank}', `#${ci.regional_rank}`)
              .replace('{region}', regionName2)
          : EN_STRINGS.ci_rank_regional
              .replace('#{rank}', `#${ci.regional_rank}`)
              .replace('{region}', regionName2);
        const nationalRankStr = lang === 'es'
          ? ES_STRINGS.ci_rank_national
              .replace('#{rank}', `#${ci.rank}`)
              .replace('{total}', String(TOTAL_COMMUNES))
          : EN_STRINGS.ci_rank_national
              .replace('#{rank}', `#${ci.rank}`)
              .replace('{total}', String(TOTAL_COMMUNES));
        const caveatText = lang === 'es' ? ES_STRINGS.ci_caveat_text : EN_STRINGS.ci_caveat_text;
        const sectionHeading = lang === 'es' ? ES_STRINGS.ci_section_heading : EN_STRINGS.ci_section_heading;
        return (
          <div className="panel-section composite-index-section">
            <h4>{sectionHeading}</h4>
            <div>
              <span className="stat-big">{Math.round(ci.score)}</span>
              <span className="stat-unit">{bandLabel}</span>
            </div>
            <div className="ci-rank">
              {nationalRankStr} · {rankRegional}
            </div>
            {/* D-07: always-visible caveat — never behind <details> */}
            <div className="ci-caveat">{caveatText}</div>
          </div>
        );
      })()}

      {/* 3. Stat card: rate */}
      <div className="stat-card" style={{ overflow: 'visible' }}>
        <div className="stat-big">{displayRate}</div>
        <div className="stat-unit" style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
          {lang === 'es'
            ? `Tasa por 100.000 hab. (${year})`
            : `Rate per 100,000 inhab. (${year})`}
          <RateTooltip
            lang={lang}
            label={lang === 'es' ? ES_STRINGS.rate_tooltip_title : EN_STRINGS.rate_tooltip_title}
            tip={lang === 'es' ? ES_STRINGS.rate_tooltip_body : EN_STRINGS.rate_tooltip_body}
          />
        </div>
        {/* Multiplier vs national average (D-04) */}
        {rate !== null && nationalAvg > 0 && (() => {
          const multiplierNum = rate / nationalAvg;
          const multiplierStr = formatDecimal(multiplierNum, lang, 1);
          const compTemplate = lang === 'es' ? ES_STRINGS.comparison_national : EN_STRINGS.comparison_national;
          const compLabel = compTemplate.replace('{multiplier}', multiplierStr);
          const barWidth = `${Math.min((rate / (nationalAvg * 3)), 1) * 100}%`;
          return (
            <div className="comparison-block">
              <div className="comparison-bar-wrapper" aria-hidden="true">
                <div className="comparison-bar-track">
                  <div
                    className="comparison-bar-fill"
                    style={{ width: barWidth, background: `var(--s${level})` }}
                  />
                  <div className="comparison-bar-avg-marker" style={{ left: '33.3%' }} />
                </div>
              </div>
              <div className="comparison-bar-label">{compLabel}</div>
            </div>
          );
        })()}
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

      {/* 7. Homicide breakdown (D-06/D-07) — separate from vida family bar (HOM-02) */}
      {(() => {
        const hom = data.featured_rates?.homicidios;
        const homCount = data.featured_rates?.homicidios_count;
        // Use !== undefined (not truthiness) — confirmed 0 must NOT read as "no data" (Pitfall 5)
        const homRate = hom !== undefined ? (hom[String(year)] !== undefined ? hom[String(year)] : null) : null;
        const count = homCount !== undefined ? (homCount[String(year)] !== undefined ? homCount[String(year)] : null) : null;
        const hasData = homRate !== null;
        return (
          <div className="panel-section">
            <h4>{lang === 'es' ? `Homicidios (${year})` : `Homicide (${year})`}</h4>
            {hasData ? (
              <div>
                <span className="stat-mid">{formatRate(homRate!, lang)}</span>
                {lang === 'es' ? ' por 100.000 hab.' : ' per 100,000 inhab.'}
                {count !== null && (
                  <span className="stat-sub">
                    {' '}({count} {lang === 'es' ? (count === 1 ? 'caso' : 'casos') : (count === 1 ? 'case' : 'cases')})
                  </span>
                )}
              </div>
            ) : (
              <p style={{ color: 'var(--muted)' }}>
                {lang === 'es' ? `Sin casos reportados — CEAD ${year}` : `No reported cases — CEAD ${year}`}
              </p>
            )}
            <div className="official-row" style={{ fontSize: '0.78rem', marginTop: 4 }}>
              {lang === 'es'
                ? `Fuente: CEAD, subgrupo 101 Delitos contra la Vida (${year})`
                : `Source: CEAD, subgroup 101 Life Crimes (${year})`}
            </div>
          </div>
        );
      })()}

      {/* 8. Incidents section */}
      <div className="panel-section">
        <h4>{lang === 'es' ? 'Incidentes recientes' : 'Recent incidents'}</h4>
        <IncidentsList incidents={data.incidents} lang={lang} />
      </div>

      {/* 9. CTA button */}
      <a href={ctaHref} className="panel-cta">
        {lang === 'es' ? 'Ver ficha completa' : 'View full profile'}
      </a>

      {/* 10. Official source row */}
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
