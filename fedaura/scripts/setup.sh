#!/usr/bin/env bash
set -euo pipefail
FEDAURA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$FEDAURA_DIR"
command -v uv >/dev/null
command -v node >/dev/null
command -v podman >/dev/null
if [[ ! -x .venv/bin/python ]]; then uv venv --python 3.13 .venv; fi
if [[ -f requirements.lock ]]; then
  uv pip install --python .venv/bin/python -r requirements.lock
else
  uv pip install --python .venv/bin/python -e app/packages/api -e app/packages/db podman-compose websockets
fi
npm install --prefix .tools pnpm@9.15.9 --ignore-scripts --no-audit --no-fund
cd app
HUSKY=0 ../.tools/node_modules/.bin/pnpm install --frozen-lockfile --ignore-scripts
cd ..
if [[ ! -f .env ]]; then cp .env.example .env; fi
mkdir -p runtime
ollama pull qwen3.5:9b
printf '\nSetup complete. Run: bash fedaura/demo.sh up assistant\n'
