"""Schema-level tests for RuptureGenerationTask.

Ports the create / with_metrics / update cases from
`graphql_api/tests/test_rupture_generation_schema.py`. RGT was previously
only exercised via fixtures in other test files (test_rupture_set.py,
test_smoketest_ab.py) — this pins the create + update contract directly.

Out of scope (documented exceptions in COVERAGE_GAPS.md):
  - DateTime input validation (timezone-required, ISO-format-required) —
    ADR-001 Phase 1 chose `parse_value=str` for the DateTime scalar.
  - `test_transforms_old_fields` (git_refs → environment migration) —
    pre-2020 legacy data shape; the POC data layer doesn't replicate
    Graphene's runtime field-rename hack.
"""

import base64

import pytest

from schema import schema

CREATE_RGT = """
mutation CreateRGT($input: CreateAutomationTaskInput!) {
    create_rupture_generation_task(input: $input) {
        task_result {
            id
            task_type
            state
            result
            created
            duration
            arguments { k v }
            environment { k v }
            metrics { k v }
        }
    }
}
"""

UPDATE_RGT = """
mutation UpdateRGT($input: UpdateAutomationTaskInput!) {
    update_rupture_generation_task(input: $input) {
        task_result {
            id
            duration
            state
            result
            metrics { k v }
        }
    }
}
"""


def _make_input(**overrides):
    base = {
        "state": "UNDEFINED",
        "result": "UNDEFINED",
        "task_type": "RUPTURE_SET",
        "created": "2026-01-01T00:00:00Z",
        "duration": 600,
        "arguments": [
            {"k": "max_jump_distance", "v": "55.5"},
            {"k": "permutation_strategy", "v": "DOWNDIP"},
        ],
        "environment": [
            {"k": "gitref_opensha_ucerf3", "v": "ABC"},
            {"k": "JAVA", "v": "-Xmx24G"},
        ],
    }
    base.update(overrides)
    return base


@pytest.fixture
def created_rgt(gql_context):
    """Mirrors legacy test_create_minimum_fields_happy_case."""
    result = schema.execute_sync(
        CREATE_RGT,
        variable_values={"input": _make_input()},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_rupture_generation_task"]["task_result"]


def test_create_returns_id(created_rgt):
    """The Relay global ID encodes the RuptureGenerationTask typename."""
    gid = created_rgt["id"]
    decoded = base64.b64decode(gid).decode()
    assert decoded.startswith("RuptureGenerationTask:"), decoded


def test_create_minimum_fields_round_trip(created_rgt):
    """Create with the legacy "minimum fields" shape — verify fields round-trip."""
    assert created_rgt["task_type"] == "RUPTURE_SET"
    assert created_rgt["state"] == "UNDEFINED"
    assert created_rgt["result"] == "UNDEFINED"
    assert created_rgt["duration"] == 600
    assert created_rgt["created"] == "2026-01-01T00:00:00Z"
    assert {"k": "max_jump_distance", "v": "55.5"} in created_rgt["arguments"]


def test_create_with_metrics(gql_context):
    """Mirrors legacy test_create_with_metrics — create RGT carrying a metrics list."""
    result = schema.execute_sync(
        CREATE_RGT,
        variable_values={
            "input": _make_input(metrics=[{"k": "rupture_count", "v": "206776"}])
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    task = result.data["create_rupture_generation_task"]["task_result"]
    assert task["metrics"] == [{"k": "rupture_count", "v": "206776"}]


def test_update_with_metrics(gql_context, created_rgt):
    """Mirrors legacy test_update_with_metrics — update RGT with metrics + state + result."""
    update = schema.execute_sync(
        UPDATE_RGT,
        variable_values={
            "input": {
                "task_id": created_rgt["id"],
                "duration": 909,
                "metrics": [{"k": "rupture_count", "v": "20"}],
                "result": "FAILURE",
                "state": "DONE",
            }
        },
        context_value=gql_context,
    )
    assert update.errors is None, update.errors
    task = update.data["update_rupture_generation_task"]["task_result"]
    assert task["id"] == created_rgt["id"]
    assert task["duration"] == 909
    assert task["state"] == "DONE"
    assert task["result"] == "FAILURE"
    assert task["metrics"] == [{"k": "rupture_count", "v": "20"}]
