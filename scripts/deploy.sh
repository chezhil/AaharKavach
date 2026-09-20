#!/usr/bin/env bash
# Deploy the backend to AWS.
#
#   ./scripts/deploy.sh
#
# Reads GROQ_API_KEY from the gitignored .env and reuses the JWT signing
# secret already on the deployed stack, so a redeploy does not silently reset
# either one. Passing no parameters to `sam deploy` resets them to the
# template defaults — which would put "super_secret_dev_key" back in place and
# invalidate every token already issued.
set -euo pipefail
cd "$(dirname "$0")/.."

STACK="${AAHAR_STACK:-aaharkavach}"
REGION="${AWS_REGION:-us-east-1}"

[ -f .env ] || { echo "No .env — copy .env.example and add GROQ_API_KEY."; exit 1; }
GROQ="$(grep -E '^GROQ_API_KEY=' .env | cut -d= -f2- || true)"
[ -n "$GROQ" ] || echo "warning: GROQ_API_KEY is empty — the deployed agent will fall back to the rulebook."

# Reuse the secret the stack already has; generate one on a first deploy.
JWT="$(aws lambda get-function-configuration \
  --function-name "$(aws lambda list-functions --region "$REGION" \
      --query "Functions[?starts_with(FunctionName, '${STACK}-ProfilesFunction')].FunctionName | [0]" \
      --output text 2>/dev/null)" \
  --region "$REGION" --query 'Environment.Variables.JWT_SECRET' --output text 2>/dev/null || true)"
if [ -z "$JWT" ] || [ "$JWT" = "None" ] || [ "$JWT" = "super_secret_dev_key" ]; then
  JWT="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
  echo "Generated a new JWT signing secret (previous tokens, if any, stop working)."
fi

# The repo venv first: it has the deps check_lambda_package.py imports.
# `python` is not on PATH on a stock macOS, so never assume it.
PY_BIN="$PWD/.venv/bin/python"   # still at the repo root here
[ -x "$PY_BIN" ] || PY_BIN="$(command -v python3 || command -v python)"

cd backend
sam build
"$PY_BIN" ../scripts/check_lambda_package.py
sam deploy \
  --stack-name "$STACK" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset \
  --parameter-overrides "GroqApiKey=$GROQ" "JwtSecret=$JWT" "UseAgent=true"

echo
echo "API URL:"
aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text
