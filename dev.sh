#!/usr/bin/env bash
# Start the API and the web app together. Ctrl-C stops both.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Creating .venv and installing Python dependencies…"
  python3 -m venv .venv
  .venv/bin/pip install -q -r data/requirements.txt -r backend/src/requirements.txt
fi

if [ ! -d frontend/node_modules ]; then
  echo "Installing frontend dependencies…"
  (cd frontend && npm install)
fi

.venv/bin/python backend/local_server.py &
API=$!
trap 'kill $API 2>/dev/null || true' EXIT

(cd frontend && npm run dev)
