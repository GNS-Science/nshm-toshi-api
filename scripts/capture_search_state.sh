#!/usr/bin/env bash
#
# Capture the live state of Toshi search before decommissioning it.
#
# Every call here is a describe/list/get — nothing is created, modified or
# deleted. The output is a single markdown file intended to be committed, so
# that the pre-teardown state of both search backends is recoverable from git.
#
# Usage:
#   ./scripts/capture_search_state.sh [stage]          # defaults to prod
#   OUT=/tmp/state.md ./scripts/capture_search_state.sh test
#   CAPTURE_DRIFT=1 ./scripts/capture_search_state.sh  # also starts CFN drift detection
#
# Requires: valid AWS credentials (aws sts get-caller-identity must succeed),
# and `uv sync` for the signed index-level requests.

set -uo pipefail

STAGE="${1:-prod}"
REGION="${AWS_REGION:-ap-southeast-2}"
STACK="nzshm22-toshi-api-${STAGE}"
OUT="${OUT:-docs/search-state-$(date +%Y-%m-%d)-${STAGE}.md}"

section() {
    printf '\n## %s\n' "$1" >> "$OUT"
}

note() {
    printf '\n%s\n' "$1" >> "$OUT"
}

# Mask values of environment variables whose names look like secrets. Lambda
# configurations carry real credentials (LEGACY_API_KEY), and this output is
# meant to be committed.
redact() {
    sed -E 's/"([A-Z0-9_]*(KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL)[A-Z0-9_]*)": "[^"]*"/"\1": "***REDACTED***"/g'
}

# Run a command, recording both the invocation and its output (or its error).
# Failures are captured rather than fatal — a missing resource is itself a
# finding worth recording.
run() {
    local desc="$1"; shift
    printf '\n### %s\n\n```\n$ %s\n' "$desc" "$*" >> "$OUT"
    local output
    if output=$("$@" 2>&1 | redact); then
        printf '%s\n' "${output:-(empty)}" >> "$OUT"
    else
        printf 'COMMAND FAILED:\n%s\n' "$output" >> "$OUT"
    fi
    printf '```\n' >> "$OUT"
    echo "  captured: $desc"
}

# Signed request against an OpenSearch endpoint. $1 = host, $2 = path,
# $3 = signing service name ("es" for managed domains, "aoss" for collections).
signed_get() {
    local host="$1" path="$2" service="$3"
    ES_HOST="$host" ES_PATH="$path" ES_SERVICE="$service" ES_REGION="$REGION" \
        uv run python - <<'PY' 2>&1
import os
import boto3
import requests
from requests_aws4auth import AWS4Auth

host = os.environ["ES_HOST"].rstrip("/")
if not host.startswith("http"):
    host = f"https://{host}"
creds = boto3.Session().get_credentials()
auth = AWS4Auth(
    creds.access_key,
    creds.secret_key,
    os.environ["ES_REGION"],
    os.environ["ES_SERVICE"],
    session_token=creds.token,
)
resp = requests.get(f"{host}{os.environ['ES_PATH']}", auth=auth, timeout=30)
print(f"HTTP {resp.status_code}")
print(resp.text[:20000])
PY
}

echo "Capturing search state for stage '${STAGE}' in ${REGION} -> ${OUT}"

# ── Preflight ─────────────────────────────────────────────────────────────────
if ! command -v aws >/dev/null 2>&1; then
    echo "ERROR: aws CLI not found" >&2
    exit 1
fi

if ! ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>&1); then
    echo "ERROR: no usable AWS credentials. Re-authenticate, then re-run." >&2
    echo "$ACCOUNT_ID" >&2
    exit 1
fi

mkdir -p "$(dirname "$OUT")"
: > "$OUT"

START_DATE=$(date -u -d '120 days ago' +%Y-%m-%dT00:00:00Z 2>/dev/null \
    || date -u -v-120d +%Y-%m-%dT00:00:00Z)
END_DATE=$(date -u +%Y-%m-%dT00:00:00Z)
COST_START=$(date -u -d '120 days ago' +%Y-%m-01 2>/dev/null || date -u -v-120d +%Y-%m-01)
COST_END=$(date -u +%Y-%m-%d)

