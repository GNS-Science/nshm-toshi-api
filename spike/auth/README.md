# SPIKE: Modern Auth for nshm-toshi-api

Self-contained spike proving JWT auth via AWS Cognito + Lambda Authorizer as a replacement for the
single shared `x-api-key` in `TempApiKey`.

## Prerequisites

- AWS account (second/test account with IAM Identity Center partially set up)
- Python 3.12 + `poetry install` done
- `boto3`, `click`, `PyJWT`, `requests` available (`pip install PyJWT requests click`)
- AWS CLI profile configured: `aws configure --profile test-account`

## Quick Start

### 1. Provision Cognito

```bash
python spike/auth/cognito_setup.py --profile test-account
# Outputs: spike/auth/cognito_config.json
```

This creates:
- A User Pool named `toshi-spike`
- Resource server `toshi` with scopes `read` and `write`
- App client `toshi-scientist` (Device Authorization Grant, public)
- App client `toshi-automation` (Client Credentials, confidential)
- Test users: `scientist@example.com` / `Automati0n!` and `readonly@example.com` / `Read0nly!`

### 2. Scientist Interactive Login

```bash
python spike/auth/toshi_auth.py login
# Prints: Open https://... and enter code XXXX-YYYY
# After browser auth, saves token to ~/.toshi/credentials

python spike/auth/toshi_auth.py whoami
# Shows: user, scopes, expiry

python spike/auth/toshi_auth.py token
# Prints raw Bearer token (auto-refreshes if expired)
```

### 3. Automation / M2M Token

```bash
# Set env vars from cognito_config.json output:
export TOSHI_CLIENT_ID=<automation_client_id>
export TOSHI_CLIENT_SECRET=<automation_client_secret>
export TOSHI_COGNITO_DOMAIN=<domain>.auth.ap-southeast-2.amazoncognito.com

python spike/auth/toshi_auth.py m2m-token
# Prints Bearer token for use in Authorization header
```

### 4. Deploy Authorizer (optional, for API Gateway testing)

The Lambda authorizer is in `spike/auth/authorizer/`. To test against a real API Gateway:

```bash
# Copy authorizer into a temp deploy location
cp -r spike/auth/authorizer /tmp/toshi-authorizer
cd /tmp/toshi-authorizer
pip install -r requirements.txt -t .
zip -r function.zip .
aws lambda create-function --function-name toshi-jwt-authorizer \
  --runtime python3.12 --handler handler.handler \
  --zip-file fileb://function.zip \
  --role arn:aws:iam::<account>:role/<lambda-execution-role> \
  --environment Variables="{COGNITO_USER_POOL_ID=<pool_id>,COGNITO_REGION=ap-southeast-2,LEGACY_API_KEY=<key>}"
```

Then in `serverless.yml`, replace `private: true` with the `authorizer:` block shown in the comments
at the bottom of this file.

### 5. Local Stack Smoke Test

```bash
yarn sls dynamodb start --stage local &
yarn sls s3 start &
poetry run yarn sls wsgi serve &

python spike/auth/test_e2e.py --local
```

The Flask middleware (`spike/auth/middleware.py`) is **no-op** when `SLS_OFFLINE=1` or `TESTING=1`,
so local dev is unaffected.

---

## Architecture

```
Client (Runzi / scientist CLI)
    │
    │  Authorization: Bearer <JWT>
    ▼
API Gateway
    │
    ├── Lambda Authorizer ──► Validates JWT signature/expiry/scopes
    │                          Returns IAM Allow/Deny + {userId, scopes} context
    ▼
Flask (graphql_api/)
    │
    ├── before_request middleware ──► Reads context from request headers
    │                                  Maps operation type → required scope
    │                                  Enforces toshi/read vs toshi/write
    ▼
GraphQL resolvers / mutations (unchanged)
```

## Key Questions to Answer

1. **Latency** — Lambda authorizer cold-start: measure P99 with AWS X-Ray
2. **Token lifetime** — 1h Cognito tokens: does `m2m-token` auto-refresh mid-job?
3. **Device Flow UX** — Test from SSH terminal; record steps
4. **IAM Identity Center federation** — How hard to add Azure AD SAML IdP to this pool?
5. **Backward compat** — `x-api-key` still works via authorizer `LEGACY_API_KEY` env var

## Findings Log

| Date | Finding |
|------|---------|
| (TBD) | Record observations here as the spike progresses |

---

## serverless.yml Authorizer Snippet

When moving to production, replace:
```yaml
- http:
    path: graphql
    method: POST
    private: true
```
with:
```yaml
- http:
    path: graphql
    method: POST
    authorizer:
      name: jwtAuthorizer
      resultTtlInSeconds: 300
      identitySource: method.request.header.Authorization
      type: token
```

And add the authorizer function:
```yaml
functions:
  jwtAuthorizer:
    handler: spike/auth/authorizer/handler.handler
    environment:
      COGNITO_USER_POOL_ID: ${env:COGNITO_USER_POOL_ID}
      COGNITO_REGION: ${self:provider.region}
      LEGACY_API_KEY: ${env:LEGACY_API_KEY, ''}
```
