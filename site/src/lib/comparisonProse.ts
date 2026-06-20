/**
 * comparisonProse.ts — Deterministic bilingual prose engine for A-vs-B commune comparison.
 *
 * Mirrors the structure of proseEngine.ts with 5 comparison-specific directional blocks:
 *   1. Composite-index score delta with direction (A's score vs B's, points higher/lower,
 *      both 2024 national ranks)
 *   2. Dominant per-family rate divergence between communes (gap factor + direction)
 *   3. Per-commune trend direction narrative (A trending X vs B trending Y)
 *   4. National rank context (A rank #X vs B rank #Y of 346)
 *   5. Regional context (same-region → regional rank comparison; closing regional info)
 *   Closing: CEAD attribution
 *
 * D-05 Sober language: never "zona peligrosa", "zona segura garantizada", unqualified
 *   "the safest" / "la más segura", "safe", "dangerous", "seguro", "peligroso".
 *   Use: "higher reported incidence", "lower reported rate", "ranked {X} nationally".
 *
 * D-03: EN and ES sentence banks are hand-maintained in parallel — no translation
 *   library or API call.
 *
 * Non-swappability: every block includes at least one DIRECTIONAL datum (signed score
 *   delta, gap factor, rank position) so swapping commA and commB changes meaning.
 *
 * Target: 400–500 words per call; ≥300-word floor enforced by getStaticPaths callers.
 * The word-count throw does NOT live here — it lives in [pair].astro getStaticPaths.
 */

import {
  latestCompleteYearRate,
  loadIndex,
  type CommuneData,
  type SeriesEntry,
} from './data.ts';
import { regionNameEs } from '../config/i18n.ts';

// ---------------------------------------------------------------------------
// Internal types (mirrored from proseEngine.ts)
// ---------------------------------------------------------------------------

type Locale = 'en' | 'es';
type Trend = 'up' | 'down' | 'stable';

// ---------------------------------------------------------------------------
// Helper functions (adapted from proseEngine.ts — kept local to this module)
// ---------------------------------------------------------------------------

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

function interpolate(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (_, key) =>
    key in vars ? String(vars[key as keyof typeof vars]) : `{${key}}`
  );
}

/** Returns the latest non-partial series entry for a commune */
function latestCompleteEntry(commune: CommuneData): SeriesEntry | undefined {
  const year = commune.latestCompleteYear;
  return commune.series.find((s) => s.year === year && !s.partial);
}

/** Returns the family with the largest rate in byFamily, plus the runner-up */
function topTwoFamilies(byFamily: Record<string, number>): [string, string] {
  const entries = Object.entries(byFamily).sort((a, b) => b[1] - a[1]);
  return [entries[0]?.[0] ?? 'propiedad', entries[1]?.[0] ?? 'vida'];
}

/**
 * The family where A and B diverge the most in absolute terms.
 *
 * `empty` is true when there is no meaningful per-category divergence to report
 * — either both communes lack by-family data (latestCompleteEntry undefined →
 * `{}`) or every category is identical. In that case callers MUST emit a neutral
 * sentence rather than the seeded propiedad/0/0 default, which would fabricate a
 * "property crimes 0 vs 0, gap 1×" claim (WR-06).
 */
function mostDivergentFamily(
  byFamilyA: Record<string, number>,
  byFamilyB: Record<string, number>
): { family: string; rateA: number; rateB: number; factor: number; empty: boolean } {
  const families = Object.keys(byFamilyA);
  let maxDivergence = 0;
  let result = { family: 'propiedad', rateA: 0, rateB: 0, factor: 1, empty: true };
  for (const fam of families) {
    const rA = byFamilyA[fam] ?? 0;
    const rB = byFamilyB[fam] ?? 0;
    const diff = Math.abs(rA - rB);
    if (diff > maxDivergence) {
      maxDivergence = diff;
      const higher = Math.max(rA, rB);
      const lower = Math.min(rA, rB);
      result = {
        family: fam,
        rateA: rA,
        rateB: rB,
        factor: lower > 0 ? higher / lower : (higher > 0 ? higher : 1),
        empty: false,
      };
    }
  }
  return result;
}

function trendLabel(trend: string, locale: Locale): string {
  const labels: Record<string, { en: string; es: string }> = {
    up: { en: 'rising', es: 'al alza' },
    down: { en: 'declining', es: 'a la baja' },
    stable: { en: 'stable', es: 'estable' },
  };
  return locale === 'en' ? (labels[trend]?.en ?? trend) : (labels[trend]?.es ?? trend);
}

