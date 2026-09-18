#!/usr/bin/env bash
# Pre-flight for the AWS swap. Read-only — creates nothing, costs nothing.
#
#   ./scripts/check_aws.sh
set -uo pipefail
cd "$(dirname "$0")/.."

pass(){ printf "  \033[32mok\033[0m   %s\n" "$1"; }
fail(){ printf "  \033[31mFAIL\033[0m %s\n" "$1"; }
info(){ printf "       %s\n" "$1"; }

echo "── credentials ──"
if ! command -v aws >/dev/null 2>&1; then
  fail "aws CLI not installed — brew install awscli"
else
  pass "aws CLI $(aws --version 2>&1 | cut -d' ' -f1)"
fi

if ID=$(aws sts get-caller-identity --output text --query Arn 2>/dev/null); then
  pass "authenticated as $ID"
else
  fail "no credentials — run: aws configure"
  info "needs an Access Key ID and Secret from the IAM console"
  exit 1
fi

REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region 2>/dev/null)}}"
if [ -n "$REGION" ]; then pass "region $REGION"; else fail "no region set — aws configure set region ap-south-1"; fi

echo
echo "── bedrock ──"
if MODELS=$(aws bedrock list-inference-profiles --query 'inferenceProfileSummaries[].inferenceProfileId' --output text 2>/dev/null) && [ -n "$MODELS" ]; then
  pass "inference profiles available:"
  for m in $MODELS; do info "$m"; done
  info "pick one and set AAHAR_BEDROCK_MODEL to it"
else
  fail "no inference profiles returned"
  info "enable model access in the Bedrock console for this region, then retry"
fi

echo
echo "── textract ──"
if aws textract help >/dev/null 2>&1; then
  pass "textract available in this CLI"
  info "permission is only exercised on a real call"
else
  fail "textract not available"
fi

echo
echo "── deploy readiness ──"
command -v sam >/dev/null 2>&1 && pass "sam $(sam --version 2>&1 | awk '{print $4}')" || fail "sam CLI missing"
[ -f backend/template.yaml ] && pass "template present" || fail "template missing"
echo
echo "Next: cd backend && sam build && python ../scripts/check_lambda_package.py && sam deploy --guided"
