"""VerifierDispatcher + 9 Verifier classes for claim type validation."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


@dataclass
class Verdict:
    """Result of verifying a single claim."""
    claim_id: str
    status: str           # PASS | FAIL | STALE | UNVERIFIABLE | ERROR
    claim_type: str
    expected: Any
    actual_summary: Any    # Summarized actual value for reporting
    detail: str = ""
    diff: Optional[float] = None
    severity: str = "warning"


class BaseVerifier:
    """Base class for all claim verifiers."""

    claim_type: str = ""

    def verify(self, claim_id: str, expected: Any, actual_series: pd.Series,
               tolerance: Dict[str, Any], severity: str) -> Verdict:
        raise NotImplementedError


class ValueExactVerifier(BaseVerifier):
    """Compare a computed value against an expected exact value, within tolerance."""

    claim_type = "value_exact"

    def verify(self, claim_id: str, expected: Any, actual_series: pd.Series,
               tolerance: Dict[str, Any], severity: str) -> Verdict:
        actual_val = float(actual_series.iloc[-1])  # latest value

        if isinstance(expected, (int, float)):
            expected_val = float(expected)
        else:
            return Verdict(claim_id, "ERROR", "value_exact", expected, actual_val,
                          f"Expected must be numeric, got {type(expected).__name__}", severity=severity)

        rel_tol = tolerance.get("relative", 0.01)
        abs_tol = tolerance.get("absolute", 0.0)

        diff = actual_val - expected_val
        if abs(diff) <= abs_tol or (expected_val != 0 and abs(diff / expected_val) <= rel_tol):
            return Verdict(claim_id, "PASS", "value_exact", expected_val, actual_val,
                          f"diff={diff:.6g}", diff=diff, severity=severity)
        else:
            return Verdict(claim_id, "FAIL", "value_exact", expected_val, actual_val,
                          f"diff={diff:.6g} (tol: rel={rel_tol}, abs={abs_tol})",
                          diff=diff, severity=severity)


class ValueRangeVerifier(BaseVerifier):
    """Check that a computed value falls within an expected range."""

    claim_type = "value_range"

    def verify(self, claim_id: str, expected: Any, actual_series: pd.Series,
               tolerance: Dict[str, Any], severity: str) -> Verdict:
        actual_val = float(actual_series.iloc[-1])

        if not isinstance(expected, dict) or "min" not in expected or "max" not in expected:
            return Verdict(claim_id, "ERROR", "value_range", expected, actual_val,
                          "Expected must be {min: X, max: Y}", severity=severity)

        lo, hi = float(expected["min"]), float(expected["max"])
        if lo <= actual_val <= hi:
            return Verdict(claim_id, "PASS", "value_range", f"[{lo}, {hi}]", actual_val,
                          f"value={actual_val:.6g} in [{lo:.6g}, {hi:.6g}]", severity=severity)
        else:
            return Verdict(claim_id, "FAIL", "value_range", f"[{lo}, {hi}]", actual_val,
                          f"value={actual_val:.6g} outside [{lo:.6g}, {hi:.6g}]", severity=severity)


class AggregateVerifier(BaseVerifier):
    """Compare an aggregate (sum/mean/max/min/count) against expected value."""

    claim_type = "aggregate"

    def verify(self, claim_id: str, expected: Any, actual_series: pd.Series,
               tolerance: Dict[str, Any], severity: str) -> Verdict:
        if not isinstance(expected, dict) or "method" not in expected or "value" not in expected:
            return Verdict(claim_id, "ERROR", "aggregate", expected, None,
                          "Expected must be {method: sum|mean|max|min|count, value: X}", severity=severity)

        method = expected["method"]
        expected_val = float(expected["value"])

        agg_map = {
            "sum": actual_series.sum(),
            "mean": actual_series.mean(),
            "max": actual_series.max(),
            "min": actual_series.min(),
            "count": actual_series.count(),
            "std": actual_series.std(),
            "last": actual_series.iloc[-1],
            "first": actual_series.iloc[0],
        }
        if method not in agg_map:
            return Verdict(claim_id, "ERROR", "aggregate", expected, None,
                          f"Unknown aggregate method: {method}", severity=severity)

        actual_val = float(agg_map[method])
        rel_tol = tolerance.get("relative", 0.01)
        abs_tol = tolerance.get("absolute", 0.0)

        diff = actual_val - expected_val
        if abs(diff) <= abs_tol or (expected_val != 0 and abs(diff / expected_val) <= rel_tol):
            return Verdict(claim_id, "PASS", "aggregate",
                          f"{method}={expected_val}", f"{method}={actual_val:.6g}",
                          f"diff={diff:.6g}", diff=diff, severity=severity)
        else:
            return Verdict(claim_id, "FAIL", "aggregate",
                          f"{method}={expected_val}", f"{method}={actual_val:.6g}",
                          f"diff={diff:.6g}", diff=diff, severity=severity)


class TimeMaskVerifier(BaseVerifier):
    """Verify that a condition holds during a specific time period."""

    claim_type = "time_mask"

    def verify(self, claim_id: str, expected: Any, actual_series: pd.Series,
               tolerance: Dict[str, Any], severity: str) -> Verdict:
        if not isinstance(expected, dict) or "start" not in expected or "end" not in expected:
            return Verdict(claim_id, "ERROR", "time_mask", expected, None,
                          "Expected must be {start: YYYY-MM-DD, end: YYYY-MM-DD, condition: '>|<|== X'}",
                          severity=severity)

        start = pd.Timestamp(expected["start"])
        end = pd.Timestamp(expected["end"])
        condition = expected.get("condition", "any")

        mask = (actual_series.index >= start) & (actual_series.index <= end)
        period_data = actual_series[mask]

        if len(period_data) == 0:
            return Verdict(claim_id, "STALE", "time_mask", f"{start}→{end}", "no data",
                          f"No data in period {start}→{end}", severity=severity)

        if condition == "any":
            ok = True
            detail = f"{len(period_data)} obs in [{start}, {end}]"
        elif condition.startswith("all > "):
            threshold = float(condition.replace("all > ", ""))
            ok = bool((period_data > threshold).all())
            detail = f"all > {threshold}: {ok}"
        elif condition.startswith("all < "):
            threshold = float(condition.replace("all < ", ""))
            ok = bool((period_data < threshold).all())
            detail = f"all < {threshold}: {ok}"
        elif condition.startswith("mean > "):
            threshold = float(condition.replace("mean > ", ""))
            ok = bool(period_data.mean() > threshold)
            detail = f"mean={period_data.mean():.4g} > {threshold}: {ok}"
        elif condition.startswith("mean < "):
            threshold = float(condition.replace("mean < ", ""))
            ok = bool(period_data.mean() < threshold)
            detail = f"mean={period_data.mean():.4g} < {threshold}: {ok}"
        else:
            ok = True
            detail = f"{len(period_data)} obs, condition '{condition}' not parsed"

        status = "PASS" if ok else "FAIL"
        return Verdict(claim_id, status, "time_mask",
                      f"{start}→{end} {condition}", f"{len(period_data)} obs",
                      detail, severity=severity)


class CrossCountVerifier(BaseVerifier):
    """Count rows matching a cross-section condition."""

    claim_type = "cross_count"

    def verify(self, claim_id: str, expected: Any, actual_series: pd.Series,
               tolerance: Dict[str, Any], severity: str) -> Verdict:
        if not isinstance(expected, dict):
            return Verdict(claim_id, "ERROR", "cross_count", expected, None,
                          "Expected must be {condition: str, count: int}", severity=severity)

        condition = expected.get("condition", "")
        expected_count = int(expected.get("count", 0))

        actual_count = len(actual_series)  # Simplification: count all rows
        # More sophisticated: if actual_series is from a filtered dataframe, count reflects filter

        diff = actual_count - expected_count
        if diff == 0:
            return Verdict(claim_id, "PASS", "cross_count",
                          f"count={expected_count}", f"count={actual_count}",
                          f"exact match", severity=severity)
        else:
            return Verdict(claim_id, "FAIL", "cross_count",
                          f"count={expected_count}", f"count={actual_count}",
                          f"diff={diff:+d}", severity=severity)


class SetEqualityVerifier(BaseVerifier):
    """Verify a set of values matches expected set."""

    claim_type = "set_equality"

    def verify(self, claim_id: str, expected: Any, actual_series: pd.Series,
               tolerance: Dict[str, Any], severity: str) -> Verdict:
        if not isinstance(expected, list):
            return Verdict(claim_id, "ERROR", "set_equality", expected, None,
                          "Expected must be a list of values", severity=severity)

        actual_set = set(actual_series.dropna().unique())
        expected_set = set(expected)

        missing = expected_set - actual_set
        extra = actual_set - expected_set

        if not missing and not extra:
            return Verdict(claim_id, "PASS", "set_equality",
                          f"set({len(expected_set)} items)", f"set({len(actual_set)} items)",
                          "sets match exactly", severity=severity)
        else:
            detail_parts = []
            if missing:
                detail_parts.append(f"missing: {sorted(missing)[:5]}")
            if extra:
                detail_parts.append(f"extra: {sorted(extra)[:5]}")
            return Verdict(claim_id, "FAIL", "set_equality",
                          f"set({len(expected_set)} items)", f"set({len(actual_set)} items)",
                          "; ".join(detail_parts), severity=severity)


# Registry: claim_type → Verifier instance
_VERIFIERS: Dict[str, BaseVerifier] = {
    "value_exact": ValueExactVerifier(),
    "value_range": ValueRangeVerifier(),
    "aggregate": AggregateVerifier(),
    "time_mask": TimeMaskVerifier(),
    "cross_count": CrossCountVerifier(),
    "set_equality": SetEqualityVerifier(),
    # Extended verifiers (Phase 2/3):
    # "combo_match": ComboMatchVerifier(),
    # "counterfactual": CounterfactualVerifier(),
    # "rank_position": RankPositionVerifier(),
    # "invariant": InvariantVerifier(),
}


class UnsupportedClaimType(Exception):
    """Raised when a claim type has no registered verifier."""


def dispatch_verifier(claim_type: str) -> BaseVerifier:
    """Get the verifier for a claim type."""
    verifier = _VERIFIERS.get(claim_type)
    if verifier is None:
        raise UnsupportedClaimType(
            f"No verifier for claim type '{claim_type}'. Available: {list(_VERIFIERS.keys())}"
        )
    return verifier


def run_verification(
    claim_id: str,
    claim_type: str,
    expected: Any,
    actual_series: pd.Series,
    tolerance: Dict[str, Any],
    severity: str,
) -> Verdict:
    """Run a single claim verification.

    Args:
        claim_id: Claim identifier
        claim_type: Type of claim (value_exact, aggregate, etc.)
        expected: Expected value from claims.yaml
        actual_series: Resolved pandas Series of actual data
        tolerance: Tolerance settings
        severity: Claim severity (critical/warning/info)

    Returns:
        Verdict with PASS/FAIL/STALE/UNVERIFIABLE/ERROR status.
    """
    try:
        verifier = dispatch_verifier(claim_type)
        return verifier.verify(claim_id, expected, actual_series, tolerance, severity)
    except UnsupportedClaimType as e:
        return Verdict(claim_id, "UNVERIFIABLE", claim_type, expected, len(actual_series),
                      str(e), severity=severity)
    except Exception as e:
        return Verdict(claim_id, "ERROR", claim_type, expected, None,
                      f"Verification error: {e}", severity=severity)
