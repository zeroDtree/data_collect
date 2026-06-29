#!/usr/bin/env bash

# @help-begin
# Build and start data-collect with Docker Compose.
#
# Usage:
#   ./deploy/up.sh
#
# Requires .env and .env.secrets in the data_collect directory root.
# Set DATA_COLLECT_TRAEFIK_MODE to external, shared, or standalone.
# @help-end

# @help-options-begin
#   -h, --help              show help
# @help-options-end

set -euo pipefail

log() { printf '==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib.sh"

for arg in "$@"; do
  case "$arg" in
    -h|--help) dc_usage "$0" ;;
    *) die "Unexpected argument: $arg (see --help)" ;;
  esac
done

dc_root

if [[ ! -f "${ENV_FILE}" ]]; then
  if [[ -f "${ROOT}/.env.example" ]]; then
    cp "${ROOT}/.env.example" "${ENV_FILE}"
    log "Created ${ENV_FILE} from .env.example (edit before production use)"
  else
    die "Missing ${ENV_FILE}"
  fi
fi

dc_load_env
dc_mode

if [[ -z "${PUBLIC_HOST:-}" ]]; then
  die "PUBLIC_HOST is required in .env"
fi

if [[ -z "${WEBHOOK_TOKEN:-}" ]]; then
  die "WEBHOOK_TOKEN is required in .env.secrets"
fi

case "${mode}" in
  external|shared)
    if [[ -z "${TRAEFIK_DOCKER_NETWORK:-}" ]]; then
      die "TRAEFIK_DOCKER_NETWORK is required for mode=${mode}"
    fi
    docker network inspect "${TRAEFIK_DOCKER_NETWORK}" >/dev/null 2>&1 \
      || die "Docker network not found: ${TRAEFIK_DOCKER_NETWORK}"
    ;;
  standalone)
    if [[ -z "${ACME_EMAIL:-}" ]]; then
      die "ACME_EMAIL is required for mode=standalone"
    fi
    ;;
esac

log "Traefik mode: ${mode}"
dc_compose up -d --build

log "Done. Verify: curl -Ik https://${PUBLIC_HOST}/health"