{
    echo "# Toshi search — captured live state"
    echo
    echo "- **Captured:** $(date -u +%Y-%m-%dT%H:%M:%SZ) by \`scripts/capture_search_state.sh\`"
    echo "- **Stage:** ${STAGE}"
    echo "- **Region:** ${REGION}"
    echo "- **Stack:** ${STACK}"
    echo "- **Account:** ${ACCOUNT_ID}"
    echo
    echo "Pre-teardown snapshot of both search backends: the managed domain declared"
    echo "in serverless.yml, and the OpenSearch Serverless collection that exists only"
    echo "in live AWS state. Read-only capture — see the script for what was run."
    echo
    echo "> Secret-looking environment values are masked. Still contains account IDs and"
    echo "> endpoint hostnames — review before sharing outside the team."
} >> "$OUT"

# ── CloudFormation: what the stack believes it owns ──────────────────────────
section "CloudFormation stack resources"
note "What the template thinks exists. Compare against the OpenSearch sections below."

run "All stack resources" \
    aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION"

run "Search-related stack resources only" \
    aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION" \
    --query "StackResources[?contains(ResourceType, 'arch')].{Logical:LogicalResourceId,Type:ResourceType,Physical:PhysicalResourceId,Status:ResourceStatus}"

if [ "${CAPTURE_DRIFT:-0}" = "1" ]; then
    run "Start drift detection (poll with describe-stack-drift-detection-status)" \
        aws cloudformation detect-stack-drift --stack-name "$STACK" --region "$REGION"
fi

# ── Lambda: the config that exists only in live state ────────────────────────
section "Lambda environment"
note "The open question: ES_ENDPOINT / ES_INDEX are not in serverless.yml (removed in 6e9b8d9, 2026-06-16) yet reads still work, so they must be set out-of-band. This is what a deploy would overwrite."

for fn in graphql jwtAuthorizer; do
    run "Function environment: ${STACK}-${fn}" \
        aws lambda get-function-configuration \
        --function-name "${STACK}-${fn}" --region "$REGION" \
        --query "{Runtime:Runtime,Memory:MemorySize,Timeout:Timeout,LastModified:LastModified,Environment:Environment}"
done

# ── Managed domain ───────────────────────────────────────────────────────────
section "OpenSearch managed domain"
note "Declared in serverless.yml:238-251 as Elasticsearch 6.2 / t2.small / 10GB gp2. Any divergence below is drift accumulated since 2020."

run "Domain names" aws opensearch list-domain-names --region "$REGION"

DOMAINS=$(aws opensearch list-domain-names --region "$REGION" \
    --query 'DomainNames[].DomainName' --output text 2>/dev/null)

for domain in $DOMAINS; do
    run "Domain status: ${domain}" \
        aws opensearch describe-domain --domain-name "$domain" --region "$REGION"
    run "Domain config (includes access policies): ${domain}" \
        aws opensearch describe-domain-config --domain-name "$domain" --region "$REGION" \
        --query 'DomainConfig.{Engine:EngineVersion.Options,Cluster:ClusterConfig.Options,EBS:EBSOptions.Options,Access:AccessPolicies.Options,Advanced:AdvancedOptions.Options}'

    ENDPOINT=$(aws opensearch describe-domain --domain-name "$domain" --region "$REGION" \
        --query 'DomainStatus.Endpoint' --output text 2>/dev/null)

    for metric in ClusterIndexWritesBlocked FreeStorageSpace SearchRate IndexingRate; do
        run "Metric ${metric}: ${domain}" \
            aws cloudwatch get-metric-statistics --namespace AWS/ES --metric-name "$metric" \
            --dimensions "Name=DomainName,Value=${domain}" "Name=ClientId,Value=${ACCOUNT_ID}" \
            --start-time "$START_DATE" --end-time "$END_DATE" \
            --period 86400 --statistics Maximum Sum --region "$REGION" \
            --query 'sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Sum:Sum}'
    done

    # Index-level state. `_settings` is the one that answers whether writes are
    # blocked by the disk flood-stage watermark (index.blocks.read_only_allow_delete).
    if [ -n "$ENDPOINT" ] && [ "$ENDPOINT" != "None" ]; then
        for path in "/_cluster/health" "/_cat/indices?v" "/_all/_settings" "/toshi_index_mapped/_mapping" "/toshi_index_mapped/_count"; do
            printf '\n### Index state %s: %s\n\n```\n' "$path" "$domain" >> "$OUT"
            signed_get "$ENDPOINT" "$path" "es" >> "$OUT"
            printf '```\n' >> "$OUT"
            echo "  captured: index state ${path}"
        done
    else
        note "No endpoint resolved for ${domain} — skipped index-level capture."
    fi
