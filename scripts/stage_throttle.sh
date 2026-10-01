#!/usr/bin/env bash
# Set, check or roll back the API Gateway stage throttle for toshi.
#
# The throttle is not part of the CloudFormation stack: Serverless has no setting
# for a REST API stage throttle. Instead the `deploy` script in package.json runs
# `apply` after every `serverless deploy`, and a failure here fails the deploy -
# a stage must not go out unthrottled without anyone noticing.
#
# Sizing rationale: see the concurrency-cap comment in serverless.yml.
#
#   bash scripts/stage_throttle.sh <stage> check
#   bash scripts/stage_throttle.sh <stage> apply
#   bash scripts/stage_throttle.sh <stage> rollback    (back to the account default)
#
# <stage> is the stage name (test, prod). The REST API is found by its name,
# <stage>-nzshm22-toshi-api; set REST_API_ID to skip the lookup.
#
# Needs apigateway:GET on /restapis and apigateway:PATCH on the stage.
#
# DRY_RUN=1 prints the aws commands that change anything instead of running them.
set -euo pipefail

REGION=ap-southeast-2
SERVICE=nzshm22-toshi-api
RATE=50
BURST=500
DEFAULT_RATE=10000
DEFAULT_BURST=5000
QUERY='methodSettings."*/*".[throttlingRateLimit,throttlingBurstLimit]'

usage() {
  echo "usage: $0 <stage> <check|apply|rollback>" >&2
  exit 2
}

fail() {
  echo "stage_throttle: $*" >&2
  exit 1
}

[ "$#" -eq 2 ] || usage
stage="$1"
action="$2"
case "$action" in check | apply | rollback) ;; *) usage ;; esac

api_id="${REST_API_ID:-}"
if [ -z "$api_id" ]; then
  api_name="${stage}-${SERVICE}"
  api_id=$(aws apigateway get-rest-apis --region "$REGION" \
    --query "items[?name=='${api_name}'].id" --output text)
  # zero matches prints nothing (or "None"); several print tab-separated ids
  case "$api_id" in
    "" | None) fail "no REST API named ${api_name} in ${REGION}" ;;
    *[[:space:]]*) fail "more than one REST API named ${api_name}: ${api_id}" ;;
  esac
fi

# Prints "<rate> <burst>" as the stage has them; "None None" when never set.
current() {
  aws apigateway get-stage \
    --rest-api-id "$api_id" --stage-name "$stage" --region "$REGION" \
    --query "$QUERY" --output text
}

set_throttle() {
  local rate="$1" burst="$2"
  local cmd=(aws apigateway update-stage
    --rest-api-id "$api_id" --stage-name "$stage" --region "$REGION"
    --patch-operations
    "op=replace,path=/*/*/throttling/rateLimit,value=${rate}"
    "op=replace,path=/*/*/throttling/burstLimit,value=${burst}")
  if [ "${DRY_RUN:-}" = "1" ]; then
    printf '%q ' "${cmd[@]}"
    echo
    return
  fi
  "${cmd[@]}" >/dev/null

  # read it back: a call that succeeds without the setting landing is still a failure
  local got_rate got_burst
  read -r got_rate got_burst <<<"$(current)"
  if [ "${got_rate%.*}" != "$rate" ] || [ "$got_burst" != "$burst" ]; then
    fail "${stage} stage reads back rate=${got_rate} burst=${got_burst}, expected ${rate} and ${burst}"
  fi
  echo "stage_throttle: ${stage} stage throttled to ${rate} req/s, burst ${burst}"
}

case "$action" in
  check) current ;;
  apply) set_throttle "$RATE" "$BURST" ;;
  rollback) set_throttle "$DEFAULT_RATE" "$DEFAULT_BURST" ;;
esac
