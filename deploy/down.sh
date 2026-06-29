#!/usr/bin/env bash

# @help-begin
# Stop data-collect Docker Compose stack.
#
# Usage:
#   ./deploy/down.sh [-v|--volumes]
#
# Requires .env and .env.secrets in the data_collect directory root.
# @help-end

# @help-options-begin
#   -v, --volumes   remove named volumes (standalone Traefik ACME volume)
#   -h, --help      show help
# @help-options-end

set -euo pipefail

log() { printf '==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib.sh"

remove_volumes=0

for arg in "$@"; do
  case "$arg" in
    -h|--help) dc_usage "$0" ;;
    -v|--volumes) remove_volumes=1 ;;
    *) die "Unexpected argument: $arg (see --help)" ;;
  esac
done

dc_load_env
dc_mode

log "Traefik mode: ${mode}"
if [[ "${remove_volumes}" -eq 1 ]]; then
  dc_compose down -v
  log "Done. Named volumes removed. ./data/ on host is unchanged."
else
  dc_compose down
  log "Done. ./data/ on host is unchanged."
fi
