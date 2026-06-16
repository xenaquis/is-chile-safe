/**
 * proseEngine.ts — Deterministic bilingual prose variation engine.
 *
 * Implements D-01/D-02: combinatorial variation keyed off 5 data dimensions:
 *   1. vs-national comparison (signed %, against loadNationalAverage MEAN)
 *   2. vs-regional comparison (signed %, against loadRegionalAverage MEAN)
 *   3. trend ('up' | 'down' | 'stable')
 *   4. dominant + secondary crime family (from by_family at latestCompleteYear)
 *   5. comparable commune (nearestComparable)
 *
 * CRITICAL — Pitfall 1 guard:
 *   vs-national and vs-regional MUST be computed against the per-capita MEANS
 *   (loadNationalAverage / loadRegionalAverage), NOT against loadNational() or
 *   loadRegion() series rate_per_100k (pop-weighted regional incidence — a
 *   different statistic than the unweighted commune-mean these comparisons need).
 *
 * D-05 Sober language: never "zona peligrosa", "ranking definitivo",
 *   "zona segura garantizada", unqualified "the safest" / "la más segura".
 *
 * D-03: EN and ES sentence banks are hand-maintained in parallel — no translation
 *   library or API call. Both locales share the same branch logic; only the
 *   string constants differ.
 *
 * Target: 500+ words per call for any non-empty commune dataset.
 */

import {
  loadNationalAverage,
  loadRegionalAverage,
  nearestComparable,
  latestCompleteYearRate,
  type CommuneData,
  type ComparableResult,
} from './data.ts';
import { regionNameEs } from '../config/i18n.ts';

// ---------------------------------------------------------------------------
// Internal types
// ---------------------------------------------------------------------------

type Locale = 'en' | 'es';

type Trend = 'up' | 'down' | 'stable';

/** national-rank tier derived from rank vs 346 communes */
type RankTier = 'top10' | 'top25' | 'mid' | 'bottom25' | 'bottom10';

/** vs-national / vs-regional comparison bucket */
type ComparisonBand = 'high_above' | 'mid_above' | 'near' | 'mid_below' | 'high_below';

// ---------------------------------------------------------------------------
// Helper functions
// ---------------------------------------------------------------------------

/**
 * Map a national rank to an incidence tier (WR-01).
 *
 * IMPORTANT: rank 1 = HIGHEST reported incidence (per EN_OPENING.up.top10
 * "highest reported crime incidence"), rank `total` = LOWEST. The tier names
 * therefore track incidence, not rank order: `top10` is the highest-incidence
 * decile, `bottom10` the lowest.
 *
 * Bands are RANK-PERCENTILE cuts (not rate-percentile). For total = 346 the
 * Math.round breakpoints are: top10 = 35, top25 = 87, bot25 = 260, bot10 = 311.
 * Edge cases (pinned): rank 35 -> top10, rank 87 -> top25, rank 260 -> bottom25,
 * rank 311 -> bottom10, ranks 88..259 -> mid. The `mid` band spans 88..259 by
 * design — verify against UI-SPEC if the intended cuts ever change.
 */
function rankTier(nationalRank: number, total = 346): RankTier {
  const top10 = Math.round(total * 0.1);
  const top25 = Math.round(total * 0.25);
  const bot25 = Math.round(total * 0.75);
  const bot10 = Math.round(total * 0.9);
  if (nationalRank <= top10) return 'top10';
  if (nationalRank <= top25) return 'top25';
  if (nationalRank >= bot10) return 'bottom10';
  if (nationalRank >= bot25) return 'bottom25';
  return 'mid';
}

function comparisonBand(signedPct: number): ComparisonBand {
  const abs = Math.abs(signedPct);
  if (signedPct > 0) {
    if (abs >= 50) return 'high_above';
    if (abs >= 20) return 'mid_above';
    return 'near';
  } else {
    if (abs >= 50) return 'high_below';
    if (abs >= 20) return 'mid_below';
    return 'near';
  }
}

function dominantFamily(byFamily: Record<string, number>): [string, string] {
  const entries = Object.entries(byFamily).sort((a, b) => b[1] - a[1]);
  const dominant = entries[0]?.[0] ?? 'propiedad';
  const secondary = entries[1]?.[0] ?? 'vida';
  return [dominant, secondary];
}