// ---------------------------------------------------------------------------
// Block builders — EN
// ---------------------------------------------------------------------------

function EN_BLOCK1_INDEX(
  nameA: string, nameB: string,
  scoreA: number, scoreB: number,
  rankA: number, rankB: number,
  year = 2024
): string {
  const delta = scoreA - scoreB;
  const absDelta = Math.abs(delta);
  const direction = delta > 0
    ? `${fmt(absDelta)} points higher than`
    : delta < 0
    ? `${fmt(absDelta)} points lower than`
    : 'equal to';
  return `On the ${year} composite crime index published by CEAD and the Servicio de Prevención y Participación Ciudadana, ${nameA} scored ${fmt(scoreA)}, which is ${direction} ${nameB}'s score of ${fmt(scoreB)}. Both scores reflect reported incidence across multiple crime categories weighted by population and economic-activity proxies. ${nameA} holds national rank #${rankA} of 346 communes on this index, while ${nameB} holds rank #${rankB} of 346. A lower score corresponds to lower reported incidence relative to national peers; a higher score signals comparatively elevated reported activity.`;
}

function EN_BLOCK2_FAMILY(
  nameA: string, nameB: string,
  family: string,
  rateA: number, rateB: number,
  factor: number,
  empty: boolean,
  locale: Locale = 'en'
): string {
  if (empty) {
    // No per-category data, or no measurable divergence — emit a neutral,
    // non-fabricated sentence (WR-06) instead of a "0 vs 0, gap 1×" claim.
    return `Per-category reported incidence for ${nameA} and ${nameB} is comparable across the CEAD crime categories for the reference year, or category-level data is not yet available for both communes. The CEAD breakdown covers seven crime categories (crimes against persons, property crimes, violent robbery, public-order incidents, domestic violence, drug-related offenses, and weapons offenses); the year-by-year figures for each commune are available on its individual data page.`;
  }
  const famLabel = familyName(family, locale);
  const higher = rateA >= rateB ? nameA : nameB;
  const lower = rateA >= rateB ? nameB : nameA;
  const higherRate = Math.max(rateA, rateB);
  const lowerRate = Math.min(rateA, rateB);
  const gapStr = fmt(factor);
  return `The sharpest per-category difference between the two communes is in ${famLabel}. ${higher} reports ${fmt(higherRate)} incidents per 100,000 inhabitants in this category, compared with ${fmt(lowerRate)} for ${lower} — a gap of approximately ${gapStr}×. This divergence reflects distinct local characteristics, including population density, urbanisation patterns, and differences in policing and reporting infrastructure. The CEAD breakdown covers seven crime categories (crimes against persons, property crimes, violent robbery, public-order incidents, domestic violence, drug-related offenses, and weapons offenses); this category produces the widest absolute gap between the two communes.`;
}

function EN_BLOCK3_TREND(
  nameA: string, trendA: string,
  nameB: string, trendB: string
): string {
  const lblA = trendLabel(trendA, 'en');
  const lblB = trendLabel(trendB, 'en');
  if (trendA === trendB) {
    return `Both ${nameA} and ${nameB} show a ${lblA} trend in reported incidence according to the CEAD multi-year series. When two communes share the same trend direction, the gap between them may be widening or narrowing depending on the speed of change in each. The full annual series for each commune is available on its individual data page, where the year-by-year progression can be inspected.`;
  }
  return `Looking at the CEAD multi-year series, ${nameA} shows a ${lblA} trend in reported incidence while ${nameB} shows a ${lblB} trend. This divergence in trajectory means the current rate gap may evolve over time — a ${lblA} trend in ${nameA} combined with a ${lblB} trend in ${nameB} could change their relative positions in future reporting periods. Year-on-year fluctuations are normal and can reflect changes in recording practices or population estimates rather than underlying behavioral shifts.`;
}

