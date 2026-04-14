# Modern Auth Implementation Plan — nshm-toshi-api

Documents the implementation of JWT auth via AWS Cognito + Lambda Authorizer as a replacement
for the single shared `x-api-key` in `TempApiKey`.

## Prerequisites

- AWS account with IAM Identity Center partially set up
- Python 3.12 + `poetry install` done
- `boto3`, `click`, `PyJWT`, `requests` available (`pip install PyJWT requests click`)
- AWS CLI profile configured: `aws configure --profile AdministratorAccess-595842668254`

## Quick Start

### Configuration & Secrets Management
To test the auth integration locally, note the distinction between public config and private test data:
- **`auth_config.json`** (Committed): Stores generated public infrastructure output (e.g., `user_pool_id`, `scientist_client_id`, `cognito_domain`).
- **`.env`** (Gitignored): Stores the `TOSHI_CLIENT_SECRET` generated during setup for M2M flow.
- **`test_users.json`** (Gitignored): Stores user credentials for E2E tests and manual `toshi_auth.py login` validation. A version with the required user profiles must be created locally before running `cognito_setup.py`.

### Phase 1 — IAM Roles + Cognito Identity Pool (SSO without Entra)

#### 0. AWS Profile Setup

Configure AWS CLI profile with SSO:
```bash
aws configure sso
# SSO start URL: https://d-976795968d.awsapps.com/start/#
# SSO region: ap-southeast-2
```

#### 1. Provision Cognito User Pool + Identity Pool
```bash
poetry run python auth/cognito_setup.py --profile AdministratorAccess-595842668254
# Outputs: auth/auth_config.json and auth/.env
```

This creates:
- User Pool `toshi` with resource server and scopes
- App clients for scientists and automation
- Identity Pool for AWS credential exchange
- Users with groups: `toshi-readers`, `toshi-writers`, `runzi-local`, `runzi-batch`, `runzi-admin`

#### 2. Create IAM Roles
```bash
poetry run python auth/iam_roles.py \
    --profile AdministratorAccess-595842668254 \
    --identity-pool-id <identity_pool_id_from_auth_config.json>
# Outputs: auth/iam_roles_config.json
```

This creates IAM roles:
- `toshi-runzi-local` — ECR pull, S3 read/write
- `toshi-runzi-batch` — + Batch submit/describe
- `toshi-runzi-admin` — + Batch configure, ECR push

#### 3. Update Identity Pool Role Mappings

The Identity Pool was created with placeholder role mappings. Update them manually in AWS Console:

1. Go to Cognito → Identity Pools → `toshi-identity-pool`
2. Edit → Role mappings
3. Set each group to its corresponding IAM role:
   - `toshi-readers` → use default authenticated role
   - `toshi-writers` → use default authenticated role
   - `runzi-local` → `toshi-runzi-local`
   - `runzi-batch` → `toshi-runzi-batch`
   - `runzi-admin` → `toshi-runzi-admin`

Or use the AWS CLI:
```bash
aws cognito-identity set-identity-pool-roles \
    --identity-pool-id <identity_pool_id> \
    --role-mappings file://role-mappings.json \
    --roles authenticated=<role_arn>
```

#### 4. Test Login + AWS Credentials
```bash
# Login with test user
poetry run python auth/toshi_auth.py login

# Get AWS credentials
poetry run python auth/toshi_auth.py aws-creds

# Use AWS CLI with the credentials
export AWS_PROFILE=toshi
aws ecr describe-repositories --region ap-southeast-2
```

### Phase 2 — Entra OIDC Federation (deferred)

See `IDP_INTEGRATION_PLAN.md` for Entra ID federation setup.

---

### Legacy Quick Start (pre-Identity Pool)

This section documents the original setup without Identity Pool. Superseded by Phase 1 above.

#### 1. Provision Cognito
```bash
poetry run python auth/cognito_setup.py --profile AdministratorAccess-595842668254
```

#### 2. Scientist Login
```bash
poetry run python auth/toshi_auth.py login
poetry run python auth/toshi_auth.py whoami
poetry run python auth/toshi_auth.py token
```

#### 3. Automation / M2M Token

This flow is for **Runzi and other automated pipelines** that call the Toshi API without a human
user in the loop. It uses the OAuth 2.0 Client Credentials grant: the `toshi-automation` app
client authenticates directly with its client secret and receives a short-lived access token.

Key differences from the scientist flow:
- **No user identity** — the JWT `sub` is the client ID, not a person; `username` claim is absent
- **No refresh token** — tokens cannot be refreshed; just request a new one when it expires
- **Scopes are fixed** — the client always gets `toshi/read toshi/write` regardless of the caller
- **Secret must be kept secure** — treat `automation_client_secret` like a password; store it in
  AWS Secrets Manager or CI/CD secret variables, never in source control

```bash
poetry run python auth/toshi_auth.py m2m-token
# Prints Bearer token (reads client_id from auth_config.json and secret from .env)

# Use the raw token directly in a request:
TOKEN=$(poetry run python auth/toshi_auth.py m2m-token --raw)
curl -H "Authorization: Bearer $TOKEN" https://<api-url>/graphql -d '{"query":"{...}"}'

# Override credentials via env vars (preferred for CI/CD):
TOSHI_CLIENT_ID=<id> TOSHI_CLIENT_SECRET=<secret> poetry run python auth/toshi_auth.py m2m-token
```

