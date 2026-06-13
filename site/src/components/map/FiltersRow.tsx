/**
 * FiltersRow.tsx — Year select + crime-type chips + events toggle.
 *
 * Chip display order per UI-SPEC: Todos, vida, propiedad, robos_violentos,
 * incivilidades, vif, drogas, armas.
 *
 * Each chip carries the catalog by_family ARRAY INDEX (from catalog.json family_keys:
 * 0=vida, 1=robos_violentos, 2=vif, 3=drogas, 4=armas, 5=propiedad, 6=incivilidades).
 * Do NOT confuse chip display order with array index.
 *
 * Events toggle is rendered now (Wave 3 will wire full behavior).
 */

interface ChipDef {
  key: string | null; // null = "todos"
  familyIndex: number | null; // catalog by_family index; null for todos
  labelEs: string;
  labelEn: string;
  featured: boolean;
}

// Catalog family_keys order (catalog.json):
//   0=vida, 1=robos_violentos, 2=vif, 3=drogas, 4=armas, 5=propiedad, 6=incivilidades
const CHIP_DEFS: ChipDef[] = [
  { key: null,              familyIndex: null, labelEs: 'Todos',                      labelEn: 'All types',         featured: false },
  { key: 'vida',            familyIndex: 0,    labelEs: 'Vida y convivencia',          labelEn: 'Life crimes',       featured: true  },
  { key: 'propiedad',       familyIndex: 5,    labelEs: 'Propiedad',                   labelEn: 'Property crimes',   featured: true  },
  { key: 'robos_violentos', familyIndex: 1,    labelEs: 'Robos violentos',             labelEn: 'Violent robbery',   featured: false },
  { key: 'incivilidades',   familyIndex: 6,    labelEs: 'Incivilidades',               labelEn: 'Disorder',          featured: false },
  { key: 'vif',             familyIndex: 2,    labelEs: 'VIF',                         labelEn: 'Domestic violence', featured: false },
  { key: 'drogas',          familyIndex: 3,    labelEs: 'Drogas',                      labelEn: 'Drug crimes',       featured: false },
  { key: 'armas',           familyIndex: 4,    labelEs: 'Armas',                       labelEn: 'Weapons',           featured: false },
];

// Available years: 2025 → 2005, newest first
const AVAILABLE_YEARS: number[] = Array.from({ length: 21 }, (_, i) => 2025 - i);

interface Props {
  lang: 'en' | 'es';
  year: number;
  onYearChange: (year: number) => void;
  crimeFamily: string | null; // null = todos
  onFamilyChange: (key: string | null, index: number | null) => void;
  showEvents: boolean;
  onEventsToggle: (v: boolean) => void;
}

export function FiltersRow({
  lang,
  year,
  onYearChange,
  crimeFamily,
  onFamilyChange,
  showEvents,
  onEventsToggle,
}: Props) {
  return (
    <div className="filters-row">
      {/* Year selector */}
      <select
        className="chip select"
        value={year}
        onChange={(e) => onYearChange(Number(e.target.value))}
        aria-label={lang === 'es' ? 'Filtrar por año' : 'Filter by year'}
      >
        {AVAILABLE_YEARS.map((y) => (
          <option key={y} value={y}>{y}</option>
        ))}
      </select>

      {/* Crime-type chips */}
      {CHIP_DEFS.map(({ key, familyIndex, labelEs, labelEn, featured }) => {
        const isActive = crimeFamily === key;
        return (
          <button
            key={key ?? '__todos__'}
            className={`chip${isActive ? ' active' : ''}`}
            onClick={() => onFamilyChange(isActive ? null : key, isActive ? null : familyIndex)}
            aria-pressed={isActive}
          >
            {featured && !isActive && (
              <span
                className="accent-dot"
                aria-hidden="true"
                style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--primary)', display: 'inline-block', marginRight: 6, flexShrink: 0 }}
              />
            )}
            {lang === 'es' ? labelEs : labelEn}
          </button>
        );
      })}

      {/* Events toggle chip — no-op handler (Wave 3 wires full behavior) */}
      <button
        className={`chip ev-chip${showEvents ? ' active' : ''}`}
        onClick={() => onEventsToggle(!showEvents)}
        aria-pressed={showEvents}
      >
        <span className="ev-dot-mini" aria-hidden="true" />
        {lang === 'es' ? 'Noticias recientes' : 'Recent incidents'}
      </button>
    </div>
  );
}
