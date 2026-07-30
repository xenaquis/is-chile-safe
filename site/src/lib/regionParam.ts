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
  const focusRegion = new URLSearchParams(search).get('region');
  if (!focusRegion) return null;

  const cuts = idx
    .filter((c) => c.region_id === focusRegion)
    .map((c) => c.cut);

  return cuts.length > 0 ? cuts : null;
}
