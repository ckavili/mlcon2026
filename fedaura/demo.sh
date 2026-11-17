#!/usr/bin/env bash
set -euo pipefail
FEDAURA_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ "${1:-}" == setup ]]; then
  exec bash "$FEDAURA_DIR/scripts/setup.sh"
fi
if [[ ! -x "$FEDAURA_DIR/.venv/bin/python" ]]; then
  echo 'Run bash fedaura/demo.sh setup first.' >&2
  exit 1
fi
exec "$FEDAURA_DIR/.venv/bin/python" "$FEDAURA_DIR/scripts/demo.py" "$@"
