#!/bin/sh
set -eu
mkdir -p "${BIOVOLT_EXPORT_DIR:-/data/exports}"
exec "$@"
