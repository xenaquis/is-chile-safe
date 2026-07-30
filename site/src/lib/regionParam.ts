/**
 * regionParam.ts — ?region= single-value region-focus resolver (MAPSH-04 / F-48).
 *
 * Mirrors the existing `?cut=` deep-link pattern in spirit (MapIsland.tsx:228-232)
 * but is NOT a reuse of parseFilterParams (Phase 28 Outcome N1 / F-35 N1) — this is
 * a single-value semantic, never the /news/ CSV multi-value semantics.
 *
 * Pure function: no fetch, no DOM access beyond the passed-in `search` string.
 * Unknown or malformed region_id degrades silently to `null` — never throws,
 * never triggers a fetch of a non-existent resource (F-48).
 *
 * T-30-02: the region value is used only as an opaque lookup key against an
 * already-loaded, code-controlled array (`idx`) — never interpolated into a
 * fetch URL, DOM string, or dangerouslySetInnerHTML.
 */

import type { CommuneIndexEntry } from '../components/map/SearchBox';

export function resolveRegionFocus(
  search: string,
  idx: CommuneIndexEntry[]
): string[] | null {
  const raw = new URLSearchParams(search).get('region');
  if (!raw) return null;

  // M-07: region_id in data/cead/meta/index.json is unpadded ("1"…"16"), but
  // ?region=05 is the padded form used elsewhere in Chilean CUT data (and the
  // premortem's own worked example). Trim whitespace and strip leading zeros
  // before matching so a valid padded value doesn't silently degrade to "no
  // focus" — that's indistinguishable from the feature never having worked.
  const norm = raw.trim().replace(/^0+(?=\d)/, '');

  const cuts = idx
    .filter((c) => c.region_id === norm)
    .map((c) => c.cut);

  return cuts.length > 0 ? cuts : null;
}

/**
 * M-07: the "?cut= wins over ?region=" precedence rule, extracted from
 * MapIsland.tsx as a tiny pure helper so it is directly testable — previously
 * it lived only as an inline guard with no test coverage of its own.
 * Returns true when there is no valid 4-5 digit ?cut= present, i.e. region
 * focus should be applied.
 */
export function shouldApplyRegionFocus(search: string): boolean {
  const focusCut = new URLSearchParams(search).get('cut');
  return !(focusCut !== null && /^\d{4,5}$/.test(focusCut));
}
