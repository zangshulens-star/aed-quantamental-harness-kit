"""ReportGenerator — JSON, Markdown, and terminal output for verification results."""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..core.verifiers import Verdict


@dataclass
class VerificationReport:
    """Aggregated results from a verification run."""
    run_time: str
    claims_file: str
    project_name: str
    verdicts: List[Verdict]
    summary: Dict[str, int] = field(default_factory=dict)
    exit_code: int = 0

    def __post_init__(self):
        self.summary = self._compute_summary()
        self.exit_code = self._compute_exit_code()

    def _compute_summary(self) -> Dict[str, int]:
        counts = {"PASS": 0, "FAIL": 0, "STALE": 0, "UNVERIFIABLE": 0, "ERROR": 0, "TOTAL": len(self.verdicts)}
        for v in self.verdicts:
            counts[v.status] = counts.get(v.status, 0) + 1
        return counts

    def _compute_exit_code(self) -> int:
        # 0 = ALL PASS (or no critical failures)
        # 1 = >=1 critical FAIL
        # 2 = >=1 STALE
        # 3 = >=1 UNVERIFIABLE
        # 4 = CONFIG_ERROR (handled at CLI level)
        critical_fails = [v for v in self.verdicts if v.status == "FAIL" and v.severity == "critical"]
        if critical_fails:
            return 1
        if self.summary.get("STALE", 0) > 0:
            return 2
        if self.summary.get("UNVERIFIABLE", 0) > 0:
            return 3
        return 0

    @classmethod
    def from_verdicts(cls, verdicts: List[Verdict], claims_file: str, project_name: str) -> "VerificationReport":
        return cls(
            run_time=datetime.now(timezone.utc).isoformat(),
            claims_file=claims_file,
            project_name=project_name,
            verdicts=verdicts,
        )


def _status_icon(status: str) -> str:
    icons = {"PASS": "[PASS]", "FAIL": "[FAIL]", "STALE": "[STALE]",
             "UNVERIFIABLE": "[UNV]", "ERROR": "[ERR]"}
    return icons.get(status, "[???]")


def render_terminal(report: VerificationReport) -> str:
    """Render verification report as colored terminal output."""
    lines = []
    lines.append("=" * 72)
    lines.append(f"  Quant Harness — Claim Verification Report")
    lines.append(f"  Project: {report.project_name}")
    lines.append(f"  Claims:  {report.claims_file}")
    lines.append(f"  Time:    {report.run_time}")
    lines.append("=" * 72)

    # Summary bar
    s = report.summary
    lines.append(f"\n  TOTAL={s['TOTAL']}  PASS={s['PASS']}  FAIL={s['FAIL']}  "
                 f"STALE={s['STALE']}  UNV={s['UNVERIFIABLE']}  ERR={s['ERROR']}")

    # Group by chapter
    by_chapter: Dict[str, List[Verdict]] = {}
    for v in report.verdicts:
        chap = getattr(v, "chapter", "?")
        if chap not in by_chapter:
            by_chapter[chap] = []
        by_chapter[chap].append(v)

    # If no chapter grouping (old-style verdicts), just list them
    for chapter, vlist in sorted(by_chapter.items()):
        lines.append(f"\n── {chapter} ──")
        for v in vlist:
            icon = _status_icon(v.status)
            lines.append(f"  {icon} {v.claim_id:<12s} {v.claim_type:<16s}  {v.detail}")

    # Overall exit code
    lines.append(f"\nExit code: {report.exit_code}")
    return "\n".join(lines)


def render_json(report: VerificationReport) -> str:
    """Render verification report as JSON."""
    output = {
        "run_time": report.run_time,
        "project": report.project_name,
        "claims_file": report.claims_file,
        "summary": report.summary,
        "exit_code": report.exit_code,
        "verdicts": [
            {
                "claim_id": v.claim_id,
                "status": v.status,
                "type": v.claim_type,
                "expected": str(v.expected),
                "actual": str(v.actual_summary),
                "detail": v.detail,
                "diff": v.diff,
                "severity": v.severity,
            }
            for v in report.verdicts
        ],
    }
    return json.dumps(output, indent=2, ensure_ascii=False)


def render_markdown(report: VerificationReport) -> str:
    """Render verification report as Markdown table."""
    lines = []
    lines.append(f"# Quant Harness — Verification Report")
    lines.append(f"")
    lines.append(f"**Project:** {report.project_name}  ")
    lines.append(f"**Claims:** `{report.claims_file}`  ")
    lines.append(f"**Time:** {report.run_time}  ")
    lines.append(f"")

    s = report.summary
    lines.append(f"| Status | Count |")
    lines.append(f"|--------|------:|")
    lines.append(f"| TOTAL  | {s['TOTAL']} |")
    lines.append(f"| PASS   | {s['PASS']} |")
    lines.append(f"| FAIL   | {s['FAIL']} |")
    lines.append(f"| STALE  | {s['STALE']} |")
    lines.append(f"| UNVERIFIABLE | {s['UNVERIFIABLE']} |")
    lines.append(f"| ERROR  | {s['ERROR']} |")
    lines.append(f"")
    lines.append(f"**Exit code:** {report.exit_code}")
    lines.append(f"")

    # Detail table
    lines.append(f"| Claim | Type | Expected | Actual | Status | Detail |")
    lines.append(f"|-------|------|----------|--------|--------|--------|")
    for v in report.verdicts:
        exp_str = str(v.expected)[:40]
        act_str = str(v.actual_summary)[:30]
        lines.append(f"| {v.claim_id} | {v.claim_type} | {exp_str} | {act_str} | {v.status} | {v.detail[:60]} |")

    return "\n".join(lines)


def output_report(report: VerificationReport, fmt: str = "terminal", file=None):
    """Write the report to a file or stdout.

    Args:
        report: VerificationReport to output.
        fmt: Output format — 'terminal', 'json', or 'markdown'.
        file: File path or None for stdout.
    """
    renders = {
        "terminal": render_terminal,
        "json": render_json,
        "markdown": render_markdown,
    }
    renderer = renders.get(fmt, render_terminal)
    output_str = renderer(report)

    if file:
        with open(file, "w", encoding="utf-8") as f:
            f.write(output_str)
    else:
        print(output_str)
