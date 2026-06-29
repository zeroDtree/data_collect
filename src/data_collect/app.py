from __future__ import annotations

import argparse
from typing import Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request

from data_collect.auth import verify_bearer_token
from data_collect.config import Settings, load_settings
from data_collect.service import IngestError, ingest_payload


def create_app(settings: Settings) -> FastAPI:
    application = FastAPI(title="data-collect", docs_url=None, redoc_url=None)

    @application.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    @application.post("/webhook")
    async def webhook(
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        if not verify_bearer_token(authorization, settings.webhook_token):
            raise HTTPException(status_code=401, detail="invalid or missing bearer token")

        try:
            payload = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=422, detail="request body must be JSON") from exc

        if not isinstance(payload, dict):
            raise HTTPException(status_code=422, detail="request body must be a JSON object")

        try:
            result = ingest_payload(
                payload,
                db_path=settings.db_path,
                export_path=settings.export_path,
                schema=settings.schema,
            )
        except IngestError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

        return {"ok": True, "inserted": result.inserted, "updated": result.updated}

    return application


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the webhook data collection server.")
    parser.add_argument("--host", help="Override DATA_COLLECT_HOST")
    parser.add_argument("--port", type=int, help="Override DATA_COLLECT_PORT")
    args = parser.parse_args(argv)

    settings = load_settings()
    host = args.host or settings.host
    port = args.port or settings.port

    uvicorn.run(create_app(settings), host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
