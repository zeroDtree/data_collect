FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build

ENV UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY schema.yaml ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable
RUN /app/.venv/bin/python -c "import data_collect; import data_collect.app"
RUN /app/.venv/bin/data-collect --help >/dev/null

FROM python:3.12-slim-bookworm

WORKDIR /app

RUN groupadd -r datacollect \
    && useradd -r -g datacollect -d /app datacollect \
    && mkdir -p /data \
    && chown datacollect:datacollect /data

COPY --from=build --chown=datacollect:datacollect /app/.venv /app/.venv
COPY --from=build --chown=datacollect:datacollect /app/schema.yaml /app/schema.yaml

ENV PATH="/app/.venv/bin:${PATH}"
ENV DATA_COLLECT_SCHEMA=/app/schema.yaml

USER datacollect

EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/health')" || exit 1

CMD ["data-collect", "--host", "0.0.0.0"]
