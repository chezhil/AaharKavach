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

# Run the real Strands agent by default. The Groq key comes from the gitignored
# .env at the repo root (copy .env.example). Without one the agent is skipped
# and the deterministic rulebook answers, which is a safe default rather than
# an error. Set AAHAR_USE_AGENT=false to skip the model call entirely.
#
# Deliberately NOT exported here: local_server.py's _load_dotenv() reads .env
# with os.environ.setdefault(), which is a no-op once a shell var is already
# set — so exporting a default in this shell would silently override .env's own
# value on every run from a fresh shell, with no error. providers.py's
# DEFAULT_PROVIDER ("groq") and .env cover this instead.

.venv/bin/python backend/local_server.py &
API=$!
trap 'kill $API 2>/dev/null || true' EXIT

(cd frontend && npm run dev)
