#!/bin/sh
set -eu
base_url="${BIOVOLT_BASE_URL:-http://localhost}"
curl --fail --silent "$base_url/healthz" >/dev/null
curl --fail --silent "$base_url/api/health" >/dev/null
echo "BioVolt stack is healthy"
