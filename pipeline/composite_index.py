"""
pipeline/composite_index.py

Pure compute functions for the composite crime-exposure index.
No file I/O — importable by tests and by build_composite_index.py.

Mirrors pipeline/cead/normalizer.py style: pure functions, no side effects.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats.mstats import winsorize

from pipeline.composite_config import (
    METRIC_WEIGHTS,
    SII_CAP_RATIO,
    WINSORIZE_LIMITS,
)


def normalize_metric(series: pd.Series) -> pd.Series:
    """Winsorize then min-max scale to [0, 100]. NaN communes preserved as NaN.

    Uses scipy.stats.mstats.winsorize with limits=[0.01, 0.01] (D-01).
    NaN re-injection is load-bearing: winsorize may treat NaN as valid values
    depending on scipy version — we restore the original NaN mask after scaling.

    Args:
        series: pd.Series of float values (rate per 100k). NaN = missing commune.

    Returns:
        pd.Series of float in [0, 100] with NaN preserved for missing communes.
    """
    arr = np.array(series, dtype=float)

    # Winsorize on original array (including NaN — scipy masked array handles this)
    arr_w = np.array(winsorize(arr, limits=list(WINSORIZE_LIMITS)))

    lo = np.nanmin(arr_w)
    hi = np.nanmax(arr_w)

    if hi == lo:
        result = np.zeros(len(arr))
    else:
        result = (arr_w - lo) / (hi - lo) * 100.0

    # Re-inject NaN by original mask — this is the load-bearing step
    result[np.isnan(arr)] = np.nan

    return pd.Series(result, index=series.index)


def get_exposure_denominator(
    cut: str,
    sii_by_cut: dict[str, float | None],
    ine_pop: dict[str, float],
) -> tuple[float, bool]:
    """Return the effective exposure denominator and whether the SII cap was triggered.

    SII cap logic (D-04):
      - If commune absent from SII (None) or INE population <= 0 -> INE fallback, no cap.
      - If sii_workers / ine_population > SII_CAP_RATIO -> INE fallback, cap triggered.
      - Otherwise -> use SII workers.

    Critical: None from dict.get() means absent. Never conflate with 0 (Pitfall 1).

    Args:
        cut: CUT code string.
        sii_by_cut: {cut: trabajadores_2024} — None means commune absent from SII.
        ine_pop: {cut: population_2024} — INE population estimate.

    Returns:
        (effective_denominator, used_cap_fallback)
    """
    ine = float(ine_pop.get(cut, 0))
    sii = sii_by_cut.get(cut)  # None if commune absent from SII 2024

    if sii is None or ine <= 0:
        return ine, False  # no SII data — use INE (or 0 if both absent)

    ratio = sii / ine
    if ratio > SII_CAP_RATIO:
        return ine, True   # cap triggered — fall back to INE
    return float(sii), False


def assert_year_alignment(cead_year: int, spd_year: int, sii_year: int) -> None:
    """Fail loudly if the three data sources are not from the same reference year.

    Must be called BEFORE any compute (D-10, T-18-04).

    Args:
        cead_year: The CEAD year used for index computation.
        spd_year: The SPD VHC year.
        sii_year: The SII exposure year.

    Returns:
        None

    Raises:
        ValueError: If any year does not match the others.
    """
    if not (cead_year == spd_year == sii_year):
        raise ValueError(
            f"Year misalignment: CEAD={cead_year}, SPD={spd_year}, SII={sii_year}. "
            "All must match. Index anchors to the latest year where all three sources "
            "are final (<=2024)."
        )


def compute_composite(
    per_metric_normalized: dict[str, float | None],
) -> tuple[float, int]:
    """Compute the weighted composite score for a single commune.

    Metrics with NaN/None (absent for this commune) are excluded from the
    weighted sum; their weight is redistributed proportionally to available
    metrics by normalizing the weight sum of present metrics to 1.0.

    Args:
        per_metric_normalized: {metric_key: normalized_score_0_100 or None/NaN}

    Returns:
        (composite_score_0_100, available_metrics_count)
    """
    total_weight = 0.0
    weighted_sum = 0.0
    available = 0

    for metric, weight in METRIC_WEIGHTS.items():
        value = per_metric_normalized.get(metric)
        if value is None or (isinstance(value, float) and np.isnan(value)):
            continue
        weighted_sum += value * weight
        total_weight += weight
        available += 1

    if total_weight == 0 or available == 0:
        return 0.0, 0

    # Redistribute weight of absent metrics proportionally
    score = (weighted_sum / total_weight) * 100.0 / 100.0 * 100.0
    # Simplified: weighted_sum already uses [0,100] normalized values,
    # and we rescale by total_weight to normalize weights of present metrics
    score = weighted_sum / total_weight

    return float(score), available
