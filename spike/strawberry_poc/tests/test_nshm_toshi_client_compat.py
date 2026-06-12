"""Regression tests — exact query shapes that nshm-toshi-client sends.

The wire-format issue surfaced by chrisdicaprio's mini-Phase-4 runzi testing:
legacy `create_file` and `create_file_relation` use POSITIONAL ARGUMENTS in
the SDL (no `input:` wrapper), and nshm-toshi-client sends them in exactly
that shape. The POC had wrapped both in `CreateFileInput!` / `CreateFileRelationInput!`
which rejected the client's queries at GraphQL validation time.

After realignment (PR-after-#320), both mutations match legacy SDL:

    create_file(file_name: String!, md5_digest: String!, file_size: BigInt!, …)
    create_file_relation(file_id: ID!, role: FileRole!, thing_id: ID!)

These tests reproduce the *exact* mutation strings nshm-toshi-client uses
(copied verbatim from `LIB/nshm-toshi-client/nshm_toshi_client/toshi_file.py`
and `toshi_task_file.py`), so future schema drift is caught before clients
break in production.
"""

import base64

import pytest

from schema import schema

# ── Verbatim from nshm-toshi-client/nshm_toshi_client/toshi_file.py ───────────

NSHM_TOSHI_CLIENT_CREATE_FILE = """
    mutation ($digest: String!, $file_name: String!, $file_size: BigInt!) {
      create_file(
          md5_digest: $digest
          file_name: $file_name
          file_size: $file_size
      ) {
          ok
          file_result { id, file_name, file_size, md5_digest, post_url, meta {k v}}
      }
    }
"""


def test_nshm_toshi_client_create_file_query_shape(gql_context):
    """The exact GraphQL string nshm-toshi-client sends must validate + execute."""
    result = schema.execute_sync(
        NSHM_TOSHI_CLIENT_CREATE_FILE,
        variable_values={"digest": "abc==", "file_name": "client-test.zip", "file_size": 1024},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    file_result = result.data["create_file"]["file_result"]
    assert file_result["file_name"] == "client-test.zip"
    assert file_result["file_size"] == 1024
    assert file_result["md5_digest"] == "abc=="


# ── Verbatim from nshm-toshi-client/nshm_toshi_client/toshi_task_file.py ──────

NSHM_TOSHI_CLIENT_CREATE_FILE_RELATION = """
    mutation ($file_id: ID!, $thing_id: ID!, $role: FileRole!) {
        create_file_relation(
            file_id: $file_id
            thing_id: $thing_id
            role: $role
        ) {
            ok
        }
    }
"""


@pytest.fixture
def thing_id(gql_context):
    from data.dynamo import create_thing  # noqa: PLC0415

    data = create_thing(
        gql_context["dynamodb"],
        "AutomationTask",
        {"state": "done", "result": "success", "task_type": "INVERSION", "created": "2026-01-01T00:00:00Z"},
    )
    return base64.b64encode(f"AutomationTask:{data['object_id']}".encode()).decode()


@pytest.fixture
def file_id(gql_context):
    result = schema.execute_sync(
        NSHM_TOSHI_CLIENT_CREATE_FILE,
        variable_values={"digest": "abc==", "file_name": "fr-test.zip", "file_size": 100},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_file"]["file_result"]["id"]


def test_nshm_toshi_client_create_file_relation_query_shape(gql_context, thing_id, file_id):
    """The exact create_file_relation GraphQL string nshm-toshi-client sends."""
    result = schema.execute_sync(
        NSHM_TOSHI_CLIENT_CREATE_FILE_RELATION,
        variable_values={"file_id": file_id, "thing_id": thing_id, "role": "WRITE"},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    assert result.data["create_file_relation"]["ok"] is True


# ── SDL contract pins ─────────────────────────────────────────────────────────


def test_create_file_sdl_matches_legacy_positional_shape():
    """create_file SDL must use positional args, not input: wrapper."""
    sdl = schema.as_str()
    import re

    m = re.search(r"create_file\([^)]+\)[^\n]+", sdl, re.S)
    assert m, "create_file missing from SDL"
    sig = m.group(0)
    # Legacy SDL has these positional args; new shape must too.
    assert "file_name: String!" in sig, f"create_file lost file_name positional: {sig}"
    assert "md5_digest: String!" in sig, f"create_file lost md5_digest positional: {sig}"
    assert "file_size: BigInt!" in sig, f"create_file lost file_size positional: {sig}"
    # And must NOT have the input wrapper.
    assert "input: CreateFileInput" not in sig, (
        f"create_file regressed to input-wrapper form — would break nshm-toshi-client: {sig}"
    )


def test_create_file_relation_sdl_matches_legacy_positional_shape():
    """create_file_relation SDL must use positional args, not input: wrapper."""
    sdl = schema.as_str()
    import re

    m = re.search(r"create_file_relation\([^)]+\)[^\n]+", sdl, re.S)
    assert m, "create_file_relation missing from SDL"
    sig = m.group(0)
    assert "file_id: ID!" in sig, f"create_file_relation lost file_id positional: {sig}"
    assert "role: FileRole!" in sig, f"create_file_relation lost role positional: {sig}"
    assert "thing_id: ID!" in sig, f"create_file_relation lost thing_id positional: {sig}"
    assert "input: CreateFileRelationInput" not in sig, f"create_file_relation regressed to input-wrapper form: {sig}"
