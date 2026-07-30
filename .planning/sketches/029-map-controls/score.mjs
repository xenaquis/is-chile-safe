/**
 * score.mjs — the falsifiable rubric for Phase 29's map control-shell design loop.
 *
 * `scoreControlShell` is injected into a page via BrowserOS `evaluate_script` as
 * `(${scoreControlShell.toString()})(opts)`. The invocation wrapper is mandatory:
 * a bare function definition returns nothing.
 *
 * DESIGN RULE (operating lesson 9 / F-24): every criterion must be able to come back
 * FAIL against a real input. Where a measurement is impossible, the result is an
 * explicit NOT_MEASURED_FAIL sentinel — never a missing key, because a missing key
 * renders as a blank cell and reads as coverage.
 *
 * This same file is Phase 30's regression instrument: the design spec requires the
 * `data-role` hooks below to ship into the real /map/ DOM, so this runs unchanged
 * against the real app.
 */

export function scoreControlShell(opts) {
  const o = opts || {};
  const results = {
    capturedAt: new Date().toISOString(),
    pageUrl: location.href,
    viewportWidthPx: window.innerWidth,
    viewportHeightPx: window.innerHeight,
    stressCondition: o.stressCondition || 'none',
  };

  const inViewport = (r) =>
    r.width > 0 && r.height > 0 &&
    r.left >= 0 && r.top >= 0 &&
    r.right <= window.innerWidth && r.bottom <= window.innerHeight;

  const isTopmost = (el, r) => {
    const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    return hit === el || el.contains(hit);
  };

  // --- Criterion 1: can a first-time user find and activate the news layer? -----------
  const newsToggle = document.querySelector('[data-role="news-toggle"], .ev-chip');
  if (!newsToggle) {
    results.newsToggleMissing = true;
    results.newsToggleDiscoverable = false;
    results.criterion1 = 'FAIL';
  } else {
    const r = newsToggle.getBoundingClientRect();
    results.newsToggleMissing = false;
    results.newsToggleRect = { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
    results.newsToggleInViewport = inViewport(r);
    // Topmost at its own centre: proves it is not painted under a Leaflet pane.
    results.newsToggleTopmost = isTopmost(newsToggle, r);
    results.newsToggleDiscoverable = results.newsToggleInViewport && results.newsToggleTopmost;
    results.criterion1 = results.newsToggleDiscoverable ? 'PASS' : 'FAIL';
  }

  // --- Criterion 2: can they find the filters? ----------------------------------------
  // The first draft was true-by-construction twice over: `[style*="overflow"]` matches
  // only INLINE styles (the sketches use <style> blocks, so it never matched), and for a
  // FAB `closest()` returns null, making scrollWidth === clientWidth for free.
  // Replaced with the same viewport+topmost test, PLUS a whole-document overflow scan
  // that cannot be defeated by renaming a class.
  // A responsive shell has more than one filter entry point in the DOM (a grouped rail at
  // wide widths, a FAB below the mobile breakpoint) with the inactive one display:none.
  // `querySelector` returns the first in DOCUMENT order, which would pick the HIDDEN one
  // and score the design as undiscoverable. Take the first candidate that is actually
  // rendered. (Found by execution on iter-2 before any score was recorded.)
  const filterCandidates = Array.prototype.slice.call(
    document.querySelectorAll('[data-role="filter-entry"], .filters-row, #filter-fab')
  );
  const filterEntry =
    filterCandidates.filter((el) => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(el).display !== 'none';
    })[0] || null;
  results.filterEntryCandidates = filterCandidates.length;
  if (!filterEntry) {
    results.filterEntryMissing = true;
    results.filterEntryDiscoverable = false;
  } else {
    const fr = filterEntry.getBoundingClientRect();
    results.filterEntryMissing = false;
    results.filterEntryDiscoverable = inViewport(fr) && isTopmost(filterEntry, fr);
  }

  results.hiddenOverflowElements = Array.prototype.slice
    .call(document.querySelectorAll('*'))
    .filter((el) => {
      const ox = getComputedStyle(el).overflowX;
      return el.scrollWidth - el.clientWidth > 8 && (ox === 'auto' || ox === 'scroll' || ox === 'hidden');
    })
    .map((el) => ({
      cls: String(el.className || el.tagName),
      overflowPx: el.scrollWidth - el.clientWidth,
      // A scroll container with a suppressed scrollbar is the exact baseline root cause
      // (map.css:47-59). Record it, because "it scrolls" is not the same as "it is findable".
      scrollbarSuppressed: getComputedStyle(el).scrollbarWidth === 'none',
    }));
  results.filterOverflowsContainer = results.hiddenOverflowElements.length > 0;
  results.filterOverflowPx = results.hiddenOverflowElements.reduce((m, x) => Math.max(m, x.overflowPx), 0);
  results.entryPointCount = document.querySelectorAll('[data-role="entry-point"]').length;
  results.criterion2 =
    results.filterEntryDiscoverable && !results.filterOverflowsContainer ? 'PASS' : 'FAIL';

  // --- Criterion 3: touch targets >= 44px ----------------------------------------------
  const interactive = Array.prototype.slice.call(
    document.querySelectorAll('a[href],button,input,select,textarea,summary,[role="button"],[data-role]')
  );
  results.touchTargetDetail = interactive
    .map((el) => {
      const r = el.getBoundingClientRect();
      return { t: (el.textContent || el.tagName).trim().slice(0, 24), w: Math.round(r.width), h: Math.round(r.height) };
    })
    .filter((x) => x.w > 0 && x.h > 0 && (x.w < 44 || x.h < 44));
  results.touchTargetViolations = results.touchTargetDetail.length;
  results.criterion3 = results.touchTargetViolations === 0 ? 'PASS' : 'FAIL';

  // --- Criterion 4: no keyboard/focus trap — settled BY CONSTRUCTION (F-41) -------------
  // Counting focusables + negative tabindexes + scanning for key interceptors is stronger
  // evidence than sampling N Tab presses (which can never prove absence), and it is one
  // call instead of thirty MCP round-trips. It also works inside the 375px iframe, where
  // the parent's document.activeElement stays pinned to the <iframe> element.
  const focusables = Array.prototype.slice.call(
    document.querySelectorAll('a[href],button,input,select,textarea,summary,[tabindex]')
  );
  const scriptText = Array.prototype.slice
    .call(document.querySelectorAll('script'))
    .map((s) => s.textContent || '')
    .join('\n');
  results.focusableCount = focusables.length;
  results.negativeTabindexCount = focusables.filter((el) => el.tabIndex < 0).length;
  results.keyInterceptors = ['keydown', 'keyup', 'preventDefault'].filter((k) => scriptText.indexOf(k) !== -1);
  results.keyboardTrapFree =
    results.negativeTabindexCount === 0 && results.keyInterceptors.length === 0;
  results.criterion4 = results.keyboardTrapFree ? 'PASS' : 'FAIL';

  // --- Criterion 5: no map occlusion / Leaflet pane conflict ---------------------------
  const mapPane = document.querySelector('.leaflet-map-pane, .leaflet-container');
  // Only controls that are actually PAINTED can occlude the map or conflict with a pane.
  // A responsive shell keeps its inactive alternative in the DOM at display:none (the FAB
  // above the mobile breakpoint, the grouped rail below it); scoring those produced a
  // z-index violation for a control the user cannot see. Found by execution on iter-2.
  const controls = Array.prototype.slice
    .call(document.querySelectorAll('.map-topbar, .legend, .mode-toggle, [data-role="filter-entry"], [data-role="news-toggle"], [data-role="entry-point"]'))
    .filter((el) => {
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') return false;
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    });
  // An element inherits its ancestor's stacking context, so `auto` is only a defect on a
  // control that has no positioned control ancestor carrying an explicit z-index >= 700.
  // (Found by execution on iter-1: the first form flagged `.filters-row` — z-index:auto but
  // nested inside `.map-topbar` at 800, which governs it. That was a false positive in the
  // RUBRIC, not a defect in the design. Corrected here; note this tightens nothing and
  // loosens no threshold — it fixes a measurement, which is why it is not barred by
  // STRESS.md's freeze. The unparented-`auto` case below still fails.)
  const governed = (el) => {
    let p = el.parentElement;
    while (p) {
      if (controls.indexOf(p) !== -1) {
        const pz = getComputedStyle(p).zIndex;
        if (pz !== 'auto' && Number(pz) >= 700) return true;
      }
      p = p.parentElement;
    }
    return false;
  };
  results.controlZIndexes = controls.map((el) => {
    const raw = getComputedStyle(el).zIndex; // may be the string "auto"
    return {
      cls: String(el.className || el.tagName),
      zIndexRaw: raw,
      zIndex: raw === 'auto' ? null : Number(raw),
      governedByAncestor: raw === 'auto' ? governed(el) : false,
    };
  });
  // z-index:auto on an always-visible non-modal control with NO governing ancestor IS a
  // violation: its paint order is DOM-order dependent and will not survive contact with
  // the real 970-line map.css. The first draft's `Number('auto') || 0` scored such a
  // control as fully compliant.
  results.zIndexViolations = results.controlZIndexes.filter(
    (c) => (c.zIndex === null && !c.governedByAncestor) || (c.zIndex > 0 && c.zIndex < 700)
  );

  if (!mapPane) {
    // Fail closed, loudly. The first draft omitted these keys entirely when there was no
    // Leaflet, so the column read blank in every row forever and nobody would have noticed.
    results.criterion5 = 'NOT_MEASURED_FAIL';
    results.mapVisibleWidthPx = null;
    results.mapWidthRatio = null;
    results.controlCoveragePct = null;
  } else {
    const mr = mapPane.getBoundingClientRect();
    const mapArea = Math.max(1, mr.width * mr.height);
    let covered = 0;
    controls.forEach((el) => {
      const r = el.getBoundingClientRect();
      const ix = Math.max(0, Math.min(r.right, mr.right) - Math.max(r.left, mr.left));
      const iy = Math.max(0, Math.min(r.bottom, mr.bottom) - Math.max(r.top, mr.top));
      covered += ix * iy;
    });
    results.mapVisibleWidthPx = Math.round(mr.width);
    results.mapWidthRatio = Number((mr.width / window.innerWidth).toFixed(3)); // measured, NOT gating (F-43)
    results.controlCoveragePct = Number(((covered / mapArea) * 100).toFixed(1));
    results.criterion5 = results.zIndexViolations.length === 0 ? 'PASS' : 'FAIL';
  }

  return results;
}

/**
 * Thresholds pre-registered in STRESS.md before iteration 1 was built (F-02 precedent).
 * `mapWidthRatio` is deliberately absent: measured and reported, never gating (F-43).
 */
export function verdict(r) {
  const narrow = r.viewportWidthPx <= 375;
  return {
    c1_newsToggleDiscoverable: r.newsToggleDiscoverable === true,
    c2_filtersDiscoverable: r.filterEntryDiscoverable === true && r.filterOverflowsContainer === false,
    c3_touchTargets: r.touchTargetViolations === 0,
    c4_keyboardTrapFree: r.keyboardTrapFree === true,
    c5_zIndexAndOcclusion:
      r.criterion5 === 'PASS' &&
      (!narrow || (typeof r.controlCoveragePct === 'number' && r.controlCoveragePct <= 25)),
  };
}

export const CRITERIA = [
  'c1_newsToggleDiscoverable',
  'c2_filtersDiscoverable',
  'c3_touchTargets',
  'c4_keyboardTrapFree',
  'c5_zIndexAndOcclusion',
];
