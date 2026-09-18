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

# Run the real Strands agent by default. Credentials come from the gitignored
# .env at the repo root (copy .env.example). Without one the agent is skipped
# and the deterministic rulebook answers, which is a safe default rather than
# an error. Set AAHAR_USE_AGENT=false to skip the model call entirely.
export AAHAR_USE_AGENT="${AAHAR_USE_AGENT:-true}"
export AAHAR_MODEL_PROVIDER="${AAHAR_MODEL_PROVIDER:-groq}"

.venv/bin/python backend/local_server.py &
API=$!
trap 'kill $API 2>/dev/null || true' EXIT

(cd frontend && npm run dev)
