# Cognito permission model — reference

A condensed walk-through of how `nshm-toshi-api` translates Cognito identity into permissions, covering three independent systems that all read the same Cognito user pool. All file:line references point at the `deploy-test` branch.

## TL;DR — three permission systems, one identity

| System | Permission tokens | Configured by | Consumed by |
|---|---|---|---|
| **GraphQL API scopes** | `toshi/read`, `toshi/write` | (a) group membership for users via `USER_PASSWORD_AUTH`, OR (b) OAuth `scope` claim for OAuth-code-flow users and M2M clients | `auth/authorizer/handler.py` → `auth/middleware.py` |
| **AWS resource access** | IAM role attached via Identity Pool | `runzi-*` group membership + Identity Pool role-mapping rules | `serverless.yml::ToshiIdentityPoolRoleAttachment` |
| **Caller allowlist (audience)** | `client_id` claim must be in allowlist | Lambda env var `COGNITO_CLIENT_ID` (comma-separated) | `auth/authorizer/handler.py::validate_cognito_token` — the `allowed_ids` audience check |

The three systems are *disjoint by design* — adding a user to a `toshi-*` group never affects their IAM role, and vice versa.

---

## Q1: Where are the permissions set for a particular Cognito group?

There are two things that look like "group permissions" — keep them separate.

### Group existence (just declares the group)

Five `AWS::Cognito::UserPoolGroup` resources in `serverless.yml` — `ToshiGroupWriters`, `ToshiGroupReaders`, `ToshiGroupRunziLocal`, `ToshiGroupRunziBatch`, `ToshiGroupRunziAdmin`:

```yaml
ToshiGroupWriters:    { GroupName: toshi-writers   }
ToshiGroupReaders:    { GroupName: toshi-readers   }
ToshiGroupRunziLocal: { GroupName: runzi-local     }
ToshiGroupRunziBatch: { GroupName: runzi-batch     }
ToshiGroupRunziAdmin: { GroupName: runzi-admin     }
```

These resources do not grant any permissions on their own — they only make the group name valid in the user pool.

### Group → API scope mapping (hardcoded in code)

`auth/authorizer/handler.py::validate_cognito_token` — the `aws.cognito.signin.user.admin` branch:

```python
if 'aws.cognito.signin.user.admin' in scopes:
    groups = payload.get('cognito:groups', [])
    toshi_scopes = []
    if 'toshi-readers' in groups or 'toshi-writers' in groups:
        toshi_scopes.append('toshi/read')
    if 'toshi-writers' in groups:
        toshi_scopes.append('toshi/write')
    scopes = ' '.join(toshi_scopes) if toshi_scopes else scopes
```

This is the **only** code that turns group membership into API scopes, and it only fires for `USER_PASSWORD_AUTH` tokens (whose `scope` claim is literally `aws.cognito.signin.user.admin`). It recognises exactly two groups:

| Cognito group | API scopes granted |
|---|---|
| `toshi-readers` | `toshi/read` |
| `toshi-writers` | `toshi/read` + `toshi/write` |

Membership in `runzi-*` groups grants **zero** API scopes — those groups only matter to the Identity Pool role mapping below. Also documented at `docs/AUTH_GUIDE.md` § "Scopes Reference".

### Group → IAM role mapping (a different permission system)

`serverless.yml::ToshiIdentityPoolRoleAttachment` — Cognito Identity Pool role-mapping rules:

```yaml
ToshiIdentityPoolRoleAttachment:
  Type: AWS::Cognito::IdentityPoolRoleAttachment
  Properties:
    Roles:
      authenticated: !GetAtt ToshiRunziLocalRole.Arn
    RoleMappings:
      ToshiProvider:
        Type: Rules
        AmbiguousRoleResolution: AuthenticatedRole
        RulesConfiguration:
          Rules:
            - Claim: cognito:groups
              MatchType: Contains
              Value: runzi-local
              RoleARN: !GetAtt ToshiRunziLocalRole.Arn
            - Claim: cognito:groups
              MatchType: Contains
              Value: runzi-batch
              RoleARN: !GetAtt ToshiRunziBatchRole.Arn
            - Claim: cognito:groups
              MatchType: Contains
              Value: runzi-admin
              RoleARN: !GetAtt ToshiRunziAdminRole.Arn
```

These rules are evaluated **in order**; the first match wins. The IAM role's policies (defined elsewhere in `serverless.yml`) determine what AWS resources the user can touch. This pathway grants **no API access** — only direct AWS resource access via STS temporary credentials.

