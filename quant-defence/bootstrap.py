#!/usr/bin/env python3
"""Quant Harness bootstrap — initialize a project for claim verification.

Usage:
    python bootstrap.py --project-dir /path/to/project
    python path/to/_quant_harness/bootstrap.py --project-dir .

Creates:
    {project_dir}/validation/
        claims.yaml          ← Annotated template
        regression/          ← Empty directory for regression tests
        snapshots/           ← Empty directory for freeze snapshots

Optionally installs:
    {project_dir}/.githooks/pre-commit

Detection:
    - Scans for engine entry points (Python files with 'build_' or 'run_' functions)
    - Lists CSV data sources found in data/ or output/ directories
"""

import argparse
import ast
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _find_engine_candidates(project_dir: Path) -> List[Tuple[str, str, List[str]]]:
    """Scan for potential engine entry points.

    Returns list of (file_path, function_name, [arg_names]) tuples.
    """
    candidates = []
    search_dirs = ["backtest", "engine", "src", "signals", "pipeline", "."]

    for search_dir in search_dirs:
        search_path = project_dir / search_dir
        if not search_path.exists():
            continue

        for py_file in search_path.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Heuristic: functions starting with build_, run_, compute_, generate_
                    name = node.name
                    if any(name.startswith(p) for p in ("build_", "run_", "compute_", "generate_", "main")):
                        args = [a.arg for a in node.args.args if a.arg != "self"]
                        rel_path = str(py_file.relative_to(project_dir))
                        candidates.append((rel_path, name, args))

    return candidates


def _find_csv_files(project_dir: Path) -> List[str]:
    """Find CSV files in common data directories."""
    csv_files = []
    search_dirs = ["data", "output", "vendor_output", "backtest"]

    for search_dir in search_dirs:
        search_path = project_dir / search_dir
        if not search_path.exists():
            continue
        for csv_file in search_path.rglob("*.csv"):
            if csv_file.stat().st_size < 10 * 1024 * 1024:  # Skip > 10MB
                csv_files.append(str(csv_file.relative_to(project_dir)))

    return sorted(csv_files)[:30]  # Cap at 30


def _check_git_repo(project_dir: Path) -> bool:
    """Check if project_dir is inside a git repository."""
    current = project_dir
    while current != current.parent:
        if (current / ".git").exists():
            return True
        current = current.parent
    return False


def run_bootstrap(project_dir: str, install_hook: bool = False) -> Dict:
    """Run bootstrap initialization.

    Args:
        project_dir: Path to the project root.
        install_hook: Whether to install the git pre-commit hook.

    Returns:
        Report dict with detected paths and next steps.
    """
    project_path = Path(project_dir).resolve()
    if not project_path.exists():
        raise FileNotFoundError(f"Project directory not found: {project_dir}")

    # Create validation directory structure
    validation_dir = project_path / "validation"
    validation_dir.mkdir(exist_ok=True)
    (validation_dir / "regression").mkdir(exist_ok=True)
    (validation_dir / "snapshots").mkdir(exist_ok=True)

    # Copy claims template if not already present
    claims_path = validation_dir / "claims.yaml"
    if not claims_path.exists():
        template_dir = Path(__file__).resolve().parent / "quant_harness" / "templates"
        template_path = template_dir / "claims_template.yaml"
        if template_path.exists():
            shutil.copy(template_path, claims_path)
        else:
            # Running from pip install — template is in package data
            import quant_harness
            pkg_dir = Path(quant_harness.__file__).parent
            template_path = pkg_dir / "templates" / "claims_template.yaml"
            if template_path.exists():
                shutil.copy(template_path, claims_path)
            else:
                claims_path.write_text("# Claims registry — please populate\n", encoding="utf-8")

    # Detect project structure
    engine_candidates = _find_engine_candidates(project_path)
    csv_files = _find_csv_files(project_path)
    is_git = _check_git_repo(project_path)

    # Install git hook if requested
    hook_installed = False
    if install_hook and is_git:
        githooks_dir = project_path / ".githooks"
        githooks_dir.mkdir(exist_ok=True)
        hook_template = Path(__file__).resolve().parent / "quant_harness" / "templates" / "pre_commit_hook.sh"
        hook_dest = githooks_dir / "pre-commit"
        if hook_template.exists():
            shutil.copy(hook_template, hook_dest)
            hook_dest.chmod(0o755)
            hook_installed = True

    return {
        "project_dir": str(project_path),
        "validation_dir": str(validation_dir),
        "claims_file": str(claims_path),
        "claims_existed": claims_path.stat().st_size > 100,
        "engine_candidates": engine_candidates,
        "csv_files_found": csv_files,
        "git_repo": is_git,
        "hook_installed": hook_installed,
    }


def _print_report(report: Dict):
    """Print a human-readable bootstrap report."""
    print()
    print("=" * 64)
    print("  Quant Harness — Bootstrap Complete")
    print("=" * 64)
    print(f"  Project:     {report['project_dir']}")
    print(f"  Validation:  {report['validation_dir']}")
    print(f"  Claims file: {report['claims_file']}")
    print()

    # Engine candidates
    if report["engine_candidates"]:
        print("  Detected engine candidates:")
        for fpath, fname, args in report["engine_candidates"][:5]:
            args_str = ", ".join(args) if args else "()"
            print(f"    {fpath}::{fname}({args_str})")
        print(f"    ({len(report['engine_candidates'])} total)")
    else:
        print("  No engine candidates detected.")
    print()

    # CSV files
    if report["csv_files_found"]:
        print(f"  CSV data sources: {len(report['csv_files_found'])} files detected")
        for f in report["csv_files_found"][:5]:
            print(f"    {f}")
        if len(report["csv_files_found"]) > 5:
            print(f"    ... and {len(report['csv_files_found']) - 5} more")
    else:
        print("  No CSV data sources detected.")
    print()

    # Git hook
    if report["hook_installed"]:
        print("  Git hook: installed at .githooks/pre-commit")
    elif report["git_repo"]:
        print("  Git hook: not installed (use --install-hook to install)")
    else:
        print("  Git hook: skipped (not a git repository)")
    print()

    # Next steps
    print("  Next steps:")
    print("    1. Edit validation/claims.yaml — register your core claims")
    print("    2. Set meta.engine_entry to your main engine function")
    print("    3. Run: qh-verify --claims validation/claims.yaml --all")
    print("    4. Add qh-verify to your pre-freeze checklist")
    print()


def main():
    p = argparse.ArgumentParser(
        prog="quant_harness.bootstrap",
        description="Initialize a project for Quant Harness claim verification.",
    )
    p.add_argument("--project-dir", default=".", help="Path to project root (default: current directory)")
    p.add_argument("--install-hook", action="store_true", help="Install git pre-commit hook")
    args = p.parse_args()

    try:
        report = run_bootstrap(args.project_dir, install_hook=args.install_hook)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    _print_report(report)


if __name__ == "__main__":
    main()