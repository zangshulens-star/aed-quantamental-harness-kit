"""qh-sensitivity — Parameter sensitivity scanner (Phase 3)."""

import argparse
import sys


def _parse_args():
    p = argparse.ArgumentParser(
        prog="qh-sensitivity",
        description="Scan parameter sensitivity of claims to parameter grid.",
    )
    p.add_argument("--engine", required=True, help="Engine function (file.py::func_name)")
    p.add_argument("--params", required=True, help="PARAM_SPEC.yaml file")
    p.add_argument("--claims", required=True, help="Claims registry YAML")
    p.add_argument("--output", choices=["json", "markdown", "terminal"], default="terminal")
    return p.parse_args()


def main():
    args = _parse_args()
    print("qh-sensitivity: Not yet implemented (Phase 3).")
    print(f"  Engine: {args.engine}")
    print(f"  Params: {args.params}")
    print(f"  Claims: {args.claims}")
    sys.exit(0)


if __name__ == "__main__":
    main()