### To add a new permission level for the API

You'd need both:
1. Define the group (`AWS::Cognito::UserPoolGroup`) in `serverless.yml`
2. Add a branch in `auth/authorizer/handler.py::validate_cognito_token` (the `aws.cognito.signin.user.admin` branch) mapping the new group name to one of the existing scopes (or to a new scope, which also requires adding it to `serverless.yml::ToshiResourceServer`)

---

## Q2: A user that can read/write the API AND perform AWS resource operations

Cognito users can belong to multiple groups, and the two permission systems consume **disjoint** sets of group names. Combining them is just multi-group membership.

The codebase has a worked example in the module docstring of `auth/create_users.py`:

```python
"groups": ["toshi-writers", "runzi-local"]
```

For a user who needs API read/write + Runzi-local AWS access:

```bash
aws cognito-idp admin-add-user-to-group \
  --user-pool-id <pool> --username <user> --group-name toshi-writers

aws cognito-idp admin-add-user-to-group \
  --user-pool-id <pool> --username <user> --group-name runzi-local
```

### How the user obtains both kinds of credential

A single login produces two artefacts derived from the same authentication:

1. **Access token** → `Authorization: Bearer <token>` to the GraphQL API. The authorizer sees `cognito:groups: ["toshi-writers", "runzi-local"]` and grants `toshi/read toshi/write` (the `runzi-local` is invisible to the API).
2. **AWS temporary credentials** → obtained by exchanging the **ID token** at the Cognito Identity Pool via `GetCredentialsForIdentity`. The role-mapping rules in `serverless.yml::ToshiIdentityPoolRoleAttachment` match `runzi-local` and hand back credentials for `ToshiRunziLocalRole`.

The Identity Pool ID is exported as `serverless.yml::Outputs.IdentityPoolId`.

### One subtlety: multiple `runzi-*` groups

If a user is in two `runzi-*` groups (e.g. both `runzi-local` and `runzi-batch`), the role-mapping rules are evaluated in order and the **first match wins**. `runzi-local` is listed first, so it would always shadow `runzi-batch` for that user. `AmbiguousRoleResolution: AuthenticatedRole` is the fallback (which is `ToshiRunziLocalRole`, per `serverless.yml::ToshiIdentityPoolRoleAttachment.Properties.Roles.authenticated`). This doesn't bite mixed `toshi-*` + single `runzi-*` setups — only when stacking `runzi-*` groups.

---

## Q3: M2M operations — how do client_id/client_secret in Secrets Manager map into API permissions?

Completely different path from users — no Cognito groups involved at all.

The `{client_id, client_secret}` in Secrets Manager are credentials for a specific Cognito app client. That app client's `AllowedOAuthScopes` allow-list is the **only** thing that determines what scopes its tokens can carry.

### The baseline automation client

`serverless.yml::ToshiAutomationClient`:

```yaml
ToshiAutomationClient:
  Type: AWS::Cognito::UserPoolClient
  DependsOn: ToshiResourceServer
  Properties:
    ClientName: toshi-automation
    GenerateSecret: true
    AllowedOAuthFlows: [ client_credentials ]
    AllowedOAuthScopes:
      - toshi/read
      - toshi/write
    AllowedOAuthFlowsUserPoolClient: true
```

Each additional M2M caller is minted by `auth/create_m2m_secret.py::main` (the `cognito.create_user_pool_client(...)` call) using the same shape, defaulting to `toshi/read toshi/write`. Pass `--scopes "toshi/read"` for a read-only M2M caller.

The Secrets Manager container itself (`serverless.yml::ToshiM2MSecret`) just stores the `{client_id, client_secret}` JSON — it carries no permission information.

### Runtime flow

1. **Caller fetches the secret** from Secrets Manager (typically via `nshm_toshi_client.ToshiTokenManager`, pointed at `NZSHM22_TOSHI_M2M_SECRET_ARN`).
2. **POST to Cognito's `/oauth2/token`** with HTTP Basic auth (client_id:client_secret), `grant_type=client_credentials`, and the desired `scope=toshi/read toshi/write`.
3. **Cognito issues an access token** whose `scope` claim contains the intersection of (requested scopes, `AllowedOAuthScopes`). The token has:
   - `token_use=access`
   - `client_id=<this client>`
   - **No** `cognito:groups`
   - **No** `username`
