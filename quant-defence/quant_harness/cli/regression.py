"""qh-regression — Regression test runner (Phase 2)."""

import argparse
import sys


def _parse_args():
    p = argparse.ArgumentParser(
        prog="qh-regression",
        description="Run regression tests from a regression directory.",
    )
    p.add_argument("--regression-dir", required=True, help="Path to regression test directory")
    p.add_argument("--output", choices=["json", "markdown", "terminal"], default="terminal")
    return p.parse_args()


def main():
    args = _parse_args()
    print("qh-regression: Not yet implemented (Phase 2).")
    print(f"  Regression dir: {args.regression_dir}")
    sys.exit(0)


if __name__ == "__main__":
    main()
