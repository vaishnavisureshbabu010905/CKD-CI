from __future__ import annotations
import numpy as np
from scipy import stats
from typing import Sequence


def _psi(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
    """Population Stability Index between two distributions."""
    expected = np.array(expected, dtype=float)
    actual = np.array(actual, dtype=float)
    # compute quantiles from expected
    breakpoints = np.percentile(expected, np.linspace(0, 100, buckets + 1))
    eps = 1e-6
    psi = 0.0
    for i in range(buckets):
        low = breakpoints[i]
        high = breakpoints[i + 1]
        exp_pct = ((expected >= low) & (expected <= high)).sum() / (len(expected) + eps)
        act_pct = ((actual >= low) & (actual <= high)).sum() / (len(actual) + eps)
        # avoid division by zero
        if exp_pct <= 0:
            exp_pct = eps
        if act_pct <= 0:
            act_pct = eps
        psi += (exp_pct - act_pct) * np.log(exp_pct / act_pct)
    return float(psi)


def compute_drift_score(baseline: Sequence[float], current: Sequence[float]) -> dict:
    try:
        score = _psi(np.asarray(baseline), np.asarray(current))
        # simple thresholding: PSI > 0.2 moderate, >0.3 significant
        drift_detected = score > 0.2
        return {"drift_score": score, "drift_detected": bool(drift_detected)}
    except Exception:
        return {"drift_score": 0.0, "drift_detected": False}
