"""qh-lookahead — Look-ahead bias detection (Phase 3)."""

import argparse
import sys


def _parse_args():
    p = argparse.ArgumentParser(
        prog="qh-lookahead",
        description="Detect look-ahead bias by shifting input dates forward.",
    )
    p.add_argument("--engine", required=True, help="Engine function (file.py::func_name)")
    p.add_argument("--shifts", default="1,2,3,6", help="Comma-separated shift months (default: 1,2,3,6)")
    p.add_argument("--output", choices=["json", "markdown", "terminal"], default="terminal")
    return p.parse_args()


def main():
    args = _parse_args()
    print("qh-lookahead: Not yet implemented (Phase 3).")
    print(f"  Engine: {args.engine}")
    print(f"  Shifts: {args.shifts}")
    sys.exit(0)


if __name__ == "__main__":
    main()
