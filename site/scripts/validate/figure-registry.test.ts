// figure-registry.test.ts — mutation test for the hardened F16 check (DOCS-05).
//
// Imports only from the side-effect-free `figure-registry.lib.mjs` module (F-67):
// figure-registry.mjs itself performs file IO and process.exit at module-load time,
// so it is never imported here. All fixtures are hardcoded strings — data/SOURCES.md
// (read-only for this milestone) is never read at test time. The "real section" fixture
// below is a verbatim copy of data/SOURCES.md lines 324-349 ("## INE ENUSC SAE —
// communal VHDV victimization (experimental)" through the line before "## SPD —
// institutional authority").

import { describe, it, expect } from 'vitest';
import { extractSection, checkF16, checkF16Detail } from './figure-registry.lib.mjs';

const REAL_HEADING = '## INE ENUSC SAE — communal VHDV victimization (experimental)';
const NEXT_HEADING = '## SPD — institutional authority (parent of CEAD + taxonomy)';

// Verbatim copy of data/SOURCES.md lines 324-349 (the real, fully-populated section).
const REAL_SECTION_BODY = `## INE ENUSC SAE — communal VHDV victimization (experimental)

**Full name:** ENUSC 2024 — Victimización en Hogares por Delitos Violentos (VHDV), modelo de Estimación en Áreas Pequeñas (SAE).

**Publisher:** Instituto Nacional de Estadísticas (INE) — Estadísticas Experimentales: Seguridad Ciudadana.

**Official landing:**
\`https://www.ine.gob.cl/estadisticas/estadisticas-experimentales/seguridad-ciudadana\`

**File URL (sfvrsn may rotate on republish):**
\`https://www.ine.gob.cl/docs/default-source/estadisticas-experimentales-seguridad-ciudadana/cuadros-estadisticos/2024/tabulados-sae--enusc-2024-vhdv.xlsx?sfvrsn=671c099f_4\`

**Measure semantics:**
Proportion of households reporting at least one violent crime (VHDV). Value is 0–1 (proportion), NOT per-100k. Do not rescale. Communal SAE estimates cover 136 of 346 comunas; the remaining 210 have no estimate.

**INE status:** Estadística experimental, "etapa inicial de madurez" (INE's own label).

**Vintage:** Reference year 2024; first published 2026-01-21.

**sha256 of ingested file:** \`ad9503826fd21590eca7cf37629872df09f3115ad0c6d80dfe5cedcb63c3d4ba\`

**Used by:** \`data/snapshots/enusc_vhdv.json\` → \`data/cead/comunas/{CUT}.json\` (enusc_vhdv field) → \`site/src/pages/commune/[slug].astro\` section 6c (F16). See also \`data/snapshots/ATTRIBUTION.md\`.

**Licence:** Datos públicos del Estado de Chile (INE terms).

**Distinct from:** \`## ENUSC — underreporting / cifra negra\` (F11 above) which references the ENUSC national survey for underreporting statistics, not the SAE communal estimates.
`;

