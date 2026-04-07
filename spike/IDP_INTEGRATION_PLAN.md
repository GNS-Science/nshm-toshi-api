# SSO Integration Plan — nshm-toshi-api

## Context

The existing auth spike proved out JWT-based access control for Toshi API using a Cognito User Pool with a Lambda Authorizer. The next step is to:

1. **Federate GNS Azure AD (Entra ID) as the authentication IdP** — scientists log in with GNS corporate credentials; no separate Toshi password.
2. **Extend the identity system beyond Toshi API** — Runzi users also need temporary AWS credentials (Batch, ECR) tied to the same identity.
3. **Dev team retains full control** — all authorization infrastructure lives in our own account. IT team's only involvement is a one-time Entra App Registration.

> **Options considered and migration path:** See `IDP_INTEGRATION_OPTIONS_STUDY.md` for the full options analysis (IAM Identity Center, Entra Direct, Cognito), pros/cons, and the step-by-step migration path from Cognito Identity Pool to IAM Identity Center when IT team is ready.

---

## Target Architecture

```
GNS Entra ID (Azure AD)
    │
    └── Cognito User Pool  (OIDC federation via our own Entra App Registration)
            │
            ├── JWT Bearer token  →  API Gateway → Lambda Authorizer → Toshi Flask API
            │
            └── Cognito Identity Pool  →  STS AssumeRoleWithWebIdentity
                    →  IAM roles in our account  (Batch, ECR, S3)
```

**Single login, two tokens:**
```bash
toshi_auth login        # browser → GNS Entra login → Cognito JWT + STS creds cached locally
toshi_auth whoami       # show identity, groups, token expiry
toshi_auth aws-creds    # write STS creds to ~/.aws/credentials [toshi]
```

**M2M (Batch task containers):**
- IAM Task Roles on Batch job definitions — no SSO, no Cognito
- Toshi API calls from jobs: existing client credentials flow (unchanged)

