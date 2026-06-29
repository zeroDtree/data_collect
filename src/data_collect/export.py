from __future__ import annotations

import csv
from pathlib import Path

from data_collect.models import Record
from data_collect.schema import Schema


def write_export(
    *,
    export_path: Path,
    schema: Schema,
    records: list[Record],
) -> None:
    export_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [spec.export_header for spec in schema.fields]
    rows = [
        {spec.export_header: record.data.get(spec.key, "") for spec in schema.fields}
        for record in records
    ]
    with export_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
