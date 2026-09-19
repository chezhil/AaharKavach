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
#
# Deliberately NOT exported here: local_server.py's _load_dotenv() reads .env
# with os.environ.setdefault(), which is a no-op once a shell var is already
# set. Exporting a default in this shell — before Python ever sees .env —
# used to silently override .env's own AAHAR_MODEL_PROVIDER (e.g. "bedrock")
# with "groq" on every run from a fresh shell, with no error: the primary
# provider became "groq" while AAHAR_BEDROCK_MODEL still held a Bedrock model
# id, so the build_model() "different vendor, blank the id" guard never
# tripped and Groq got asked for a Bedrock model id it doesn't have.
# providers.py's own DEFAULT_PROVIDER ("bedrock") and .env cover this instead.

.venv/bin/python backend/local_server.py &
API=$!
trap 'kill $API 2>/dev/null || true' EXIT

(cd frontend && npm run dev)
