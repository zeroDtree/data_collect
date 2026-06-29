from __future__ import annotations

import re
from typing import Any

from data_collect.schema import FieldSpec, Schema

LINUX_USERNAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _normalize_value(value: str, spec: FieldSpec) -> str:
    if spec.normalize == "lowercase":
        return value.lower()
    if spec.normalize == "strip":
        return value.strip()
    return value


def _validate_value(value: str, spec: FieldSpec) -> str | None:
    if spec.validate == "email":
        if not value:
            return f"{spec.key} is required"
        if not EMAIL_PATTERN.match(value):
            return f"{spec.key} format is invalid"
        return None
    if spec.validate == "linux_username":
        if not value:
            return f"{spec.key} is required"
        if not LINUX_USERNAME_PATTERN.match(value):
            return (
                f"{spec.key} must start with a letter or underscore and contain only "
                "lowercase letters, digits, _, - (max 32 chars)"
            )
        return None
    if spec.required and not value:
        return f"{spec.key} is required"
    return None


def parse_payload(payload: dict[str, Any], schema: Schema) -> dict[str, str]:
    record: dict[str, str] = {}
    errors: list[str] = []

    for spec in schema.fields:
        raw = payload.get(spec.input_key)
        if raw is None:
            value = ""
        else:
            value = str(raw).strip() if isinstance(raw, str) else str(raw).strip()

        value = _normalize_value(value, spec)
        if err := _validate_value(value, spec):
            errors.append(err)
            continue
        record[spec.key] = value

    if errors:
        raise ValidationError(errors[0])

    return record
