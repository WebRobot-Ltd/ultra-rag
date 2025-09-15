#!/usr/bin/env bash
set -euo pipefail

# Usage: ./run_local.sh <UPSTREAM_URL> <PORT>
# Example: ./run_local.sh http://127.0.0.1:8002/mcp 8100

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <UPSTREAM_URL> <PORT>"
  exit 1
fi

UPSTREAM_URL="$1"
PORT="$2"

export UPSTREAM_URL

echo "Starting auth proxy -> $UPSTREAM_URL on :$PORT"
PYTHONPATH="$(dirname "$(cd "$(dirname "$0")/../.." && pwd)")/src:$(dirname "$(cd "$(dirname "$0")/../.." && pwd)"" \
  uvicorn servers.auth_proxy.app:app --host 0.0.0.0 --port "$PORT"