function EN_BLOCK4_NATIONAL_RANK(
  nameA: string, rankA: number,
  nameB: string, rankB: number
): string {
  const tierDesc = (rank: number): string => {
    const top10 = Math.round(346 * 0.1);
    const top25 = Math.round(346 * 0.25);
    const bot25 = Math.round(346 * 0.75);
    const bot10 = Math.round(346 * 0.9);
    if (rank <= top10) return 'highest-incidence decile';
    if (rank <= top25) return 'upper quartile';
    if (rank >= bot10) return 'lowest-incidence decile';
    if (rank >= bot25) return 'lower quartile';
    return 'middle tier';
  };
  const diff = Math.abs(rankA - rankB);
  return `Nationally, ${nameA} holds rank #${rankA} of 346 communes (rank 1 = highest reported incidence), placing it in the ${tierDesc(rankA)}. ${nameB} holds rank #${rankB} of 346, placing it in the ${tierDesc(rankB)}. The two communes are separated by ${diff} national rank position${diff !== 1 ? 's' : ''} on the CEAD incidence scale. National ranks are derived from the most recent complete annual data and are recalculated whenever the data pipeline runs.`;
}

function EN_BLOCK5_REGIONAL(
  nameA: string, regRankA: number,
  nameB: string, regRankB: number,
  regionName: string,
  regionSize: number,
  sameRegion: boolean
): string {
  if (sameRegion) {
    return `Both communes belong to the ${regionName} region, which contains ${regionSize} communes in total. Within the region, ${nameA} holds regional rank #${regRankA} and ${nameB} holds regional rank #${regRankB} (rank 1 = highest reported incidence within the region). Regional comparisons account for shared socioeconomic conditions, urban-density patterns, and local reporting infrastructure that influence measured incidence levels across communes in the same administrative area. Comparing two communes within the same region provides a geographically relevant benchmark beyond what the national rank alone can offer.`;
  }
  return `${nameA} and ${nameB} belong to different regions: within its own region, ${nameA} holds regional rank #${regRankA}, and ${nameB} holds regional rank #${regRankB}. Because the two communes sit in different regions, the national rank is the more meaningful basis for comparison than a shared regional baseline. Regional conditions — socioeconomic factors, population density, and local enforcement capacity — differ substantially across regions and shape how the reported rate relates to the underlying environment.`;
}

function EN_CLOSING_CMP(nameA: string, nameB: string, year: number): string {
  return `All figures cited above are drawn from CEAD (Centro de Estudios y Análisis del Delito), the official Chilean body responsible for compiling police-reported crime statistics, and from the Servicio de Prevención y Participación Ciudadana (SPD) homicide database. Data represent reported incidents only; actual incidence may differ due to under-reporting, which varies by crime type and territory. The comparison uses the most recent complete annual data available for ${nameA} and ${nameB} at the time of publication (reference year: ${year}). For methodology details including the composite index formula, winsorisation method, and rate-per-100,000-inhabitants definition, see the methodology page.`;
}

// ---------------------------------------------------------------------------
// Block builders — ES
// ---------------------------------------------------------------------------

function ES_BLOCK1_INDEX(
  nameA: string, nameB: string,
  scoreA: number, scoreB: number,
  rankA: number, rankB: number,
  year = 2024
): string {
  const delta = scoreA - scoreB;
  const absDelta = Math.abs(delta);
  const direction = delta > 0
    ? `${fmt(absDelta)} puntos más alta que`
    : delta < 0
    ? `${fmt(absDelta)} puntos más baja que`
    : 'igual a';
  return `En el índice compuesto de incidencia delictiva ${year} publicado por el CEAD y el Servicio de Prevención y Participación Ciudadana, ${nameA} obtuvo una puntuación de ${fmt(scoreA)}, que es ${direction} la puntuación de ${nameB} (${fmt(scoreB)}). Ambas puntuaciones reflejan la incidencia reportada en múltiples categorías delictivas, ponderada por población y proxies de actividad económica. ${nameA} ocupa la posición nacional #${rankA} de 346 comunas en este índice, mientras que ${nameB} ocupa la posición #${rankB} de 346. Una puntuación más baja corresponde a menor incidencia reportada respecto a los pares nacionales; una puntuación más alta señala una actividad reportada comparativamente elevada.`;
}

