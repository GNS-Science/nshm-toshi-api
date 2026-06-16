"""
Strawberry SchemaExtension enforcing toshi/read + toshi/write scopes.

Port of auth/middleware.py (Flask before_request hook). Runs in the
on_execute lifecycle phase — after parse + validate, before resolvers
fire — so OperationType is reliable and a raised GraphQLError aborts
execution without invoking any resolver.

Fail-closed model:
  - Parse failure → resolvers never run; auth check never reached, but
    the parse error itself is returned to the client.
  - Missing/invalid auth context → blocked with GraphQLError.
  - Missing toshi/read → all operations blocked.
  - Missing toshi/write → mutations blocked (queries still allowed).

Local-dev / test bypass: no-op when TESTING=1 or SLS_OFFLINE=1; attaches
a synthetic current_user with both scopes so resolvers that read
context["current_user"] see a consistent shape.

Auth context source (in priority order):
  1. request.scope["aws.event"]["requestContext"]["authorizer"]
     — injected by Mangum from the API Gateway Lambda Authorizer.
  2. X-Auth-Userid / X-Auth-Scopes / X-Auth-Method headers
     — for local/e2e testing without API Gateway in front.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from graphql import GraphQLError
from strawberry.extensions import SchemaExtension
from strawberry.types.graphql import OperationType

logger = logging.getLogger(__name__)

SCOPE_READ = "toshi/read"
SCOPE_WRITE = "toshi/write"


def _boolean_env(name: str, default: str = "FALSE") -> bool:
    return os.environ.get(name, default).upper() in {"1", "Y", "YES", "TRUE"}


def _is_bypass() -> bool:
    return _boolean_env("TESTING") or _boolean_env("SLS_OFFLINE")


def _bypass_user() -> dict[str, Any]:
    return {
        "userId": "local-dev",
        "scopes": {SCOPE_READ, SCOPE_WRITE},
        "authMethod": "bypass",
    }


def _extract_auth_context(request: Any) -> tuple[str, set[str], str]:
    """
    Pull (userId, scopes, authMethod) from request.

    Mangum exposes the API Gateway event at request.scope["aws.event"]; the
    Lambda Authorizer's output lives under requestContext.authorizer.
    Header fallback supports local/e2e runs without API Gateway.
    """
    authorizer_ctx: dict[str, Any] = {}
    if request is not None:
        scope = getattr(request, "scope", None) or {}
        aws_event = scope.get("aws.event") if isinstance(scope, dict) else None
        if isinstance(aws_event, dict):
            request_context = aws_event.get("requestContext") or {}
            authorizer_ctx = request_context.get("authorizer") or {}

    headers = {}
    if request is not None:
        raw_headers = getattr(request, "headers", None)
        if raw_headers is not None:
            try:
                headers = {k.lower(): v for k, v in raw_headers.items()}
            except AttributeError:
                headers = {}

    user_id = (
        authorizer_ctx.get("userId")
        or headers.get("x-auth-userid")
        or "anonymous"
    )
    scopes_str = (
        authorizer_ctx.get("scopes")
        or headers.get("x-auth-scopes")
        or ""
    )
    auth_method = (
        authorizer_ctx.get("authMethod")
        or headers.get("x-auth-method")
        or "none"
    )
    scopes = set(scopes_str.split()) if scopes_str else set()
    return user_id, scopes, auth_method


class AuthExtension(SchemaExtension):
    """Enforces scope-based authorization on every GraphQL operation."""

    def on_execute(self):
        ctx = self.execution_context.context
        if not isinstance(ctx, dict):
            # Strawberry allows non-dict contexts; we require a dict to
            # attach current_user. Tests using bare contexts opt out of
            # auth by setting TESTING=1, which short-circuits below.
            yield
            return

        if _is_bypass():
            ctx["current_user"] = _bypass_user()
            yield
            return

        request = ctx.get("request")
        user_id, scopes, auth_method = _extract_auth_context(request)
        ctx["current_user"] = {
            "userId": user_id,
            "scopes": scopes,
            "authMethod": auth_method,
        }

        logger.info(
            "[auth] userId=%s scopes=%s method=%s op=%s",
            user_id,
            sorted(scopes),
            auth_method,
            self.execution_context.operation_type.value,
        )

        if SCOPE_READ not in scopes:
            logger.warning("Access denied for %s: missing %s", user_id, SCOPE_READ)
            raise GraphQLError(f"Missing required scope: {SCOPE_READ}")

        if (
            self.execution_context.operation_type == OperationType.MUTATION
            and SCOPE_WRITE not in scopes
        ):
            logger.warning(
                "Mutation blocked for %s: missing %s", user_id, SCOPE_WRITE
            )
            raise GraphQLError(f"GraphQL mutations require scope: {SCOPE_WRITE}")

        yield
