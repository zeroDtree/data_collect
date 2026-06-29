# data_collect

Generic webhook service: accept JSON payloads, validate against a YAML schema, store in SQLite, and export CSV.

Self-contained — this directory can be copied or split into its own repository.

## Quick start

```bash
cp .env.example .env
cp .env.secrets.example .env.secrets
# Edit schema.yaml or: cp examples/registration.yaml schema.yaml
uv sync
uv run data-collect
```

Test:

```bash
curl -X POST "http://127.0.0.1:8787/webhook" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"id":"1"}'
```

## Schema

Edit [`schema.yaml`](schema.yaml). See [`examples/registration.yaml`](examples/registration.yaml) for a multi-field example.

| Field property | Purpose |
|----------------|---------|
| `input_key` | JSON key in webhook body |
| `export_header` | CSV column name |
| `required` | Reject empty values |
| `unique` | Reject duplicates across records |
| `immutable_on_update` | Reject changes on upsert |
| `normalize` | `strip`, `lowercase`, or `none` |
| `validate` | `email`, `linux_username`, or `none` |

`primary_key` must name a required field used for upsert.

## Configuration

| Variable | File | Description |
|----------|------|-------------|
| `WEBHOOK_TOKEN` | `.env.secrets` | Bearer token for `POST /webhook` |
| `DATA_COLLECT_SCHEMA` | env | Schema path (default `./schema.yaml`) |
| `DATA_COLLECT_DATA_DIR` | env | Data directory (default `./data`) |
| `DATA_COLLECT_TRAEFIK_MODE` | `.env` | `external`, `shared`, or `standalone` |
| `PUBLIC_HOST` | `.env` | Hostname for Traefik routing |

Runtime outputs under `./data/`:

| File | Purpose |
|------|---------|
| `records.sqlite` | Stored records (JSON per row) |
| `export.csv` | Full CSV export |

## Docker deploy

```bash
cp .env.example .env
cp .env.secrets.example .env.secrets
# Edit .env (mode, PUBLIC_HOST, TRAEFIK_*) and .env.secrets (WEBHOOK_TOKEN)
./deploy/up.sh
curl -Ik "https://${PUBLIC_HOST}/health"

./deploy/down.sh            # stop containers, keep ./data/
./deploy/down.sh --volumes  # also remove named volumes (e.g. standalone ACME)
```

### Traefik modes

| Mode | When to use |
|------|-------------|
| `external` | Edge Traefik with custom entrypoint / cert resolver |
| `shared` | Join an existing Docker network (fixed `websecure` + `letsencrypt`) |
| `standalone` | This compose stack runs its own Traefik on 80/443 |

Set `TRAEFIK_DOCKER_NETWORK` for `external` and `shared`. Set `ACME_EMAIL` for `standalone`.

Port `8787` is not published publicly; Traefik routes HTTPS to the container.

## API

| Route | Auth | Description |
|-------|------|-------------|
| `GET /health` | no | Liveness probe |
| `POST /webhook` | Bearer | Ingest one record |

Success: `{"ok": true, "inserted": bool, "updated": bool}`

## Tests

```bash
uv run pytest
uv run ruff check && uv run ty check
```

## Examples

See [`examples/README.md`](examples/README.md) for the registration schema and optional downstream integrations.
