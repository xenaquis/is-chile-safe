/**
 * EN/ES UI string map + crime-family slug translations.
 * Sober editorial tone per D-05 — never "zona peligrosa", "ranking definitivo", "zona segura garantizada".
 * Ported from ischilesafe.com/data.js I18N and extended with Phase 2 UI-SPEC additions.
 */

export interface I18nStrings {
  // Navigation
  nav_home: string;
  nav_map: string;
  nav_methodology: string;

  // Page h1 patterns (use {name} placeholder)
  page_commune_h1: string;
  page_region_h1: string;
  page_crime_h1: string;

  // Rate stat
  rate_label: string;
  rate_unit: string;

  // Rank labels
  national_rank_label: string;
  regional_rank_label: string;
  rank_of: string;

  // Trend
  trend_up: string;
  trend_down: string;
  trend_stable: string;
  trend_label: string;

  // Sparkline
  sparkline_heading: string;

  // Partial year badge
  partial_year_badge: string;

  // vs-national / vs-regional callouts
  vs_national_above: string;
  vs_national_below: string;
  vs_national_near: string;
  vs_regional_above: string;
  vs_regional_below: string;
  vs_regional_near: string;

  // Family breakdown heading
  family_breakdown_heading: string;

  // Comparable commune headings
  comparable_same_region_heading: string;
  comparable_national_fallback_heading: string;

  // Map placeholder text
  map_placeholder_text: string;

  // Methodology caveat
  methodology_caveat_link: string;
  methodology_caveat_text: string;

  // Low-population caveat
  low_population_caveat: string;

  // Incidence level labels (matches --s1..--s5)
  level_1: string;
  level_2: string;
  level_3: string;
  level_4: string;
  level_5: string;
}

export const EN_STRINGS: I18nStrings = {
  // Navigation
  nav_home: 'Home',
  nav_map: 'Map',
  nav_methodology: 'Methodology',

  // Page h1 patterns
  page_commune_h1: '{name} — Reported Crime Data',
  page_region_h1: '{name} Region — Crime Incidence Overview',
  page_crime_h1: '{name} — National Crime Incidence',

  // Rate stat
  rate_label: 'Rate per 100,000 inhabitants ({year})',
  rate_unit: 'per 100k inh.',

  // Rank labels
  national_rank_label: 'National rank',
  regional_rank_label: 'Regional rank',
  rank_of: 'of',

  // Trend
  trend_up: 'Rising',
  trend_down: 'Declining',
  trend_stable: 'Stable',
  trend_label: 'Trend',

  // Sparkline
  sparkline_heading: 'Annual evolution (2005–present)',

  // Partial year badge
  partial_year_badge: 'Partial year ({year})',

  // vs-national / vs-regional callouts
  vs_national_above: '{pct}% above national average',
  vs_national_below: '{pct}% below national average',
  vs_national_near: 'Near the national average',
  vs_regional_above: '{pct}% above regional average',
  vs_regional_below: '{pct}% below regional average',
  vs_regional_near: 'Near the regional average',

  // Family breakdown heading
  family_breakdown_heading: 'Reported incidence by crime category ({year})',

  // Comparable commune headings
  comparable_same_region_heading: 'Comparable commune (same region)',
  comparable_national_fallback_heading: 'Comparable commune (national)',

  // Map placeholder text
  map_placeholder_text: 'Interactive map — coming in next update',

  // Methodology caveat
  methodology_caveat_link: 'Methodology',
  methodology_caveat_text:
    'Figures represent reported crimes per 100,000 inhabitants. Under-reporting varies by crime type. Source: CEAD — Centro de Estudios y Análisis del Delito (official Chilean police statistics). See our {link} for details.',

  // Low-population caveat
  low_population_caveat:
    'This commune has a small resident population. Rates per 100,000 inhabitants can show high statistical volatility even with small changes in absolute counts. Interpret trends with caution and compare with regional context rather than national rankings.',

  // Incidence level labels
  level_1: 'Low incidence',
  level_2: 'Medium-low incidence',
  level_3: 'Medium incidence',
  level_4: 'Medium-high incidence',
  level_5: 'High incidence',
};

