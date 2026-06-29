from __future__ import annotations

from pathlib import Path
from typing import Any

from data_collect.export import write_export
from data_collect.models import UpsertResult
from data_collect.schema import Schema
from data_collect.store import Store
from data_collect.validate import ValidationError, parse_payload


class IngestError(Exception):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def ingest_payload(
    payload: dict[str, Any],
    *,
    db_path: Path,
    export_path: Path,
    schema: Schema,
) -> UpsertResult:
    try:
        data = parse_payload(payload, schema)
    except ValidationError as exc:
        raise IngestError(exc.message, status_code=422) from exc

    with Store(db_path) as store:
        try:
            result = store.upsert(data, schema)
        except ValueError as exc:
            raise IngestError(str(exc), status_code=422) from exc
        write_export(
            export_path=export_path,
            schema=schema,
            records=store.list_all(schema),
        )
    return result
