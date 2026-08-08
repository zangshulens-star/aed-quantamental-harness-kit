"""qh-version-check — Version consistency checker (Phase 2)."""

import argparse
import sys


def _parse_args():
    p = argparse.ArgumentParser(
        prog="qh-version-check",
        description="Check version consistency between paper run_ids and manifest.",
    )
    p.add_argument("--paper", required=True, help="Path to paper directory")
    p.add_argument("--manifest", help="Path to manifest JSON file")
    p.add_argument("--output", choices=["json", "markdown", "terminal"], default="terminal")
    return p.parse_args()


def main():
    args = _parse_args()
    print("qh-version-check: Not yet implemented (Phase 2).")
    print(f"  Would scan: {args.paper}")
    print(f"  Manifest: {args.manifest or '(not provided)'}")
    sys.exit(0)


if __name__ == "__main__":
    main()
