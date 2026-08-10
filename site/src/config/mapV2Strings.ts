/**
 * mapV2Strings.ts — strings for the MAPV2 controls (layer rail, histogram
 * legend, news strip). Kept OUT of config/i18n.ts on purpose, following the
 * comparatorStrings.ts precedent: the map island is client:only and these
 * strings are only used there, so i18n.ts (SSR string table) stays untouched.
 */

export interface MapV2Strings {
  layer_group: string;        // aria-label of the layer radiogroup
  legend_dist: string;        // legend title, family/total mode
  legend_ci: string;          // legend title, composite mode
  legend_communes: string;    // "comunas" count suffix
  legend_isolated: string;    // "Aislado:" prefix on the active-band clear chip
  legend_band_hint: string;   // title= hint on band rows
  legend_hist_aria: string;   // aria-label of the histogram strip
  news_strip_days: string;    // "últimos {n} días"
  news_strip_incidents: string; // "incidentes"
  news_strip_all: string;     // scope when no family filter
  news_strip_day_hint: string;
  news_strip_clear_day: string;
  legend_zero_homicides: string; // MPX-A4: "Sin homicidios reportados: N" row
}

export const MAPV2_EN: MapV2Strings = {
  layer_group: 'Map layer',
  legend_dist: 'National distribution',
  legend_ci: 'Crime Index',
  legend_communes: 'communes',
  legend_isolated: 'Isolated:',
  legend_band_hint: 'Click to isolate this band on the map',
  legend_hist_aria: 'Distribution of communes across the incidence scale',
  news_strip_days: 'last {n} days',
  news_strip_incidents: 'press incidents',
  news_strip_all: 'all crime types',
  news_strip_day_hint: 'Click a day to filter the pins',
  news_strip_clear_day: 'Clear day filter',
  legend_zero_homicides: 'No homicides reported',
};

export const MAPV2_ES: MapV2Strings = {
  layer_group: 'Capa del mapa',
  legend_dist: 'Distribución nacional',
  legend_ci: 'Índice Delictivo',
  legend_communes: 'comunas',
  legend_isolated: 'Aislado:',
  legend_band_hint: 'Clic para aislar esta banda en el mapa',
  legend_hist_aria: 'Distribución de las comunas en la escala de incidencia',
  news_strip_days: 'últimos {n} días',
  news_strip_incidents: 'incidentes de prensa',
  news_strip_all: 'todos los tipos',
  news_strip_day_hint: 'Clic en un día para filtrar los pines',
  news_strip_clear_day: 'Quitar filtro de día',
  legend_zero_homicides: 'Sin homicidios reportados',
};

export function mapV2Strings(lang: 'en' | 'es'): MapV2Strings {
  return lang === 'es' ? MAPV2_ES : MAPV2_EN;
}
