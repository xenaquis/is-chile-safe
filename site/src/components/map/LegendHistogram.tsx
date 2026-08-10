/**
 * LegendHistogram.tsx — MAPV2 replacement for Legend.tsx.
 *
 * The legend stops being a passive color key: it shows the distribution of
 * the 346 communes across the current layer's scale (histogram strip), the
 * commune count per band, and each band row is a button that ISOLATES that
 * band on the map (MapIsland dims everything else via applyBandDim, still
 * setStyle-in-place — D-12).
 *
 * Composite mode: no rate unit exists, so the histogram strip is hidden and
 * rows show qualitative label + count only (matches the old Legend, which
 * also hid numeric ranges in composite mode).
 *
 * Desktop expanded / mobile <details> pattern ported from Legend.tsx.
 */
import { INCIDENCE_COLORS } from './colors';
import { EN_STRINGS, ES_STRINGS } from '../../config/i18n';
import { formatRate } from '../../lib/formatNumber';
import { mapV2Strings } from '../../config/mapV2Strings';
import { computeHistBins, type LayerStats } from './bandStats';

interface Props {
  lang: 'en' | 'es';
  stats: LayerStats | null;
  mode: 'composite' | 'family';
  band: number | null;
  onBandChange: (band: number | null) => void;
  showIncidents?: boolean;
}

const QUAL_LABELS_EN = [
  EN_STRINGS.legend_qual_1,
  EN_STRINGS.legend_qual_2,
  EN_STRINGS.legend_qual_3,
  EN_STRINGS.legend_qual_4,
  EN_STRINGS.legend_qual_5,
];

const QUAL_LABELS_ES = [
  ES_STRINGS.legend_qual_1,
  ES_STRINGS.legend_qual_2,
  ES_STRINGS.legend_qual_3,
  ES_STRINGS.legend_qual_4,
  ES_STRINGS.legend_qual_5,
];

function fmt(n: number, lang: 'en' | 'es'): string {
  return formatRate(n, lang);
}

/** Numeric range label for band i given 4 quantile thresholds. */
function bandLabel(i: number, breaks: number[], lang: 'en' | 'es'): string {
  const lo = i === 0 ? 0 : (breaks[i - 1] ?? 0) + 1;
  const hi = i < breaks.length ? breaks[i] : null;
  if (hi === null || hi === undefined) return `${fmt(lo, lang)}+`;
  return `${fmt(lo, lang)} – ${fmt(hi, lang)}`;
}

export function LegendHistogram({ lang, stats, mode, band, onBandChange, showIncidents }: Props) {
  const qualLabels = lang === 'es' ? QUAL_LABELS_ES : QUAL_LABELS_EN;
  const v2 = mapV2Strings(lang);
  const unitNote = lang === 'es' ? ES_STRINGS.legend_per_100k_note : EN_STRINGS.legend_per_100k_note;
  const title = mode === 'composite' ? v2.legend_ci : v2.legend_dist;

  const closedLabel = title + ' ▸';
  const openLabel = title + ' ▾';

  const bins = stats && stats.breaks
    ? computeHistBins(stats.values, stats.breaks)
    : [];

  const legendBody = (
    <>
      {bins.length > 0 && (
        <div className="legend-hist" role="img" aria-label={v2.legend_hist_aria}>
          {bins.map((b, i) => (
            <span
              key={i}
              className="legend-hist-bin"
              title={`${b.count} ${v2.legend_communes} · ${fmt(b.lo, lang)}–${fmt(b.hi, lang)}`}
              style={{
                height: `${Math.max(6, Math.round(b.share * 100))}%`,
                background: INCIDENCE_COLORS[b.band - 1],
                opacity: band === null || band === b.band ? 1 : 0.22,
              }}
            />
          ))}
        </div>
      )}
      <div className="legend-bands">
        {INCIDENCE_COLORS.map((color, i) => {
          const lv = i + 1;
          const active = band === lv;
          return (
            <button
              key={i}
              type="button"
              className={`legend-band-btn${active ? ' active' : ''}`}
              aria-pressed={active}
              title={v2.legend_band_hint}
              style={{ opacity: band === null || active ? 1 : 0.38 }}
              onClick={() => onBandChange(active ? null : lv)}
            >
              <span
                className="legend-swatch"
                style={{ background: color }}
                aria-hidden="true"
              />
              <span className="legend-band-label">
                <span className="legend-qual-label">{qualLabels[i]}</span>
                {stats && stats.breaks && stats.breaks.length === 4 && (
                  <span className="legend-range">{bandLabel(i, stats.breaks, lang)}</span>
                )}
              </span>
              <span className="legend-count">{stats ? stats.counts[i] : ''}</span>
            </button>
          );
        })}
      </div>
      {/* MPX-A4: zero-homicide communes are a distinct fact from "band 1" —
          shown as their own row, never folded into the band-1 count. */}
      {stats && stats.zeroCount !== undefined && (
        <div className="legend-band-row legend-zero-row">
          <span className="legend-qual-label">{v2.legend_zero_homicides}</span>
          <span className="legend-count">{stats.zeroCount}</span>
        </div>
      )}
      {band !== null && (
        <button type="button" className="legend-clear" onClick={() => onBandChange(null)}>
          {v2.legend_isolated} {qualLabels[band - 1]} ×
        </button>
      )}
      {mode !== 'composite' && <div className="legend-unit">{unitNote}</div>}
      {showIncidents && (
        <div className="legend-band-row legend-incident-row">
          <span className="legend-swatch legend-swatch-pin" aria-hidden="true" />
          <span className="legend-band-label">
            <span className="legend-qual-label">
              {lang === 'es' ? 'Incidentes reportados' : 'Reported incidents'}
            </span>
          </span>
        </div>
      )}
    </>
  );

  return (
    <div className="legend legend-v2">
      {/* Desktop: fully expanded */}
      <div className="legend-desktop">
        <div className="legend-title">{title}</div>
        {legendBody}
      </div>
      {/* Mobile (≤480px): collapsible via <details> */}
      <details className="legend-mobile">
        <summary className="legend-title legend-summary">
          <span className="legend-summary-closed">{closedLabel}</span>
          <span className="legend-summary-open">{openLabel}</span>
        </summary>
        {legendBody}
      </details>
    </div>
  );
}