function familyName(key: string, locale: Locale): string {
  const names: Record<string, { en: string; es: string }> = {
    vida: { en: 'crimes against persons', es: 'delitos contra las personas' },
    robos_violentos: { en: 'violent robbery', es: 'robos con violencia' },
    propiedad: { en: 'property crimes', es: 'delitos contra la propiedad' },
    vif: { en: 'domestic violence', es: 'violencia intrafamiliar' },
    drogas: { en: 'drug-related offenses', es: 'delitos relacionados con drogas' },
    armas: { en: 'weapons offenses', es: 'delitos de armas' },
    incivilidades: { en: 'public-order incidents', es: 'incivilidades y orden público' },
  };
  return locale === 'en'
    ? (names[key]?.en ?? key)
    : (names[key]?.es ?? key);
}

function fmt(n: number): string {
  return n.toLocaleString('en-US', { maximumFractionDigits: 1 });
}

// ---------------------------------------------------------------------------
// EN sentence banks
// ---------------------------------------------------------------------------

/** Opening paragraph variants (trend × rankTier) */
const EN_OPENING: Record<Trend, Record<RankTier, string>> = {
  up: {
    top10:
      '{commune}, located in the {region} region, is among the communes with the highest reported crime incidence in Chile. CEAD data show a rising trend, placing it at national rank {nationalRank} of 346 communes with an official rate of {rate} reported incidents per 100,000 inhabitants in {year}.',
    top25:
      '{commune} ({region} region) registers a reported incidence rate that places it in the upper quarter of Chilean communes. The CEAD series reflects a rising trend, with {rate} incidents per 100,000 inhabitants recorded in {year} — national rank {nationalRank} of 346.',
    mid:
      '{commune} ({region} region) shows a rising trend in reported crime incidence according to CEAD records. In {year}, the commune registered {rate} incidents per 100,000 inhabitants, placing it at rank {nationalRank} of 346 nationally.',
    bottom25:
      '{commune} ({region} region) is among the communes with comparatively lower reported incidence in Chile, although CEAD data indicate an upward trend in recent years. The {year} figure stood at {rate} incidents per 100,000 inhabitants — national rank {nationalRank} of 346.',
    bottom10:
      '{commune} ({region} region) records among the lowest reported crime incidence rates nationally, despite a modest upward trend in the CEAD series. In {year}, the official rate was {rate} incidents per 100,000 inhabitants, corresponding to national rank {nationalRank} of 346.',
  },
  down: {
    top10:
      '{commune} ({region} region) carries a high level of reported incidence — rank {nationalRank} of 346 communes nationally — but CEAD data reveal a declining trend that has been consistent over recent years. The {year} figure reached {rate} incidents per 100,000 inhabitants.',
    top25:
      '{commune} ({region} region) registered {rate} reported incidents per 100,000 inhabitants in {year}, placing it at national rank {nationalRank} of 346. CEAD records show a declining trend in recent periods, suggesting the trajectory is moving toward lower incidence.',
    mid:
      'According to CEAD records, {commune} ({region} region) has seen a declining trend in reported crime incidence. The commune ranked {nationalRank} of 346 nationally in {year}, with an official rate of {rate} incidents per 100,000 inhabitants.',
    bottom25:
      '{commune} ({region} region) maintains comparatively low reported crime incidence — rank {nationalRank} of 346 — and CEAD data indicate a further declining trend. In {year}, the rate stood at {rate} incidents per 100,000 inhabitants.',
    bottom10:
      '{commune} ({region} region) records some of the lowest reported incidence rates in the country. CEAD data also show a declining trend. The {year} official rate was {rate} incidents per 100,000 inhabitants — national rank {nationalRank} of 346.',
  },
  stable: {
    top10:
      '{commune} ({region} region) consistently appears among the communes with the highest reported crime incidence in Chile. CEAD data show a stable trend at rank {nationalRank} of 346, with {rate} incidents per 100,000 inhabitants recorded in {year}.',
    top25:
      '{commune} ({region} region) has maintained a relatively stable level of reported incidence in recent years. CEAD figures place it at national rank {nationalRank} of 346, with {rate} incidents per 100,000 inhabitants in {year}.',
    mid:
      'Official CEAD data for {commune} ({region} region) show a stable trend in reported crime incidence. The commune ranked {nationalRank} of 346 nationally in {year}, recording {rate} incidents per 100,000 inhabitants.',
    bottom25:
      '{commune} ({region} region) has maintained comparatively low reported incidence levels in recent years according to CEAD. The {year} figure was {rate} incidents per 100,000 inhabitants — national rank {nationalRank} of 346 — with a stable trend.',
    bottom10:
      '{commune} ({region} region) consistently records among the lowest reported incidence rates in Chile. CEAD data show a stable trend, with {rate} incidents per 100,000 inhabitants in {year} — national rank {nationalRank} of 346.',
  },
};

