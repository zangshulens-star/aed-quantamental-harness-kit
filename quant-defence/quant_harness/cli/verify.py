"""qh-verify — Claim verification (main tool).

Validates every claim in a claims.yaml registry against actual data or engine output.
"""

import argparse
import sys
from pathlib import Path

from ..core.loader import load_claims, ClaimsRegistry, SchemaError
from ..core.resolver import resolve_claim, ResolutionError
from ..core.verifiers import run_verification, Verdict
from ..core.reporter import VerificationReport, output_report


def _parse_args():
    p = argparse.ArgumentParser(
        prog="qh-verify",
        description="Verify quantitative claims against data or engine output.",
    )
    p.add_argument("--claims", required=True, help="Path to claims.yaml registry")
    p.add_argument("--all", action="store_true", help="Verify all claims (default)")
    p.add_argument("--chapter", help="Verify only claims in a specific chapter")
    p.add_argument("--severity", choices=["critical", "warning", "info"], help="Filter by severity")
    p.add_argument("--ids", nargs="*", help="Verify specific claim IDs")
    p.add_argument("--output", choices=["terminal", "json", "markdown"], default="terminal",
                   help="Output format (default: terminal)")
    p.add_argument("--output-file", help="Write output to file instead of stdout")
    p.add_argument("--diff", help="Snapshot directory for diff mode (reserved for future use)")
    p.add_argument("--engine-root", help="Override project root directory")
    return p.parse_args()


def main():
    args = _parse_args()

    # Load claims
    try:
        registry = load_claims(args.claims)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(4)
    except SchemaError as e:
        print(f"CONFIG ERROR:\n{e}", file=sys.stderr)
        sys.exit(4)

    # Override project root if specified
    if args.engine_root:
        registry.meta["project_root"] = args.engine_root

    project_root = registry.project_root
    engine_entry = registry.meta.get("engine_entry", "")

    # Filter claims
    claims = registry.filter(
        chapter=args.chapter,
        severity=args.severity,
        ids=args.ids,
    )

    if not claims:
        print("No claims matched filter criteria.", file=sys.stderr)
        sys.exit(0)

    # Verify each claim
    verdicts: list[Verdict] = []
    for claim in claims:
        try:
            actual = resolve_claim(claim.id, claim.source, engine_entry, project_root)
            verdict = run_verification(
                claim.id, claim.type, claim.expected, actual,
                claim.tolerance, claim.severity,
            )
        except ResolutionError as e:
            verdict = Verdict(claim.id, "ERROR", claim.type, claim.expected, None,
                            str(e), severity=claim.severity)

        verdicts.append(verdict)

    # Generate and output report
    report = VerificationReport.from_verdicts(
        verdicts, args.claims, registry.meta.get("project_name", "unknown")
    )

    output_report(report, fmt=args.output, file=args.output_file)

    sys.exit(report.exit_code)


if __name__ == "__main__":
    main()
