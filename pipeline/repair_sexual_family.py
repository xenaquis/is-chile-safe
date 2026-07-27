"""
pipeline/repair_sexual_family.py

Deterministic, LLM-free repair script: re-classifies news incidents that were
mis-classified as family "vida" but whose text clearly indicates a sexual crime,
promoting them to the news-only family "sexuales".

DEATH-DOMINATES RULE: If an incident matches both a sexual-crime term AND a death
term (homicidio, femicidio, etc.) it stays "vida" — the death classification dominates.
This mirrors the classifier SYSTEM_PROMPT carve-out added in task j6z-1.

R2 CREDS GUARD: R2 credentials are loaded from pipeline/.env (or environment). If any
required var (R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET) is
absent or an empty string, the R2 step is SKIPPED with a loud warning and the script
exits 0 — local repair already succeeded. GitHub Actions injects unset secrets as empty
strings; treating "" as missing prevents accidental writes to Bucket="" (known gotcha).

IDEMPOTENT: Re-running flips nothing new — only "vida" items are candidates, and once
flipped to "sexuales" they no longer match the candidate predicate.

Usage:
    python pipeline/repair_sexual_family.py           # local repair only
    python pipeline/repair_sexual_family.py --r2      # attempt R2 sync after local repair
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import pathlib
import re
import sys

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Sexual-crime keywords — explicit alternatives that do NOT false-hit "violento"/"violencia".
# Anchored to avoid "violento" prefix hit: use word-boundary assertions and full-form stems.
_SEXUAL_TERMS = "|".join([
    r"violaci[oó]n",           # violacion / violación (full noun, not "violento")
    r"viol[oó]",               # violó / violo (past tense verb)
    r"violad[ao]r?e?s?",       # violada/violado/violador/violadores
    r"\babuso sexual",         # abuso sexual (anchored to avoid "abusivo")
    r"estupro",
    r"grooming",
    r"pornograf[ií]a infantil",
    r"connotaci[oó]n sexual",
    r"acoso sexual",
    r"agresi[oó]n sexual",
    r"abuso deshonesto",
    r"ultraje",
    r"\bsexual\b",             # standalone adjective (e.g. "delito sexual")
])

_SEXUAL_RE = re.compile(_SEXUAL_TERMS, re.IGNORECASE)

# Death terms — when co-present, family stays "vida" (death dominates).
_DEATH_TERMS = "|".join([
    r"muri[oó]",
    r"muerte",
    r"asesin",
    r"homicid",
    r"femicid",
    r"parricid",
    r"cad[aá]ver",
    r"fallec",
    r"occiso",
    r"degollad",
])

_DEATH_RE = re.compile(_DEATH_TERMS, re.IGNORECASE)

# Allowed news-family set (must match pipeline/news/schema.py VALID_FAMILIES)
_VALID_NEWS_FAMILIES = {
    "vida", "propiedad", "robos_violentos", "incivilidades",
    "vif", "drogas", "armas", "sexuales",
}


# ---------------------------------------------------------------------------
# Core predicate (module-level, unit-testable)
# ---------------------------------------------------------------------------

def determine_family(
    title_es: str,
    title_en: str,
    summary: str,
    current_family: str,
) -> str:
    """Return the corrected family string for an incident.

    Only incidents with current_family == "vida" are eligible for promotion.
    Returns "sexuales" if the combined text matches a sexual-crime term and
    does NOT match a death term (death-dominates rule).
    Returns current_family unchanged in all other cases.
    """
    if current_family != "vida":
        return current_family

    combined = " ".join(filter(None, [title_es, title_en, summary]))

    if not _SEXUAL_RE.search(combined):
        return current_family  # no sexual term — leave as vida

    if _DEATH_RE.search(combined):
        return current_family  # death term co-present — death dominates, keep vida

    return "sexuales"


# ---------------------------------------------------------------------------
# Local repair
# ---------------------------------------------------------------------------

def repair_local(current_json_path: pathlib.Path) -> tuple[int, int]:
    """Load, flip, write back. Returns (flipped_count, skipped_death_count)."""
    data = json.loads(current_json_path.read_text(encoding="utf-8"))
    incidents = data["incidents"]

    flipped: list[dict] = []
    skipped_death: list[dict] = []

    for inc in incidents:
        old_family = inc["family"]
        new_family = determine_family(
            inc.get("title_es", ""),
            inc.get("title_en", ""),
            inc.get("summary", ""),
            old_family,
        )
        if new_family != old_family:
            logger.info("FLIP  id=%s | %s | %s -> %s",
                        inc.get("id", "?"), inc.get("title_es", "")[:80], old_family, new_family)
            inc["family"] = new_family
            flipped.append(inc)
        elif old_family == "vida":
            # Check if it was a sexual+death co-hit (kept as vida intentionally)
            combined = " ".join(filter(None, [
                inc.get("title_es", ""), inc.get("title_en", ""), inc.get("summary", "")
            ]))
            if _SEXUAL_RE.search(combined) and _DEATH_RE.search(combined):
                logger.info("KEEP  id=%s | %s (death+sexual -> vida)",
                            inc.get("id", "?"), inc.get("title_es", "")[:80])
                skipped_death.append(inc)

    current_json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info("Local repair done: %d flipped to sexuales, %d death-dominated kept as vida",
                len(flipped), len(skipped_death))
    return len(flipped), len(skipped_death)


# ---------------------------------------------------------------------------
# R2 repair (optional, guarded)
# ---------------------------------------------------------------------------

def _load_r2_creds() -> dict[str, str] | None:
    """Load R2 creds from env / pipeline/.env. Returns None if any required var is empty."""
    try:
        from dotenv import load_dotenv  # type: ignore
        env_file = pathlib.Path(__file__).parent / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=False)
    except ImportError:
        pass  # python-dotenv not installed; rely on shell env

    required = ["R2_ENDPOINT_URL", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"]
    creds: dict[str, str] = {}
    for key in required:
        val = os.environ.get(key, "")
        if not val.strip():
            logger.warning(
                "R2 creds: %s is empty or missing — skipping R2 sync. "
                "Set %s in pipeline/.env or environment to enable R2 repair.",
                key, key,
            )
            return None
        creds[key] = val
        # Log name only, never value
        logger.info("R2 creds: %s is set", key)
    return creds


def repair_r2(creds: dict[str, str], current_json_path: pathlib.Path) -> None:
    """Rebuild R2 archive outputs (incidents.csv + corpus-state.json) from repaired local JSON.

    The archive_r2 module's build_corpus_state() and to_csv() read inc["family"] fresh
    each run from the incidents list, so re-running archive_r2 after correcting
    current.json produces correct CSV and corpus-state outputs.

    URL ledger (url-ledger.jsonl): url-ledger rows do NOT carry a "family" field —
    only status/url/id/kind/text_sha256/fetched_at. No ledger rewrite is needed.
    """
    logger.info("Attempting R2 rebuild via pipeline.archive_r2 ...")
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pipeline.archive_r2"],
            capture_output=False,
            cwd=str(current_json_path.parents[2]),
        )
        if result.returncode != 0:
            logger.error("archive_r2 exited with code %d — check output above", result.returncode)
        else:
            logger.info("R2 rebuild complete (incidents.csv + corpus-state.json updated).")
            logger.info(
                "NOTE: url-ledger.jsonl rows do not carry a 'family' field — no ledger rewrite needed."
            )
    except Exception as exc:
        logger.error("R2 rebuild failed: %s: %s", type(exc).__name__, exc)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Repair sexual-crime mis-classifications in current.json")
    parser.add_argument("--r2", action="store_true", help="Attempt R2 archive rebuild after local repair")
    args = parser.parse_args()

    repo_root = pathlib.Path(__file__).parents[1]
    current_json_path = repo_root / "data" / "incidents" / "current.json"

    if not current_json_path.exists():
        logger.error("current.json not found at %s", current_json_path)
        sys.exit(1)

    flipped, kept_death = repair_local(current_json_path)

    # Summary
    data = json.loads(current_json_path.read_text(encoding="utf-8"))
    by_family: dict[str, int] = {}
    for inc in data["incidents"]:
        by_family[inc["family"]] = by_family.get(inc["family"], 0) + 1

    print("\n=== Repair Summary ===")
    print(f"Flipped vida -> sexuales: {flipped}")
    print(f"Death-dominated kept as vida: {kept_death}")
    print("Family counts after repair:")
    for fam, cnt in sorted(by_family.items()):
        print(f"  {fam}: {cnt}")
    print("=====================\n")

    if args.r2:
        creds = _load_r2_creds()
        if creds is None:
            logger.warning("R2 sync skipped — creds not available. Local repair succeeded.")
        else:
            repair_r2(creds, current_json_path)
    else:
        logger.info("R2 sync skipped (pass --r2 to attempt). Local repair succeeded.")
        logger.info(
            "To update R2 archive, run: python pipeline/repair_sexual_family.py --r2"
        )


if __name__ == "__main__":
    main()
