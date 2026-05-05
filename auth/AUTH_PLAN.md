# SPIKE: Modern Auth for nshm-toshi-api

## Context

The API currently uses a single shared `x-api-key` secret distributed to all clients. It is explicitly `TempApiKey` in `serverless.yml` ("Api key until we have an auth function"). The goal is to replace this with per-user/per-service JWT auth that scales to more scientists making mutations from Runzi jobs.

**Key constraints from discovery:**
- GNS is migrating to AWS IAM Identity Center + Azure AD (Entra ID) — imminent but Azure AD integration not yet complete
- User has a second AWS account with IAM Identity Center partially set up to SPIKE into
- Runzi runs in **two environments**: AWS compute (EC2/Lambda/Batch — can use IAM roles) and local/HPC machines (needs stored credentials)
- `requests-aws4auth` is already in the codebase (used for Elasticsearch auth)

---

## Recommended Architecture

### Two-layer auth model

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

### Identity Provider: AWS Cognito User Pool (now) → federate to IAM Identity Center (soon)

**Why Cognito first**: IAM Identity Center doesn't yet have Azure AD wired up. Cognito User Pool acts as the token issuer with Toshi-specific scopes. Once IAM Identity Center + Azure AD is live, we add it as a SAML/OIDC federation source to the Cognito pool — the Lambda authorizer and Flask middleware don't change.

### Token Flows by Client Type

| Client | Flow | Credential | Notes |
|--------|------|-----------|-------|
| Scientists (interactive) | OAuth 2.0 Device Authorization Grant (RFC 8628) | Username + password in browser | CLI prints URL+code; works from SSH/terminals |
| Runzi on AWS (EC2/Lambda/Batch) | Client Credentials + Secrets Manager | `client_id/secret` stored in AWS Secrets Manager | IAM role reads secret; no hardcoded creds |
| Runzi local / HPC | Client Credentials | `client_id/secret` in env vars or `~/.toshi/credentials` | Same Cognito app client as above |

### Cognito Scopes
- `toshi/read` — allows GraphQL queries only
- `toshi/write` — allows GraphQL mutations (superset of read)

*(Future: `toshi/admin` for schema migrations, bulk operations)*

### IAM Identity Center Migration Path
When IAM Identity Center + Azure AD is ready: add as SAML/OIDC external IdP to the Cognito User Pool. Scientists then authenticate transparently with GNS Microsoft credentials. JWT issuer stays the same; nothing else changes.

---

## SPIKE Scope

Self-contained in this `auth/` directory. Uses the user's second AWS account with IAM Identity Center. Proves the end-to-end flow before committing to a production implementation.

### Deliverable 1: Cognito Setup Script
**`auth/cognito_setup.py`** — boto3 script to create all Cognito resources:
- User Pool with `toshi` resource server + `read`/`write` scopes
- App client for scientists (Device Authorization Grant, public client — no secret)
- App client for automation (Client Credentials, confidential client)
- 2–3 test users

Run once: `python auth/cognito_setup.py --profile <your-aws-profile>`. Outputs config as JSON for use in subsequent steps.

### Deliverable 2: Scientist CLI Tool
**`auth/toshi_auth.py`** — standalone Python script (uses `click` already in dev deps):

```
python toshi_auth.py login         # Device flow: prints URL+code, polls, saves token
python toshi_auth.py token         # Prints current Bearer token (auto-refreshes)
python toshi_auth.py whoami        # Decodes + prints JWT claims (user, scopes, expiry)
python toshi_auth.py m2m-token     # Client credentials flow for Runzi/automation
```

Token storage: `~/.toshi/credentials` (JSON). Uses `requests` + `PyJWT` (new dep).

### Deliverable 3: Lambda Authorizer
**`auth/authorizer/handler.py`** — standalone Python Lambda function:

- Accepts `Authorization: Bearer <token>` header OR legacy `x-api-key` (backward compat)
- Fetches Cognito JWKS from `https://cognito-idp.<region>.amazonaws.com/<pool_id>/.well-known/jwks.json` (cached in-process between warm invocations)
- Validates: signature, expiry, issuer (`iss`), `client_id` audience, `token_use` (access only)
- Returns: IAM policy (Allow/Deny) + context `{"userId": "...", "scopes": "toshi/read toshi/write"}`
- On failure: raises `Exception("Unauthorized")` (API Gateway returns 401)

