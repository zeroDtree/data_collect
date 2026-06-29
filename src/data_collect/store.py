from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from data_collect.models import Record, UpsertResult
from data_collect.schema import Schema

_SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    pk TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def upsert(self, data: dict[str, str], schema: Schema) -> UpsertResult:
        pk = data[schema.primary_key]
        existing = self._get_by_pk(pk)
        now = utc_now_iso()

        if existing is None:
            self._check_unique(data, schema, exclude_pk=None)
            self._conn.execute(
                "INSERT INTO records (pk, data, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (pk, json.dumps(data, ensure_ascii=False), now, now),
            )
            self._conn.commit()
            return UpsertResult(inserted=True, updated=False)

        existing_data = json.loads(existing["data"])
        for spec in schema.fields:
            if not spec.immutable_on_update:
                continue
            old = existing_data.get(spec.key, "")
            new = data.get(spec.key, "")
            if old != new:
                msg = (
                    f"{spec.key} change not allowed for {schema.primary_key}={pk!r}: "
                    f"{old!r} -> {new!r}"
                )
                raise ValueError(msg)

        self._check_unique(data, schema, exclude_pk=pk)
        self._conn.execute(
            "UPDATE records SET data = ?, updated_at = ? WHERE pk = ?",
            (json.dumps(data, ensure_ascii=False), now, pk),
        )
        self._conn.commit()
        return UpsertResult(inserted=False, updated=True)

    def list_all(self, schema: Schema) -> list[Record]:
        cur = self._conn.execute("SELECT * FROM records ORDER BY pk")
        return [self._row_to_record(row) for row in cur.fetchall()]

    def _get_by_pk(self, pk: str) -> sqlite3.Row | None:
        cur = self._conn.execute("SELECT * FROM records WHERE pk = ?", (pk,))
        return cur.fetchone()

    def _check_unique(
        self,
        data: dict[str, str],
        schema: Schema,
        *,
        exclude_pk: str | None,
    ) -> None:
        unique_fields = [spec for spec in schema.fields if spec.unique]
        if not unique_fields:
            return

        for row in self._conn.execute("SELECT pk, data FROM records"):
            if exclude_pk is not None and row["pk"] == exclude_pk:
                continue
            existing = json.loads(row["data"])
            for spec in unique_fields:
                new_val = data.get(spec.key, "")
                old_val = existing.get(spec.key, "")
                if new_val and new_val == old_val:
                    msg = f"duplicate {spec.key}: {new_val!r}"
                    raise ValueError(msg)

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> Record:
        return Record(pk=row["pk"], data=json.loads(row["data"]))