export const ES_STRINGS: I18nStrings = {
  // Navegación
  nav_home: 'Inicio',
  nav_map: 'Mapa',
  nav_methodology: 'Metodología',

  // Patrones de h1
  page_commune_h1: '{name} — Datos de Incidencia Delictiva Reportada',
  page_region_h1: 'Región de {name} — Panorama de Incidencia Delictiva',
  page_crime_h1: '{name} — Incidencia Nacional',

  // Estadística de tasa
  rate_label: 'Tasa por 100.000 hab. ({year})',
  rate_unit: 'por 100k hab.',

  // Etiquetas de ranking
  national_rank_label: 'Ranking nacional',
  regional_rank_label: 'Ranking regional',
  rank_of: 'de',

  // Tendencia
  trend_up: 'Al alza',
  trend_down: 'A la baja',
  trend_stable: 'Estable',
  trend_label: 'Tendencia',

  // Sparkline
  sparkline_heading: 'Evolución anual (2005–presente)',

  // Distintivo año parcial
  partial_year_badge: 'Año parcial ({year})',

  // Comparaciones vs. nacional / regional
  vs_national_above: '{pct}% sobre el promedio nacional',
  vs_national_below: '{pct}% bajo el promedio nacional',
  vs_national_near: 'Cercano al promedio nacional',
  vs_regional_above: '{pct}% sobre el promedio regional',
  vs_regional_below: '{pct}% bajo el promedio regional',
  vs_regional_near: 'Cercano al promedio regional',

  // Encabezado desglose por familia
  family_breakdown_heading: 'Incidencia reportada por categoría delictiva ({year})',

  // Encabezados de comuna comparable
  comparable_same_region_heading: 'Comuna comparable (misma región)',
  comparable_national_fallback_heading: 'Comuna comparable (a nivel nacional)',

  // Texto de marcador de mapa
  map_placeholder_text: 'Mapa interactivo — disponible próximamente',

  // Nota metodológica
  methodology_caveat_link: 'Metodología',
  methodology_caveat_text:
    'Las cifras representan delitos reportados por 100.000 habitantes. La sub-notificación varía según el tipo de delito. Fuente: CEAD — Centro de Estudios y Análisis del Delito (estadísticas policiales oficiales de Chile). Ver {link} para más detalles.',

  // Advertencia de baja población
  low_population_caveat:
    'Esta comuna tiene una pequeña población residente. Las tasas por 100.000 habitantes pueden presentar alta volatilidad estadística incluso ante pequeños cambios en los valores absolutos. Interprete las tendencias con cautela y compare con el contexto regional más que con los rankings nacionales.',

  // Etiquetas de nivel de incidencia
  level_1: 'Incidencia baja',
  level_2: 'Incidencia media-baja',
  level_3: 'Incidencia media',
  level_4: 'Incidencia media-alta',
  level_5: 'Incidencia alta',
};

// D-17: Crime-family URL slug translations
// family key (data) -> { en: EN URL slug, es: ES URL slug }
export interface FamilySlugPair {
  en: string;
  es: string;
}

export const FAMILY_SLUGS: Record<string, FamilySlugPair> = {
  vida: { en: 'homicide', es: 'homicidios' },
  robos_violentos: { en: 'violent-robbery', es: 'robos-violentos' },
  vif: { en: 'domestic-violence', es: 'violencia-intrafamiliar' },
  drogas: { en: 'drug-crimes', es: 'drogas' },
  armas: { en: 'weapons', es: 'armas' },
  propiedad: { en: 'property', es: 'propiedad' },
  incivilidades: { en: 'disorder', es: 'incivilidades' },
};

export interface NavStrings {
  home: string;
  map: string;
  methodology: string;
}

export const NAV_STRINGS: Record<'en' | 'es', NavStrings> = {
  en: {
    home: EN_STRINGS.nav_home,
    map: EN_STRINGS.nav_map,
    methodology: EN_STRINGS.nav_methodology,
  },
  es: {
    home: ES_STRINGS.nav_home,
    map: ES_STRINGS.nav_map,
    methodology: ES_STRINGS.nav_methodology,
  },
};
