"""ClaimLoader — parse claims.yaml and validate against schema."""

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.schema_validator import validate_or_raise, SchemaError

# Lazy-loaded schema
_SCHEMA_CACHE: Optional[Dict[str, Any]] = None


def _get_schema() -> Dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        schema_path = Path(__file__).parent.parent / "schemas" / "claims_schema.yaml"
        with open(schema_path, "r", encoding="utf-8") as f:
            _SCHEMA_CACHE = yaml.safe_load(f)
    return _SCHEMA_CACHE


@dataclass
class Claim:
    """A single claim from the registry."""
    id: str
    chapter: str
    type: str
    text: str
    expected: Any
    severity: str
    source: Dict[str, Any] = field(default_factory=dict)
    tolerance: Dict[str, Any] = field(default_factory=dict)
    note: Optional[str] = None
    status: str = "active"
    needs_review: bool = False

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "Claim":
        return cls(
            id=raw["id"],
            chapter=raw["chapter"],
            type=raw["type"],
            text=raw["text"],
            expected=raw["expected"],
            severity=raw["severity"],
            source=raw.get("source", {}),
            tolerance=raw.get("tolerance", {}),
            note=raw.get("note"),
            status=raw.get("status", "active"),
            needs_review=raw.get("needs_review", False),
        )


@dataclass
class ClaimsRegistry:
    """Parsed and validated claims registry."""
    meta: Dict[str, Any]
    claims: List[Claim]
    file_path: Optional[Path] = None

    @property
    def project_root(self) -> Path:
        root = self.meta.get("project_root", ".")
        if self.file_path and not os.path.isabs(root):
            return (self.file_path.parent / root).resolve()
        return Path(root).resolve()

    def filter(
        self,
        chapter: Optional[str] = None,
        severity: Optional[str] = None,
        claim_type: Optional[str] = None,
        ids: Optional[List[str]] = None,
    ) -> List[Claim]:
        """Filter claims by chapter, severity, type, or explicit IDs."""
        result = self.claims
        if chapter:
            result = [c for c in result if c.chapter == chapter]
        if severity:
            result = [c for c in result if c.severity == severity]
        if claim_type:
            result = [c for c in result if c.type == claim_type]
        if ids:
            id_set = set(ids)
            result = [c for c in result if c.id in id_set]
        return result

    @property
    def critical_claims(self) -> List[Claim]:
        return self.filter(severity="critical")

    @property
    def chapter_labels(self) -> List[str]:
        return sorted(set(c.chapter for c in self.claims))


def load_claims(claims_path: str) -> ClaimsRegistry:
    """Load and validate a claims.yaml file.

    Args:
        claims_path: Path to claims.yaml file.

    Returns:
        ClaimsRegistry with parsed claims and metadata.

    Raises:
        FileNotFoundError: File doesn't exist.
        SchemaError: Validation failed.
    """
    file_path = Path(claims_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"Claims file not found: {claims_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raise SchemaError(["Claims file is empty"])

    # Validate against schema (non-fatal warnings for unknown fields)
    try:
        validate_or_raise(raw, _get_schema())
    except SchemaError as e:
        # Re-raise with file context
        raise SchemaError([f"In {claims_path}: {err}" for err in e.errors]) from None

    claims = [Claim.from_dict(c) for c in raw.get("claims", [])]
    return ClaimsRegistry(
        meta=raw.get("meta", {}),
        claims=claims,
        file_path=file_path,
    )
