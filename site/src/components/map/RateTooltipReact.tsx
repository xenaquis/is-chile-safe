/**
 * RateTooltipReact.tsx — React twin of RateTooltip.astro.
 * Identical accessible <details>/<summary> markup; styled by the same global.css
 * .rate-tooltip / .tooltip-* rules. No hooks, no state — props only.
 */

export function RateTooltip({
  label,
  tip,
  lang,
}: {
  label: string;
  tip: string;
  lang: 'en' | 'es';
}) {
  return (
    <span className="rate-tooltip">
      <details className="tooltip-details">
        <summary
          className="tooltip-trigger"
          aria-label={lang === 'es' ? `Más información: ${label}` : `More info: ${label}`}
        >
          <span aria-hidden="true">?</span>
        </summary>
        <div className="tooltip-body" role="tooltip">
          {tip}
        </div>
      </details>
    </span>
  );
}
