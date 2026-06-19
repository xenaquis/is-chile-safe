/**
 * Legend.tsx — 5-swatch incidence color legend with numeric bands + qualitative labels.
 * Renders inside the MapIsland (client:only="react").
 *
 * Props:
 *   lang   — locale for number formatting and label lookup
 *   breaks — 4 quantile thresholds from computeQuantileBreaks(); when provided,
 *             each band shows its numeric range (D-03).
 */
import { INCIDENCE_COLORS } from './colors';
import { EN_STRINGS, ES_STRINGS } from '../../config/i18n';

interface Props {
  lang: 'en' | 'es';
  breaks?: number[];
  title?: string;
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

/** Format a number using the locale-appropriate thousands separator. */
function fmt(n: number, lang: 'en' | 'es'): string {
  return Math.round(n).toLocaleString(lang === 'es' ? 'es-CL' : 'en-US');
}

/**
 * Build the numeric range label for band i given 4 quantile thresholds.
 * Band 0:  "0 – breaks[0]"
 * Band 1-3: "breaks[i-1]+1 – breaks[i]"
 * Band 4:  "breaks[3]+1+"
 */
function bandLabel(i: number, breaks: number[], lang: 'en' | 'es'): string {
  const lo = i === 0 ? 0 : breaks[i - 1] + 1;
  const hi = i < breaks.length ? breaks[i] : null;
  if (hi === null) return `${fmt(lo, lang)}+`;
  return `${fmt(lo, lang)} – ${fmt(hi, lang)}`;
}

export function Legend({ lang, breaks, title }: Props) {
  const qualLabels = lang === 'es' ? QUAL_LABELS_ES : QUAL_LABELS_EN;
  const unitNote = lang === 'es' ? ES_STRINGS.legend_per_100k_note : EN_STRINGS.legend_per_100k_note;
  const defaultTitle = lang === 'es' ? 'Incidencia reportada' : 'Reported incidence';
  const resolvedTitle = title ?? defaultTitle;

  return (
    <div className="legend">
      <div className="legend-title">{resolvedTitle}</div>
      <div className="legend-bands">
        {INCIDENCE_COLORS.map((color, i) => (
          <div className="legend-band-row" key={i}>
            <span
              className="legend-swatch"
              style={{ background: color }}
              aria-hidden="true"
            />
            <span className="legend-band-label">
              <span className="legend-qual-label">{qualLabels[i]}</span>
              {breaks && breaks.length === 4 && (
                <span className="legend-range">{bandLabel(i, breaks, lang)}</span>
              )}
            </span>
          </div>
        ))}
      </div>
      <div className="legend-unit">{unitNote}</div>
    </div>
  );
}
