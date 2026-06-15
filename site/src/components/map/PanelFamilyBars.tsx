/**
 * PanelFamilyBars.tsx — 7-family horizontal bar chart for the ResultPanel.
 *
 * Ports FamilyBreakdownBars.astro to React.
 *
 * byFamily is a 7-element catalog-indexed array:
 *   0=vida, 1=robos_violentos, 2=vif, 3=drogas, 4=armas, 5=propiedad, 6=incivilidades
 * (catalog.json family_keys order)
 *
 * Display order per UI-SPEC: vida, propiedad, robos_violentos, incivilidades, vif, drogas, armas
 * Map: catalog index → key, then reorder to FAMILY_ORDER.
 *
 * Bar fill = var(--s{level}); bar-width is a CSS % string (never a bare number).
 * Featured families (vida, propiedad) get --primary accent dot before label.
 *
 * Per-family tooltip (D-02): each row shows a RateTooltip with the family's
 * self-contained definition from familyDefs.ts. No cross-plan glossary anchor.
 */

import { RateTooltip } from './RateTooltipReact';
import {
  FAMILY_ORDER,
  FAMILY_LABELS_EN,
  FAMILY_LABELS_ES,
  FAMILY_DEFS_EN,
  FAMILY_DEFS_ES,
} from '../../lib/familyDefs';

// Catalog family_keys → index (catalog.json):
// 0=vida, 1=robos_violentos, 2=vif, 3=drogas, 4=armas, 5=propiedad, 6=incivilidades
const CATALOG_INDEX_TO_KEY: string[] = [
  'vida',           // 0
  'robos_violentos',// 1
  'vif',            // 2
  'drogas',         // 3
  'armas',          // 4
  'propiedad',      // 5
  'incivilidades',  // 6
];

const FEATURED = new Set(['vida', 'propiedad']);

interface Props {
  byFamily: number[]; // 7-element catalog-indexed array
  locale: 'en' | 'es';
  level: 1 | 2 | 3 | 4 | 5;
}

export function PanelFamilyBars({ byFamily, locale, level }: Props) {
  // Map catalog index → key → value record
  const byKey: Record<string, number> = {};
  CATALOG_INDEX_TO_KEY.forEach((key, i) => {
    byKey[key] = byFamily[i] ?? 0;
  });

  // Build rows in FAMILY_ORDER
  const vals = FAMILY_ORDER.map((key) => byKey[key] ?? 0);
  const max = Math.max(...vals, 1);

  const rows = FAMILY_ORDER.map((key, i) => {
    const val = vals[i] ?? 0;
    const widthPct = Math.round((val / max) * 100) + '%';
    const label = (locale === 'es' ? FAMILY_LABELS_ES[key] : FAMILY_LABELS_EN[key]) ?? key;
    const tip = (locale === 'es' ? FAMILY_DEFS_ES[key] : FAMILY_DEFS_EN[key]) ?? '';
    const featured = FEATURED.has(key);
    return { key, val, widthPct, label, tip, featured };
  });

  return (
    <div className="family-bars">
      {rows.map(({ key, val, widthPct, label, tip, featured }) => (
        <div className="family-bar-row" key={key}>
          <span className={`family-bar-label${featured ? ' featured' : ''}`}>
            {featured && (
              <span className="accent-dot" aria-hidden="true" />
            )}
            {label}
            <RateTooltip lang={locale} label={label} tip={tip} />
          </span>
          <span className="family-bar-track" aria-hidden="true">
            <span
              className="family-bar-fill"
              style={{ width: widthPct, background: `var(--s${level})` }}
            />
          </span>
          <span className="family-bar-val">{Math.round(val)}</span>
        </div>
      ))}
    </div>
  );
}
