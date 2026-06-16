# Authentication Guide — nshm-toshi-api

This guide explains how to authenticate with the Toshi API as an end user. The API is migrating
from a single shared `x-api-key` to per-user Cognito JWTs, while maintaining backward compatibility
with legacy API key clients during the transition.

There are three client personas:

| Persona | Flow | Tool |
|---------|------|------|
| **Scientist** (interactive) | Cognito username/password → Bearer JWT | `toshi_auth.py login` |
| **Automation / Runzi** (M2M) | OAuth 2.0 Client Credentials → Bearer JWT | `toshi_auth.py m2m-token` |
| **Legacy client** (transition) | Shared `x-api-key` header | No change required |

> **Upcoming: GNS SSO integration.** Cognito will soon be federated with GNS Entra ID (Azure AD).
> Once live, scientists log in with their GNS corporate credentials via a browser — no separate
> Toshi password. The `toshi_auth login` command will handle this automatically. M2M flows and
> the Lambda Authorizer are **unchanged**. See [Flow E: SSO Login (Entra federation)](#flow-e-scientist-login-with-gns-sso-upcoming)
> and [Flow F: AWS credentials after SSO migration](#flow-f-aws-credentials-after-sso-migration-future).

---

## Architecture Overview

All requests pass through API Gateway and a Lambda Authorizer before reaching the Flask/GraphQL app.
The authorizer validates the token and injects auth context (user ID + scopes) for the Flask
middleware to enforce.

```mermaid
flowchart LR
    subgraph Clients
        A[Scientist\ntoshi_auth login]
        B[Runzi / Automation\ntoshi_auth m2m-token]
        C[Legacy client\nx-api-key header]
    end

    subgraph IdP ["Identity Providers"]
        Cog[Cognito User Pool\ngroups + scopes]
        Entra["GNS Entra ID ⟵ upcoming\n(OIDC federation into Cognito)"]
        Entra -. "federated login" .-> Cog
    end

    subgraph AWS
        GW[API Gateway]
        Auth[Lambda Authorizer\nauth/authorizer/handler.py]
        JWKS[(Cognito JWKS\ncached 1h)]
        Flask[Flask App\nGraphQL]
        MW[Middleware\nscope enforcement]
    end

    A -- "toshi_auth login\n→ Bearer JWT" --> Cog
    Cog -- "JWT issued by Cognito\n(always, even after Entra federation)" --> A
    B -- "client_credentials grant\n→ Bearer JWT" --> Cog
    A -- "Authorization: Bearer JWT" --> GW
    B -- "Authorization: Bearer JWT" --> GW
    C -- "x-api-key: <key>" --> GW

    GW --> Auth
    Auth <-.->|"fetch public keys\n(RS256 verification)"| JWKS
    Auth -- "IAM Allow +\n{userId, scopes}" --> GW
    GW -- "request +\nserverless.authorizer context" --> Flask
    Flask --> MW
    MW -- "check toshi/read\ncheck toshi/write\n(mutations only)" --> Flask
```

> **Key point:** Cognito is a permanent component — the Lambda Authorizer always validates
> Cognito-issued JWTs. Entra federation means Cognito *delegates authentication* to GNS Entra,
> but still issues the JWT. The authorizer and middleware are unchanged by the SSO migration.

---

## Flow A: Scientist Interactive Login

> **Current behaviour** (before GNS SSO is wired in). Scientists authenticate with a Toshi-specific
> username and password. See [Flow E](#flow-e-scientist-login-with-gns-sso-upcoming) for what changes
> once Entra is federated.

Scientists authenticate once with username and password. Tokens are stored locally and
auto-refreshed. Works from SSH terminals — no browser required.

```mermaid
sequenceDiagram
    actor S as Scientist
    participant CLI as toshi_auth CLI
    participant Cog as Cognito (cognito-idp)
    participant Creds as ~/.toshi/credentials
    participant GW as API Gateway
    participant Auth as Lambda Authorizer
    participant JWKS as Cognito JWKS
    participant MW as Flask Middleware
    participant GQL as GraphQL

    Note over S,Creds: One-time login
    S->>CLI: toshi_auth login
    CLI->>S: prompt for email + password
    S->>CLI: email, password
    CLI->>Cog: InitiateAuth(USER_PASSWORD_AUTH)<br/>ClientId, USERNAME, PASSWORD
    Cog-->>CLI: AccessToken (JWT, 1h)<br/>IdToken, RefreshToken (30d)
    CLI->>Creds: save tokens (JSON, mode 0600)

    Note over S,GQL: Making an API request
    S->>CLI: toshi_auth token --raw
    CLI->>Creds: load credentials
    alt token expired (< 60s remaining)
        CLI->>Cog: InitiateAuth(REFRESH_TOKEN_AUTH)<br/>ClientId, REFRESH_TOKEN
        Cog-->>CLI: new AccessToken + IdToken
        CLI->>Creds: update credentials
    end
    CLI-->>S: Bearer <access_token>

    S->>GW: POST /graphql<br/>Authorization: Bearer <access_token>
    GW->>Auth: invoke authorizer with request headers

    Auth->>JWKS: GET /.well-known/jwks.json<br/>(cached 1h across warm invocations)
    JWKS-->>Auth: public keys (RS256)
    Auth->>Auth: verify signature, expiry, issuer<br/>token_use must be "access"
    Note over Auth: USER_PASSWORD_AUTH tokens carry<br/>scope "aws.cognito.signin.user.admin"<br/>Effective scopes derived from cognito:groups:<br/>toshi-readers → toshi/read<br/>toshi-writers → toshi/read + toshi/write
    Auth-->>GW: IAM Allow policy +<br/>context {userId, scopes, authMethod:"jwt"}

    GW->>MW: request + serverless.authorizer context
    MW->>MW: read scopes from environ["serverless.authorizer"]<br/>check toshi/read present
    alt GraphQL mutation
        MW->>MW: check toshi/write present
    end
    MW->>GQL: allow request
    GQL-->>S: GraphQL response
```

### Quick Start

```bash
# Login (once)
uv run python auth/toshi_auth.py login

# Inspect your token and group membership
uv run python auth/toshi_auth.py whoami

# Make an API call
TOKEN=$(uv run python auth/toshi_auth.py token --raw)
curl -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     https://<api-url>/graphql \
     -d '{"query":"{ about }"}'
```

---

## Flow B: Automation / Runzi (Machine-to-Machine)

Runzi and other automated pipelines use the OAuth 2.0 Client Credentials grant. There is no
user identity — the token identifies the automation client itself. Tokens last 1 hour and cannot
be refreshed — a new one must be requested when the old one expires.

For jobs shorter than ~50 minutes a single token at startup is sufficient. For long-running jobs
(hours to days) use `ToshiTokenManager` from `nshm-toshi-client`, which handles re-fetch
transparently inside the transport layer — application code never touches tokens directly.

```mermaid
sequenceDiagram
    actor R as Runzi / Automation
    participant CLI as toshi_auth CLI
    participant Tok as Cognito OAuth2<br/>/oauth2/token
    participant GW as API Gateway
    participant Auth as Lambda Authorizer
    participant JWKS as Cognito JWKS
    participant MW as Flask Middleware
    participant GQL as GraphQL

    Note over R,GQL: On first API call (and silently on expiry)
    R->>CLI: ToshiTokenManager.get_token()<br/>(via nshm-toshi-client transport)
    CLI->>Tok: POST /oauth2/token<br/>Authorization: Basic base64(client_id:client_secret)<br/>grant_type=client_credentials<br/>scope=toshi/read toshi/write
    Tok-->>CLI: access_token (JWT, 1h)<br/>(no refresh token)
    CLI-->>R: <access_token> (cached until ~60s before expiry)

    R->>GW: POST /graphql<br/>Authorization: Bearer <access_token>
    GW->>Auth: invoke authorizer with request headers

    Auth->>JWKS: GET /.well-known/jwks.json (cached)
    JWKS-->>Auth: public keys
    Auth->>Auth: verify signature, expiry, issuer<br/>verify client_id claim<br/>scopes read directly from token:<br/>toshi/read toshi/write
    Auth-->>GW: IAM Allow policy +<br/>context {userId: client_id, scopes, authMethod:"jwt"}

    GW->>MW: request + serverless.authorizer context
    MW->>MW: check toshi/read ✓<br/>check toshi/write ✓ (for mutations)
    MW->>GQL: allow request
    GQL-->>R: GraphQL response
```

### Python (all Runzi jobs and scripts)

No application code changes required. Set three environment variables in the job environment
(Batch job definition, CI/CD secrets, or local `.env`) and `nshm-toshi-client` wires up
token management automatically:

| Variable | Sensitivity | Source |
|----------|-------------|--------|
| `NZSHM22_TOSHI_COGNITO_CLIENT_ID` | Low — public | `auth/auth_config.json` |
| `NZSHM22_TOSHI_COGNITO_CLIENT_SECRET` | **High — treat as password** | `auth/.env` (gitignored) |
| `NZSHM22_TOSHI_COGNITO_DOMAIN` | Low — public | `auth/auth_config.json` |

#### Handling `NZSHM22_TOSHI_COGNITO_CLIENT_SECRET`

This secret allows anything that holds it to mint valid API tokens with full read+write access.
It must be handled with the same care as a password:

| Context | How to supply it |
|---------|-----------------|
| AWS Batch job containers | Secrets Manager → env var injection at job start (same pattern as current `NZSHM22_TOSHI_API_SECRET_*`) |
| CI/CD pipelines | GitHub Actions secret (or equivalent) — never in source |
| Local dev | `auth/.env` (gitignored) — already the established pattern |

**Never** put it in `auth_config.json` (committed), directly in a Batch job definition (visible
in AWS console), application code, or log output.

It can be rotated in Cognito at any time without touching application code — just update the
value in Secrets Manager and redeploy. This is an improvement over the current shared `x-api-key`,
which requires a coordinated update across all consumers. Cognito also logs every token issuance,
so any misuse is auditable.

Existing application code continues to work unchanged:

```python
# No changes needed — token management is handled by the library
api = RuptureGenerationTask(API_URL, S3_URL, auth_token=None, headers=None)
```

The client detects the Cognito env vars at startup, creates a `ToshiTokenManager` internally,
and silently re-fetches tokens near expiry. Jobs of any duration work correctly.

### Shell / curl (one-off testing only)

Only use the CLI directly when calling the API outside Python — e.g. manual `curl` tests.
The token is valid for 1 hour; re-run if it expires.

```bash
TOKEN=$(TOSHI_CLIENT_ID=<id> TOSHI_CLIENT_SECRET=<secret> \
        uv run python auth/toshi_auth.py m2m-token --raw)

curl -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     https://<api-url>/graphql \
     -d '{"query":"{ about }"}'
```

---

## Flow C: Legacy x-api-key (Transition Period)

Existing clients using the shared `x-api-key` continue to work unchanged during the migration.
The Lambda Authorizer checks the key against the `LEGACY_API_KEY` environment variable and grants
full read+write access if it matches.

```mermaid
sequenceDiagram
    actor L as Legacy Client
    participant GW as API Gateway
    participant Auth as Lambda Authorizer
    participant MW as Flask Middleware
    participant GQL as GraphQL

    L->>GW: POST /graphql<br/>x-api-key: <shared-key>
    Note right of L: Also accepted:<br/>Authorization: x-api-key <key>

    GW->>Auth: invoke authorizer with request headers
    Auth->>Auth: detect x-api-key header (checked first,<br/>before JWT path)
    Auth->>Auth: compare against LEGACY_API_KEY env var
    Auth-->>GW: IAM Allow policy +<br/>context {userId:"legacy",<br/>scopes:"toshi/read toshi/write",<br/>authMethod:"apikey"}

    GW->>MW: request + serverless.authorizer context
    MW->>MW: check toshi/read ✓<br/>check toshi/write ✓
    MW->>GQL: allow request
    GQL-->>L: GraphQL response
```

> **Note:** The `x-api-key` path will be removed once all clients have migrated to JWT auth.
> Check the changelog for deprecation notices.

---

## Flow D: AWS Credentials via Identity Pool

Scientists who need temporary AWS credentials (for S3, ECR, etc.) can exchange their Cognito
access token for short-lived IAM credentials scoped to their Runzi role.

```mermaid
sequenceDiagram
    actor S as Scientist
    participant CLI as toshi_auth CLI
    participant Creds as ~/.toshi/credentials
    participant CI as Cognito Identity Pool
    participant AWS as ~/.aws/credentials

    S->>CLI: toshi_auth aws-creds
    CLI->>Creds: load access_token<br/>(auto-refresh if < 300s remaining)

    CLI->>CI: get_id(IdentityPoolId,<br/>Logins={cognito-idp.../pool_id: access_token})
    CI-->>CLI: IdentityId

    CLI->>CI: get_credentials_for_identity(IdentityId,<br/>Logins={cognito-idp.../pool_id: access_token})
    Note over CI: Role mapping by Cognito group:<br/>runzi-local → toshi-runzi-local IAM role<br/>runzi-batch → toshi-runzi-batch IAM role<br/>runzi-admin → toshi-runzi-admin IAM role
    CI-->>CLI: AccessKeyId, SecretKey,<br/>SessionToken, Expiration (~1h)

    CLI->>AWS: write [toshi] section<br/>(aws_access_key_id, aws_secret_access_key,<br/>aws_session_token, region)
    AWS-->>S: credentials ready
```

### Quick Start

```bash
# Exchange Cognito token for AWS credentials
uv run python auth/toshi_auth.py aws-creds

# Use the [toshi] profile
export AWS_PROFILE=toshi
aws ecr describe-repositories --region ap-southeast-2
aws s3 ls s3://my-nshm-bucket/
```

> Credentials expire in ~1 hour. Re-run `aws-creds` to refresh.

---

## Flow E: Scientist Login with GNS SSO (upcoming)

Once GNS Entra ID is federated into Cognito (Phase 2), scientists log in with their GNS corporate
credentials via a browser. The `toshi_auth login` command handles the PKCE flow automatically —
the same command, a different exchange underneath.

**What changes for scientists:** browser opens instead of a password prompt.
**What doesn't change:** `toshi_auth token`, `toshi_auth whoami`, `aws-creds`, all API calls —
identical to today. The Lambda Authorizer and middleware are completely unaffected.

```mermaid
sequenceDiagram
    actor S as Scientist
    participant CLI as toshi_auth CLI
    participant Loc as localhost callback<br/>(ephemeral HTTP server)
    participant CogUI as Cognito Hosted UI
    participant Entra as GNS Entra ID<br/>(Azure AD)
    participant Cog as Cognito (cognito-idp)
    participant Creds as ~/.toshi/credentials
    participant GW as API Gateway
    participant Auth as Lambda Authorizer
    participant JWKS as Cognito JWKS

    Note over S,Creds: One-time login (browser-based PKCE flow)
    S->>CLI: toshi_auth login
    CLI->>CLI: generate PKCE code_verifier + code_challenge<br/>spin up localhost:{random_port} callback server
    CLI->>S: open browser to Cognito Hosted UI\n(with code_challenge + redirect_uri=localhost)
    S->>CogUI: browser request
    CogUI->>Entra: redirect to GNS Entra OIDC login
    Note over S,Entra: Scientist logs in with GNS\ncorporate credentials + MFA
    Entra-->>CogUI: OIDC id_token (Entra identity confirmed)
    CogUI->>CogUI: map Entra claims to Cognito user<br/>assign Cognito groups (toshi-readers / toshi-writers)
    CogUI-->>Loc: redirect to localhost with authorization code
    Loc-->>CLI: receive authorization code
    CLI->>Cog: POST /oauth2/token<br/>grant_type=authorization_code<br/>code + code_verifier (PKCE exchange)
    Cog-->>CLI: AccessToken (JWT, 1h)<br/>IdToken, RefreshToken (30d)
    CLI->>Creds: save tokens (JSON, mode 0600)

    Note over S,JWKS: API requests — identical to Flow A from here
    S->>GW: POST /graphql<br/>Authorization: Bearer <access_token>
    GW->>Auth: invoke authorizer
    Auth->>JWKS: fetch public keys (cached)
    JWKS-->>Auth: RS256 public keys
    Auth->>Auth: verify JWT — issuer is still Cognito\n(not Entra — Cognito issues the token)
    Auth-->>GW: IAM Allow + {userId, scopes, authMethod:"jwt"}
    Note over GW,Auth: Lambda Authorizer unchanged —\nit only ever sees Cognito-issued JWTs
```

### SSH / headless fallback

For terminals without a browser (remote servers, HPC):

```bash
toshi_auth login --no-browser
# Prints: Open this URL in a browser: https://toshi-auth.xxx.auth.../login?...
# Paste the redirected localhost URL back when prompted
```

### Quick Start (after SSO is live)

```bash
# Login — browser opens to GNS SSO
uv run python auth/toshi_auth.py login

# Everything else identical to today
uv run python auth/toshi_auth.py whoami
TOKEN=$(uv run python auth/toshi_auth.py token --raw)
curl -H "Authorization: Bearer $TOKEN" https://<api-url>/graphql -d '{"query":"{ about }"}'
```

---

## Flow F: AWS Credentials after SSO Migration (future)

Currently, `toshi_auth aws-creds` exchanges a Cognito token for temporary STS credentials via
the Cognito Identity Pool (Flow D). Once the IT team completes Entra ↔ IAM Identity Center
federation, scientists can use the standard `aws sso login` instead — one less custom command.

**Cognito remains permanent.** This migration only affects how AWS service credentials (S3, ECR,
Batch) are obtained. The Toshi API JWT flow is unchanged in both current and future states.

```mermaid
flowchart TB
    subgraph Now ["Now — Cognito Identity Pool (Flow D)"]
        direction LR
        N1["toshi_auth login\n→ Cognito JWT"] --> N2["toshi_auth aws-creds\n→ Cognito Identity Pool\n→ STS AssumeRoleWithWebIdentity"]
        N2 --> N3["~/.aws/credentials\n[toshi] section"]
        N3 --> N4["AWS_PROFILE=toshi\naws / boto3"]
    end

    subgraph Future ["Future — IAM Identity Center"]
        direction LR
        F1["toshi_auth login\n→ Cognito JWT\n(unchanged)"] --> F2["aws sso login --profile nshm\n→ IAM Identity Center\n→ STS via Permission Sets"]
        F2 --> F3["~/.aws/credentials\n[nshm] section"]
        F3 --> F4["AWS_PROFILE=nshm\naws / boto3"]
    end

    Now -- "IT team completes\nEntra ↔ IAM Identity Center\nfederation" --> Future
```

### What triggers the migration

- IT team federates Entra into IAM Identity Center (their task, their timeline)
- IT team creates Permission Sets matching the policies in `auth/iam_roles.py`
- Scientists switch one command: `toshi_auth aws-creds` → `aws sso login --profile nshm`
- `toshi_auth login` for Toshi API access is **unchanged throughout**

### Why not start with IAM Identity Center

The Identity Center approach requires IT team to complete Entra federation before anyone can get
AWS credentials. The Cognito Identity Pool path (Flow D) gives the team full AWS service access
now, with a clean handover when IT team is ready. See `auth/IDP_INTEGRATION_OPTIONS_STUDY.md`
for the full trade-off analysis.

---

## Scopes Reference

| Scope | Required for |
|-------|-------------|
| `toshi/read` | All GraphQL queries |
| `toshi/write` | GraphQL mutations (create/update operations) |

Scopes are granted based on Cognito group membership:

| Group | Scopes granted |
|-------|---------------|
| `toshi-readers` | `toshi/read` |
| `toshi-writers` | `toshi/read` + `toshi/write` |

---

## Token Reference

| Token | Lifetime | Refreshable | Stored at |
|-------|---------|------------|-----------|
| Scientist access token | 1 hour | Yes (via refresh token) | `~/.toshi/credentials` |
| Scientist refresh token | 30 days | N/A | `~/.toshi/credentials` |
| M2M access token | 1 hour | No — re-request on expiry | Cached in `ToshiTokenManager` (in-process) |
| AWS temp credentials (now) | ~1 hour | No — re-run `aws-creds` | `~/.aws/credentials [toshi]` |
| AWS SSO credentials (future) | ~8 hours | Auto (sso-session) | `~/.aws/sso/cache/` |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `401 Unauthorized` | Token missing, expired, or invalid signature | Re-run `toshi_auth login` or `m2m-token` |
| `403 Missing required scope: toshi/read` | User not in `toshi-readers` or `toshi-writers` group | Ask an admin to add you to the correct Cognito group |
| `403 GraphQL mutations require scope: toshi/write` | User is in `toshi-readers` only | Ask an admin to add you to `toshi-writers` |
| CORS error on token fetch | Cognito `/oauth2/token` has no CORS headers | Run from a DevTools console on a `localhost` tab, not from a page origin |
| `aws-creds` fails with no credentials | Not logged in, or token too stale to auto-refresh | Re-run `toshi_auth login` first |
| Browser doesn't open on `toshi_auth login` (after SSO) | Headless terminal or browser launch failed | Use `toshi_auth login --no-browser` and paste the URL |
| Login redirects to Entra but fails with account error | GNS Entra account not provisioned or MFA not set up | Contact IT team |
| Entra login succeeds but API returns 403 | Cognito group not assigned for your account | Contact dev team admin to assign `toshi-readers` or `toshi-writers` group |

---

## Local Development

Auth enforcement is **bypassed** when `SLS_OFFLINE=1` or `TESTING=1`. Local dev and test runs
are unaffected — the middleware sets a synthetic user `{userId: "local-dev", scopes: {toshi/read, toshi/write}}`.

```bash
# Local stack — no auth required
yarn sls dynamodb start --stage local &
yarn sls s3 start &
uv run yarn sls wsgi serve   # Flask on http://localhost:5000/graphql
```