Token lifetime is 1 hour. Runzi should call `m2m-token` at the start of each job (or check
expiry before each request) rather than caching a token across jobs.

### 4. Deploy to AWS

```bash
# Ensure SSO session is active
aws sso login --profile AdministratorAccess-595842668254

# Deploy (≈2 min)
AWS_PROFILE=AdministratorAccess-595842668254 poetry run serverless deploy --stage dev
```

**Live endpoints (ap-southeast-2, account 595842668254):**

| Method | URL |
|--------|-----|
| OPTIONS | `https://97udko2406.execute-api.ap-southeast-2.amazonaws.com/dev/graphql` |
| POST   | `https://97udko2406.execute-api.ap-southeast-2.amazonaws.com/dev/graphql` |
| GET    | `https://97udko2406.execute-api.ap-southeast-2.amazonaws.com/dev/graphql` |

API key (for `x-api-key` header): see AWS Console → API Gateway → API Keys → `TempApiKey-nzshm22-toshi-api-dev`.

#### Deployment Gotchas

- **Wrong AWS account**: Serverless Framework uses the default AWS provider on the org if no
  profile is set. Always pass `AWS_PROFILE=AdministratorAccess-595842668254` explicitly, and
  remove any default provider on the Serverless Dashboard org.

- **Stuck ES stack deletion**: The original stack included an `AWS::Elasticsearch::Domain` resource.
  ES domains take 20–30 min to delete in CloudFormation. If an old stack is stuck deleting and blocks
  resource creation (S3 bucket name clash, etc.), append `-v2` (or similar) to `provider.stackName`
  and `custom.s3_bucket` in `serverless.yml` to deploy a fresh stack in parallel.

- **`serverless-plugin-ifelse` array exclusion**: The plugin nulls array entries rather than
  splicing them, producing `null` values in CloudFormation IAM statements that CF rejects. Avoid
  excluding `provider.iamRoleStatements` array indices with this plugin; use `Resources` entries
  instead, or just remove the conditional resource entirely.

### 5. Test M2M credentials from a browser console

Useful for verifying the token and API without any local tooling — open DevTools in any browser
(F12 → Console) and paste:

```js
// Step 1 — get an M2M token from Cognito
const COGNITO_DOMAIN = 'https://toshi-auth.<pool-suffix>.auth.ap-southeast-2.amazoncognito.com';
const CLIENT_ID     = '<automation_client_id>';      // from auth_config.json
const CLIENT_SECRET = '<automation_client_secret>';  // from .env

const creds = btoa(`${CLIENT_ID}:${CLIENT_SECRET}`);
const tokenRes = await fetch(`${COGNITO_DOMAIN}/oauth2/token`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': `Basic ${creds}`,
  },
  body: 'grant_type=client_credentials&scope=toshi/read',
});
const { access_token } = await tokenRes.json();
console.log('token:', access_token);

// Step 2 — call the API
const API = 'https://97udko2406.execute-api.ap-southeast-2.amazonaws.com/dev/graphql';
const gql = await fetch(API, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`,
  },
  body: JSON.stringify({ query: '{ about }' }),
});
console.log(await gql.json());
```

Fill in `CLIENT_ID` from `auth/auth_config.json`
and `CLIENT_SECRET` from `auth/.env`.

> **Note:** the Cognito token endpoint does **not** set CORS headers, so the token fetch in Step 1
> will be blocked by the browser if run from a normal page origin. Run it from the DevTools console
> of a tab that is already on `localhost`.

### 6. Local Stack Smoke Test

```bash
yarn sls dynamodb start --stage local &
yarn sls s3 start &
poetry run yarn sls wsgi serve &

python auth/test_e2e.py --local
```

The Flask middleware (`auth/middleware.py`) is **no-op** when `SLS_OFFLINE=1` or `TESTING=1`,
so local dev is unaffected.

---

## Findings Log

| Date | Finding |
|------|---------|
| 2026-03-05 | AWS Cognito hosted UI does NOT support Device Authorization Grant (RFC 8628). `/oauth2/device_authorization` returns HTTP 400. Replaced with `USER_PASSWORD_AUTH` via `InitiateAuth` boto3 API — works from SSH terminals, no browser needed. |
| 2026-03-05 | `login`, `whoami`, and `token` commands all working. Token saved to `~/.toshi/credentials`. Auto-refresh via `REFRESH_TOKEN_AUTH` confirmed. |
| 2026-03-05 | Initial deploy to AWS (account 595842668254, ap-southeast-2). Elasticsearch removed entirely — not needed for auth. Stack named with `-v2` suffix to sidestep stuck ES deletion from prior stack. `serverless-plugin-ifelse` dropped. |
| 2026-03-05 | API live and responding. `x-api-key` auth confirmed working. |
| 2026-03-05 | Full JWT auth flow confirmed end-to-end: M2M token → API Gateway → Lambda Authorizer → Flask middleware. Key fix: authorizer context is in `request.environ['serverless.authorizer']` (set by serverless-wsgi), not in HTTP headers as originally assumed. |
