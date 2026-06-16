"""
HTTP-level integration test for AuthExtension.

Validates the end-to-end path:
    TestClient → ASGI → FastAPI route → GraphQLRouter
        → get_context(request) → AuthExtension.on_execute

TestClient drives the app directly (no Mangum), so this exercises the
X-Auth-* header fallback path the extension uses for local/e2e runs.
The Mangum/API-Gateway-authorizer path is covered by the unit tests in
test_auth.py via a synthetic request.scope["aws.event"].
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def http_client(monkeypatch):
    """A TestClient with the conftest's TESTING bypass turned off."""
    monkeypatch.delenv("TESTING", raising=False)
    monkeypatch.delenv("SLS_OFFLINE", raising=False)
    return TestClient(app)


def _post_graphql(client, body, headers=None):
    return client.post("/graphql", json=body, headers=headers or {})


def test_http_anonymous_query_blocked(http_client):
    response = _post_graphql(http_client, {"query": "{ __typename }"})
    assert response.status_code == 200  # GraphQL errors surface in body
    payload = response.json()
    assert payload["data"] is None
    assert any("toshi/read" in err["message"] for err in payload["errors"])


def test_http_read_scope_via_headers_allows_query(http_client):
    response = _post_graphql(
        http_client,
        {"query": "{ __typename }"},
        headers={
            "X-Auth-Userid": "alice",
            "X-Auth-Scopes": "toshi/read",
            "X-Auth-Method": "header-bypass",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("errors") is None
    assert payload["data"]["__typename"]  # query reached resolver


def test_http_options_preflight_not_subject_to_auth(http_client):
    """OPTIONS never reaches the GraphQL handler — the extension can't fire."""
    response = http_client.options(
        "/graphql",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    # FastAPI/Starlette returns 405 by default when CORS middleware isn't
    # installed; the relevant assertion is that no auth-error JSON body is
    # produced (i.e. the GraphQL handler never saw the request).
    assert response.status_code in {200, 405}
    if response.headers.get("content-type", "").startswith("application/json"):
        assert "toshi" not in response.text


def test_http_bypass_via_testing_env_when_enabled(monkeypatch):
    """With TESTING=1, no auth headers required."""
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.delenv("SLS_OFFLINE", raising=False)
    client = TestClient(app)
    response = _post_graphql(client, {"query": "{ __typename }"})
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("errors") is None
    assert payload["data"]["__typename"]  # query reached resolver
