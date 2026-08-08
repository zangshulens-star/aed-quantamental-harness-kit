"""DataResolver — resolve claim values from CSV, engine, or subprocess."""

import importlib
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd


class ResolutionError(Exception):
    """Raised when a claim's value cannot be resolved."""

    def __init__(self, claim_id: str, source: Dict[str, Any], detail: str):
        self.claim_id = claim_id
        self.source = source
        self.detail = detail
        super().__init__(f"[{claim_id}] {detail}")


def _resolve_from_csv(
    source: Dict[str, Any],
    project_root: Path,
    claim_id: str,
) -> Any:
    """Resolve value by reading a CSV file."""
    csv_rel = source.get("csv")
    if not csv_rel:
        raise ResolutionError(claim_id, source, "source.csv is required for from_csv method")

    csv_path = project_root / csv_rel
    if not csv_path.exists():
        raise ResolutionError(claim_id, source, f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=True)

    filter_q = source.get("filter")
    if filter_q:
        try:
            df = df.query(filter_q)
        except Exception as e:
            raise ResolutionError(claim_id, source, f"Filter query failed: {e}") from None

    column = source.get("column")
    if not column:
        raise ResolutionError(claim_id, source, "source.column is required for from_csv method")

    if column not in df.columns:
        raise ResolutionError(claim_id, source, f"Column '{column}' not found in CSV. Available: {list(df.columns)}")

    return df[column]


def _resolve_from_engine(
    source: Dict[str, Any],
    engine_entry: str,
    project_root: Path,
    claim_id: str,
) -> Any:
    """Resolve value by running an engine function via importlib."""
    if not engine_entry:
        raise ResolutionError(claim_id, source, "meta.engine_entry is required for recompute_from_engine method")

    if "::" not in engine_entry:
        raise ResolutionError(claim_id, source, f"engine_entry must be 'path/to/file.py::function_name', got: {engine_entry}")

    module_path, func_name = engine_entry.split("::", 1)
    full_path = project_root / module_path

    if not full_path.exists():
        raise ResolutionError(claim_id, source, f"Engine module not found: {full_path}")

    # Add project root to sys.path for imports
    sys.path.insert(0, str(project_root))
    try:
        spec = importlib.util.spec_from_file_location("_qh_engine", str(full_path))
        if spec is None or spec.loader is None:
            raise ResolutionError(claim_id, source, f"Cannot load module spec for {full_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        func = getattr(module, func_name, None)
        if func is None:
            raise ResolutionError(claim_id, source, f"Function '{func_name}' not found in {module_path}")

        engine_args = source.get("engine_args", {})
        result = func(**engine_args)

        column = source.get("column")
        if column and isinstance(result, pd.DataFrame):
            if column not in result.columns:
                raise ResolutionError(claim_id, source, f"Column '{column}' not in engine output. Available: {list(result.columns)}")
            return result[column]

        return result
    except ResolutionError:
        raise
    except Exception as e:
        raise ResolutionError(claim_id, source, f"Engine execution failed: {e}") from None
    finally:
        if str(project_root) in sys.path:
            sys.path.remove(str(project_root))


def _resolve_from_custom_python(
    source: Dict[str, Any],
    project_root: Path,
    claim_id: str,
) -> Any:
    """Resolve value by running a custom Python script via subprocess."""
    script_rel = source.get("script")
    if not script_rel:
        raise ResolutionError(claim_id, source, "source.script is required for custom_python method")

    script_path = project_root / script_rel
    if not script_path.exists():
        raise ResolutionError(claim_id, source, f"Script not found: {script_path}")

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--output", tmp_path],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(project_root),
        )
        if result.returncode != 0:
            raise ResolutionError(claim_id, source, f"Script failed (exit {result.returncode}): {result.stderr[:500]}")

        df = pd.read_csv(tmp_path)
        column = source.get("column")
        if column:
            if column not in df.columns:
                raise ResolutionError(claim_id, source, f"Column '{column}' not in script output. Available: {list(df.columns)}")
            return df[column]
        return df
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def resolve_claim(
    claim_id: str,
    source: Dict[str, Any],
    engine_entry: str,
    project_root: Path,
) -> pd.Series:
    """Resolve the actual value for a claim.

    Returns a pandas Series (numeric values for verification).
    """
    method = source.get("method", "from_csv")

    if method == "from_csv":
        return _resolve_from_csv(source, project_root, claim_id)
    elif method == "recompute_from_engine":
        return _resolve_from_engine(source, engine_entry, project_root, claim_id)
    elif method == "custom_python":
        return _resolve_from_custom_python(source, project_root, claim_id)
    else:
        raise ResolutionError(claim_id, source, f"Unknown resolution method: {method}")
