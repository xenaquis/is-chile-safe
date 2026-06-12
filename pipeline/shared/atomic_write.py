"""
pipeline/shared/atomic_write.py

Atomic JSON write utility using os.replace().
Prevents partial reads if the pipeline crashes mid-write.
Works on Windows and POSIX alike (os.replace is atomic on same filesystem).
"""
import json
import os
import pathlib


def atomic_write_json(path: pathlib.Path, data: dict | list) -> None:
    """
    Write JSON atomically: write to a .tmp file, then os.replace() to final path.

    Args:
        path: Destination file path (will be created or overwritten).
        data: JSON-serialisable dict or list.

    Side effects:
        Creates parent directories if missing.
        No .tmp file remains after a successful call.
        File is UTF-8 encoded with non-ASCII characters preserved (ensure_ascii=False).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(tmp, path)  # atomic on same filesystem (POSIX + Windows)
