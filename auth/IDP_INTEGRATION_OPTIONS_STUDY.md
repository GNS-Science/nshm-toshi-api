# IDP Integration — Options Study

This document captures the approaches considered for SSO and AWS access management, with pros/cons and a migration path. See `IDP_INTEGRATION_PLAN.md` for the recommended implementation plan.

---

## Background

Two requirements drive the integration:

1. **Toshi API authentication** — the API Gateway Lambda Authorizer requires a Bearer JWT. This means a token-issuing identity provider (Cognito) is permanently required, regardless of what else is in place.
2. **AWS service credentials** — Runzi users need temporary STS credentials for Batch, ECR, and S3. These can come from multiple sources.

The question is: which IdP/mechanism handles each requirement, and who controls it?

---

## Options Considered

### Option A — IAM Identity Center with Permission Sets *(IT team's initial preference)*

```
Entra AD → IAM Identity Center → Permission Sets → STS credentials (Batch/ECR)
                                                 ↘ [Cognito still required for Toshi API JWT]
```

IT team federates Entra into IAM Identity Center, creates Permission Sets (IAM policies), and assigns AD groups to them. Scientists use `aws sso login` for AWS service credentials.

**Pros**
- IT team's native model — Permission Sets are what they expect to manage
- Central governance and audit in one place (IAM Identity Center console)
- `aws sso login` is standard AWS tooling; no custom CLI code for AWS credentials
- Long-term correct enterprise pattern for AWS access management

**Cons**
- **IAM Identity Center is centralised in the management account** — dev team cannot create Permission Sets independently. Every new role/policy requires IT team action or a formal delegation setup. There is no "per-OU" or "per-account" Permission Set management — it is one shared service across the org
- **Cognito is still required regardless** — API Gateway's Lambda Authorizer needs a Bearer JWT. IAM Identity Center does not issue JWTs for application-level auth. There is no path to remove Cognito for Toshi API
- **Hard dependency on IT team readiness** — until Entra ↔ IAM Identity Center federation is complete, nothing works. IT team are new to AWS; this federation is non-trivial (requires both Entra admin and IAM Identity Center admin in the management account)
- High setup friction. Risk of blocking scientists for weeks while IT team ramps up on IAM Identity Center + SAML/OIDC federation

**Verdict:** Right destination, wrong starting point. Deferred — see migration path below.

---

### Option B — Entra Direct, no Cognito *(considered, rejected)*

```
Entra AD → Lambda Authorizer validates Entra JWTs directly → Toshi API
Entra Service Principals → M2M tokens
```

Skip Cognito entirely. The Lambda Authorizer validates tokens issued directly by Entra, using Entra's JWKS endpoint.

**Pros**
- Fewer moving parts — no Cognito User Pool to manage
- IT team manages everything in their domain (Entra)

**Cons**
- **Dev team loses control of authorization** — group membership, scope definitions, and app client config all move to Entra (IT team domain). Adding a new role (e.g. `toshi-external-readonly`) requires IT team to create an Entra App Role
- Entra access tokens have a different claim structure — the Lambda Authorizer requires significant changes and ongoing coupling to Entra's evolving token format
- M2M via Entra service principals is considerably more complex than Cognito client credentials
- No clean way to have Cognito-style custom scopes (`toshi/read`, `toshi/write`) without IT team creating custom App Roles in Entra
- Onboarding friction for external collaborators who do not have a GNS Entra account

**Verdict:** Rejected. Transfers too much control to IT team, complicates M2M, and tightly couples the API's auth layer to Entra's token format.

---

### Option C — Cognito + Cognito Identity Pool *(recommended)*

```
Entra AD → Cognito User Pool (OIDC federation) → JWT Bearer token → Toshi API
                                               → Cognito Identity Pool
                                                   → STS AssumeRoleWithWebIdentity
                                                   → IAM roles in our account (Batch/ECR/S3)
```

Cognito federates Entra as an OIDC identity provider. Cognito issues JWTs for Toshi API and, via a Cognito Identity Pool, exchanges them for temporary STS credentials to call AWS services directly.

**Pros**
- **Dev team fully independent** — all config (groups, scopes, role mappings, IAM policies) lives in our own account. No IT team involvement after a one-time Entra App Registration
- **Cognito must exist anyway** for Toshi API JWT — the Identity Pool is a thin addition at zero extra IT overhead
- **Works immediately** — a single Entra App Registration is the only external ask to IT team
- **Clean migration path to IAM Identity Center** when IT team is ready (see below) — the IAM role policies defined now become the exact Permission Set definitions IT team will use
- Entra group claims captured from day one (`custom:ad_groups`), providing data needed for future automated group assignment
- Scientists authenticate via familiar GNS Entra SSO browser login — identical experience regardless of which backend is used

