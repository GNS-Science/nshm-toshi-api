# ADR-003: Cognito Permission Model — Two Axes and a Cumulative AWS Ladder

## Status

Accepted. Implemented on branch `refine/cognito-permission-model`; not yet
merged or deployed (see *Consequences → Verification*).

## Context

`nshm-toshi-api` uses a single AWS Cognito user pool to drive **two
different permission systems that happen to share one login**, plus a
third cross-cutting gate. Conflating them is the root of the problem this
ADR resolves.

1. **Toshi API access** — "what GraphQL operations may I perform?"
   Expressed as the scopes `toshi/read` / `toshi/write`, carried in the
   JWT and enforced by the Lambda authorizer (`auth/authorizer/handler.py`)
   and Flask middleware (`auth/middleware.py`). For interactive
   (`USER_PASSWORD_AUTH`) logins the scopes are derived from Cognito group
   membership (`toshi-readers` → read, `toshi-writers` → read+write); for
   machine (M2M `client_credentials`) tokens they come straight from the
   token's `scope` claim.

2. **AWS session access** — "what AWS resources may I touch directly?"
   (S3, ECR, AWS Batch). This is a *separate* exchange: after login the
   token is swapped — via the Cognito **Identity Pool** — for temporary
   STS credentials tied to an IAM role. Governed by the `runzi-local` /
   `runzi-batch` / `runzi-admin` groups and the Identity Pool role-mapping
   rules (`serverless.yml::ToshiIdentityPoolRoleAttachment`).

3. **Caller allowlist (audience)** — an orthogonal gate: a token's
   `client_id` must be in the authorizer's `COGNITO_CLIENT_ID` allowlist
   or it is rejected. Not a permission "axis", just admission control.

### The bug that prompted this

A Cognito Identity Pool assigns **exactly one IAM role per login** — it
cannot union two. The role-mapping rules were ordered `local → batch →
admin` and evaluated **first-match-wins**. So a power user placed in
*both* `runzi-local` and `runzi-batch` (the intuitive way to "add" Batch
rights to a local user) always matched the `runzi-local` rule first,
received the local-only role, and **could never submit Batch jobs**.
Adding more groups did not add power — it just changed which single rule
matched first.

### Why fix it carefully rather than minimally

The five groups tangled the two systems: nothing in the design said the
`runzi-*` tiers were meant to be *alternatives* rather than *additive*,
the role policies duplicated their base permissions by copy-paste (prone
to drift), and the "first match wins" ordering encoded the bug. The
decision was to repair the bug *and* make the intended user model
explicit, while keeping the change inside this repo's `serverless.yml`.

### Who actually uses this (user stories)

| # | Actor | API axis | AWS axis |
|---|---|---|---|
| 1 | **Scientist (default)** — logs in, runs runzi locally, reads/writes Toshi + S3, pulls ECR. *The norm.* | `toshi-writers` | `runzi-local` |
| 2 | **Power user** — scientist who also submits cloud Batch runs. *A few named users today; possibly any scientist later.* | `toshi-writers` | `runzi-batch` |
| 3 | **Operator/admin** — power user who also manages Batch compute environments and pushes ECR images. | `toshi-writers` | `runzi-admin` |
| 4 | **Automation / Batch job (machine)** — runs inside a Batch container, writes results. *One shared M2M identity.* | M2M `toshi/read`+`toshi/write` | none from Cognito (see *Consequences → Deferred*) |
| 5 | **Internal read service (machine)** — queries Toshi read-only. *Future: public/REST read.* | M2M `toshi/read` only | none |

## Decision

1. **The permission model is two independent axes plus an orthogonal
   allowlist.** A human carries one selection on the API axis
   (`toshi-readers` *or* `toshi-writers`) and one on the AWS axis (a single
   `runzi-*` tier). Machines have only the API axis. The two axes consume
   disjoint group names and never affect one another.

2. **The AWS axis is a cumulative ladder: `local ⊂ batch ⊂ admin`.** Each
   tier's IAM role is self-contained and contains everything below it. A
   user belongs to **exactly one** tier — the highest they need. This
   directly accommodates the "any scientist might occasionally submit
   Batch" future: promotion is a single group move, not a second
   membership.

3. **Fix the role assignment by ordering and structure, not by trying to
   union roles** (which the Identity Pool cannot do):
   - Order the role-mapping rules **most-privileged-first**
     (`admin → batch → local`) so that if a user is in several tiers, the
     highest matches first.
   - Build the ladder by **composition of shared managed policies** so higher
     tiers cannot drift below lower ones. Each tier is one incremental
     `AWS::IAM::ManagedPolicy` — `ToshiRunziBaseManagedPolicy` (ECR pull, S3
     read/write to the `ths-poc-arrow-test` (Toshi Hazard Store dataset) and
     `nzshm22-static-reports-test` (reports) buckets, M2M secret read),
     `ToshiRunziBatchManagedPolicy` (Batch submit), and
     `ToshiRunziAdminManagedPolicy` (Batch + ECR administration). Each role
     attaches the base plus the increments of all lower tiers via
     `ManagedPolicyArns`: `local=[base]`, `batch=[base, batch]`,
     `admin=[base, batch, admin]`. Because admin attaches the *same* batch
     policy object the batch role uses, `admin ⊇ batch ⊇ local` holds by
     construction — no duplicated statements to keep in sync, and a new
     permission added to a tier automatically flows up to every higher tier.

