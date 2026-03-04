# SPIKE: Modern Auth for nshm-toshi-api

Self-contained spike proving JWT auth via AWS Cognito + Lambda Authorizer as a replacement for the
single shared `x-api-key` in `TempApiKey`.

## Prerequisites

- AWS account (second/test account with IAM Identity Center partially set up)
- Python 3.12 + `poetry install` done
- `boto3`, `click`, `PyJWT`, `requests` available (`pip install PyJWT requests click`)
- AWS CLI profile configured: `aws configure --profile AdministratorAccess-595842668254`

## Quick Start

### 0. 

- configured new subaccount ds-spike
- granted permission sets in new account to chrisbc user
- console access YAY
- created new profile with...

```
chrisbc@MLX01 nshm-toshi-api % aws configure sso
SSO session name (Recommended): ds-spike
SSO start URL [None]: https://d-976795968d.awsapps.com/start/#
SSO region [None]: ap-southeast-2
SSO registration scopes [sso:account:access]:
Attempting to open your default browser.
If the browser does not open, open the following URL:
...
```

new profile: AdministratorAccess-595842668254


### 1. Provision Cognito - DONE

```bash
poetry run python spike/auth/cognito_setup.py --profile AdministratorAccess-595842668254
# Outputs: spike/auth/cognito_config.json
```

This creates:
- A User Pool named `toshi-spike`
- Resource server `toshi` with scopes `read` and `write`
- App client `toshi-scientist` (USER_PASSWORD_AUTH, public — no client secret)
- App client `toshi-automation` (Client Credentials, confidential)
- Test users: `scientist@example.com` / `Scienti5t!` and `readonly@example.com` / `Read0nly!`

### 2. Scientist Login

```bash
poetry run python spike/auth/toshi_auth.py login
# Prompts for email and password, saves token to ~/.toshi/credentials

poetry run python spike/auth/toshi_auth.py whoami
# Shows: user, scopes, expiry

poetry run python spike/auth/toshi_auth.py token
# Prints raw Bearer token (auto-refreshes if expired)
```

> **Note:** AWS Cognito does not support the OAuth 2.0 Device Authorization Grant (RFC 8628).
> The `login` command uses Cognito's `USER_PASSWORD_AUTH` flow via boto3's `InitiateAuth` API
> instead. This works from SSH terminals — no browser required. The app client must have
> `ALLOW_USER_PASSWORD_AUTH` enabled (already set in `cognito_setup.py`).

### 3. Automation / M2M Token

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
poetry run python spike/auth/toshi_auth.py m2m-token
# Prints Bearer token (reads client_id/secret from cognito_config.json)

# Use the raw token directly in a request:
TOKEN=$(poetry run python spike/auth/toshi_auth.py m2m-token --raw)
curl -H "Authorization: Bearer $TOKEN" https://<api-url>/graphql -d '{"query":"{...}"}'

# Override credentials via env vars (preferred for CI/CD):
TOSHI_CLIENT_ID=<id> TOSHI_CLIENT_SECRET=<secret> poetry run python spike/auth/toshi_auth.py m2m-token
```

Token lifetime is 1 hour. Runzi should call `m2m-token` at the start of each job (or check
expiry before each request) rather than caching a token across jobs.

### 4. Deploy to AWS (spike stack)

The spike deploys via Serverless Framework directly from the repo root.  Elasticsearch is
excluded — it is not needed to prove auth and was removed to keep deploy times short.

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

API key (for `x-api-key` header): see AWS Console → API Gateway → API Keys → `TempApiKey-spike-toshi-api-dev`.

**CloudFormation stack:** `spike-toshi-api-dev-v2` (note `-v2` suffix — see Deployment Gotchas below).

#### Deployment Gotchas

- **Wrong AWS account**: Serverless Framework uses the default AWS provider on the org if no
  profile is set. Always pass `AWS_PROFILE=AdministratorAccess-595842668254` explicitly, and
  remove any default provider on the Serverless Dashboard org.

- **Stuck ES stack deletion**: The original stack included an `AWS::Elasticsearch::Domain` resource.
  ES domains take 20–30 min to delete in CloudFormation. ES has been removed entirely from the
  spike (`serverless-plugin-ifelse` also dropped). If the old stack is stuck deleting and blocks
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
const COGNITO_DOMAIN = 'https://toshi-spike.auth.ap-southeast-2.amazoncognito.com'; // update if different
const CLIENT_ID     = '<automation_client_id>';      // from cognito_config.json
const CLIENT_SECRET = '<automation_client_secret>';  // from cognito_config.json

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

Fill in `CLIENT_ID` and `CLIENT_SECRET` from `spike/auth/cognito_config.json`
(keys `automation_client_id` / `automation_client_secret`).

> **Note:** the Cognito token endpoint does **not** set CORS headers, so the token fetch in Step 1
> will be blocked by the browser if run from a normal page origin. Run it from the DevTools console
> of a tab that is already on `localhost` or use the `x-api-key` workaround below while the
> Lambda Authorizer is not yet wired in.

**While the JWT authorizer is not yet active** (API still uses `private: true` / `x-api-key`):

```js
const API = 'https://97udko2406.execute-api.ap-southeast-2.amazonaws.com/dev/graphql';
const res = await fetch(API, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': '<TempApiKey value from AWS Console>',
  },
  body: JSON.stringify({ query: '{ about }' }),
});
console.log(await res.json());
// Expected: { data: { about: "Hello, I am nshm_toshi_api, version: 0.5.2! [SPIKE/286-modern-auth]" } }
```

### 6. Local Stack Smoke Test

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
3. **SSH terminal UX** — USER_PASSWORD_AUTH works; no browser required. ✓ Confirmed.
4. **IAM Identity Center federation** — How hard to add Azure AD SAML IdP to this pool?
5. **Backward compat** — `x-api-key` still works via authorizer `LEGACY_API_KEY` env var

## Findings Log

| Date | Finding |
|------|---------|
| 2026-03-05 | AWS Cognito hosted UI does NOT support Device Authorization Grant (RFC 8628). `/oauth2/device_authorization` returns HTTP 400. Replaced with `USER_PASSWORD_AUTH` via `InitiateAuth` boto3 API — works from SSH terminals, no browser needed. |
| 2026-03-05 | `login`, `whoami`, and `token` commands all working. Token saved to `~/.toshi/credentials`. Auto-refresh via `REFRESH_TOKEN_AUTH` confirmed. |
| 2026-03-05 | Spike stack deployed to AWS (account 595842668254, ap-southeast-2). Elasticsearch removed entirely — not needed for auth proof. Stack named `spike-toshi-api-dev-v2` to sidestep stuck ES deletion from prior stack. `serverless-plugin-ifelse` dropped. |
| 2026-03-05 | API live and responding. `x-api-key` auth confirmed working. `{about}` query returns `"Hello, I am nshm_toshi_api, version: 0.5.2! [SPIKE/286-modern-auth]"`. |

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
