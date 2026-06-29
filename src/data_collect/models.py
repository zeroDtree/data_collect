from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Record:
    pk: str
    data: dict[str, str]


@dataclass(frozen=True)
class UpsertResult:
    inserted: bool
    updated: bool
