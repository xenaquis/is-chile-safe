/**
 * Legend.tsx — 5-swatch incidence color legend.
 * Renders inside the MapIsland (client:only="react").
 */
import { INCIDENCE_COLORS } from './colors';

interface Props {
  lang: 'en' | 'es';
}

export function Legend({ lang }: Props) {
  return (
    <div className="legend">
      <div className="legend-title">
        {lang === 'es' ? 'Incidencia reportada' : 'Reported incidence'}
      </div>
      <div className="legend-swatches">
        {INCIDENCE_COLORS.map((c, i) => (
          <span key={i} className="legend-swatch" style={{ background: c }} />
        ))}
      </div>
      <div className="legend-labels">
        <span>{lang === 'es' ? 'Baja' : 'Low'}</span>
        <span>{lang === 'es' ? 'Alta' : 'High'}</span>
      </div>
      <div className="legend-unit">
        {lang === 'es' ? 'Tasa por 100.000 hab.' : 'Rate per 100,000 inhab.'}
      </div>
    </div>
  );
}