describe('figure-registry.lib.mjs — checkF16 (DOCS-05 hardening)', () => {
  it('Test 1: heading-only stub (zero body) returns false, even though the heading text itself contains "VHDV"', () => {
    const fixture = `${REAL_HEADING}\n\n---\n\n${NEXT_HEADING}\n\nSome unrelated body text for the next section.\n`;
    expect(checkF16(fixture)).toBe(false);
  });

  it('Test 2: the real, fully-populated section returns true', () => {
    const fixture = `${REAL_SECTION_BODY}\n---\n\n${NEXT_HEADING}\n\nSome unrelated body text for the next section.\n`;
    expect(checkF16(fixture)).toBe(true);
  });

  it('Test 3: extractSection bounds correctly across three "## " sections (middle section only, no spill into the third)', () => {
    const fixture = [
      '## First section',
      'First body text.',
      '',
      '## Middle section',
      'Middle body text line one.',
      'Middle body text line two.',
      '',
      '## Third section',
      'Third body text — must not appear in the middle extraction.',
      '',
    ].join('\n');

    const extracted = extractSection(fixture, '## Middle section');
    expect(extracted).toContain('Middle body text line one.');
    expect(extracted).toContain('Middle body text line two.');
    expect(extracted).not.toContain('Third body text');
    expect(extracted).not.toContain('## Third section');
  });

  it('Test 4: the padded-stub case — filler-with-no-tokens fails via the token check, and a too-short genuine-looking body fails via the length check', () => {
    // 4a: heading + ~250 chars of filler containing none of the token-group members
    // — long enough to pass the length gate, but must still fail via the token check.
    const filler = 'x'.repeat(250);
    const fixtureA = `${REAL_HEADING}\n${filler}\n\n${NEXT_HEADING}\n\nUnrelated next-section body.\n`;
    expect(filler.length).toBeGreaterThan(200);
    expect(checkF16(fixtureA)).toBe(false);

    // 4b: heading + 150 chars of genuine-looking body containing real tokens from
    // both groups, but under the 200-char floor — must fail via the LENGTH check.
    const shortBody =
      'VHDV ENUSC Victimizacion en Hogares SAE — a genuine-looking but too-short body that still contains real tokens from both groups but under the 200-char floor.';
    expect(shortBody.length).toBeLessThanOrEqual(200);
    const fixtureB = `${REAL_HEADING}\n${shortBody}\n\n${NEXT_HEADING}\n\nUnrelated next-section body.\n`;
    expect(checkF16(fixtureB)).toBe(false);
  });

  it('Test 4c (WR-01/H1): padded-stub-with-VHDV — a filler body that copies the heading\'s own "VHDV" word, long enough to clear the length floor, must still fail: one provenance marker is below the threshold', () => {
    // This is the exact hole WR-01 identified: token-free filler (4a) was never
    // a real probe of the token check, because a stub that merely repeats "VHDV"
    // from the heading into its filler used to pass on tokens + length alone.
    const filler = 'x'.repeat(250);
    const stubWithVHDV = `${REAL_HEADING}\n${filler}VHDV\n\n${NEXT_HEADING}\n\nUnrelated next-section body.\n`;
    expect(checkF16(stubWithVHDV)).toBe(false);
  });

  it('Test 4d (RR-H3): deleting ONE line from the real section is an ordinary edit and must NOT redden the build', () => {
    // Fix cycle 2 deliberately REVERSED this test's expectation. The first
    // hardening required the literal strings `sha256` AND `136 of 346`, so
    // deleting the checksum line — or merely reformatting `136 of 346` to
    // `136/346` — failed the build against a still-perfectly-valid registry
    // entry. That is a landmine for the next person to edit SOURCES.md, and
    // the mirror image of the stub hole it was closing. The contract is now
    // an N-of-M provenance-marker threshold: ordinary edits survive, gutting
    // does not. See figure-registry.lib.mjs's RR-H3 note.
    const gutted = REAL_SECTION_BODY.replace(
      /\*\*sha256 of ingested file:\*\* `[a-f0-9]+`\n\n/,
      ''
    );
    // Sanity: the replace actually removed the line (guards against the regex
    // silently no-op'ing and the test passing for the wrong reason).
    expect(gutted).not.toContain('sha256');
    const fixture = `${gutted}\n---\n\n${NEXT_HEADING}\n\nSome unrelated body text for the next section.\n`;
    expect(checkF16(fixture)).toBe(true);
  });

  it('Test 4e (RR-H3): a body reduced below the provenance-marker threshold still fails, so 4d is a tolerance and not a hole', () => {
    // 4d on its own would be indistinguishable from "the check no longer checks
    // anything". This pins the other side: strip the section down to prose that
    // clears the length floor but carries fewer than three provenance markers,
    // and it must still be rejected.
    const thinBody =
      'This entry used to describe a dataset. ' +
      'It no longer records where the file came from, who published it, or what it measures. ' +
      'It is left here only so the heading still exists in the registry file. ' +
      'VHDV is mentioned once in passing and nothing else is documented at all here.';
    const fixture = `${REAL_HEADING}\n\n${thinBody}\n\n${NEXT_HEADING}\n\nNext section body.\n`;
    expect(thinBody.length).toBeGreaterThan(200);
    expect(checkF16(fixture)).toBe(false);
  });

  it('Test 4f (RR-H3): a failure reports its real cause, not an empty token list', () => {
    // The caller used to print `Missing tokens: []` for every F16 failure, because
    // the substance requirements were never members of figure.tokens.
    const detail = checkF16Detail(`${REAL_HEADING}\n\n${NEXT_HEADING}\n`);
    expect(detail.ok).toBe(false);
    expect(detail.reason).toMatch(/stub|chars/i);
    expect(detail.reason.length).toBeGreaterThan(10);
  });
});
