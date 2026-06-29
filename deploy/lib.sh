# Shared helpers for data_collect deploy scripts. Source from deploy/up.sh or deploy/down.sh.

dc_root() {
  local lib_dir
  lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  ROOT="$(cd "${lib_dir}/.." && pwd)"
  ENV_FILE="${ROOT}/.env"
  SECRETS_FILE="${ROOT}/.env.secrets"
}

dc_usage() {
  local script="$1"
  awk '/^# @help-begin$/{f=1; next} /^# @help-end$/{f=0} f' "${script}"
  printf '%s\n' '#' 'Options:' '#'
  awk '/^# @help-options-begin$/{f=1; next} /^# @help-options-end$/{f=0} f' "${script}"
  exit 0
}

dc_load_env() {
  dc_root
  [[ -f "${ENV_FILE}" ]] || die "Missing ${ENV_FILE}"
  [[ -f "${SECRETS_FILE}" ]] || die "Missing ${SECRETS_FILE} (copy from .env.secrets.example)"

  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  # shellcheck disable=SC1090
  source "${SECRETS_FILE}"
  set +a
}

dc_mode() {
  mode="${DATA_COLLECT_TRAEFIK_MODE:-}"
  case "${mode}" in
    external|shared|standalone) ;;
    *)
      die "DATA_COLLECT_TRAEFIK_MODE must be external, shared, or standalone (got: ${mode:-empty})"
      ;;
  esac

  overlay="${ROOT}/compose.${mode}.yaml"
  [[ -f "${overlay}" ]] || die "Missing compose overlay: ${overlay}"
}

dc_compose() {
  dc_mode
  cd "${ROOT}"
  docker compose \
    -f compose.yaml \
    -f "compose.${mode}.yaml" \
    --env-file "${ENV_FILE}" \
    --env-file "${SECRETS_FILE}" \
    "$@"
}
