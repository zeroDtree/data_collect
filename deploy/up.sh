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

usage() {
  awk '/^# @help-begin$/{f=1; next} /^# @help-end$/{f=0} f' "$0"
  printf '%s\n' '#' 'Options:' '#'
  awk '/^# @help-options-begin$/{f=1; next} /^# @help-options-end$/{f=0} f' "$0"
  exit 0
}

for arg in "$@"; do
  case "$arg" in
    -h|--help) usage ;;
    *) die "Unexpected argument: $arg (see --help)" ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ROOT}/.env"
SECRETS_FILE="${ROOT}/.env.secrets"

if [[ ! -f "${ENV_FILE}" ]]; then
  if [[ -f "${ROOT}/.env.example" ]]; then
    cp "${ROOT}/.env.example" "${ENV_FILE}"
    log "Created ${ENV_FILE} from .env.example (edit before production use)"
  else
    die "Missing ${ENV_FILE}"
  fi
fi

if [[ ! -f "${SECRETS_FILE}" ]]; then
  die "Missing ${SECRETS_FILE} (copy from .env.secrets.example)"
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
# shellcheck disable=SC1090
source "${SECRETS_FILE}"
set +a

mode="${DATA_COLLECT_TRAEFIK_MODE:-}"
case "${mode}" in
  external|shared|standalone) ;;
  *)
    die "DATA_COLLECT_TRAEFIK_MODE must be external, shared, or standalone (got: ${mode:-empty})"
    ;;
esac

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

OVERLAY="${ROOT}/compose.${mode}.yaml"
[[ -f "${OVERLAY}" ]] || die "Missing compose overlay: ${OVERLAY}"

log "Traefik mode: ${mode}"
cd "${ROOT}"
docker compose \
  -f compose.yaml \
  -f "compose.${mode}.yaml" \
  --env-file "${ENV_FILE}" \
  --env-file "${SECRETS_FILE}" \
  up -d --build

log "Done. Verify: curl -Ik https://${PUBLIC_HOST}/health"