/** vs-national comparison paragraph variants */
const EN_VS_NATIONAL: Record<ComparisonBand, string> = {
  high_above:
    'Relative to the national average computed across non-low-population communes, {commune} is considerably above average: the {year} rate of {rate} per 100,000 inhabitants exceeds the national mean by approximately {pct}%. This comparison is calculated against the per-capita mean of participating communes, providing a meaningful benchmark of relative incidence.',
  mid_above:
    'Compared with the per-capita national mean across Chilean communes, {commune} registers reported incidence that is moderately above average — roughly {pct}% higher than the mean in {year}. While this signals elevated reported activity relative to the national baseline, the rate also reflects factors specific to the commune\'s urban context and population density.',
  near:
    'The reported incidence rate of {commune} in {year} is close to the per-capita national mean computed across non-low-population communes. The difference is within a narrow margin, suggesting that the commune\'s reported activity broadly tracks the national level for communes of comparable data quality.',
  mid_below:
    '{commune}\'s reported incidence rate in {year} falls moderately below the per-capita national mean across Chilean communes — approximately {pct}% lower. This relative position reflects reported data only; actual differences may be influenced by local reporting patterns and the commune\'s demographic profile.',
  high_below:
    'The {year} reported rate for {commune} is substantially below the national per-capita mean, by approximately {pct}%. This positions the commune well below the national baseline in relative terms, though the comparison is based on reported statistics only and should be interpreted within the context of local data collection practices.',
};

/** vs-regional comparison paragraph variants */
const EN_VS_REGIONAL: Record<ComparisonBand, string> = {
  high_above:
    'Within the {region} region, {commune} stands considerably above the regional average: its {year} rate exceeds the regional per-capita mean by approximately {pct}%. The regional comparison draws on the mean of non-low-population communes within {region}, providing a geographically relevant benchmark.',
  mid_above:
    'Within {region}, {commune} registers reported incidence moderately above the regional per-capita mean — roughly {pct}% higher in {year}. The commune\'s position within its region reflects both absolute incidence levels and the distribution of reported activity across other {region} communes.',
  near:
    'Within {region}, {commune}\'s {year} rate is close to the regional per-capita mean. The commune sits near the midpoint of its regional distribution, indicating that its reported incidence aligns broadly with the typical level for the region.',
  mid_below:
    '{commune}\'s reported incidence in {year} was approximately {pct}% below the per-capita mean for the {region} region. Among {region} communes, this places {commune} on the lower side of the regional distribution.',
  high_below:
    'Compared with other communes in {region}, {commune}\'s {year} rate is substantially below the regional per-capita mean — by approximately {pct}%. This positions it among the lower-incidence communes in the region according to CEAD-reported data.',
};

/** Dominant crime family paragraph (3 variants by family tier) */
function EN_FAMILY_PARA(dominant: string, secondary: string, year: number, _dominantPct: number, commune: string): string {
  const dom = familyName(dominant, 'en');
  const sec = familyName(secondary, 'en');
  return `In ${year}, the leading category in ${commune}'s reported crime profile was ${dom}, which accounted for the largest share of total reported incidents. The second most prevalent category was ${sec}. This composition reflects ${commune}'s particular urban and socioeconomic characteristics. The CEAD breakdown covers seven crime families: crimes against persons, property crimes, violent robbery, public-order incidents, domestic violence, drug-related offenses, and weapons offenses. The relative weight of each category in the total rate is visible in the incidence-by-category chart above.`;
}

/** Comparable commune paragraph */
function EN_COMPARABLE_PARA(comp: ComparableResult, commune: string, rate: number, year: number, targetLowPop: boolean): string {
  const scope = comp.fallback ? 'nationally' : 'within the same region';
  // WR-04: do not assert "similar incidence tier" for low-population targets —
  // their rate is statistically volatile, so the similarity claim may be false.
  const similarity = targetLowPop
    ? `Because ${commune} has a small resident population, its rate is statistically volatile, so this comparison is offered as the nearest available reference rather than a claim of shared incidence tier.`
    : `The two communes share a similar incidence tier, making the comparison informative for understanding ${commune}'s position relative to a concrete peer rather than an abstract national average.`;
  return `A useful reference point for contextualizing ${commune}'s data is ${comp.name} (${comp.regionName}), identified as the nearest comparable commune ${scope} based on reported incidence. In ${year}, ${comp.name} recorded approximately ${fmt(comp.rate)} incidents per 100,000 inhabitants, compared with ${fmt(rate)} for ${commune}. ${similarity} ${comp.name} holds national rank ${comp.national_rank} of 346.`;
}

