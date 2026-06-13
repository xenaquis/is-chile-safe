/**
 * PanelSparkline.tsx — Inline SVG bar sparkline for the ResultPanel.
 *
 * Mirrors Sparkline.astro exactly (WR-05: step derived from width so bars never overflow).
 * Active-year bar uses primaryColor prop (not CSS var — React state-driven).
 * Partial-year bars at 0.5 opacity.
 * aria-hidden — decorative; screen readers use stat cards.
 */

interface Props {
  series: Array<{ year: number; rate_per_100k: number; partial?: boolean }>;
  activeYear?: number;
  primaryColor?: string;
  width?: number;
  height?: number;
}

export function PanelSparkline({
  series,
  activeYear,
  primaryColor = '#0f766e',
  width = 480,
  height = 44,
}: Props) {
  const maxRate = series.length > 0 ? Math.max(...series.map((s) => s.rate_per_100k), 1) : 1;

  // WR-05: fit bars to width so they never overflow
  const step = series.length > 0 ? width / series.length : 8;
  const barW = Math.max(1, step - 1);

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      height={height}
      style={{ width: '100%', height: 'auto', overflow: 'visible', display: 'block' }}
      aria-hidden="true"
      className="sparkline"
    >
      {series.map((s, i) => {
        const barH = Math.max(2, Math.round((s.rate_per_100k / maxRate) * height));
        const isActive = s.year === activeYear;
        return (
          <rect
            key={s.year}
            x={i * step}
            y={height - barH}
            width={barW}
            height={barH}
            rx="2"
            fill={isActive ? primaryColor : 'var(--muted)'}
            opacity={s.partial ? 0.5 : 1}
          />
        );
      })}
    </svg>
  );
}
