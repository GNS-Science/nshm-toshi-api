#!/usr/bin/env bash
# Set, check or roll back the API Gateway stage throttle for toshi.
#
# The throttle is NOT deployed by serverless.yml: Serverless has no setting for a
# REST API stage throttle. It is set on the stage by hand with this script, once
# per stage, with operator credentials. Stage settings survive redeploys, but a
# stage that is deleted and recreated comes back at the account default
# (10,000 req/s) and needs `apply` again.
#
# Sizing rationale: see the concurrency-cap comment in serverless.yml.
#
#   bash scripts/stage_throttle.sh <rest-api-id> <stage> check
#   bash scripts/stage_throttle.sh <rest-api-id> <stage> apply
#   bash scripts/stage_throttle.sh <rest-api-id> <stage> rollback
#
# <stage> is the stage name (test, prod). <rest-api-id> is the id of that stage's
# REST API - the first label of its invoke URL, or look it up with:
#
#   aws apigateway get-rest-apis --region ap-southeast-2 \
#     --query "items[?contains(name,'toshi')].[id,name]" --output text
#
# DRY_RUN=1 prints the aws command instead of running it.
set -euo pipefail

REGION=ap-southeast-2
RATE=50
BURST=500
DEFAULT_RATE=10000
DEFAULT_BURST=5000

usage() {
  echo "usage: $0 <rest-api-id> <stage> <check|apply|rollback>" >&2
  exit 2
}

[ "$#" -eq 3 ] || usage
api_id="$1"
stage="$2"
action="$3"

run() {
  if [ "${DRY_RUN:-}" = "1" ]; then
    printf '%q ' "$@"; echo
  else
    "$@"
  fi
}

set_throttle() {
  run aws apigateway update-stage \
    --rest-api-id "$api_id" --stage-name "$stage" --region "$REGION" \
    --patch-operations \
      "op=replace,path=/*/*/throttling/rateLimit,value=$1" \
      "op=replace,path=/*/*/throttling/burstLimit,value=$2" \
    --query 'methodSettings."*/*".[throttlingRateLimit,throttlingBurstLimit]'
}

case "$action" in
  check)
    run aws apigateway get-stage \
      --rest-api-id "$api_id" --stage-name "$stage" --region "$REGION" \
      --query 'methodSettings."*/*".[throttlingRateLimit,throttlingBurstLimit]'
    ;;
  apply) set_throttle "$RATE" "$BURST" ;;
  rollback) set_throttle "$DEFAULT_RATE" "$DEFAULT_BURST" ;;
  *) usage ;;
esac
