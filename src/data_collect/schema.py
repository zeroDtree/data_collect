from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

NORMALIZE_VALUES = frozenset({"none", "strip", "lowercase"})
VALIDATE_VALUES = frozenset({"none", "email", "linux_username"})


@dataclass(frozen=True)
class FieldSpec:
    key: str
    input_key: str
    export_header: str
    required: bool
    unique: bool
    immutable_on_update: bool
    normalize: str
    validate: str


@dataclass(frozen=True)
class Schema:
    primary_key: str
    fields: tuple[FieldSpec, ...]

    def field(self, key: str) -> FieldSpec | None:
        for spec in self.fields:
            if spec.key == key:
                return spec
        return None

    def primary_field(self) -> FieldSpec:
        spec = self.field(self.primary_key)
        if spec is None:
            msg = f"primary_key {self.primary_key!r} is not defined in fields"
            raise ValueError(msg)
        return spec


def load_schema(path: Path) -> Schema:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        msg = f"schema must be a YAML mapping: {path}"
        raise ValueError(msg)

    primary_key = data.get("primary_key")
    if not isinstance(primary_key, str) or not primary_key.strip():
        msg = f"schema primary_key must be a non-empty string: {path}"
        raise ValueError(msg)
    primary_key = primary_key.strip()

    raw_fields = data.get("fields")
    if not isinstance(raw_fields, dict) or not raw_fields:
        msg = f"schema fields must be a non-empty mapping: {path}"
        raise ValueError(msg)

    fields: list[FieldSpec] = []
    seen_keys: set[str] = set()
    for key, raw in raw_fields.items():
        if not isinstance(key, str) or not key.strip():
            msg = f"invalid field key in schema: {key!r}"
            raise ValueError(msg)
        field_key = key.strip()
        if field_key in seen_keys:
            msg = f"duplicate field key in schema: {field_key!r}"
            raise ValueError(msg)
        seen_keys.add(field_key)

        if not isinstance(raw, dict):
            msg = f"field {field_key!r} must be a mapping"
            raise ValueError(msg)

        input_key = raw.get("input_key", field_key)
        if not isinstance(input_key, str) or not input_key.strip():
            msg = f"fields.{field_key}.input_key must be a non-empty string"
            raise ValueError(msg)
        input_key = input_key.strip()

        export_header = raw.get("export_header", field_key)
        if not isinstance(export_header, str) or not export_header.strip():
            msg = f"fields.{field_key}.export_header must be a non-empty string"
            raise ValueError(msg)
        export_header = export_header.strip()

        normalize = raw.get("normalize", "strip")
        if not isinstance(normalize, str) or normalize not in NORMALIZE_VALUES:
            msg = f"fields.{field_key}.normalize must be one of {sorted(NORMALIZE_VALUES)}"
            raise ValueError(msg)

        validate = raw.get("validate", "none")
        if not isinstance(validate, str) or validate not in VALIDATE_VALUES:
            msg = f"fields.{field_key}.validate must be one of {sorted(VALIDATE_VALUES)}"
            raise ValueError(msg)

        fields.append(
            FieldSpec(
                key=field_key,
                input_key=input_key,
                export_header=export_header,
                required=bool(raw.get("required", False)),
                unique=bool(raw.get("unique", False)),
                immutable_on_update=bool(raw.get("immutable_on_update", False)),
                normalize=normalize,
                validate=validate,
            )
        )

    if primary_key not in seen_keys:
        msg = f"primary_key {primary_key!r} must exist in fields"
        raise ValueError(msg)

    primary = next(f for f in fields if f.key == primary_key)
    if not primary.required:
        msg = f"primary_key field {primary_key!r} must be required: true"
        raise ValueError(msg)

    return Schema(primary_key=primary_key, fields=tuple(fields))
