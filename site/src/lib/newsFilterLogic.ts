/**
 * newsFilterLogic.ts — shared, pure client-filter module for /news/ and
 * /es/noticias/ (Phase 28, NEWSUI-01..07).
 *
 * Module Published Contract (F-27 — the shipped filter logic must BE this
 * unit-tested module, imported by both pages' inline <script> blocks, never
 * a copy-pasted twin. `norm()` is the canonical definition for the news
 * pages only — communes/index.astro keeps its own separate inline copy,
 * this is NOT a single canonical norm() repo-wide, per F-30 wording).
 *
 * F-28 self-exclusion: `cardMatchesFilters`/`computeFacetCounts` apply every
 * active filter dimension EXCEPT the one being counted (`excludeDimension`),
 * so that per-option counts reflect "how many cards would match if this
 * option were chosen" rather than a fully-filtered residual count. The `q`
 * comuna search is cross-cutting and is ALWAYS applied regardless of
 * excludeDimension.
 *
 * Window-width invariant: WINDOW_7D_WIDTH_DAYS/WINDOW_30D_WIDTH_DAYS are the
 * INCLUSIVE window widths (7 means anchor + 6 prior days), ported verbatim
 * from newsFacets.ts:82-90,179-216 — UTC/string-only arithmetic, never
 * toLocaleDateString/getMonth()/bare new Date(y,m,d).
 *
 * Every function here is pure: no DOM access, no document/window reference,
 * no I/O — this module has zero filesystem dependency.
 */

export const WINDOW_7D_WIDTH_DAYS = 7;
export const WINDOW_30D_WIDTH_DAYS = 30;

export const FILTER_LOGIC_MARKER = 'newsFilterLogic/v1';

export type WindowValue = 'today' | '7d' | '30d' | '';

export interface FilterParams {
  family: string[];
  region: string[];
  window: WindowValue;
  q: string;
}

/**
 * norm(s) — accent-insensitive lowercase normalization (NEWSUI-03).
 * Algorithm copied verbatim from communes/index.astro:175-176, defined ONCE
 * here for the news pages (F-27/F-30) — never re-declared inline in a page
 * <script>. communes/index.astro keeps its own separate copy.
 *
 * Trims leading/trailing whitespace (WR-06): callers only ever compare
 * norm(query) against norm(communeName), which never carries surrounding
 * whitespace, so trimming here cannot drop information a caller relies on —
 * it only makes a pasted/typed "santiago " (trailing space is routine from
 * mobile autocomplete/paste/double-tap-space) match the same set as
 * "santiago".
 */
export function norm(s: string): string {
  return s
    .trim()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase();
}

const VALID_WINDOW_VALUES: ReadonlySet<string> = new Set(['today', '7d', '30d']);

/**
 * parseFilterParams — parses a "?a=b&c=d" (leading '?' optional) query
 * string into a typed FilterParams. Hostile/malformed `window` values
 * degrade to '' (all dates) — never throws (RESEARCH.md Security Domain).
 */
export function parseFilterParams(search: string): FilterParams {
  const params = new URLSearchParams(search);

  const familyRaw = params.get('family');
  const family = familyRaw ? familyRaw.split(',').filter((v) => v.length > 0) : [];

  const regionRaw = params.get('region');
  const region = regionRaw ? regionRaw.split(',').filter((v) => v.length > 0) : [];

  const windowRaw = params.get('window') ?? '';
  const window: WindowValue = VALID_WINDOW_VALUES.has(windowRaw) ? (windowRaw as WindowValue) : '';

  const q = params.get('q') ?? '';

  return { family, region, window, q };
}

/**
 * serializeFilterParams — inverse of parseFilterParams. Returns a query
 * string WITHOUT the leading '?'. Omits a dimension entirely when it is
 * empty so the URL stays minimal.
 */
export function serializeFilterParams(params: FilterParams): string {
  const usp = new URLSearchParams();
  if (params.family.length > 0) usp.set('family', params.family.join(','));
  if (params.region.length > 0) usp.set('region', params.region.join(','));
  if (params.window !== '') usp.set('window', params.window);
  if (params.q !== '') usp.set('q', params.q);
  return usp.toString();
}