4. **The API read/write axis is left as-is** — it already works. Group →
   scope derivation lives in `validate_cognito_token`; enforcement
   (read for queries, write for mutations, fail-closed) lives in
   `check_auth`. This ADR adds characterization tests for both rather than
   changing them.

5. **Scope boundary: this change stays in `nshm-toshi-api/serverless.yml`.**
   Relocating the compute-permission domain to its own stack/repo, and
   bringing Batch-container permissions into IaC, are explicitly deferred
   (below).

### Specific decisions

| Area | Decision | Rationale |
|---|---|---|
| AWS-tier semantics | One tier per user; cumulative; highest wins | An Identity Pool grants one role; cannot union |
| Rule ordering | `admin → batch → local` (most-privileged first) | First-match-wins must surface the highest tier |
| Tier permissions | Layered shared managed policies (base / +batch / +admin), composed via `ManagedPolicyArns` | Guarantees `admin ⊇ batch ⊇ local` by construction; one source of truth per tier, no copy-paste drift |
| Attribution of Batch writes | One shared automation M2M identity | No per-user attribution requirement today |
| Read-only machine identity | Deferred | Outside of scope |
| Legacy `x-api-key` | Retained (full read+write) | Backward-compat; retiring it is out of scope |

## Consequences

**Positive**
- The reported bug is fixed: a user in `{local, batch}` now assumes
  `ToshiRunziBatchRole` (which includes the local permissions) and can
  both write S3 and submit Batch jobs.
- Base AWS permissions are defined in exactly one place; the three tiers
  can no longer drift apart.
- The intended model is explicit and documented
  (`docs/cognito-permission-model-reference.md`), including the
  "exactly one tier, highest wins" invariant commented in `serverless.yml`.

**Trade-offs / things this makes harder**
- A human still needs **two** group memberships (one per axis). This is
  intentional — the axes are genuinely independent — but it means
  provisioning a scientist is "add to `toshi-writers` + add to one
  `runzi-*` tier", not a single action.
- The cumulative-ladder convention is a *convention*: the ordering only
  protects against accidental multi-membership. Editing the rule order
  without understanding the invariant would silently reintroduce the bug
  (hence the warning comment in `serverless.yml`).

**Deferred (this decision does not address; documented so the next step
is deliberate — see the reference doc's "Deferred / future" section)**
- **No least-privilege read-only machine identity (actor #5).** The single
  `ToshiAutomationClient` holds both scopes, so read-only services share
  read+write creds or use the full-access legacy key. A
  `ToshiReadOnlyAutomationClient` (scope `toshi/read` only) is a small
  follow-up.
- **Batch-container permissions are not IaC.** A container's AWS
  permissions come from the Batch job definition's `jobRoleArn`, which is
  copied wholesale from a manually console-created job definition
  (`nzshm-runzi/runzi/cli/build_and_deploy_container.py`) — invisible to
  any IaC. This is distinct from the workstation S3 grant (the Cognito
  `runzi-*` role, which *is* IaC).
- **Compute environments, job queues, the ECR repos (the `nshm-runzi-*`
  repository glob), and the S3 buckets they use** are manual/external; only the
  IAM permissions to use them are defined here. The base policy currently grants
  S3 read/write to `ths-poc-arrow-test` (the Toshi Hazard Store Arrow dataset)
  and `nzshm22-static-reports-test` (reports, written directly by
  `runzi/aws/s3_folder_upload.py`). Both are hardcoded to the `-test` suffix
  rather than `${stage}`-derived, and `nzshm22-toshi-api-<stage>` (the Toshi
  object store) is reached via the API rather than direct S3 — so the exact
  bucket set and stage handling should be reconciled (and names confirmed against
  the env-configured THS dataset URIs) when this becomes IaC.
- **A future split** of the compute-permission domain (Identity Pool +
  `runzi-*` roles + batch job role + compute resources) into a dedicated
  runzi-infra stack/repo.

**Verification**
- `uv run pytest auth/tests/` passes (50), including new tests for the
  group→scope derivation and the read/write enforcement gate.
- The `serverless.yml` template was validated structurally (parses; roles
  attach the layered managed policies — `local`=1, `batch`=2, `admin`=3, with no
  inline policies; rule order `admin → batch → local`).
- `yarn sls package` was **not** completed in the authoring environment
  (Serverless v4 requires valid AWS credentials even to package, which
  were unavailable). **Run `yarn sls package --stage <stage>` with valid
  credentials before merge/deploy**, and confirm the end-to-end ladder fix
  by having a `{runzi-local, runzi-batch}` user assume the batch role and
  perform both `s3:PutObject` and `batch:SubmitJob`.

## Related decisions

- `auth/IMPLEMENTATION_PLAN.md` — the decision to provision Cognito/IAM
  Serverless-natively (in `serverless.yml`) rather than via a separate CDK
  stack. This ADR works within that boundary; the deferred "split" would
  revisit it for the *compute* domain specifically.
- `auth/IDP_INTEGRATION_PLAN.md` / `auth/IDP_INTEGRATION_OPTIONS_STUDY.md`
  — the future migration toward IT-managed SSO (Entra/IAM Identity Center);
  Cognito remains the API JWT issuer regardless.
- `docs/cognito-permission-model-reference.md` — the operational reference
  (how-to, decision matrix, diagnostics) implementing this model.