/** Regional context paragraph */
function EN_REGIONAL_PARA(commune: string, region: string, regionalRank: number): string {
  return `${commune} is one of the communes that make up the ${region} region. Within the region, it holds regional rank ${regionalRank}, a position that reflects its incidence level relative to other communes in the same administrative area. Regional comparisons are particularly relevant because they account for shared socioeconomic conditions, urban density patterns, and local reporting infrastructure that may influence measured incidence across the region.`;
}

/** Low-population caveat paragraph */
const EN_LOW_POP_CAVEAT =
  'Note: this commune has a small resident population. As a result, the rate per 100,000 inhabitants is statistically sensitive to small variations in absolute event counts. Year-on-year fluctuations may reflect statistical volatility rather than real changes in underlying trends. This commune is excluded from national rankings for this reason. Comparisons with national or regional averages should be interpreted with this caveat in mind.';

/** Closing paragraph */
function EN_CLOSING(commune: string, year: number, rate: number): string {
  return `The data presented here are sourced from CEAD (Centro de Estudios y Análisis del Delito), the official Chilean body that compiles police-reported crime statistics. All figures represent reported incidents — actual incidence may differ due to under-reporting, which varies by crime type and territory. The ${year} rate of ${fmt(rate)} incidents per 100,000 inhabitants for ${commune} reflects the most recent complete annual data available at the time of this publication. For more information on methodology and the rate-per-100,000 definition, see the methodology section.`;
}

// ---------------------------------------------------------------------------
// ES sentence banks (hand-maintained parallel, NOT translated from EN)
// ---------------------------------------------------------------------------

const ES_OPENING: Record<Trend, Record<RankTier, string>> = {
  up: {
    top10:
      '{commune}, ubicada en la {region}, figura entre las comunas con mayor incidencia delictiva reportada en Chile. Los datos del CEAD muestran una tendencia al alza, situándola en la posición {nationalRank} de 346 comunas a nivel nacional, con una tasa oficial de {rate} incidentes reportados por 100.000 habitantes en {year}.',
    top25:
      '{commune} ({region}) registra una tasa de incidencia reportada que la ubica en el cuarto superior del universo de comunas chilenas. La serie del CEAD refleja una tendencia al alza, con {rate} incidentes por 100.000 habitantes en {year} — posición nacional {nationalRank} de 346.',
    mid:
      '{commune} ({region}) presenta una tendencia al alza en la incidencia delictiva reportada según los registros del CEAD. En {year}, la comuna registró {rate} incidentes por 100.000 habitantes, ubicándose en la posición {nationalRank} de 346 a nivel nacional.',
    bottom25:
      '{commune} ({region}) se encuentra entre las comunas con incidencia reportada comparativamente más baja en Chile, aunque los datos del CEAD evidencian una tendencia al alza en años recientes. La cifra de {year} fue de {rate} incidentes por 100.000 habitantes — posición nacional {nationalRank} de 346.',
    bottom10:
      '{commune} ({region}) registra una de las tasas de incidencia reportada más bajas del país, aunque con una leve tendencia al alza en la serie CEAD. En {year}, la tasa oficial fue de {rate} incidentes por 100.000 habitantes, correspondiendo a la posición nacional {nationalRank} de 346.',
  },
  down: {
    top10:
      '{commune} ({region}) mantiene un nivel elevado de incidencia reportada —posición {nationalRank} de 346 comunas—, pero los datos del CEAD muestran una tendencia a la baja que ha sido sostenida en períodos recientes. La cifra de {year} alcanzó {rate} incidentes por 100.000 habitantes.',
    top25:
      '{commune} ({region}) registró {rate} incidentes reportados por 100.000 habitantes en {year}, situándose en la posición nacional {nationalRank} de 346. Los registros del CEAD muestran una tendencia a la baja en períodos recientes, lo que sugiere una trayectoria hacia menores niveles de incidencia.',
    mid:
      'Según los registros del CEAD, {commune} ({region}) ha experimentado una tendencia a la baja en la incidencia delictiva reportada. La comuna se ubicó en la posición {nationalRank} de 346 a nivel nacional en {year}, con una tasa oficial de {rate} incidentes por 100.000 habitantes.',
    bottom25:
      '{commune} ({region}) mantiene una incidencia reportada comparativamente baja —posición {nationalRank} de 346— y los datos del CEAD indican una tendencia a la baja adicional. En {year}, la tasa fue de {rate} incidentes por 100.000 habitantes.',
    bottom10:
      '{commune} ({region}) registra algunas de las tasas de incidencia reportada más bajas del país. Los datos del CEAD también muestran una tendencia a la baja. La tasa oficial de {year} fue de {rate} incidentes por 100.000 habitantes — posición nacional {nationalRank} de 346.',
  },
  stable: {
    top10:
      '{commune} ({region}) figura de forma consistente entre las comunas con mayor incidencia delictiva reportada en Chile. Los datos del CEAD muestran una tendencia estable en la posición {nationalRank} de 346, con {rate} incidentes por 100.000 habitantes registrados en {year}.',
    top25:
      '{commune} ({region}) ha mantenido un nivel relativamente estable de incidencia reportada en años recientes. Las cifras del CEAD la sitúan en la posición nacional {nationalRank} de 346, con {rate} incidentes por 100.000 habitantes en {year}.',
    mid:
      'Los datos oficiales del CEAD para {commune} ({region}) muestran una tendencia estable en la incidencia delictiva reportada. La comuna se ubicó en la posición {nationalRank} de 346 a nivel nacional en {year}, registrando {rate} incidentes por 100.000 habitantes.',
    bottom25:
      '{commune} ({region}) ha mantenido niveles de incidencia reportada comparativamente bajos en años recientes según el CEAD. La cifra de {year} fue de {rate} incidentes por 100.000 habitantes — posición nacional {nationalRank} de 346 — con una tendencia estable.',
    bottom10:
      '{commune} ({region}) registra de forma consistente una de las tasas de incidencia reportada más bajas en Chile. Los datos del CEAD muestran una tendencia estable, con {rate} incidentes por 100.000 habitantes en {year} — posición nacional {nationalRank} de 346.',
  },
};

