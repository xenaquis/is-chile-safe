/**
 * figure-registry.lib.mjs — pure, side-effect-free helpers for figure-registry.mjs.
 *
 * F-67: deliberately NOT given a `process.argv[1] === fileURLToPath(import.meta.url)`
 * CLI guard, and deliberately kept in a sibling module rather than folded into
 * figure-registry.mjs. `all.mjs` judges each validator purely on exit status
 * (`result.status === 0`), so a guard that mis-compares on this Windows/OneDrive
 * path would make figure-registry.mjs execute nothing, exit 0, and print PASS —
 * silently disabling F16 plus the DOCS-01/DOCS-03 content guards it protects.
 * This module performs no file IO and has no top-level execution of any kind,
 * so importing it (from the vitest spec or from figure-registry.mjs) is always safe.
 */

/**
 * extractSection(content, heading) — returns the substring starting at `heading`'s
 * first LINE-START occurrence in `content`, up to (but not including) the next line
 * starting with `## `, or EOF if none exists.
 *
 * Line-start anchoring matters: `data/SOURCES.md` contains an inline backtick
 * reference to "`## INE ENUSC SAE — communal VHDV`" (a cross-reference in prose,
 * not a heading) that appears BEFORE the real heading in file order. A naive
 * `content.indexOf(heading)` would match that inline reference instead of the
 * actual `## ` heading and extract the wrong (much shorter) span.
 */
export function extractSection(content, heading) {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp('^' + escaped, 'm');
  const match = re.exec(content);
  if (!match) return '';

  const start = match.index;
  const rest = content.slice(start + heading.length);
  const nextIdx = rest.search(/\n## /);
  if (nextIdx === -1) return content.slice(start);
  return content.slice(start, start + heading.length + nextIdx);
}

/**
 * checkF16(content) — hardened F16 check (DOCS-05, WR-01/H1 hardening).
 *
 * Extracts the '## INE ENUSC SAE' section, strips the heading line itself
 * (everything up to and including the first newline), and evaluates the
 * REMAINING BODY:
 *   - returns false if the body is empty or its length is <= 200 characters
 *     (this is the mandatory heading-strip: the real heading text already
 *     contains BOTH of token group 1's members, `## INE ENUSC SAE` and `VHDV`,
 *     so without stripping it a heading-only stub would pass on tokens alone —
 *     the length check is what actually proves body content exists)
 *   - returns false unless the BODY (heading excluded) carries at least
 *     MIN_PROVENANCE_MARKERS distinct provenance markers (see below) — this is
 *     what closes the WR-01 hole, where `heading + 'VHDV' + 200 chars of filler`
 *     passed because tokens were matched against `heading + body`
 *   - otherwise applies the existing two-token-group OR check against
 *     `heading + body`, so group 1's `'## INE ENUSC SAE'` token can still
 *     match the heading while the length/substance tests can only be
 *     satisfied by real body content.
 *
 * RR-H3 (fix cycle 2) — why a MARKER THRESHOLD rather than three exact literals:
 * the first hardening required `VHDV` AND `sha256` AND the literal `136 of 346`,
 * which coupled the build to one section's exact present-day wording. Reformatting
 * `136 of 346` to `136/346` or `136 de 346`, writing `SHA-256`, or re-wrapping the
 * line would each have reddened the build against a perfectly correct registry
 * entry — a landmine for the next person to touch this file, and the mirror image
 * of the hole it was closing. Requiring N-of-M markers keeps a gutted stub failing
 * (it carries at most one) while tolerating ordinary edits. The body is whitespace-
 * normalized first so a re-wrap cannot split a marker, matching the DOCS-01 guard.
 *
 * checkF16Detail(content) returns the REASON as well, so a failure can name its
 * real cause. The bare `Missing tokens: []` this used to produce told the reader
 * nothing, because the substance requirements were never in `figure.tokens`.
 */

/** Markers a genuine registry entry carries; a gutted stub carries at most one. */
const F16_PROVENANCE_MARKERS = ['sha256', 'ine.gob.cl', 'VHDV', 'SAE', 'Publisher', 'Measure semantics'];
const F16_MIN_BODY_LENGTH = 200;
const MIN_PROVENANCE_MARKERS = 3;

export function checkF16Detail(content) {
  const heading = '## INE ENUSC SAE';
  const section = extractSection(content, heading);
  if (!section) return { ok: false, reason: `no '${heading}' section found (searched line-anchored)` };

  const newlineIdx = section.indexOf('\n');
  const rawBody = newlineIdx === -1 ? '' : section.slice(newlineIdx + 1);
  const body = rawBody.replace(/\s+/g, ' ').trim();

  if (body.length <= F16_MIN_BODY_LENGTH) {
    return {
      ok: false,
      reason: `section body is ${body.length} chars (<= ${F16_MIN_BODY_LENGTH}) — the section looks like a stub, not a populated registry entry`,
    };
  }

  const present = F16_PROVENANCE_MARKERS.filter((m) => body.includes(m));
  if (present.length < MIN_PROVENANCE_MARKERS) {
    return {
      ok: false,
      reason:
        `section body carries only ${present.length} provenance marker(s) [${present.join(', ')}] ` +
        `— at least ${MIN_PROVENANCE_MARKERS} of [${F16_PROVENANCE_MARKERS.join(', ')}] are required`,
    };
  }

  const whole = heading + ' ' + body;
  const tokenGroups = [
    ['## INE ENUSC SAE', 'VHDV'],
    ['ENUSC', 'Victimizacion en Hogares', 'SAE'],
  ];
  if (!tokenGroups.some((group) => group.every((token) => whole.includes(token)))) {
    return { ok: false, reason: 'no token group fully matched within the bounded section' };
  }

  return { ok: true, reason: `${present.length} provenance markers, body ${body.length} chars` };
}

export function checkF16(content) {
  return checkF16Detail(content).ok;
}
