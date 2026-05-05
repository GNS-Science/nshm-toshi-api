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

Infrastructure outputs (pool IDs, client IDs, domain) come from `sls info --verbose` after deploy.
Local files used by auth scripts:

- **`auth/.env`** (Gitignored): Stores `TOSHI_CLIENT_SECRET` for M2M flow. Fetch once after deploy (see Phase 1 step 3).
- **`test_users.json`** (Gitignored): User credentials for E2E tests and `toshi_auth.py login`. Create locally before running `create_users.py`.

### Phase 1 — IAM Roles + Cognito Identity Pool (SSO without Entra)

All Cognito and IAM resources are now provisioned by `sls deploy` via CloudFormation resources
in `serverless.yml`. No separate provisioning scripts needed.

#### 0. AWS Profile Setup

Configure AWS CLI profile with SSO:
```bash
aws configure sso
# SSO start URL: https://d-976795968d.awsapps.com/start/#
# SSO region: ap-southeast-2
```

#### 1. Deploy (provisions everything)
```bash
aws sso login --profile AdministratorAccess-595842668254
AWS_PROFILE=AdministratorAccess-595842668254 poetry run serverless deploy --stage dev
```

This creates in one stack:
- User Pool `toshi-dev` with resource server (`toshi/read`, `toshi/write` scopes)
- App clients: `toshi-scientist` (public) and `toshi-automation` (confidential)
- User groups: `toshi-readers`, `toshi-writers`, `runzi-local`, `runzi-batch`, `runzi-admin`
- Identity Pool with rules-based role mappings
- IAM roles: `toshi-runzi-local-dev`, `toshi-runzi-batch-dev`, `toshi-runzi-admin-dev`

#### 2. Retrieve outputs
```bash
AWS_PROFILE=AdministratorAccess-595842668254 poetry run serverless info --stage dev --verbose
# Shows: UserPoolId, IdentityPoolId, ScientistClientId, AutomationClientId, CognitoDomain, etc.
```

#### 3. Fetch automation client secret

The client secret cannot be a CloudFormation Output (security). Retrieve it once after deploy:
```bash
aws cognito-idp describe-user-pool-client \
    --user-pool-id <UserPoolId> \
    --client-id <AutomationClientId> \
    --profile AdministratorAccess-595842668254 \
    --query 'UserPoolClient.ClientSecret' --output text
# Save to auth/.env as: TOSHI_CLIENT_SECRET=<secret>
```

#### 4. Create test users
```bash
# Create auth/test_users.json locally (gitignored) — see auth/.env.example for format
# Then:
python auth/create_users.py --profile AdministratorAccess-595842668254
```

#### 5. Test Login + AWS Credentials
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

---

## Provisioning Approach Decision

### Options considered

Three approaches were evaluated for replacing `cognito_setup.py` + `iam_roles.py`:

| Option | Description |
|--------|-------------|
| **A — Serverless-native** (chosen) | Add `AWS::Cognito` + `AWS::IAM` resources to `serverless.yml` under `resources.Resources` |
| **B — AWS CDK Python** | Separate `auth/cdk/` sub-project with `ToshiCognitoStack` + `ToshiIamStack` |
| **C — Keep raw boto3** | Current state: hand-rolled scripts with custom teardown logic |

CDK implementation exists for reference on branch `spike/cdk-auth-provisioning`.

### Why Serverless-native

- **Single toolchain** — `sls deploy` provisions everything; no `cdk bootstrap`, no `pip install` in a
  sub-directory, no separate deploy step.
- **Tight integration** — `jwtAuthorizer` env vars become self-referential (`!Ref ToshiUserPool`)
  rather than requiring manual wiring from a `post_deploy.py` output file.
- **Directly answers reviewer feedback** — PR #287 asked "Is the Serverless Framework not able to
  do this?". The answer is yes.
- **Same team, same deploy cadence** — auth infra and the API are deployed together by the same
  CI pipeline; coupling is a feature, not a liability here.

### When CDK would be the better choice

- Auth infra is shared across multiple API stacks (separate lifecycle needed).
- Auth is managed by a different team or permission boundary from the API.
- Entra/SSO federation makes the User Pool infra-level (rarely changes, outlives any app stack).

At that point, migrate to `spike/cdk-auth-provisioning` as the foundation.

### Key trade-off: lifecycle coupling

With Serverless-native, `sls remove` destroys the User Pool. This is fine for dev/test but
requires care in production — either:
- Use `DeletionPolicy: Retain` on the UserPool resource, or
- Run prod on a separate long-lived account/stage where teardown is not a normal operation.

---

## Findings Log

| Date | Finding |
|------|---------|
| 2026-03-05 | AWS Cognito hosted UI does NOT support Device Authorization Grant (RFC 8628). `/oauth2/device_authorization` returns HTTP 400. Replaced with `USER_PASSWORD_AUTH` via `InitiateAuth` boto3 API — works from SSH terminals, no browser needed. |
| 2026-03-05 | `login`, `whoami`, and `token` commands all working. Token saved to `~/.toshi/credentials`. Auto-refresh via `REFRESH_TOKEN_AUTH` confirmed. |
| 2026-03-05 | Initial deploy to AWS (account 595842668254, ap-southeast-2). Elasticsearch removed entirely — not needed for auth. Stack named with `-v2` suffix to sidestep stuck ES deletion from prior stack. `serverless-plugin-ifelse` dropped. |
| 2026-03-05 | API live and responding. `x-api-key` auth confirmed working. |
| 2026-03-05 | Full JWT auth flow confirmed end-to-end: M2M token → API Gateway → Lambda Authorizer → Flask middleware. Key fix: authorizer context is in `request.environ['serverless.authorizer']` (set by serverless-wsgi), not in HTTP headers as originally assumed. |
| 2026-04-28 | Middleware mutation detection replaced: regex `_MUTATION_RE` swapped for `graphql-core` AST parser (`graphql.parse` + `OperationDefinitionNode`). Fixes false positives when "mutation" appears in string literals, comments, or multi-operation documents with `operationName` selection. Fails closed on unparseable input. 12 unit tests added (`auth/test_middleware.py`). |
| 2026-04-28 | Authorizer handler: removed id-token acceptance — only access tokens carry scopes and are valid for API authorisation. Simplified `client_id` audience check (no longer conditional on `token_use`). Fixed mypy: `decode_options` typed as `jwt.types.Options` (PyJWT ≥2.12). |
| 2026-04-28 | E2E test docs: clarified that `--local` mode tests connectivity only (middleware is no-op under `IS_OFFLINE=1`); `auth_config.json` prerequisite only applies to `--remote` mode. |
