#!/usr/bin/env bash
set -euo pipefail

mkdir -p /data
chown -R datacollect:datacollect /data
exec gosu datacollect "$@"