const ES_VS_NATIONAL: Record<ComparisonBand, string> = {
  high_above:
    'En relación con el promedio nacional calculado sobre las comunas con datos estadísticamente robustos, {commune} se sitúa considerablemente por encima del promedio: la tasa de {rate} por 100.000 habitantes de {year} supera la media nacional en aproximadamente {pct}%. Esta comparación se calcula sobre el promedio per cápita de las comunas participantes, lo que proporciona un punto de referencia significativo de incidencia relativa.',
  mid_above:
    'Comparada con la media nacional per cápita entre comunas chilenas, {commune} registra una incidencia reportada moderadamente superior al promedio — aproximadamente {pct}% más alta que la media en {year}. Si bien esto señala una actividad reportada elevada en relación con la línea base nacional, la tasa también refleja factores propios del contexto urbano y la densidad poblacional de la comuna.',
  near:
    'La tasa de incidencia reportada de {commune} en {year} es cercana a la media nacional per cápita calculada sobre las comunas con datos estadísticamente robustos. La diferencia se sitúa dentro de un margen estrecho, lo que sugiere que la actividad reportada de la comuna sigue en términos generales el nivel nacional de comunas con calidad de datos comparable.',
  mid_below:
    'La tasa de incidencia reportada de {commune} en {year} se sitúa moderadamente por debajo de la media nacional per cápita entre comunas chilenas, aproximadamente {pct}% más baja. Esta posición relativa refleja solo los datos reportados; las diferencias reales pueden verse influidas por los patrones de notificación locales y el perfil demográfico de la comuna.',
  high_below:
    'La tasa reportada de {commune} en {year} se sitúa sustancialmente por debajo de la media nacional per cápita, en aproximadamente {pct}%. Esto posiciona a la comuna muy por debajo de la línea base nacional en términos relativos, aunque la comparación se basa únicamente en estadísticas reportadas y debe interpretarse en el contexto de las prácticas de recopilación de datos locales.',
};

