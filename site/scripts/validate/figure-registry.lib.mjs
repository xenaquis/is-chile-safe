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
 *   - returns false unless the BODY (heading excluded) contains `VHDV`,
 *     `sha256`, AND `136 of 346` — a padded stub that merely mentions `VHDV`
 *     in filler (the WR-01 hole: `heading + 'VHDV' + 200 chars` used to pass)
 *     will not carry the sha256 checksum line or the coverage-fraction claim
 *     that only the real, fully-populated registry entry has
 *   - otherwise applies the existing two-token-group OR check against
 *     `heading + body`, so group 1's `'## INE ENUSC SAE'` token can still
 *     match the heading while the length/substance tests can only be
 *     satisfied by real body content.
 */
export function checkF16(content) {
  const heading = '## INE ENUSC SAE';
  const section = extractSection(content, heading);
  if (!section) return false;

  const newlineIdx = section.indexOf('\n');
  const body = newlineIdx === -1 ? '' : section.slice(newlineIdx + 1);

  if (!body || body.length <= 200) return false;

  const REQUIRED_BODY_SUBSTANCE = ['VHDV', 'sha256', '136 of 346'];
  if (!REQUIRED_BODY_SUBSTANCE.every((token) => body.includes(token))) return false;

  const whole = heading + body;
  const tokenGroups = [
    ['## INE ENUSC SAE', 'VHDV'],
    ['ENUSC', 'Victimizacion en Hogares', 'SAE'],
  ];

  return tokenGroups.some((group) => group.every((token) => whole.includes(token)));
}
