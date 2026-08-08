"""qh-auto-claims — Automatic claim generation (Phase 2)."""

import argparse
import sys


def _parse_args():
    p = argparse.ArgumentParser(
        prog="qh-auto-claims",
        description="Auto-generate claims.yaml template from engine output or paper scan.",
    )
    p.add_argument("--from-engine", help="Engine function (file.py::func_name)")
    p.add_argument("--from-paper", help="Path to paper directory")
    p.add_argument("--output", default="claims_template.yaml", help="Output YAML file path")
    return p.parse_args()


def main():
    args = _parse_args()
    print("qh-auto-claims: Not yet implemented (Phase 2).")
    print(f"  Engine: {args.from_engine or '(not provided)'}")
    print(f"  Paper:  {args.from_paper or '(not provided)'}")
    print(f"  Output: {args.output}")
    sys.exit(0)


if __name__ == "__main__":
    main()