const ES_VS_REGIONAL: Record<ComparisonBand, string> = {
  high_above:
    'Dentro de la {region}, {commune} se sitúa considerablemente por encima del promedio regional: su tasa de {year} supera la media per cápita regional en aproximadamente {pct}%. La comparación regional se basa en la media de las comunas sin baja población dentro de la {region}, lo que proporciona un punto de referencia geográficamente relevante.',
  mid_above:
    'Dentro de la {region}, {commune} registra una incidencia reportada moderadamente superior a la media per cápita regional — aproximadamente {pct}% más alta en {year}. La posición de la comuna dentro de su región refleja tanto los niveles absolutos de incidencia como la distribución de la actividad reportada entre las demás comunas de la {region}.',
  near:
    'Dentro de la {region}, la tasa de {commune} en {year} es cercana a la media per cápita regional. La comuna se sitúa cerca del punto medio de su distribución regional, lo que indica que su incidencia reportada se alinea en términos generales con el nivel típico de la región.',
  mid_below:
    'La incidencia reportada de {commune} en {year} fue aproximadamente {pct}% inferior a la media per cápita de la {region}. Entre las comunas de la {region}, esto sitúa a {commune} en la parte baja de la distribución regional.',
  high_below:
    'En comparación con otras comunas de la {region}, la tasa de {commune} en {year} se sitúa sustancialmente por debajo de la media per cápita regional — en aproximadamente {pct}%. Esto la posiciona entre las comunas de menor incidencia en la región según los datos reportados del CEAD.',
};

function ES_FAMILY_PARA(dominant: string, secondary: string, year: number, _dominantPct: number, commune: string): string {
  const dom = familyName(dominant, 'es');
  const sec = familyName(secondary, 'es');
  return `En ${year}, la categoría predominante en el perfil de incidencia reportada de ${commune} fue ${dom}, que representó la mayor proporción del total de incidentes reportados. La segunda categoría más prevalente fue ${sec}. Esta composición refleja las características urbanas y socioeconómicas particulares de ${commune}. El desglose del CEAD comprende siete familias delictivas: delitos contra las personas, delitos contra la propiedad, robos con violencia, incivilidades y orden público, violencia intrafamiliar, delitos relacionados con drogas y delitos de armas. El peso relativo de cada categoría en la tasa total es visible en el gráfico de incidencia por categoría que aparece más arriba.`;
}

function ES_COMPARABLE_PARA(comp: ComparableResult, commune: string, rate: number, year: number, targetLowPop: boolean): string {
  const scope = comp.fallback ? 'a nivel nacional' : 'dentro de la misma región';
  // WR-04: no afirmar "nivel de incidencia similar" para comunas de baja población
  // — su tasa es estadísticamente volátil, por lo que la afirmación puede ser falsa.
  const similarity = targetLowPop
    ? `Dado que ${commune} tiene una pequeña población residente, su tasa es estadísticamente volátil, por lo que esta comparación se ofrece como la referencia más cercana disponible y no como una afirmación de nivel de incidencia compartido.`
    : `Las dos comunas comparten un nivel de incidencia similar, lo que hace que la comparación sea informativa para entender la posición de ${commune} en relación con un par concreto, en lugar de un promedio nacional abstracto.`;
  return `Un punto de referencia útil para contextualizar los datos de ${commune} es ${comp.name} (${regionNameEs(comp.regionName)}), identificada como la comuna comparable más cercana ${scope} en función de la incidencia reportada. En ${year}, ${comp.name} registró aproximadamente ${fmt(comp.rate)} incidentes por 100.000 habitantes, frente a ${fmt(rate)} de ${commune}. ${similarity} ${comp.name} ocupa la posición nacional ${comp.national_rank} de 346.`;
}

function ES_REGIONAL_PARA(commune: string, region: string, regionalRank: number): string {
  // `region` arrives pre-formatted (e.g. "Región Metropolitana", "Región del
  // Biobío", "Región de Tarapacá") via regionNameEs() — do NOT prepend "región de".
  return `${commune} es una de las comunas que integran la ${region}. Dentro de la región, ocupa la posición regional ${regionalRank}, una situación que refleja su nivel de incidencia en relación con las demás comunas de la misma unidad administrativa. Las comparaciones regionales son especialmente relevantes porque tienen en cuenta las condiciones socioeconómicas compartidas, los patrones de densidad urbana y la infraestructura de registro local que pueden influir en la incidencia medida a lo largo de la región.`;
}

const ES_LOW_POP_CAVEAT =
  'Nota: esta comuna tiene una pequeña población residente. Como resultado, la tasa por 100.000 habitantes es estadísticamente sensible a pequeñas variaciones en los recuentos absolutos de eventos. Las fluctuaciones interanuales pueden reflejar volatilidad estadística más que cambios reales en las tendencias subyacentes. Por este motivo, la comuna queda excluida de los rankings nacionales. Las comparaciones con los promedios nacionales o regionales deben interpretarse teniendo en cuenta esta advertencia.';