function ES_BLOCK2_FAMILY(
  nameA: string, nameB: string,
  family: string,
  rateA: number, rateB: number,
  factor: number,
  empty: boolean
): string {
  if (empty) {
    // Sin datos por categoría, o sin divergencia medible — frase neutra y no
    // fabricada (WR-06) en lugar de una afirmación "0 vs 0, brecha 1×".
    return `La incidencia reportada por categoría de ${nameA} y ${nameB} es comparable entre las categorías delictivas del CEAD para el año de referencia, o aún no hay datos por categoría disponibles para ambas comunas. El desglose del CEAD abarca siete categorías delictivas (delitos contra las personas, delitos contra la propiedad, robos con violencia, incivilidades y orden público, violencia intrafamiliar, delitos relacionados con drogas y delitos de armas); las cifras año a año de cada comuna están disponibles en su página individual de datos.`;
  }
  const famLabel = familyName(family, 'es');
  const higher = rateA >= rateB ? nameA : nameB;
  const lower = rateA >= rateB ? nameB : nameA;
  const higherRate = Math.max(rateA, rateB);
  const lowerRate = Math.min(rateA, rateB);
  const gapStr = fmt(factor);
  return `La diferencia por categoría más pronunciada entre las dos comunas se da en ${famLabel}. ${higher} reporta ${fmt(higherRate)} incidentes por 100.000 habitantes en esta categoría, frente a ${fmt(lowerRate)} de ${lower}, una brecha de aproximadamente ${gapStr}×. Esta divergencia refleja características locales distintas, incluyendo densidad poblacional, patrones de urbanización y diferencias en la infraestructura de registro y atención policial. El desglose del CEAD abarca siete categorías delictivas (delitos contra las personas, delitos contra la propiedad, robos con violencia, incivilidades y orden público, violencia intrafamiliar, delitos relacionados con drogas y delitos de armas); esta es la categoría con la brecha absoluta más amplia entre las dos comunas.`;
}

function ES_BLOCK3_TREND(
  nameA: string, trendA: string,
  nameB: string, trendB: string
): string {
  const lblA = trendLabel(trendA, 'es');
  const lblB = trendLabel(trendB, 'es');
  if (trendA === trendB) {
    return `Tanto ${nameA} como ${nameB} muestran una tendencia ${lblA} en la incidencia reportada según la serie temporal plurianual del CEAD. Cuando dos comunas comparten la misma dirección de tendencia, la brecha entre ellas puede ampliarse o reducirse según la velocidad de cambio en cada una. La serie anual completa de cada comuna está disponible en su página individual de datos, donde puede inspeccionarse la progresión año a año.`;
  }
  return `Analizando la serie temporal plurianual del CEAD, ${nameA} muestra una tendencia ${lblA} en la incidencia reportada, mientras que ${nameB} muestra una tendencia ${lblB}. Esta divergencia en la trayectoria implica que la brecha actual de tasas puede evolucionar con el tiempo: una tendencia ${lblA} en ${nameA} combinada con una tendencia ${lblB} en ${nameB} podría modificar sus posiciones relativas en futuros períodos de reporte. Las fluctuaciones interanuales son normales y pueden reflejar cambios en las prácticas de registro o en las estimaciones de población, más que variaciones en el comportamiento subyacente.`;
}

function ES_BLOCK4_NATIONAL_RANK(
  nameA: string, rankA: number,
  nameB: string, rankB: number
): string {
  const tierDesc = (rank: number): string => {
    const top10 = Math.round(346 * 0.1);
    const top25 = Math.round(346 * 0.25);
    const bot25 = Math.round(346 * 0.75);
    const bot10 = Math.round(346 * 0.9);
    if (rank <= top10) return 'décil de mayor incidencia';
    if (rank <= top25) return 'cuartil superior';
    if (rank >= bot10) return 'décil de menor incidencia';
    if (rank >= bot25) return 'cuartil inferior';
    return 'grupo intermedio';
  };
  const diff = Math.abs(rankA - rankB);
  return `A nivel nacional, ${nameA} ocupa la posición #${rankA} de 346 comunas (posición 1 = mayor incidencia reportada), ubicándose en el ${tierDesc(rankA)}. ${nameB} ocupa la posición #${rankB} de 346, en el ${tierDesc(rankB)}. Las dos comunas están separadas por ${diff} posicion${diff !== 1 ? 'es' : ''} en el ranking nacional de incidencia del CEAD. Los rankings nacionales se derivan de los datos anuales completos más recientes y se recalculan cada vez que se ejecuta el pipeline de datos.`;
}

