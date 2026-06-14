"""
Tests for InversionSolution, ScaledInversionSolution, and the append-tables mutation.

Key feasibility signals:
  1. InversionSolution.produced_by — resolves AutomationTaskUnion (RuptureGenerationTask)
  2. LabelledTableRelation — inline embedded type round-trips through DynamoDB
  3. append_inversion_solution_tables — mutation appends tables to existing record
  4. ScaledInversionSolution.source_solution — resolves SourceSolutionUnion (InversionSolution)
  5. Predecessors — inline embedded type with computed typename/relationship
"""

import base64

import pytest

from schema import schema

# ── Mutation / query strings ──────────────────────────────────────────────────

CREATE_INVERSION_SOLUTION_MUTATION = """
mutation CreateInversionSolution($input: CreateInversionSolutionInput!) {
    create_inversion_solution(input: $input) {
        ok
        inversion_solution {
            id
            file_name
            md5_digest
            file_size
            created
            meta { k v }
            metrics { k v }
            tables {
                table_id
                table_type
                label
            }
            produced_by {
                ... on RuptureGenerationTask {
                    id
                    state
                    result
                }
            }
            predecessors {
                id
                depth
                relationship
            }
        }
    }
}
"""

APPEND_TABLES_MUTATION = """
mutation AppendTables($input: AppendInversionSolutionTablesInput!) {
    append_inversion_solution_tables(input: $input) {
        ok
        inversion_solution {
            id
            tables {
                table_id
                table_type
                label
            }
        }
    }
}
"""

CREATE_SCALED_MUTATION = """
mutation CreateScaled($input: CreateScaledInversionSolutionInput!) {
    create_scaled_inversion_solution(input: $input) {
        ok
        solution {
            id
            file_name
            source_solution {
                ... on InversionSolution {
                    id
                    file_name
                }
            }
            predecessors {
                id
                depth
                typename
                relationship
            }
        }
    }
}
"""

NODE_QUERY = """
query GetNode($id: ID!) {
    node(id: $id) {
        id
        ... on InversionSolution {
            file_name
            tables {
                table_id
                table_type
            }
        }
    }
}
"""


# ── Helpers ───────────────────────────────────────────────────────────────────


def _seed_rupture_gen_task(gql_context):
    from data.dynamo import create_thing

    data = create_thing(
        gql_context["dynamodb"],
        "RuptureGenerationTask",
        {"state": "done", "result": "success", "created": "2024-01-01T00:00:00Z"},
    )
    raw_id = data["object_id"]
    return base64.b64encode(f"RuptureGenerationTask:{raw_id}".encode()).decode()


def _seed_toshi_file(gql_context, label="table.hdf5"):
    """Seed a plain ToshiFile to act as a table target."""
    from data.dynamo import create_file

    data = create_file(
        gql_context["dynamodb"],
        "ToshiFile",
        {"file_name": label},
    )
    raw_id = data["object_id"]
    return base64.b64encode(f"File:{raw_id}".encode()).decode()


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def rgt_id(gql_context):
    return _seed_rupture_gen_task(gql_context)


@pytest.fixture(scope="module")
def table_file_id(gql_context):
    return _seed_toshi_file(gql_context)