function ES_CLOSING(commune: string, year: number, rate: number): string {
  return `Los datos presentados aquí provienen del CEAD (Centro de Estudios y Análisis del Delito), el organismo oficial chileno que compila las estadísticas de delitos reportados a la policía. Todas las cifras representan incidentes reportados; la incidencia real puede diferir debido a la sub-notificación, que varía según el tipo de delito y el territorio. La tasa de ${year} de ${fmt(rate)} incidentes por 100.000 habitantes para ${commune} refleja los datos anuales completos más recientes disponibles en el momento de esta publicación. Para más información sobre la metodología y la definición de tasa por 100.000 habitantes, consulte la sección de metodología.`;
}

// ---------------------------------------------------------------------------
// Template interpolation helper
// ---------------------------------------------------------------------------

function interpolate(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (_, key) =>
    key in vars ? String(vars[key as keyof typeof vars]) : `{${key}}`
  );
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

/**
 * Build deterministic, combinatorially-varied bilingual prose for a commune page.
 *
 * IMPORTANT: This function calls loadNationalAverage() and loadRegionalAverage()
 * internally — these compute per-capita MEANS, NOT the SUM stored in national.json.
 *
 * @param commune - Enriched CommuneData from loadCommune()
 * @param locale  - 'en' | 'es'
 * @returns Plain-text multi-paragraph prose string (500+ words for typical communes)
 */