**Cons**
- `toshi_auth aws-creds` is a custom command rather than standard `aws sso login` — minor UX friction, removed once IAM Identity Center is in place
- Cognito group assignment is initially manual — operational overhead if team grows quickly (mitigated by a future Pre-Token Generation Lambda trigger reading `group_mapping.json`)
- Cognito User Pool is an additional service to operate alongside Entra and IAM Identity Center
- Long-lived Cognito app-client `client_secret` still exists on the AWS side. Storing it in AWS Secrets Manager (`ToshiM2MSecret`, populated by `auth/create_m2m_secret.py`) minimises **caller-side** exposure (Runzi no longer ships env-var creds) but does not eliminate the long-lived credential — the SM entry's `SecretString` is the same secret Cognito issued. True secretless M2M (WIF / private-key JWT) would require dropping Cognito (Option B, rejected on governance grounds). Surfaced in client-side review: GNS-Science/nshm-toshi-client#41 (discussion r3232419054).

**Verdict:** Recommended. Unblocks the team now, keeps dev team in control, and provides a clean handover path to IT team later.

---

## Migration Path: Cognito Identity Pool → IAM Identity Center

This is not a rip-and-replace. **Cognito remains permanently** for Toshi API JWT auth — that requirement does not change. The migration is specifically for **AWS service credentials** (Batch, ECR, S3), replacing `toshi_auth aws-creds` with `aws sso login` once IT team is ready.

### When to migrate

Trigger the migration when all of the following are true:
- IT team has successfully federated Entra into IAM Identity Center (they own this step)
- IT team is comfortable creating and managing Permission Sets
- The Cognito Identity Pool path has been running in production and scientists trust the login flow

There is no urgency — the Cognito path works indefinitely and coexists with IAM Identity Center.

### Migration steps

**Step 1 — IT team: complete Entra ↔ IAM Identity Center federation**
- IT team registers a **new, separate Entra App Registration** for IAM Identity Center (our Cognito App Registration is unaffected)
- Federation is configured in the IAM Identity Center console (management account)

**Step 2 — Dev team: hand over Permission Set policy definitions**
- The IAM role policies already defined in `auth/iam_roles.py` are the exact policies IT team needs — no rework
- Provide IT team with the JSON policy documents for `NSHM-RunziLocal`, `NSHM-RunziBatch`, `NSHM-RunziAdmin`
- IT team creates these as Permission Sets and assigns the relevant Entra AD groups

**Step 3 — Scientists: switch one command for AWS credentials**
```bash
# Before (Cognito Identity Pool)
toshi_auth aws-creds --profile toshi

# After (IAM Identity Center)
aws sso login --profile nshm
```
`toshi_auth login` for Toshi API JWT is **unchanged throughout** — scientists learn one new command.

**Step 4 — Retire Cognito Identity Pool (optional, when all users migrated)**
- Identity Pool and associated IAM roles can be removed
- Cognito User Pool itself is never retired — Toshi API requires it permanently

### Why defer rather than start with IAM Identity Center

| | Start with IAM Identity Center | Start with Cognito (recommended) |
|---|---|---|
| **Blocks on IT team** | Yes — nothing works until Entra federation is complete | No — one App Registration is the only ask |
| **IT team AWS experience required** | High — SAML/OIDC federation, Permission Sets, delegated admin setup | Minimal — create an App Registration in Entra |
| **Dev team independence** | Low — every Permission Set change requires IT team | Full — dev team owns everything |
| **Risk of delays blocking scientists** | High | Low |
| **Rework when eventually migrating** | N/A | Minimal — policy JSON reused directly as Permission Sets |
| **Toshi API JWT** | Cognito still required regardless | Cognito required (same) |
| **Fallback if IT stumbles** | None — scientists blocked | Yes — Cognito path continues working |

### The core argument

Cognito is not a workaround to be replaced — it is a **permanent component**. Toshi API will always need a JWT-issuing identity provider, and that provider is Cognito. The Cognito Identity Pool is a thin addition on top of infrastructure that must exist anyway, giving the team full AWS service access now. When IT team is ready, they take over the AWS credentials layer via IAM Identity Center. Scientists notice one changed command. Nothing else changes.