function ES_BLOCK5_REGIONAL(
  nameA: string, regRankA: number,
  nameB: string, regRankB: number,
  regionNameRaw: string,
  regionSize: number,
  sameRegion: boolean
): string {
  const regionPhraseEs = regionNameEs(regionNameRaw);
  if (sameRegion) {
    return `Ambas comunas pertenecen a la ${regionPhraseEs}, que agrupa ${regionSize} comunas en total. Dentro de la región, ${nameA} ocupa la posición regional #${regRankA} y ${nameB} ocupa la posición #${regRankB} (posición 1 = mayor incidencia reportada dentro de la región). Las comparaciones regionales tienen en cuenta las condiciones socioeconómicas compartidas, los patrones de densidad urbana y la infraestructura de registro local que influyen en los niveles de incidencia medidos entre comunas de la misma unidad administrativa. Comparar dos comunas dentro de la misma región ofrece un punto de referencia geográficamente relevante, más allá de lo que puede revelar el ranking nacional por sí solo.`;
  }
  return `${nameA} y ${nameB} pertenecen a regiones distintas: dentro de su propia región, ${nameA} ocupa la posición regional #${regRankA}, y ${nameB} ocupa la posición #${regRankB}. Las comparaciones interregionales son más significativas a la luz del ranking nacional que de una línea base regional compartida. Las condiciones regionales — factores socioeconómicos, densidad poblacional y capacidad de fiscalización local — difieren sustancialmente entre regiones y modelan la relación entre la tasa reportada y el entorno subyacente.`;
}

function ES_CLOSING_CMP(nameA: string, nameB: string, year: number): string {
  return `Todas las cifras mencionadas provienen del CEAD (Centro de Estudios y Análisis del Delito), organismo oficial chileno responsable de compilar las estadísticas de delitos reportados a la policía, y del Servicio de Prevención y Participación Ciudadana (SPD) para los datos de homicidios. Los datos representan únicamente incidentes reportados; la incidencia real puede diferir por sub-notificación, que varía según el tipo de delito y el territorio. La comparación utiliza los datos anuales completos más recientes disponibles para ${nameA} y ${nameB} al momento de la publicación (año de referencia: ${year}). Para detalles metodológicos, incluida la fórmula del índice compuesto, el método de winsorización y la definición de tasa por 100.000 habitantes, consulte la página de metodología.`;
}

// ---------------------------------------------------------------------------
// Region size lookup (needed for Block 5)
// ---------------------------------------------------------------------------

// WR-07: derive region sizes from data.ts's loadIndex() rather than re-reading
// meta/index.json with a second, divergent DATA_ROOT path resolver. loadIndex()
// owns the single canonical DATA_ROOT and is build-CWD-robust; this function is
// called at SSG time only (never in the browser).
let _regionSizeCache: Map<string, number> | null = null;

function getRegionSize(regionId: string): number {
  if (!_regionSizeCache) {
    _regionSizeCache = new Map();
    for (const entry of loadIndex()) {
      _regionSizeCache.set(entry.region_id, (_regionSizeCache.get(entry.region_id) ?? 0) + 1);
    }
  }
  return _regionSizeCache.get(regionId) ?? 0;
}

// ---------------------------------------------------------------------------
// Main exports
// ---------------------------------------------------------------------------

/**
 * Build deterministic directional bilingual prose for an A-vs-B commune comparison.
 *
 * Returns 5 non-swappable blocks + closing attribution. Target: 400–500 words.
 * ≥300-word assertion lives in the caller (getStaticPaths of [pair].astro).
 *
 * @param commA - Enriched CommuneData for commune A (from loadCommune())
 * @param commB - Enriched CommuneData for commune B
 * @param locale - 'en' | 'es'
 */
