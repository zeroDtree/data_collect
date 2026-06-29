from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from data_collect.schema import Schema, load_schema

_PACKAGE_DIR = Path(__file__).resolve().parent
DATA_COLLECT_ROOT = _PACKAGE_DIR.parent.parent
DEFAULT_SCHEMA = DATA_COLLECT_ROOT / "schema.yaml"
DEFAULT_DATA_DIR = DATA_COLLECT_ROOT / "data"


def load_local_env() -> None:
    load_dotenv(DATA_COLLECT_ROOT / ".env")
    load_dotenv(DATA_COLLECT_ROOT / ".env.secrets")


@dataclass(frozen=True)
class Settings:
    webhook_token: str
    host: str
    port: int
    data_dir: Path
    db_path: Path
    export_path: Path
    schema_path: Path
    schema: Schema


def load_settings() -> Settings:
    load_local_env()

    token = os.environ.get("WEBHOOK_TOKEN", "").strip()
    if not token:
        msg = "WEBHOOK_TOKEN is required"
        raise RuntimeError(msg)

    host = os.environ.get("DATA_COLLECT_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port_raw = os.environ.get("DATA_COLLECT_PORT", "8787").strip()
    try:
        port = int(port_raw)
    except ValueError:
        port = 8787

    data_dir = Path(os.environ.get("DATA_COLLECT_DATA_DIR", str(DEFAULT_DATA_DIR))).expanduser()
    db_path = data_dir / "records.sqlite"
    export_path = data_dir / "export.csv"
    schema_path = Path(os.environ.get("DATA_COLLECT_SCHEMA", str(DEFAULT_SCHEMA))).expanduser()
    schema = load_schema(schema_path)

    return Settings(
        webhook_token=token,
        host=host,
        port=port,
        data_dir=data_dir,
        db_path=db_path,
        export_path=export_path,
        schema_path=schema_path,
        schema=schema,
    )