/**
 * computeNewestDate — port of newsFacets.ts:180-183's loop. Max of a plain
 * YYYY-MM-DD string array (lexicographic order === chronological order for
 * this format). Returns null for an empty array.
 */
export function computeNewestDate(dates: string[]): string | null {
  let newestDate: string | null = null;
  for (const d of dates) {
    if (!newestDate || d > newestDate) newestDate = d;
  }
  return newestDate;
}

/**
 * lowerBoundDate — UTC-anchored lower-bound date string for a window width,
 * ported verbatim from newsFacets.ts:87-90.
 */
function lowerBoundDate(anchorMs: number, days: number): string {
  const ms = anchorMs - days * 86400000;
  return new Date(ms).toISOString().slice(0, 10);
}

/**
 * matchesWindow — window==='' always matches (true), regardless of
 * newestDate. If newestDate is null and window!=='', returns false (never
 * throws). Boundaries are INCLUSIVE both ends, using
 * WINDOW_7D_WIDTH_DAYS-1 / WINDOW_30D_WIDTH_DAYS-1 as the day offsets
 * (width 7 = anchor + 6 prior days).
 */
export function matchesWindow(dateStr: string, newestDate: string | null, window: WindowValue): boolean {
  if (window === '') return true;
  if (!newestDate) return false;

  if (window === 'today') return dateStr === newestDate;

  const anchorMs = Date.parse(newestDate + 'T00:00:00Z');
  if (window === '7d') {
    const lower7 = lowerBoundDate(anchorMs, WINDOW_7D_WIDTH_DAYS - 1);
    return dateStr >= lower7;
  }
  if (window === '30d') {
    const lower30 = lowerBoundDate(anchorMs, WINDOW_30D_WIDTH_DAYS - 1);
    return dateStr >= lower30;
  }
  return false;
}

export interface CardFilterState {
  family: string;
  regionId: string;
  date: string;
  communeNorm: string;
}

/**
 * cardMatchesFilters — applies every active filter EXCEPT excludeDimension
 * (F-28 self-exclusion). The comuna query (q) is cross-cutting and is
 * ALWAYS applied regardless of excludeDimension. family/region use
 * `.includes()` against active arrays (empty active array = dimension not
 * filtering = always matches).
 */
export function cardMatchesFilters(
  card: CardFilterState,
  active: FilterParams,
  newestDate: string | null,
  excludeDimension?: 'family' | 'region' | 'window'
): boolean {
  if (excludeDimension !== 'family' && active.family.length > 0) {
    if (!card.family || !active.family.includes(card.family)) return false;
  }

  if (excludeDimension !== 'region' && active.region.length > 0) {
    if (!card.regionId || !active.region.includes(card.regionId)) return false;
  }

  if (excludeDimension !== 'window' && active.window !== '') {
    if (!matchesWindow(card.date, newestDate, active.window)) return false;
  }

  if (active.q !== '') {
    if (!card.communeNorm || !card.communeNorm.includes(norm(active.q))) return false;
  }

  return true;
}

/**
 * computeFacetCounts — for each key in `keys`, counts cards where
 * card[dimension-equivalent field] === key AND cardMatchesFilters(card,
 * active, newestDate, dimension) is true (self-exclusion). For dimension
 * 'window', keys are 'today'|'7d'|'30d' and the per-key match uses
 * matchesWindow(card.date, newestDate, key) instead of equality.
 */
export function computeFacetCounts(
  cards: CardFilterState[],
  active: FilterParams,
  newestDate: string | null,
  dimension: 'family' | 'region' | 'window',
  keys: string[]
): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const key of keys) counts[key] = 0;

  for (const card of cards) {
    if (!cardMatchesFilters(card, active, newestDate, dimension)) continue;

    for (const key of keys) {
      let matchesKey: boolean;
      if (dimension === 'window') {
        matchesKey = matchesWindow(card.date, newestDate, key as WindowValue);
      } else if (dimension === 'family') {
        matchesKey = card.family === key;
      } else {
        matchesKey = card.regionId === key;
      }
      if (matchesKey) counts[key] += 1;
    }
  }

  return counts;
}