export function buildComparisonProse(
  commA: CommuneData,
  commB: CommuneData,
  locale: 'en' | 'es'
): string {
  const year = commA.latestCompleteYear;

  // Composite index scores (2024)
  const ciA = commA.composite_index?.['2024'];
  const ciB = commB.composite_index?.['2024'];
  const scoreA = ciA?.score ?? 0;
  const scoreB = ciB?.score ?? 0;
  const rankA = ciA?.rank ?? commA.national_rank;
  const rankB = ciB?.rank ?? commB.national_rank;
  const regRankA = ciA?.regional_rank ?? commA.regional_rank;
  const regRankB = ciB?.regional_rank ?? commB.regional_rank;

  // Per-family rates at latestCompleteYear (filter !partial — Pitfall 3)
  const entryA = latestCompleteEntry(commA);
  const entryB = latestCompleteEntry(commB);
  const byFamilyA = entryA?.by_family ?? {};
  const byFamilyB = entryB?.by_family ?? {};

  // Most divergent family
  const divergent = mostDivergentFamily(byFamilyA, byFamilyB);

  // Regional context
  const sameRegion = commA.region_id === commB.region_id;
  const regionNameRaw = commA.regionName; // enriched by loadCommune()
  // WR-08: compute unconditionally (cheap + cached) so the value is always a
  // real commune count, never a `0` sentinel that would surface as
  // "contains 0 communes" if the same-/cross-region branch logic ever changes.
  const regionSize = getRegionSize(commA.region_id);

  const paragraphs: string[] = [];

  if (locale === 'en') {
    // Block 1: Composite index score delta
    paragraphs.push(EN_BLOCK1_INDEX(
      commA.name, commB.name, scoreA, scoreB, rankA, rankB
    ));

    // Block 2: Per-family divergence
    paragraphs.push(EN_BLOCK2_FAMILY(
      commA.name, commB.name,
      divergent.family, divergent.rateA, divergent.rateB, divergent.factor,
      divergent.empty, 'en'
    ));

    // Block 3: Trend narrative
    paragraphs.push(EN_BLOCK3_TREND(
      commA.name, commA.trend,
      commB.name, commB.trend
    ));

    // Block 4: National rank context
    paragraphs.push(EN_BLOCK4_NATIONAL_RANK(
      commA.name, commA.national_rank,
      commB.name, commB.national_rank
    ));

    // Block 5: Regional context
    paragraphs.push(EN_BLOCK5_REGIONAL(
      commA.name, regRankA,
      commB.name, regRankB,
      regionNameRaw, regionSize, sameRegion
    ));

    // Closing attribution
    paragraphs.push(EN_CLOSING_CMP(commA.name, commB.name, year));
  } else {
    // Block 1: Composite index score delta (ES)
    paragraphs.push(ES_BLOCK1_INDEX(
      commA.name, commB.name, scoreA, scoreB, rankA, rankB
    ));

    // Block 2: Per-family divergence (ES)
    paragraphs.push(ES_BLOCK2_FAMILY(
      commA.name, commB.name,
      divergent.family, divergent.rateA, divergent.rateB, divergent.factor,
      divergent.empty
    ));

    // Block 3: Trend narrative (ES)
    paragraphs.push(ES_BLOCK3_TREND(
      commA.name, commA.trend,
      commB.name, commB.trend
    ));

    // Block 4: National rank context (ES)
    paragraphs.push(ES_BLOCK4_NATIONAL_RANK(
      commA.name, commA.national_rank,
      commB.name, commB.national_rank
    ));

    // Block 5: Regional context (ES)
    paragraphs.push(ES_BLOCK5_REGIONAL(
      commA.name, regRankA,
      commB.name, regRankB,
      regionNameRaw, regionSize, sameRegion
    ));

    // Closing attribution (ES)
    paragraphs.push(ES_CLOSING_CMP(commA.name, commB.name, year));
  }

  return paragraphs.join('\n\n');
}

/**
 * Build a unique meta description for an A-vs-B pair.
 * Target: 140–160 characters. Embeds both names, both composite scores, "Source: CEAD".
 *
 * @param commA - CommuneData for commune A
 * @param commB - CommuneData for commune B
 * @param locale - 'en' | 'es'
 */
export function buildMetaDescription(
  commA: CommuneData,
  commB: CommuneData,
  locale: 'en' | 'es'
): string {
  const scoreA = (commA.composite_index?.['2024']?.score ?? 0).toFixed(1);
  const scoreB = (commB.composite_index?.['2024']?.score ?? 0).toFixed(1);

  const rankA = commA.composite_index?.['2024']?.rank ?? commA.national_rank;
  const rankB = commB.composite_index?.['2024']?.rank ?? commB.national_rank;

  if (locale === 'en') {
    // Target 140–160 chars; embed both names, both scores, ranks, source attribution
    const base = `${commA.name} vs ${commB.name}: reported crime incidence index ${scoreA} vs ${scoreB} (national ranks #${rankA} and #${rankB} of 346 communes). Rates, trends, data. Source: CEAD.`;
    return base;
  } else {
    const base = `${commA.name} vs ${commB.name}: índice de incidencia delictiva ${scoreA} vs ${scoreB} (posiciones nacionales #${rankA} y #${rankB} de 346 comunas). Tasas, tendencias. Fuente: CEAD.`;
    return base;
  }
}
