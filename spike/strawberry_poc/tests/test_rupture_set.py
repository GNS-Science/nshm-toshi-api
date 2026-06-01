"""
Tests for RuptureSet — relay ID encoding, produced_by union resolution.

Key feasibility signals tested here:
  1. relay.GlobalID round-trip: base64("TypeName:id") matches Graphene format
  2. Union type (produced_by): resolves correctly to RuptureGenerationTask
  3. File table separate from Thing table: create + list work independently

Field and mutation names use snake_case (auto_camel_case=False on schema).
Mutations return payload wrapper types matching the Graphene API shape.
"""

import base64

import pytest

from schema import schema

# ── Helpers ───────────────────────────────────────────────────────────────────

CREATE_RUPTURE_SET_MUTATION = """
mutation CreateRuptureSet($input: CreateRuptureSetInput!) {
    create_rupture_set(input: $input) {
        rupture_set {
            id
            file_name
            md5_digest
            file_size
            created
            fault_models
            metrics { k v }
            produced_by {
                id
                state
                result
            }
        }
    }
}
"""

LIST_RUPTURE_SETS_QUERY = """
query {
    rupture_sets {
        edges {
            node {
                id
                file_name
                produced_by {
                    id
                }
            }
        }
    }
}
"""

NODE_QUERY = """
query GetNode($id: ID!) {
    node(id: $id) {
        id
        ... on RuptureSet {
            file_name
            md5_digest
            produced_by {
                id
                state
            }
        }
    }
}
"""


def _make_rupture_generation_task(gql_context):
    """Seed a RuptureGenerationTask directly via the data layer."""
    from data.dynamo import create_thing

    data = create_thing(
        gql_context["dynamodb"],
        "RuptureGenerationTask",
        {"state": "done", "result": "success", "created": "2024-01-01T00:00:00Z"},
    )
    raw_id = data["object_id"]
    encoded = base64.b64encode(f"RuptureGenerationTask:{raw_id}".encode()).decode()
    return encoded, raw_id


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def rupture_gen_task_id(gql_context):
    """Returns the relay GlobalID string for a seeded RuptureGenerationTask."""
    encoded, _ = _make_rupture_generation_task(gql_context)
    return encoded


@pytest.fixture(scope="module")
def created_rupture_set(gql_context, rupture_gen_task_id):
    """Creates a RuptureSet and returns the result dict."""
    result = schema.execute_sync(
        CREATE_RUPTURE_SET_MUTATION,
        variable_values={
            "input": {
                "file_name": "rupture_set_v1.zip",
                "produced_by": rupture_gen_task_id,
                "md5_digest": "abc123",
                "file_size": 1048576,
                "created": "2024-02-01T00:00:00Z",
                "fault_models": ["CFM_0_9_SANSTVZ_D90"],
                "metrics": [{"k": "num_ruptures", "v": "200000"}],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_rupture_set"]["rupture_set"]


# ── Tests ──────────────────────────────────────────────────────────────────────


def test_rupture_set_id_encoding(created_rupture_set):
    """Relay global ID must be base64('RuptureSet:<raw_id>')."""
    gid = created_rupture_set["id"]
    decoded = base64.b64decode(gid).decode()
    assert decoded.startswith("RuptureSet:"), f"Unexpected ID format: {decoded}"


def test_rupture_gen_task_id_encoding(rupture_gen_task_id):
    """Seeded RuptureGenerationTask ID must be base64('RuptureGenerationTask:<raw_id>')."""
    decoded = base64.b64decode(rupture_gen_task_id).decode()
    assert decoded.startswith("RuptureGenerationTask:")


def test_rupture_set_fields(created_rupture_set):
    assert created_rupture_set["file_name"] == "rupture_set_v1.zip"
    assert created_rupture_set["md5_digest"] == "abc123"
    assert created_rupture_set["file_size"] == 1048576
    assert created_rupture_set["created"] == "2024-02-01T00:00:00Z"
    assert created_rupture_set["fault_models"] == ["CFM_0_9_SANSTVZ_D90"]
    assert created_rupture_set["metrics"] == [{"k": "num_ruptures", "v": "200000"}]


def test_produced_by_resolved(created_rupture_set, rupture_gen_task_id):
    """produced_by must resolve to the correct RuptureGenerationTask."""
    produced_by = created_rupture_set["produced_by"]
    assert produced_by is not None
    assert produced_by["id"] == rupture_gen_task_id
    assert produced_by["state"] == "DONE"
    assert produced_by["result"] == "SUCCESS"


def test_list_rupture_sets(gql_context, created_rupture_set):
    result = schema.execute_sync(LIST_RUPTURE_SETS_QUERY, context_value=gql_context)
    assert result.errors is None, result.errors

    edges = result.data["rupture_sets"]["edges"]
    assert len(edges) >= 1
    ids = [e["node"]["id"] for e in edges]
    assert created_rupture_set["id"] in ids


def test_node_lookup(gql_context, created_rupture_set, rupture_gen_task_id):
    """Node interface lookup must return the correct RuptureSet with produced_by."""
    result = schema.execute_sync(
        NODE_QUERY,
        variable_values={"id": created_rupture_set["id"]},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors

    node = result.data["node"]
    assert node["id"] == created_rupture_set["id"]
    assert node["file_name"] == "rupture_set_v1.zip"
    assert node["md5_digest"] == "abc123"
    assert node["produced_by"]["id"] == rupture_gen_task_id
    assert node["produced_by"]["state"] == "DONE"


def test_relay_ids_are_different_types(created_rupture_set, rupture_gen_task_id):
    """File and Thing objects have different type prefixes in their global IDs."""
    rs_type = base64.b64decode(created_rupture_set["id"]).decode().split(":")[0]
    rgt_type = base64.b64decode(rupture_gen_task_id).decode().split(":")[0]
    assert rs_type == "RuptureSet"
    assert rgt_type == "RuptureGenerationTask"
    assert rs_type != rgt_type
