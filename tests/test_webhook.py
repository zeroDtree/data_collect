from __future__ import annotations

import csv
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from data_collect.app import create_app
from data_collect.config import Settings
from data_collect.schema import load_schema

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

MINIMAL_SCHEMA = {
    "primary_key": "id",
    "fields": {
        "id": {"input_key": "id", "export_header": "ID", "required": True},
        "label": {"input_key": "label", "export_header": "Label", "required": True},
    },
}

REGISTRATION_PAYLOAD = {
    "email": "user@example.com",
    "linux_username": "user01",
    "name": "Test User",
    "student_id": "20240001",
    "cohort": "2024",
}


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    return tmp_path / "data"


def write_schema(path: Path, schema: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(schema, allow_unicode=True), encoding="utf-8")
    return path


@pytest.fixture
def minimal_schema_path(data_dir: Path) -> Path:
    return write_schema(data_dir / "schema.yaml", MINIMAL_SCHEMA)


@pytest.fixture
def settings(data_dir: Path, minimal_schema_path: Path) -> Settings:
    schema = load_schema(minimal_schema_path)
    return Settings(
        webhook_token="test-secret-token",
        host="127.0.0.1",
        port=8787,
        data_dir=data_dir,
        db_path=data_dir / "records.sqlite",
        export_path=data_dir / "export.csv",
        schema_path=minimal_schema_path,
        schema=schema,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))


def auth_header(token: str = "test-secret-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_webhook_unauthorized(client: TestClient) -> None:
    response = client.post("/webhook", json={"id": "1", "label": "a"})
    assert response.status_code == 401


def test_webhook_validation_error(client: TestClient) -> None:
    response = client.post("/webhook", json={"id": "", "label": ""}, headers=auth_header())
    assert response.status_code == 422


def test_webhook_insert_and_export(client: TestClient, settings: Settings) -> None:
    response = client.post(
        "/webhook",
        json={"id": "1", "label": "first"},
        headers=auth_header(),
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True, "inserted": True, "updated": False}

    with settings.export_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows == [{"ID": "1", "Label": "first"}]


def test_webhook_update(client: TestClient, settings: Settings) -> None:
    client.post("/webhook", json={"id": "1", "label": "first"}, headers=auth_header())
    response = client.post(
        "/webhook",
        json={"id": "1", "label": "updated"},
        headers=auth_header(),
    )
    assert response.status_code == 200
    assert response.json()["updated"] is True

    with settings.export_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["Label"] == "updated"


def test_registration_example_schema_export(data_dir: Path) -> None:
    schema_path = EXAMPLES_DIR / "registration.yaml"
    schema = load_schema(schema_path)
    settings = Settings(
        webhook_token="test-secret-token",
        host="127.0.0.1",
        port=8787,
        data_dir=data_dir,
        db_path=data_dir / "records.sqlite",
        export_path=data_dir / "export.csv",
        schema_path=schema_path,
        schema=schema,
    )
    client = TestClient(create_app(settings))
    response = client.post("/webhook", json=REGISTRATION_PAYLOAD, headers=auth_header())
    assert response.status_code == 200

    with settings.export_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["邮箱"] == "user@example.com"
    assert rows[0]["linux账户名"] == "user01"


def test_registration_rejects_immutable_field_change(data_dir: Path) -> None:
    schema_path = EXAMPLES_DIR / "registration.yaml"
    schema = load_schema(schema_path)
    settings = Settings(
        webhook_token="test-secret-token",
        host="127.0.0.1",
        port=8787,
        data_dir=data_dir,
        db_path=data_dir / "records.sqlite",
        export_path=data_dir / "export.csv",
        schema_path=schema_path,
        schema=schema,
    )
    client = TestClient(create_app(settings))
    client.post("/webhook", json=REGISTRATION_PAYLOAD, headers=auth_header())
    changed = {**REGISTRATION_PAYLOAD, "linux_username": "user02"}
    response = client.post("/webhook", json=changed, headers=auth_header())
    assert response.status_code == 422
    assert "linux_username change not allowed" in response.json()["detail"]