Also adds to **`serverless.yml`**: an `authorizer:` block on the POST/GET `graphql` events, replacing `private: true`.

### Deliverable 4: Flask Middleware
**`auth/middleware.py`** — prototype `before_request` hook for `graphql_api/api.py`:

- Reads `userId` and `scopes` from headers injected by the Lambda authorizer
- Parses raw request body to detect if the GraphQL operation is a query or mutation
- Raises HTTP 403 if a mutation is requested without `toshi/write` scope
- Sets `flask.g.current_user` for future use in resolvers
- **No-op when `TESTING=1` or `SLS_OFFLINE=1`** to preserve local dev workflow

### Deliverable 5: End-to-End Validation Script
**`auth/test_e2e.py`** — verifies all flows:

1. Device Flow login → token acquired
2. `toshi/read` token → GraphQL query succeeds
3. `toshi/read` token → GraphQL mutation blocked (403)
4. `toshi/write` token → GraphQL mutation succeeds
5. M2M client credentials → mutation succeeds
6. Expired/invalid token → 401 from authorizer

---

## Files to Create / Modify

| File | Action |
|------|--------|
| `auth/README.md` | Setup instructions + findings log |
| `auth/cognito_setup.py` | boto3 Cognito provisioning script |
| `auth/toshi_auth.py` | Scientist CLI tool |
| `auth/authorizer/handler.py` | Lambda authorizer |
| `auth/authorizer/requirements.txt` | `PyJWT`, `cryptography` (authorizer deps) |
| `auth/middleware.py` | Flask middleware prototype |
| `auth/test_e2e.py` | End-to-end validation |
| `serverless.yml` | Add `authorizer:` to graphql events; remove `private: true` |
| `graphql_api/api.py` | Wire in `middleware.py` as `before_request` |
| `pyproject.toml` | Add `PyJWT` to dev deps |

---

## Key Questions the SPIKE Must Answer

1. **Latency**: Lambda authorizer cold-start overhead — acceptable for interactive use? (hot path should be <10ms)
2. **Token lifetime in long Runzi jobs**: 1-hour Cognito tokens expire mid-job — does `toshi_auth.py m2m-token` auto-refresh work reliably?
3. **Device Flow UX**: Test on SSH terminal — is it genuinely simple enough for scientists?
4. **IAM Identity Center SAML federation**: Once Azure AD is connected, how complex is adding it as a Cognito IdP? (Verify in the test account)
5. **Backward compat**: Can `x-api-key` clients continue working transparently during transition? Authorizer should accept both forms temporarily.

---

## What's NOT in the SPIKE

- Full CDK/CloudFormation/Terraform IaC for Cognito
- Admin user management UI or self-service registration
- GNS corporate SSO / Azure AD integration (follow-on, once IAM Identity Center is live)
- Token revocation / logout flows
- Production deployment to any live stage
- Per-resolver authorization (field-level, role-based) — middleware covers operation-level for now

---

## Verification

```bash
# 1. Provision Cognito in the test AWS account
python auth/cognito_setup.py --profile test-account

# 2. Test scientist interactive flow
python auth/toshi_auth.py login
python auth/toshi_auth.py whoami

# 3. Start local stack
yarn sls dynamodb start --stage local &
yarn sls s3 start &
poetry run yarn sls wsgi serve

# 4. Run end-to-end validation
python auth/test_e2e.py

# 5. Manual: test GraphQL playground with Bearer token
# open http://localhost:5000/graphql, set Authorization header
```

---

## Follow-on Work (Post-SPIKE, Not In Scope Now)

- Full IaC for Cognito provisioning
- Integrate IAM Identity Center SAML → Cognito federation
- Move `toshi_auth` CLI into `nshm-toshi-client` package
- Add `toshi/admin` scope; formal deprecation timeline for `x-api-key`
- Federate Cognito with IAM Identity Center once Azure AD is wired