4. **Authorizer validation** (`auth/authorizer/handler.py::validate_cognito_token`):
   - Signature, issuer, expiry, and `token_use=access` checks pass (same as user path).
   - **Client allowlist check** (the `allowed_ids` audience check in `validate_cognito_token`): the M2M client's `client_id` must be in the authorizer's `COGNITO_CLIENT_ID` env var — otherwise `InvalidAudienceError` → 401. The final `click.echo` "Reminder" block in `auth/create_m2m_secret.py::main` explicitly reminds you of this.
   - The `aws.cognito.signin.user.admin` branch in `validate_cognito_token` is **skipped** (M2M tokens never carry that scope). The raw `scope` claim becomes the effective scopes directly — no group derivation.
5. **Middleware** (`auth/middleware.py::check_auth`) enforces the same scope rules as for users: `toshi/read` for queries, `toshi/write` for mutations.

### Where M2M permissions are actually defined

Two places, in order of authority:

1. **Cognito app client `AllowedOAuthScopes`** (the ceiling — set at client creation)
2. **The token request's `scope` parameter** (what the caller actually asks for, must be ⊆ ceiling)

The Secrets Manager entry encodes **neither** — it just carries credentials.

### M2M and AWS resource access

M2M clients **cannot** access AWS resources via the Cognito Identity Pool path. They aren't tied to a Cognito user, can't go through `GetCredentialsForIdentity`, and have no `cognito:groups`. An M2M caller that needs direct AWS access (e.g. reading S3) must get those permissions from a different source — typically its own IAM role on the machine running the caller (Lambda execution role, EC2 instance profile, etc.).

---

## Quick decision matrix

| You want… | Add to / configure |
|---|---|
| User can run GraphQL queries | Cognito group `toshi-readers` |
| User can run GraphQL queries + mutations | Cognito group `toshi-writers` |
| User can also touch AWS resources from their own machine | Additionally add `runzi-local` / `runzi-batch` / `runzi-admin` |
| New service/script needs API access (no human) | `auth/create_m2m_secret.py --scopes "toshi/read toshi/write"`, store the returned ARN in `NZSHM22_TOSHI_M2M_SECRET_ARN`, add the new `client_id` to authorizer `COGNITO_CLIENT_ID` allowlist |
| New service should be read-only | Same, but `--scopes "toshi/read"` |
| New service also needs direct AWS access | Give the *host* (Lambda, EC2, etc.) its own IAM role — Cognito M2M won't help here |

## Diagnostic shortcuts

| Symptom | Likely cause | Where to look |
|---|---|---|
| `401 Unauthorized` | Token invalid (expired/signature/issuer), wrong `token_use`, or `client_id` not in `COGNITO_CLIENT_ID` allowlist | Lambda authorizer CloudWatch logs |
| `403 Missing required scope: toshi/read` | User not in `toshi-readers`/`toshi-writers`, or M2M client requested fewer scopes than needed | Decode the JWT, check `cognito:groups` and `scope` claims |
| `403 GraphQL mutations require scope: toshi/write` | User in `toshi-readers` only, or M2M token didn't include `toshi/write` | Same — decode the JWT |
| Token validates but AWS resource calls fail | `cognito:groups` lacks a `runzi-*` entry, or the Identity Pool role mapping doesn't cover the resource | `serverless.yml::ToshiIdentityPoolRoleAttachment`, then the IAM role policy itself |

Decode a JWT with:

```bash
echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | python -m json.tool
```

## Key files referenced

- `auth/authorizer/handler.py::validate_cognito_token` + `auth/authorizer/handler.py::handler` — JWT validation + scope derivation
- `auth/middleware.py::check_auth` — scope enforcement (the only source of 403)
- `auth/create_m2m_secret.py::main` — mint M2M client + populate SM secret
- `auth/create_users.py` — reference example of multi-group user setup (see module docstring)
- `serverless.yml::ToshiResourceServer` — defines `toshi/read`, `toshi/write` scopes
- `serverless.yml::ToshiScientistClient` + `serverless.yml::ToshiAutomationClient`
- `serverless.yml` — `AWS::Cognito::UserPoolGroup` resources (`ToshiGroupWriters`, `ToshiGroupReaders`, `ToshiGroupRunziLocal`, `ToshiGroupRunziBatch`, `ToshiGroupRunziAdmin`)
- `serverless.yml::ToshiIdentityPoolRoleAttachment` — Identity Pool role-mapping rules
- `serverless.yml::ToshiM2MSecret` — Secrets Manager container
- `docs/AUTH_GUIDE.md` — the canonical user-facing auth guide