**Future — IAM Identity Center (optional migration, IT team's pace):**
- When IT team completes Entra ↔ IAM Identity Center federation, scientists can also use `aws sso login`
- Cognito path remains and coexists — no forced migration
- IT team creates a separate Entra App Registration for their IAM Identity Center federation; ours is unaffected

---

## Admin Boundaries

| Responsibility | Owner | Notes |
|---|---|---|
| Entra App Registration (Cognito) | IT team | One-time ask: provide `client_id`, `tenant_id`, approve redirect URI |
| User identities, MFA, password policy | IT team (Entra) | Their domain throughout |
| Cognito User Pool — groups, app clients, IdP config | Dev team | Fully independent |
| Cognito Identity Pool — role mappings | Dev team | Fully independent |
| IAM roles + policies (Batch, ECR, S3) | Dev team | In our own account |
| Lambda Authorizer + Flask middleware | Dev team | Unchanged from spike |
| IAM Identity Center Permission Sets (future) | IT team | Separate path, separate timeline |

**One-time ask to IT team:**
> "Please create an App Registration in Entra ID for our AWS Cognito integration. We need the `client_id` and `tenant_id`. The redirect URI will be `https://{cognito_domain}.auth.ap-southeast-2.amazoncognito.com/oauth2/idpresponse`."

That is the only external dependency.

---

## Personas & IAM Permissions

> **Single source of truth:** `spike/auth/iam_roles.py` in this repo is the canonical definition of all runzi user permissions — covering both Toshi API access (via Cognito groups) and AWS service permissions (IAM role policies). The `nzshm-runzi` repo should reference this rather than maintaining its own scattered IAM docs.

| Persona | Cognito Group | Toshi Scope | IAM Role | AWS Permissions summary |
|---|---|---|---|---|
| Read-only scientist | `toshi-readers` | toshi/read | — | — |
| Writer scientist | `toshi-writers` | toshi/read+write | — | — |
| Runzi local | `runzi-local` | toshi/read+write | `toshi-runzi-local` | ECR list/pull, S3 read/write |
| Runzi batch | `runzi-batch` | toshi/read+write | `toshi-runzi-batch` | + Batch submit/describe |
| Runzi admin | `runzi-admin` | toshi/read+write | `toshi-runzi-admin` | + Batch configure, ECR push/create |
| M2M pipeline | — | toshi/read+write | IAM Task Role | Scoped S3 + Toshi invoke |

### IAM role policies

Permissions derived from actual `nzshm-runzi` usage (boto3 calls in `runzi/aws/`, Docker docs). Regions: `us-east-1` (ECR, Batch, Secrets Manager — current runzi setup) and `ap-southeast-2` (S3, Toshi API).

**`toshi-runzi-local`** — local workstation use
- ECR: `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer`, `ecr:DescribeRepositories`, `ecr:ListImages`
- S3: `s3:GetObject`, `s3:PutObject`, `s3:ListBucket`, `s3:PutObjectAcl` on report buckets + jars bucket
- Secrets Manager (transitional): `secretsmanager:GetSecretValue` on `NZSHM22_TOSHI_API_SECRET_*` — deprecated once JWT M2M is live

**`toshi-runzi-batch`** — all of above, plus:
- `batch:SubmitJob`, `batch:DescribeJobs`, `batch:ListJobs`, `batch:TerminateJob`
- `batch:DescribeJobQueues`, `batch:DescribeComputeEnvironments`, `batch:DescribeJobDefinitions`

**`toshi-runzi-admin`** — all of above, plus:
- `batch:CreateComputeEnvironment`, `batch:UpdateComputeEnvironment`, `batch:DeleteComputeEnvironment`
- `batch:RegisterJobDefinition`, `batch:DeregisterJobDefinition`
- `ecr:CreateRepository`, `ecr:PutImage`, `ecr:InitiateLayerUpload`, `ecr:UploadLayerPart`, `ecr:CompleteLayerUpload`, `ecr:BatchDeleteImage`

**`toshi-m2m-task-role`** (IAM Task Role on Batch job definitions — no Cognito):
- Scoped S3 read/write on job I/O buckets
- `secretsmanager:GetSecretValue` on Toshi API key secret (current) → replaced by Cognito client credentials JWT when M2M migration is done

All human-user roles have trust policy: `cognito-identity.amazonaws.com` (Identity Pool `AssumeRoleWithWebIdentity`).

### Secrets Manager transition note

Runzi currently fetches the Toshi API x-api-key from Secrets Manager (`NZSHM22_TOSHI_API_SECRET_TEST/PROD`) in `runzi/aws/aws.py`. Once JWT auth is live:
- **Human users** (`runzi-local`, `runzi-batch`, `runzi-admin`): use `toshi_auth login` JWT — Secrets Manager access can be removed from their roles
- **M2M / Batch task containers**: continue using Cognito client credentials until explicitly migrated; `secretsmanager:GetSecretValue` remains on the task role during transition

---

## Implementation Phases

### Phase 1 — IAM Roles + Cognito Identity Pool
**Files to create:**
- `spike/auth/iam_roles.py` — boto3 script: create 3 IAM roles with policies + trust policies
- Extend `spike/auth/cognito_setup.py` — add Identity Pool, role mappings by Cognito group

**Tasks:**
1. Create IAM roles `toshi-runzi-local`, `toshi-runzi-batch`, `toshi-runzi-admin`
2. Attach inline policies per role
3. Create Cognito Identity Pool:
   - Authenticated provider: Cognito User Pool
   - Role mapping: Rules type, `cognito:groups` claim → role ARN
   - Unauthenticated role: deny all (no guest access)

### Phase 2 — Entra OIDC Federation in Cognito User Pool
**Prerequisite:** IT team provides Entra App Registration `client_id` + `tenant_id`.

**Files to modify:**
- `spike/auth/cognito_setup.py` — add Entra as OIDC IdP, attribute mapping, update app client

**Tasks:**
1. Add OIDC IdP pointing at Entra discovery URL:
   `https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration`
2. Attribute mapping: Entra `email` → Cognito `email`, `groups` → `custom:ad_groups` (capture for future automation)
3. Update `toshi-scientist` app client: enable PKCE, add `openid email profile` scopes, allow Entra IdP
4. Create `spike/auth/group_mapping.json` — Entra AD group names → Cognito groups (defines the contract with IT team for future automation)

### Phase 3 — CLI Updates (`toshi_auth.py`)
**Replace `login` with PKCE Authorization Code flow:**
- Spin up `localhost:{random_port}` HTTP server
- Open browser to Cognito Hosted UI → redirects to Entra → user logs in with GNS creds
- Receive `code` on localhost callback, exchange for tokens via `/oauth2/token`
- Fallback: `--no-browser` prints URL for copy-paste (SSH/headless)

**New `aws-creds [--profile <name>]` command:**
- Reads Cognito access token from `~/.toshi/credentials`
- Calls `cognito-identity:GetId` → `cognito-identity:GetCredentialsForIdentity`
- Writes `AccessKeyId`, `SecretKey`, `SessionToken` to `~/.aws/credentials [toshi]`
- Prints `export AWS_PROFILE=toshi` for shell use

**Update `whoami`:** show Cognito group membership + mapped IAM role

### Phase 4 — Documentation + Testing
**Files:**
- `spike/auth/README.md` — update: Entra federation setup, IT team checklist, new CLI commands
- `spike/auth/docs/sso-admin-setup.md` (new) — IT team guide: what to configure in Entra, what to hand over
- `spike/auth/test_e2e.py` — extend: PKCE flow, `aws-creds` returns valid STS, ECR smoke test, role boundary test (runzi-local cannot push ECR)

---

## Open Questions (decide before Phase 2)

1. **Cognito hosted UI domain** — default Cognito domain is fine for spike/dev. Custom domain (`auth.nshm.gns.cri.nz`) needs ACM cert — defer to production.

2. **Entra group sync automation** — `custom:ad_groups` is captured at login from Phase 2 onwards. A Pre-Token Generation Lambda trigger can later auto-assign Cognito groups from `group_mapping.json`, removing manual Cognito group assignment. Implement when operational burden of manual assignment becomes real.

3. **M2M Toshi API auth** — keep client credentials (Cognito) for now. Could migrate to IAM-signed API Gateway requests later (removes Cognito dependency for Batch jobs), but not worth the change yet.

4. **IaC style** — boto3 scripts match existing spike style. If/when we productionise, move to CDK for IAM roles + Identity Pool.

---

## Key Files

| File | Action |
|---|---|
| `spike/auth/cognito_setup.py` | Extend: Identity Pool + Entra OIDC IdP + attribute mapping |
| `spike/auth/iam_roles.py` | Create: IAM roles + policies (boto3) |
| `spike/auth/group_mapping.json` | Create: Entra AD group → Cognito group mapping config |
| `spike/auth/toshi_auth.py` | Modify: PKCE login + `aws-creds` command |
| `spike/auth/authorizer/handler.py` | No changes |
| `spike/auth/middleware.py` | No changes |
| `serverless.yml` | No changes |
| `spike/auth/README.md` | Update: new setup, IT team checklist, CLI usage |
| `spike/auth/docs/sso-admin-setup.md` | Create: IT team guide |
| `spike/auth/test_e2e.py` | Extend: PKCE + aws-creds + role boundary tests |
| `nzshm-runzi` (cross-repo) | Add `docs/IAM_PERMISSIONS.md` pointing here; deprecate scattered IAM notes in Docker setup docs |

---

## Verification

1. **Phase 1:** Run `cognito_setup.py` + `iam_roles.py` → verify Identity Pool + roles in AWS console; `GetCredentialsForIdentity` returns STS creds for a test token
2. **Phase 2:** Cognito Hosted UI redirects to GNS Entra login; post-auth user appears in User Pool with `custom:ad_groups` populated
3. **Phase 3:** `toshi_auth login` → browser → GNS login → token saved; `toshi_auth aws-creds` → `~/.aws/credentials [toshi]` populated; `aws ecr describe-repositories --profile toshi` succeeds
4. **Phase 4:** `test_e2e.py --remote` passes all existing + new cases; runzi-local role cannot call `ecr:PutImage`
