"""
Tests for the Thing and AutomationTaskInterface adoptions (ADR-002 Category 1).

weka uses `... on Thing { ... }` and `... on AutomationTaskInterface { ... }`
fragment queries to traverse the task graph. These tests verify those
fragments resolve correctly against the POC.
"""

import pytest

from graphql_api.schema import schema


CREATE_GT_MUTATION = """
mutation($input: CreateGeneralTaskInput!) {
    create_general_task(input: $input) { general_task { id } }
}
"""

CREATE_AT_MUTATION = """
mutation($input: CreateAutomationTaskInput!) {
    create_automation_task(input: $input) { task_result { id } }
}
"""

CREATE_TASK_RELATION_MUTATION = """
mutation($child_id: ID!, $parent_id: ID!) {
    create_task_relation(child_id: $child_id, parent_id: $parent_id) { ok }
}
"""

# `... on Thing { children { ... } }` — weka pattern, generic Thing query
THING_FRAGMENT_QUERY = """
query($id: ID!) {
    node(id: $id) {
        id
        __typename
        ... on Thing {
            created
            children { edges { node { child { __typename ... on AutomationTask { id } } } } }
            parents { edges { node { parent { __typename ... on GeneralTask { id title } } } } }
        }
    }
}
"""

# `... on AutomationTaskInterface { parents { ... } }` — weka deep traversal
AT_INTERFACE_QUERY = """
query($id: ID!) {
    node(id: $id) {
        id
        __typename
        ... on AutomationTaskInterface {
            state
            result
            task_type
            duration
            arguments { k v }
            parents { edges { node { parent { __typename ... on GeneralTask { id title } } } } }
        }
    }
}
"""


@pytest.fixture(scope="module")
def gt_with_child_at(gql_context):
    """Seed: GeneralTask → AutomationTask (linked as child)."""
    gt = schema.execute_sync(
        CREATE_GT_MUTATION,
        variable_values={"input": {"title": "thing-iface parent GT", "agent_name": "pytest"}},
        context_value=gql_context,
    )
    assert gt.errors is None, gt.errors
    gt_id = gt.data["create_general_task"]["general_task"]["id"]

    at = schema.execute_sync(
        CREATE_AT_MUTATION,
        variable_values={
            "input": {
                "state": "DONE",
                "result": "SUCCESS",
                "task_type": "INVERSION",
                "created": "2024-01-01T00:00:00Z",
                "duration": 42.5,
                "arguments": [{"k": "x", "v": "y"}],
            }
        },
        context_value=gql_context,
    )
    assert at.errors is None, at.errors
    at_id = at.data["create_automation_task"]["task_result"]["id"]

    rel = schema.execute_sync(
        CREATE_TASK_RELATION_MUTATION,
        variable_values={"parent_id": gt_id, "child_id": at_id},
        context_value=gql_context,
    )
    assert rel.errors is None, rel.errors
    return {"gt_id": gt_id, "at_id": at_id}


# ── Thing interface tests ─────────────────────────────────────────────────────


def test_thing_interface_in_sdl():
    """The Thing interface is declared and has the expected field set."""
    sdl = schema.as_str()
    import re

    assert re.search(r"^interface Thing", sdl, re.MULTILINE) is not None
    # Field signatures
    assert "files(" in sdl  # relay connection on Thing
    assert "parents(" in sdl
    assert "children(" in sdl


def test_thing_attached_to_all_concrete_types():
    """Every Thing-like concrete type implements Thing in the SDL."""
    sdl = schema.as_str()
    import re

    matches = {
        tn: impl
        for tn, impl in re.findall(r"type (\w+) implements ([\w &]+)", sdl)
        if "Thing" in impl
    }
    # The 7 types ADR-002 specifies
    expected = {
        "GeneralTask",
        "AutomationTask",
        "RuptureGenerationTask",
        "OpenquakeHazardTask",
        "OpenquakeHazardSolution",
        "OpenquakeHazardConfig",
        "StrongMotionStation",
    }
    assert expected.issubset(matches.keys()), f"missing: {expected - matches.keys()}"


def test_thing_fragment_query_resolves_children(gql_context, gt_with_child_at):
    """The weka-style `... on Thing { children { edges { node { child } } } }` query works."""
    result = schema.execute_sync(
        THING_FRAGMENT_QUERY,
        variable_values={"id": gt_with_child_at["gt_id"]},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["__typename"] == "GeneralTask"
    child_edges = node["children"]["edges"]
    assert len(child_edges) == 1
    child = child_edges[0]["node"]["child"]
    assert child["__typename"] == "AutomationTask"
    assert child["id"] == gt_with_child_at["at_id"]


def test_thing_fragment_query_resolves_parents(gql_context, gt_with_child_at):
    """The same fragment but walking from the child up to its parent GT."""
    result = schema.execute_sync(
        THING_FRAGMENT_QUERY,
        variable_values={"id": gt_with_child_at["at_id"]},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["__typename"] == "AutomationTask"
    parent_edges = node["parents"]["edges"]
    assert len(parent_edges) == 1
    parent = parent_edges[0]["node"]["parent"]
    assert parent["__typename"] == "GeneralTask"
    assert parent["id"] == gt_with_child_at["gt_id"]
    assert parent["title"] == "thing-iface parent GT"


# ── AutomationTaskInterface tests ─────────────────────────────────────────────


def test_automation_task_interface_in_sdl():
    """AutomationTaskInterface is declared with the expected fields."""
    sdl = schema.as_str()
    import re

    assert re.search(r"^interface AutomationTaskInterface", sdl, re.MULTILINE) is not None
    matches = {
        tn: impl
        for tn, impl in re.findall(r"type (\w+) implements ([\w &]+)", sdl)
        if "AutomationTaskInterface" in impl
    }
    expected = {"AutomationTask", "RuptureGenerationTask", "OpenquakeHazardTask"}
    assert expected.issubset(matches.keys()), f"missing: {expected - matches.keys()}"


def test_automation_task_interface_fragment_resolves(gql_context, gt_with_child_at):
    """The weka-pattern `... on AutomationTaskInterface { parents { ... } }` query works."""
    result = schema.execute_sync(
        AT_INTERFACE_QUERY,
        variable_values={"id": gt_with_child_at["at_id"]},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["__typename"] == "AutomationTask"
    assert node["state"] == "DONE"
    assert node["result"] == "SUCCESS"
    assert node["task_type"] == "INVERSION"
    assert node["duration"] == 42.5
    assert node["arguments"] == [{"k": "x", "v": "y"}]
    # Parent traversal via the interface
    parent = node["parents"]["edges"][0]["node"]["parent"]
    assert parent["__typename"] == "GeneralTask"
    assert parent["id"] == gt_with_child_at["gt_id"]
