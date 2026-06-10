"""Regression tests for COVERAGE_GAPS.md Gap 14 — AT swept-argument validation.

Ports `graphql_api/tests/swept_arguments/test_automation_task_swept_arg_validation.py`.

The legacy contract: when an AutomationTask is created with a
`general_task_id`, the AT's `arguments` must satisfy the parent GT's
*swept_arguments* (keys in `argument_lists` whose value list has >1 entry).
Four error shapes are surfaced:

  1. "is not a `GeneralTask`"                     — bad relay type
  2. "was not found"                              — GT lookup miss
  3. "was not found in new AutomationTask."       — AT missing a swept key
  4. "not a member of GeneralTask.swept_arguments values" — AT value not in GT list

When `general_task_id` is omitted, validation is skipped entirely — matches
the legacy "skip-validation-with-no-gt" behaviour exercised by
`test_argument_skip_validation_with_no_gt_OK`.
"""

import base64

import pytest

from schema import schema

CREATE_GT = """
mutation CreateGT($created: DateTime!, $argument_lists: [KeyValueListPairInput!]!) {
    create_general_task(input: {
        created: $created
        title: "TEST swept-arg validation"
        description: "Gap 14"
        agent_name: "test"
        subtask_type: OPENQUAKE_HAZARD
        model_type: COMPOSITE
        argument_lists: $argument_lists
    }) {
        general_task {
            id
            argument_lists { k v }
            swept_arguments
        }
    }
}
"""

CREATE_AT = """
mutation CreateAT(
    $created: DateTime!,
    $gt_id: ID,
    $arguments: [KeyValuePairInput!]!,
) {
    create_automation_task(input: {
        general_task_id: $gt_id
        task_type: INVERSION
        state: UNDEFINED
        result: UNDEFINED
        created: $created
        duration: 600
        arguments: $arguments
        environment: [
            { k: "gitref_opensha_ucerf3", v: "ABC" },
            { k: "JAVA", v: "-Xmx24G" }
        ]
    }) {
        task_result {
            id
            general_task_id
            arguments { k v }
            task_type
        }
    }
}
"""


@pytest.fixture
def gt_id(gql_context):
    """Seed a GT with one swept arg (`swept_arg: ["A", "B"]`) and one unswept (`unswept_arg: ["BOOM"]`)."""
    result = schema.execute_sync(
        CREATE_GT,
        variable_values={
            "created": "2026-01-01T00:00:00Z",
            "argument_lists": [
                {"k": "swept_arg", "v": ["A", "B"]},
                {"k": "unswept_arg", "v": ["BOOM"]},
            ],
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_general_task"]["general_task"]["id"]


# ── Group 1: OK cases (validation passes) ─────────────────────────────────────


@pytest.mark.parametrize(
    "arguments, comment",
    [
        ([{"k": "swept_arg", "v": "A"}], "swept_arg only — value in GT list"),
        (
            [{"k": "swept_arg", "v": "A"}, {"k": "unswept_arg", "v": "Q"}],
            "swept_arg + arbitrary unswept_arg",
        ),
    ],
)
def test_argument_validation_OK(gql_context, gt_id, arguments, comment):
    """Mirrors legacy test_argument_validation_OK — AT passes when swept_arg is set
    to a value present in the parent GT's argument_lists.
    """
    result = schema.execute_sync(
        CREATE_AT,
        variable_values={
            "created": "2026-01-01T00:00:00Z",
            "gt_id": gt_id,
            "arguments": arguments,
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    at = result.data["create_automation_task"]["task_result"]
    assert at["arguments"] == arguments


# ── Group 2: validation skipped when no gt_id ─────────────────────────────────


@pytest.mark.parametrize(
    "arguments, comment",
    [
        ([{"k": "unswept_arg", "v": "Q"}], "missing swept_arg — would fail with gt_id"),
        ([{"k": "swept_arg", "v": ""}], "empty swept_arg value — would fail with gt_id"),
        ([{"k": "swept_arg", "v": "NO"}], "swept_arg value not in GT list — would fail with gt_id"),
    ],
)
def test_argument_skip_validation_with_no_gt_OK(gql_context, gt_id, arguments, comment):
    """Mirrors legacy test_argument_skip_validation_with_no_gt_OK — when
    `general_task_id` is omitted, the AT is created regardless of what
    `arguments` it carries. Same fixture is seeded to prove the validator
    isn't accidentally inspecting the seeded GT.
    """
    # NOTE: `gt_id` fixture is invoked to seed a GT, but it's NOT passed in.
    result = schema.execute_sync(
        CREATE_AT,
        variable_values={
            "created": "2026-01-01T00:00:00Z",
            "gt_id": None,
            "arguments": arguments,
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    at = result.data["create_automation_task"]["task_result"]
    assert at["arguments"] == arguments


# ── Group 3: validation FAILs with a useful error ─────────────────────────────


@pytest.mark.parametrize(
    "arguments, expected_substring",
    [
        (
            [{"k": "unswept_arg", "v": "Q"}],
            "swept_arg from GeneralTask.swept_arguments was not found in new AutomationTask.",
        ),
        (
            [{"k": "swept_arg", "v": ""}],
            "not a member of GeneralTask.swept_arguments values",
        ),
        (
            [{"k": "swept_arg", "v": "NO"}],
            "not a member of GeneralTask.swept_arguments values",
        ),
    ],
)
def test_argument_validation_expected_to_FAIL(gql_context, gt_id, arguments, expected_substring):
    """Mirrors legacy test_argument_validation_expected_to_FAIL — invalid
    AT arguments against a real GT must produce one of the four legacy
    error messages, and no AutomationTask is created.
    """
    result = schema.execute_sync(
        CREATE_AT,
        variable_values={
            "created": "2026-01-01T00:00:00Z",
            "gt_id": gt_id,
            "arguments": arguments,
        },
        context_value=gql_context,
    )
    assert result.errors is not None, "expected a validation error"
    messages = " ".join(str(e) for e in result.errors)
    assert expected_substring in messages, f"missing {expected_substring!r} in: {messages}"
    # The mutation field returns None when the resolver raises.
    assert result.data is None or result.data.get("create_automation_task") is None


# ── Group 4: invalid gt_id ────────────────────────────────────────────────────


def test_invalid_gt_id_not_found(gql_context, gt_id):
    """Mirrors legacy test_invalid_gt_id_expected_to_FAIL — non-existent GT
    surfaces "was not found".
    """
    fake_gt = base64.b64encode(b"GeneralTask:99999").decode()
    result = schema.execute_sync(
        CREATE_AT,
        variable_values={
            "created": "2026-01-01T00:00:00Z",
            "gt_id": fake_gt,
            "arguments": [],
        },
        context_value=gql_context,
    )
    assert result.errors is not None
    assert "was not found" in " ".join(str(e) for e in result.errors)
    assert result.data is None or result.data.get("create_automation_task") is None


def test_invalid_gt_id_wrong_type(gql_context, gt_id):
    """Mirrors legacy test_invalid_gt_id_expected_to_FAIL — wrong-typed GT
    surfaces "is not a `GeneralTask`".
    """
    bad_gt = base64.b64encode(b"FasterTurtle:1").decode()
    result = schema.execute_sync(
        CREATE_AT,
        variable_values={
            "created": "2026-01-01T00:00:00Z",
            "gt_id": bad_gt,
            "arguments": [],
        },
        context_value=gql_context,
    )
    assert result.errors is not None
    assert "is not a `GeneralTask`" in " ".join(str(e) for e in result.errors)
    assert result.data is None or result.data.get("create_automation_task") is None
