"""Lightweight YAML/JSON schema validator — no jsonschema dependency."""

from typing import Any, Dict, List, Optional, Tuple


class SchemaError(Exception):
    """Raised when a document fails schema validation."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


def _validate_type(value: Any, expected: str, path: str) -> List[str]:
    """Validate a value against an expected JSON type name."""
    type_map = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    if expected == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return [f"{path}: expected number, got {type(value).__name__}"]
        return []
    py_type = type_map.get(expected)
    if py_type is None:
        return []
    if not isinstance(value, py_type):
        return [f"{path}: expected {expected}, got {type(value).__name__}"]
    return []


def validate_schema(instance: Dict[str, Any], schema: Dict[str, Any], path: str = "$") -> List[str]:
    """Validate an instance against a simplified JSON Schema subset.

    Supports: type, required, properties, enum, items, additionalProperties.
    """
    errors: List[str] = []

    schema_type = schema.get("type")
    if schema_type:
        errors.extend(_validate_type(instance, schema_type, path))

    if schema_type == "object" and isinstance(instance, dict):
        required: List[str] = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required field '{key}'")

        properties = schema.get("properties", {})
        for key, prop_schema in properties.items():
            if key in instance:
                errors.extend(validate_schema(instance[key], prop_schema, f"{path}.{key}"))

        if not schema.get("additionalProperties", True):
            allowed = set(properties.keys())
            for key in instance:
                if key not in allowed:
                    errors.append(f"{path}: unexpected field '{key}'")

    elif schema_type == "array" and isinstance(instance, list):
        item_schema = schema.get("items", {})
        for i, item in enumerate(instance):
            errors.extend(validate_schema(item, item_schema, f"{path}[{i}]"))

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value '{instance}' not in allowed values: {schema['enum']}")

    return errors


def validate_or_raise(instance: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validate and raise SchemaError on failure."""
    errors = validate_schema(instance, schema)
    if errors:
        raise SchemaError(errors)