@pytest.fixture(scope="module")
def created_inversion_solution(gql_context, rgt_id, table_file_id):
    result = schema.execute_sync(
        CREATE_INVERSION_SOLUTION_MUTATION,
        variable_values={
            "input": {
                "file_name": "inversion_solution_v1.zip",
                "produced_by": rgt_id,
                "md5_digest": "deadbeef",
                "file_size": 2097152,
                "created": "2024-03-01T00:00:00Z",
                "meta": [{"k": "region", "v": "NZ"}],
                "metrics": [{"k": "total_rate_weighting", "v": "1.0"}],
                "tables": [
                    {
                        "table_id": table_file_id,
                        "table_type": "MFD_CURVES",
                        "label": "initial",
                    }
                ],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_inversion_solution"]["inversion_solution"]


# ── InversionSolution tests ───────────────────────────────────────────────────


def test_inversion_solution_id_encoding(created_inversion_solution):
    gid = created_inversion_solution["id"]
    decoded = base64.b64decode(gid).decode()
    assert decoded.startswith("InversionSolution:"), f"Unexpected ID: {decoded}"


def test_inversion_solution_fields(created_inversion_solution):
    is_ = created_inversion_solution
    assert is_["file_name"] == "inversion_solution_v1.zip"
    assert is_["md5_digest"] == "deadbeef"
    assert is_["file_size"] == 2097152
    assert is_["created"] == "2024-03-01T00:00:00Z"
    assert is_["meta"] == [{"k": "region", "v": "NZ"}]
    assert is_["metrics"] == [{"k": "total_rate_weighting", "v": "1.0"}]


def test_inversion_solution_table(created_inversion_solution, table_file_id):
    tables = created_inversion_solution["tables"]
    assert tables is not None
    assert len(tables) == 1
    t = tables[0]
    assert t["table_id"] == table_file_id
    assert t["table_type"] == "MFD_CURVES"
    assert t["label"] == "initial"


def test_inversion_solution_produced_by(created_inversion_solution, rgt_id):
    pb = created_inversion_solution["produced_by"]
    assert pb is not None
    assert pb["id"] == rgt_id
    assert pb["state"] == "DONE"
    assert pb["result"] == "SUCCESS"


def test_inversion_solution_no_predecessors_by_default(created_inversion_solution):
    assert created_inversion_solution["predecessors"] is None


def test_node_lookup(gql_context, created_inversion_solution, table_file_id):
    result = schema.execute_sync(
        NODE_QUERY,
        variable_values={"id": created_inversion_solution["id"]},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["id"] == created_inversion_solution["id"]
    assert node["file_name"] == "inversion_solution_v1.zip"
    assert node["tables"][0]["table_id"] == table_file_id


# ── Append tables mutation ────────────────────────────────────────────────────


def test_append_inversion_solution_tables(gql_context, created_inversion_solution, table_file_id):
    """append_inversion_solution_tables must add a new table without removing existing ones."""
    extra_file_id = _seed_toshi_file(gql_context, "hazard.hdf5")
    result = schema.execute_sync(
        APPEND_TABLES_MUTATION,
        variable_values={
            "input": {
                "id": created_inversion_solution["id"],
                "tables": [
                    {
                        "table_id": extra_file_id,
                        "table_type": "HAZARD_GRIDDED",
                        "label": "appended",
                    }
                ],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    tables = result.data["append_inversion_solution_tables"]["inversion_solution"]["tables"]
    assert len(tables) == 2, f"Expected 2 tables, got {len(tables)}"
    types = {t["table_type"] for t in tables}
    assert "MFD_CURVES" in types
    assert "HAZARD_GRIDDED" in types


# ── ScaledInversionSolution tests ─────────────────────────────────────────────


@pytest.fixture(scope="module")
def created_scaled(gql_context, created_inversion_solution):
    """Create a ScaledInversionSolution whose source_solution points to the InversionSolution."""
    is_id = created_inversion_solution["id"]
    result = schema.execute_sync(
        CREATE_SCALED_MUTATION,
        variable_values={
            "input": {
                "file_name": "scaled_v1.zip",
                "source_solution": is_id,
                "created": "2024-04-01T00:00:00Z",
                "predecessors": [{"id": is_id, "depth": -1}],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_scaled_inversion_solution"]["solution"]


def test_scaled_id_encoding(created_scaled):
    decoded = base64.b64decode(created_scaled["id"]).decode()
    assert decoded.startswith("ScaledInversionSolution:")


def test_scaled_source_solution_resolves(created_scaled, created_inversion_solution):
    ss = created_scaled["source_solution"]
    assert ss is not None
    assert ss["id"] == created_inversion_solution["id"]
    assert ss["file_name"] == "inversion_solution_v1.zip"


def test_scaled_predecessor_relationship(created_scaled, created_inversion_solution):
    preds = created_scaled["predecessors"]
    assert preds is not None and len(preds) == 1
    p = preds[0]
    assert p["id"] == created_inversion_solution["id"]
    assert p["depth"] == -1
    assert p["typename"] == "InversionSolution"
    assert p["relationship"] == "Parent"
