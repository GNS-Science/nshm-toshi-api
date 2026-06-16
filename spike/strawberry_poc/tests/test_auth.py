"""
Tests for AuthExtension scope enforcement.

Uses an isolated test schema (not the production schema) so we don't
need DynamoDB / Elasticsearch fixtures. A separate test confirms the
production schema actually has the extension wired.
"""

from __future__ import annotations

from typing import Any

import pytest
import strawberry
from strawberry.schema.config import StrawberryConfig

from auth import SCOPE_READ, SCOPE_WRITE, AuthExtension
from schema import schema as production_schema


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> str:
        return "pong"


@strawberry.type
class _Mutation:
    @strawberry.mutation
    def do_write(self) -> str:
        return "written"


test_schema = strawberry.Schema(
    query=_Query,
    mutation=_Mutation,
    config=StrawberryConfig(auto_camel_case=False),
    extensions=[AuthExtension],
)


class _FakeHeaders(dict):
    """Mimics Starlette's case-insensitive header access via .items()."""


class _FakeRequest:
    """Minimal stand-in for a Starlette/FastAPI Request."""

    def __init__(
        self,
        authorizer: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.scope: dict[str, Any] = {}
        if authorizer is not None:
            self.scope["aws.event"] = {"requestContext": {"authorizer": authorizer}}
        self.headers = _FakeHeaders(headers or {})


@pytest.fixture
def no_bypass(monkeypatch):
    """Disable the conftest's TESTING=1 so the enforcement path runs."""
    monkeypatch.delenv("TESTING", raising=False)
    monkeypatch.delenv("SLS_OFFLINE", raising=False)


# ---------------------------------------------------------------------------
# Bypass path (TESTING=1 / SLS_OFFLINE=1)
# ---------------------------------------------------------------------------


def test_bypass_via_testing_env_allows_query(monkeypatch):
    monkeypatch.setenv("TESTING", "1")
    result = test_schema.execute_sync("{ ping }", context_value={})
    assert result.errors is None
    assert result.data == {"ping": "pong"}


def test_bypass_via_testing_env_allows_mutation(monkeypatch):
    monkeypatch.setenv("TESTING", "1")
    result = test_schema.execute_sync("mutation { do_write }", context_value={})
    assert result.errors is None
    assert result.data == {"do_write": "written"}


def test_bypass_via_sls_offline_allows_query(no_bypass, monkeypatch):
    monkeypatch.setenv("SLS_OFFLINE", "1")
    result = test_schema.execute_sync("{ ping }", context_value={})
    assert result.errors is None


def test_bypass_attaches_synthetic_user_with_both_scopes(monkeypatch):
    monkeypatch.setenv("TESTING", "1")
    ctx: dict[str, Any] = {}
    test_schema.execute_sync("{ ping }", context_value=ctx)
    user = ctx["current_user"]
    assert user["userId"] == "local-dev"
    assert user["authMethod"] == "bypass"
    assert user["scopes"] == {SCOPE_READ, SCOPE_WRITE}


# ---------------------------------------------------------------------------
# Anonymous / unauthenticated
# ---------------------------------------------------------------------------


def test_anonymous_blocked_on_query(no_bypass):
    ctx = {"request": _FakeRequest()}
    result = test_schema.execute_sync("{ ping }", context_value=ctx)
    assert result.errors is not None
    assert "Missing required scope: toshi/read" in str(result.errors[0])


def test_anonymous_blocked_on_mutation_reports_read_scope_first(no_bypass):
    ctx = {"request": _FakeRequest()}
    result = test_schema.execute_sync("mutation { do_write }", context_value=ctx)
    assert result.errors is not None
    assert "toshi/read" in str(result.errors[0])


def test_missing_request_blocks_with_anonymous(no_bypass):
    ctx: dict[str, Any] = {}
    result = test_schema.execute_sync("{ ping }", context_value=ctx)
    assert result.errors is not None
    assert "toshi/read" in str(result.errors[0])


# ---------------------------------------------------------------------------
# Read-only token
# ---------------------------------------------------------------------------


def test_read_scope_allows_query(no_bypass):
    ctx = {
        "request": _FakeRequest(
            authorizer={
                "userId": "alice",
                "scopes": "toshi/read",
                "authMethod": "cognito-jwt",
            }
        )
    }
    result = test_schema.execute_sync("{ ping }", context_value=ctx)
    assert result.errors is None
    assert result.data == {"ping": "pong"}


def test_read_scope_blocks_mutation(no_bypass):
    ctx = {
        "request": _FakeRequest(
            authorizer={
                "userId": "alice",
                "scopes": "toshi/read",
                "authMethod": "cognito-jwt",
            }
        )
    }
    result = test_schema.execute_sync("mutation { do_write }", context_value=ctx)
    assert result.errors is not None
    assert "GraphQL mutations require scope: toshi/write" in str(result.errors[0])


# ---------------------------------------------------------------------------
# Write token
# ---------------------------------------------------------------------------


def test_write_scope_allows_mutation(no_bypass):
    ctx = {
        "request": _FakeRequest(
            authorizer={
                "userId": "bob",
                "scopes": "toshi/read toshi/write",
                "authMethod": "cognito-jwt",
            }
        )
    }
    result = test_schema.execute_sync("mutation { do_write }", context_value=ctx)
    assert result.errors is None
    assert result.data == {"do_write": "written"}


def test_authenticated_request_attaches_current_user(no_bypass):
    ctx = {
        "request": _FakeRequest(
            authorizer={
                "userId": "charlie",
                "scopes": "toshi/read toshi/write",
                "authMethod": "cognito-jwt",
            }
        )
    }
    test_schema.execute_sync("{ ping }", context_value=ctx)
    user = ctx["current_user"]
    assert user["userId"] == "charlie"
    assert user["scopes"] == {SCOPE_READ, SCOPE_WRITE}
    assert user["authMethod"] == "cognito-jwt"


# ---------------------------------------------------------------------------
# Header fallback (no Mangum: local uvicorn / e2e harness)
# ---------------------------------------------------------------------------


def test_header_fallback_when_no_authorizer(no_bypass):
    ctx = {
        "request": _FakeRequest(
            headers={
                "x-auth-userid": "header-user",
                "x-auth-scopes": "toshi/read toshi/write",
                "x-auth-method": "header-bypass",
            }
        )
    }
    result = test_schema.execute_sync("mutation { do_write }", context_value=ctx)
    assert result.errors is None
    assert ctx["current_user"]["userId"] == "header-user"
    assert ctx["current_user"]["authMethod"] == "header-bypass"


def test_authorizer_wins_over_headers_when_both_present(no_bypass):
    """API Gateway authorizer is the trust boundary; spoofed headers must lose."""
    ctx = {
        "request": _FakeRequest(
            authorizer={
                "userId": "real-alice",
                "scopes": "toshi/read",
                "authMethod": "cognito-jwt",
            },
            headers={
                "x-auth-userid": "spoofed",
                "x-auth-scopes": "toshi/read toshi/write",
                "x-auth-method": "header-bypass",
            },
        )
    }
    result = test_schema.execute_sync("mutation { do_write }", context_value=ctx)
    assert result.errors is not None
    assert "toshi/write" in str(result.errors[0])
    assert ctx["current_user"]["userId"] == "real-alice"


# ---------------------------------------------------------------------------
# Multi-operation document — operationName must drive scope check
# ---------------------------------------------------------------------------


def test_operation_name_selects_read_op_with_read_only_scope(no_bypass):
    doc = """
    query Read { ping }
    mutation Write { do_write }
    """
    ctx = {
        "request": _FakeRequest(
            authorizer={
                "userId": "alice",
                "scopes": "toshi/read",
                "authMethod": "cognito-jwt",
            }
        )
    }
    result = test_schema.execute_sync(doc, context_value=ctx, operation_name="Read")
    assert result.errors is None
    assert result.data == {"ping": "pong"}


def test_operation_name_selects_mutation_blocked_with_read_only_scope(no_bypass):
    doc = """
    query Read { ping }
    mutation Write { do_write }
    """
    ctx = {
        "request": _FakeRequest(
            authorizer={
                "userId": "alice",
                "scopes": "toshi/read",
                "authMethod": "cognito-jwt",
            }
        )
    }
    result = test_schema.execute_sync(doc, context_value=ctx, operation_name="Write")
    assert result.errors is not None
    assert "toshi/write" in str(result.errors[0])


# ---------------------------------------------------------------------------
# Fail-closed on parse error: resolvers never run because parsing fails first
# ---------------------------------------------------------------------------


def test_parse_error_blocks_execution(no_bypass):
    """If the document doesn't parse, on_execute never fires — no resolver runs."""
    ctx = {
        "request": _FakeRequest(
            authorizer={
                "userId": "alice",
                "scopes": "toshi/read toshi/write",
                "authMethod": "cognito-jwt",
            }
        )
    }
    result = test_schema.execute_sync("mutation { unclosed", context_value=ctx)
    assert result.errors is not None
    assert result.data is None


# ---------------------------------------------------------------------------
# Production schema wiring
# ---------------------------------------------------------------------------


def test_production_schema_has_auth_extension_registered():
    assert any(
        ext is AuthExtension or type(ext) is AuthExtension
        for ext in production_schema.extensions
    ), "AuthExtension is not registered on the production schema"