export function buildCommuneProse(commune: CommuneData, locale: Locale): string {
  const year = commune.latestCompleteYear;

  // commune.regionName is the bare region name ("Metropolitana", "Biobío"). The
  // ES sentence banks reference the region as a full grammatical phrase
  // ("Región Metropolitana", "Región del Biobío", "Región de Tarapacá") — never
  // the ungrammatical "región de Metropolitana" (F-006). EN keeps the bare name
  // ("the {region} region"). Comparable-commune regions are formatted inside
  // ES_COMPARABLE_PARA.
  const regionVar = locale === 'es' ? regionNameEs(commune.regionName) : commune.regionName;

  // Get latest complete year series entry
  const seriesEntry = commune.series.find((s) => s.year === year && !s.partial);
  const rate = latestCompleteYearRate(commune);
  const byFamily = seriesEntry?.by_family ?? {};

  // 5 canonical dimensions
  // Dimension 1 & 2: vs-national and vs-regional (MEANS, not SUMs)
  const nationalAvg = loadNationalAverage();
  const regionalAvg = loadRegionalAverage(commune.region_id);

  const vsNationalPct = nationalAvg > 0 ? ((rate - nationalAvg) / nationalAvg) * 100 : 0;
  const vsRegionalPct = regionalAvg > 0 ? ((rate - regionalAvg) / regionalAvg) * 100 : 0;

  // Dimension 3: trend
  const trend = commune.trend as Trend;

  // Dimension 4: dominant + secondary family
  const [dominant, secondary] = dominantFamily(byFamily);
  const dominantPct =
    rate > 0 && byFamily[dominant] !== undefined
      ? Math.round(((byFamily[dominant] as number) / rate) * 100)
      : 0;

  // Dimension 5: comparable commune
  let comp: ComparableResult;
  try {
    comp = nearestComparable(commune.cut);
  } catch {
    // Fallback: self-reference if nearestComparable fails
    comp = {
      cut: commune.cut,
      name: commune.name,
      slug: commune.slug,
      region_id: commune.region_id,
      population: commune.population,
      low_population: commune.low_population,
      rate,
      national_rank: commune.national_rank,
      trend,
      regionName: commune.regionName,
      fallback: true,
    };
  }

  // Derived tiers
  const tier = rankTier(commune.national_rank);
  const vsNatBand = comparisonBand(vsNationalPct);
  const vsRegBand = comparisonBand(vsRegionalPct);

  // Build prose
  const paragraphs: string[] = [];

  // --- Opening paragraph (trend × rankTier) ---
  const openTemplate =
    locale === 'en'
      ? EN_OPENING[trend]?.[tier] ?? EN_OPENING.stable.mid
      : ES_OPENING[trend]?.[tier] ?? ES_OPENING.stable.mid;

  paragraphs.push(
    interpolate(openTemplate, {
      commune: commune.name,
      region: regionVar,
      nationalRank: commune.national_rank,
      rate: fmt(rate),
      year,
    })
  );

  // --- Regional context paragraph ---
  paragraphs.push(
    locale === 'en'
      ? EN_REGIONAL_PARA(commune.name, commune.regionName, commune.regional_rank)
      : ES_REGIONAL_PARA(commune.name, regionVar, commune.regional_rank)
  );

  // --- vs-national paragraph ---
  const vsNatTemplate =
    locale === 'en' ? EN_VS_NATIONAL[vsNatBand] : ES_VS_NATIONAL[vsNatBand];

  paragraphs.push(
    interpolate(vsNatTemplate, {
      commune: commune.name,
      rate: fmt(rate),
      year,
      pct: Math.round(Math.abs(vsNationalPct)),
    })
  );

  // --- vs-regional paragraph ---
  const vsRegTemplate =
    locale === 'en' ? EN_VS_REGIONAL[vsRegBand] : ES_VS_REGIONAL[vsRegBand];

  paragraphs.push(
    interpolate(vsRegTemplate, {
      commune: commune.name,
      region: regionVar,
      rate: fmt(rate),
      year,
      pct: Math.round(Math.abs(vsRegionalPct)),
    })
  );

  // --- Crime family breakdown paragraph (dimension 4) ---
  paragraphs.push(
    locale === 'en'
      ? EN_FAMILY_PARA(dominant, secondary, year, dominantPct, commune.name)
      : ES_FAMILY_PARA(dominant, secondary, year, dominantPct, commune.name)
  );

  // --- Comparable commune paragraph (dimension 5) ---
  paragraphs.push(
    locale === 'en'
      ? EN_COMPARABLE_PARA(comp, commune.name, rate, year, commune.low_population)
      : ES_COMPARABLE_PARA(comp, commune.name, rate, year, commune.low_population)
  );

  // --- Low-population caveat (conditional) ---
  if (commune.low_population) {
    paragraphs.push(locale === 'en' ? EN_LOW_POP_CAVEAT : ES_LOW_POP_CAVEAT);
  }

  // --- Trends over time paragraph ---
  const firstYear = commune.series.filter((s) => !s.partial).reduce((mn, s) => Math.min(mn, s.year), 9999);
  const firstEntry = commune.series.find((s) => s.year === firstYear && !s.partial);
  const firstRate = firstEntry?.rate_per_100k ?? rate;
  const pctChangeSeries = firstRate > 0 ? ((rate - firstRate) / firstRate) * 100 : 0;
  const changeDir = pctChangeSeries > 5 ? (locale === 'en' ? 'increased' : 'aumentado') : pctChangeSeries < -5 ? (locale === 'en' ? 'decreased' : 'disminuido') : (locale === 'en' ? 'remained broadly stable' : 'permanecido en niveles similares');
  if (locale === 'en') {
    paragraphs.push(
      `Looking at the full CEAD time series, ${commune.name} recorded ${fmt(firstRate)} incidents per 100,000 inhabitants in ${firstYear}. Since then, the reported rate has ${changeDir}, reaching ${fmt(rate)} in ${year}. The multi-year series is displayed in the sparkline chart above, which shows annual values from ${firstYear} through ${year}. The most recent year of partial data (if available) is shown at reduced opacity to indicate that the figure is not yet complete. Year-on-year fluctuations are normal and can reflect changes in recording practices, population estimates, or law enforcement priorities rather than changes in underlying behavior.`
    );
  } else {
    paragraphs.push(
      `Analizando la serie temporal completa del CEAD, ${commune.name} registró ${fmt(firstRate)} incidentes por 100.000 habitantes en ${firstYear}. Desde entonces, la tasa reportada ha ${changeDir}, alcanzando ${fmt(rate)} en ${year}. La serie plurianual se muestra en el gráfico de evolución temporal que aparece más arriba, con valores anuales desde ${firstYear} hasta ${year}. El año más reciente con datos parciales (si está disponible) se muestra con opacidad reducida para indicar que la cifra aún no está completa. Las fluctuaciones interanuales son normales y pueden reflejar cambios en las prácticas de registro, las estimaciones de población o las prioridades de la fuerza policial, en lugar de cambios en el comportamiento subyacente.`
    );
  }

  // --- Closing paragraph ---
  paragraphs.push(
    locale === 'en'
      ? EN_CLOSING(commune.name, year, rate)
      : ES_CLOSING(commune.name, year, rate)
  );

  return paragraphs.join('\n\n');
}
