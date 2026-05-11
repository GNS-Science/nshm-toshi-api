# auth/ — JWT Authentication for nshm-toshi-api

Replaces the single shared `x-api-key` with per-user Cognito JWTs, while maintaining
backward compatibility with legacy API key clients during the transition.

## Architecture

```
Client (Runzi pipeline / scientist CLI / browser)
    │
    │  Authorization: Bearer <JWT>          (or legacy: x-api-key <key>)
    ▼
API Gateway
    │
    ├── Lambda Authorizer (auth/authorizer/handler.py)
    │     - Validates JWT signature, expiry, issuer against Cognito JWKS
    │     - Falls back to legacy x-api-key for backward compat (LEGACY_API_KEY env var)
    │     - Returns IAM Allow/Deny + {userId, scopes, authMethod} context
    ▼
Flask app (graphql_api/api.py)
    │
    ├── before_request middleware (auth/middleware.py)
    │     - Reads {userId, scopes} from request context set by the authorizer
    │     - Requires toshi/read for all GraphQL requests
    │     - Requires toshi/write for GraphQL mutations (AST-based detection)
    │     - No-op when TESTING=1 or SLS_OFFLINE=1
    ▼
GraphQL resolvers / mutations (graphql_api/schema/)
```

## Key Components

| File | Purpose |
|------|---------|
| `authorizer/handler.py` | Lambda Authorizer — validates JWTs (access tokens only), returns IAM policy |
| `middleware.py` | Flask before_request hook — enforces read/write scopes via AST-based mutation detection |
| `tests/test_handler.py` | Unit tests for the Lambda Authorizer (26 tests) |
| `tests/test_middleware.py` | Unit tests for mutation detection and scope enforcement (12 tests) |
| `tests/test_e2e.py` | End-to-end validation script (`--local` or `--remote` mode) |
| `toshi_auth.py` | Scientist CLI — login, token, aws-creds commands |
| `create_users.py` | Creates test users in the deployed User Pool |

Cognito and IAM resources are provisioned by `serverless.yml` (CloudFormation). No separate
provisioning scripts needed — `sls deploy` creates everything.

## Token Flows

**Scientists (interactive):** `USER_PASSWORD_AUTH` via `toshi_auth.py login`. Token saved to
`~/.toshi/credentials`, auto-refreshed. No browser required (works from SSH terminals).

**Automation / Runzi:** OAuth 2.0 Client Credentials grant via `toshi_auth.py m2m-token`.
No user identity — the JWT `sub` is the client ID. Request a fresh token at the start of
each job (1h lifetime, not refreshable).

**Legacy clients:** Pass `x-api-key: <key>` header or `Authorization: x-api-key <key>`.
Accepted by the Lambda Authorizer during the transition period via `LEGACY_API_KEY` env var.

## Scopes

| Scope | Required for |
|-------|-------------|
| `toshi/read` | All GraphQL queries |
| `toshi/write` | GraphQL mutations |

Scopes are derived from Cognito group membership for interactive users
(`toshi-readers` → read only, `toshi-writers` → read + write).
M2M tokens request scopes explicitly in the client credentials grant.

## Configuration

### Environment variables (Lambda Authorizer)

| Variable | Required | Source |
|----------|----------|--------|
| `COGNITO_USER_POOL_ID` | Yes | Auto-set from `!Ref ToshiUserPool` in `serverless.yml` |
| `COGNITO_REGION` | Yes | `provider.region` in `serverless.yml` |
| `COGNITO_CLIENT_ID` | No | Auto-set from `!Ref ToshiScientistClient` in `serverless.yml` |
| `LEGACY_API_KEY` | No | Set in `.env` — accepts this value as a valid x-api-key |

### Local config files

- **`auth/.env`** (gitignored) — contains `TOSHI_CLIENT_SECRET` for M2M flow. Fetch from
  AWS after deploy (see `IMPLEMENTATION_PLAN.md` Phase 1 step 3).
- **`test_users.json`** (gitignored) — user definitions for `create_users.py`.
  Each entry: `{"username": "...", "password": "...", "groups": [...]}`.

Pool IDs and client IDs are available from `sls info --verbose` after deploy.

## Local Development

The middleware is a **no-op** when `SLS_OFFLINE=1` or `TESTING=1`, so local dev and tests
are unaffected.

```bash
# Run local stack (auth enforcement bypassed)
yarn sls dynamodb start --stage local &
yarn sls s3 start &
uv run yarn sls wsgi serve
```

## Setup (new environment)

```bash
# 1. Deploy — provisions all Cognito + IAM resources
aws sso login --profile AdministratorAccess-595842668254
AWS_PROFILE=AdministratorAccess-595842668254 uv run serverless deploy --stage dev

# 2. Fetch automation client secret (once)
aws cognito-idp describe-user-pool-client \
    --user-pool-id <UserPoolId> --client-id <AutomationClientId> \
    --profile AdministratorAccess-595842668254 \
    --query 'UserPoolClient.ClientSecret' --output text
# Save result to auth/.env as: TOSHI_CLIENT_SECRET=<secret>

# 3. Create test users
python auth/create_users.py --profile AdministratorAccess-595842668254

# 4. Test login
uv run python auth/toshi_auth.py login
uv run python auth/toshi_auth.py aws-creds
```

See `IMPLEMENTATION_PLAN.md` for detailed setup history and deployment notes.