done

# ── Serverless collection ────────────────────────────────────────────────────
section "OpenSearch Serverless collection"
note "Exists nowhere in the repo. Billing 744 SearchOCU-hours/month (one OCU pinned continuously, ~USD 209) plus any IndexingOCU."

run "Collections" aws opensearchserverless list-collections --region "$REGION"

COLLECTIONS=$(aws opensearchserverless list-collections --region "$REGION" \
    --query 'collectionSummaries[].name' --output text 2>/dev/null)

for collection in $COLLECTIONS; do
    run "Collection detail: ${collection}" \
        aws opensearchserverless batch-get-collection --names "$collection" --region "$REGION"

    COLLECTION_ID=$(aws opensearchserverless batch-get-collection --names "$collection" \
        --region "$REGION" --query 'collectionDetails[0].id' --output text 2>/dev/null)

    # Per-collection metrics only. The OCU metrics are account-level and are
    # captured separately below — asking for them with a collection dimension
    # returns nothing, which is easily misread as "no capacity consumed".
    for metric in SearchRequestRate IngestionRequestRate SearchRequestErrors; do
        run "Metric ${metric}: ${collection}" \
            aws cloudwatch get-metric-statistics --namespace AWS/AOSS --metric-name "$metric" \
            --dimensions "Name=CollectionName,Value=${collection}" "Name=CollectionId,Value=${COLLECTION_ID}" \
            --start-time "$START_DATE" --end-time "$END_DATE" \
            --period 86400 --statistics Maximum Sum --region "$REGION" \
            --query 'sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Sum:Sum}'
    done
done

# OCU consumption is published per account, not per collection (ClientId is the
# only dimension). This is what the APS2-IndexingOCU / APS2-SearchOCU lines on
# the bill are charging for: warm capacity held whether or not anything uses it.
note "OCU metrics are account-wide. Each OCU-hour here corresponds to an OCU-hour on the bill, so these should drop to zero once the collections holding that capacity are gone."

for metric in SearchOCU IndexingOCU; do
    run "Metric ${metric}: account-wide" \
        aws cloudwatch get-metric-statistics --namespace AWS/AOSS --metric-name "$metric" \
        --dimensions "Name=ClientId,Value=${ACCOUNT_ID}" \
        --start-time "$START_DATE" --end-time "$END_DATE" \
        --period 86400 --statistics Maximum Average --region "$REGION" \
        --query 'sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Avg:Average}'
done

run "Encryption policies" aws opensearchserverless list-security-policies --type encryption --region "$REGION"
run "Network policies" aws opensearchserverless list-security-policies --type network --region "$REGION"
run "Data access policies" aws opensearchserverless list-access-policies --type data --region "$REGION"

# ── Spend ────────────────────────────────────────────────────────────────────
section "Spend by usage type"
note "'Amazon OpenSearch Service' covers both products — managed instance hours and serverless OCU hours appear under different usage types."

run "Monthly cost by usage type" \
    aws ce get-cost-and-usage \
    --time-period "Start=${COST_START},End=${COST_END}" \
    --granularity MONTHLY --metrics UnblendedCost \
    --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon OpenSearch Service"]}}' \
    --group-by Type=DIMENSION,Key=USAGE_TYPE \
    --region us-east-1

# ── Footer ───────────────────────────────────────────────────────────────────
section "Not captured here"
note "- **Manual snapshot.** Automated snapshots are destroyed with the domain. Take one to a bucket you own before deleting: see the OpenSearch \`_snapshot\` API.
- **Consumers.** Which clients call the \`search\` query (toshi-ui, runzi, ad-hoc \`scripts/elastic_cli.py\` use) is a team question, not an API call.
- **Mapping drift.** Diff the captured \`_mapping\` against the \`mapping()\` definition in \`scripts/elastic_cli.py:193\`."

echo
echo "Done. Review before committing (contains account IDs and endpoints):"
echo "  $OUT"
