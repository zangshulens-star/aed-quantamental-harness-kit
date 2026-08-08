"""qh-null-audit — NaN silent degradation detection.

Scans a panel CSV for null prevalence and assesses impact on signal quality.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import numpy as np


def _parse_args():
    p = argparse.ArgumentParser(
        prog="qh-null-audit",
        description="Detect NaN silent degradation in panel data.",
    )
    p.add_argument("--panel", required=True, help="Path to panel CSV file")
    p.add_argument("--engine", help="Engine function (file.py::func_name) for impact tracing (future)")
    p.add_argument("--output", choices=["json", "markdown", "terminal"], default="terminal")
    p.add_argument("--severity", choices=["critical", "warning", "info"], default="warning",
                   help="Minimum severity to report")
    return p.parse_args()


def audit_panel(csv_path: str) -> Dict[str, Any]:
    """Scan a CSV panel for null statistics."""
    df = pd.read_csv(csv_path, parse_dates=True)

    results = {
        "file": csv_path,
        "rows": len(df),
        "columns": len(df.columns),
        "columns_detail": [],
    }

    date_cols = [c for c in df.columns if df[c].dtype == 'object' and pd.to_datetime(df[c], errors='coerce').notna().all()]
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    for col in numeric_cols:
        null_count = int(df[col].isna().sum())
        null_pct = null_count / len(df) if len(df) > 0 else 0.0

        # Find contiguous null periods
        null_periods = []
        if null_count > 0:
            is_null = df[col].isna()
            start_idx = None
            for i, isn in enumerate(is_null):
                if isn and start_idx is None:
                    start_idx = i
                elif not isn and start_idx is not None:
                    null_periods.append((start_idx, i - 1))
                    start_idx = None
            if start_idx is not None:
                null_periods.append((start_idx, len(df) - 1))

        # Impact rating
        if null_pct > 0.30:
            impact = "CRITICAL"
        elif null_pct > 0.10:
            impact = "WARNING"
        else:
            impact = "OK"

        col_info = {
            "column": col,
            "null_count": null_count,
            "null_pct": round(null_pct * 100, 2),
            "impact": impact,
            "null_periods": len(null_periods),
            "longest_null_streak": max((e - s + 1) for s, e in null_periods) if null_periods else 0,
        }
        results["columns_detail"].append(col_info)

    return results


def render_terminal(results: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 64)
    lines.append(f"  Null Audit: {results['file']}")
    lines.append(f"  Rows: {results['rows']}  Columns: {results['columns']}")
    lines.append("=" * 64)
    lines.append(f"  {'Column':<28s} {'Null%':>7s} {'Periods':>8s} {'Streak':>7s}  Impact")
    lines.append(f"  {'-'*28} {'-'*7} {'-'*8} {'-'*7}  {'-'*8}")

    critical_count = 0
    warning_count = 0
    for col in results["columns_detail"]:
        if col["null_pct"] == 0 and col["impact"] == "OK":
            continue
        lines.append(
            f"  {col['column']:<28s} {col['null_pct']:>6.1f}% {col['null_periods']:>8d} "
            f"{col['longest_null_streak']:>7d}  {col['impact']}"
        )
        if col["impact"] == "CRITICAL":
            critical_count += 1
        elif col["impact"] == "WARNING":
            warning_count += 1

    lines.append(f"\n  Critical: {critical_count}  Warning: {warning_count}  OK: {len(results['columns_detail']) - critical_count - warning_count}")
    return "\n".join(lines)


def render_json(results: Dict[str, Any]) -> str:
    import json
    return json.dumps(results, indent=2, ensure_ascii=False)


def render_markdown(results: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"# Null Audit Report")
    lines.append(f"")
    lines.append(f"**File:** `{results['file']}`  ")
    lines.append(f"**Rows:** {results['rows']} | **Columns:** {results['columns']}  ")
    lines.append(f"")
    lines.append(f"| Column | Null % | Periods | Max Streak | Impact |")
    lines.append(f"|--------|-------:|--------:|-----------:|--------|")
    for col in results["columns_detail"]:
        lines.append(f"| {col['column']} | {col['null_pct']:.1f}% | {col['null_periods']} | {col['longest_null_streak']} | {col['impact']} |")
    return "\n".join(lines)


def main():
    args = _parse_args()

    panel_path = Path(args.panel)
    if not panel_path.exists():
        print(f"ERROR: Panel file not found: {args.panel}", file=sys.stderr)
        sys.exit(4)

    results = audit_panel(str(panel_path))

    renders = {"terminal": render_terminal, "json": render_json, "markdown": render_markdown}
    renderer = renders.get(args.output, render_terminal)
    print(renderer(results))

    # Exit code based on severity threshold
    criticals = [c for c in results["columns_detail"] if c["impact"] == "CRITICAL"]
    warnings = [c for c in results["columns_detail"] if c["impact"] == "WARNING"]

    if args.severity == "critical" and criticals:
        sys.exit(1)
    elif args.severity == "warning" and (criticals or warnings):
        sys.exit(1)
    elif criticals:
        sys.exit(1)
    elif warnings:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
