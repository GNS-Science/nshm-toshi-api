"""
Tests for OpenquakeHazardTask, OpenquakeHazardSolution, and OpenquakeHazardConfig.

Key feasibility signals:
  1. OpenquakeHazardSolution.produced_by → resolves back to the creating OpenquakeHazardTask
  2. update_openquake_hazard_task → links hazard_solution onto an existing task
  3. task.hazard_solution → resolves OpenquakeHazardSolution (bidirectional link)
  4. OpenquakeHazardConfig.template_archive → resolves ToshiFile
  5. OpenquakeHazardConfig.source_models → resolves OpenquakeNrmlUnion (ToshiFile case)
"""

import base64

import pytest

from schema import schema

# ── Mutation / query strings ──────────────────────────────────────────────────

CREATE_OQ_TASK_MUTATION = """
mutation CreateOQTask($input: CreateOpenquakeHazardTaskInput!) {
    create_openquake_hazard_task(input: $input) {
        ok
        openquake_hazard_task {
            id
            state
            result
            task_type
            created
            executor
            arguments { k v }
        }
    }
}
"""

CREATE_OQ_SOLUTION_MUTATION = """
mutation CreateOQSolution($input: CreateOpenquakeHazardSolutionInput!) {
    create_openquake_hazard_solution(input: $input) {
        ok
        openquake_hazard_solution {
            id
            created
            task_type
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

UPDATE_OQ_TASK_MUTATION = """
mutation UpdateOQTask($input: UpdateOpenquakeHazardTaskInput!) {
    update_openquake_hazard_task(input: $input) {
        ok
        openquake_hazard_task {
            id
            state
            result
            hazard_solution {
                id
                task_type
            }
        }
    }
}
"""

CREATE_OQ_CONFIG_MUTATION = """
mutation CreateOQConfig($input: CreateOpenquakeHazardConfigInput!) {
    create_openquake_hazard_config(input: $input) {
        ok
        config {
            id
            created
            template_archive {
                id
                file_name
            }
            source_models {
                ... on File {
                    id
                    file_name
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
        ... on OpenquakeHazardSolution {
            task_type
            produced_by {
                id
            }
        }
        ... on OpenquakeHazardTask {
            state
            hazard_solution {
                id
            }
        }
        ... on OpenquakeHazardConfig {
            created
            template_archive {
                id
            }
        }
    }
}
"""


# ── Helpers ───────────────────────────────────────────────────────────────────


def _seed_toshi_file(gql_context, name="archive.zip"):
    from data.dynamo import create_file

    data = create_file(gql_context["dynamodb"], "ToshiFile", {"file_name": name})
    raw_id = data["object_id"]
    return base64.b64encode(f"File:{raw_id}".encode()).decode()


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def created_oq_task(gql_context):
    result = schema.execute_sync(
        CREATE_OQ_TASK_MUTATION,
        variable_values={
            "input": {
                "state": "STARTED",
                "result": "UNDEFINED",
                "created": "2024-05-01T00:00:00Z",
                "task_type": "HAZARD",
                "executor": "openquake-3.16",
                "arguments": [{"k": "max_sites_disagg", "v": "10"}],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_openquake_hazard_task"]["openquake_hazard_task"]


@pytest.fixture(scope="module")
def created_oq_solution(gql_context, created_oq_task):
    result = schema.execute_sync(
        CREATE_OQ_SOLUTION_MUTATION,
        variable_values={
            "input": {
                "produced_by": created_oq_task["id"],
                "task_type": "HAZARD",
                "created": "2024-05-01T06:00:00Z",
                "metrics": [{"k": "num_sites", "v": "42"}],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_openquake_hazard_solution"]["openquake_hazard_solution"]


# ── OpenquakeHazardTask tests ─────────────────────────────────────────────────


def test_oq_task_id_encoding(created_oq_task):
    decoded = base64.b64decode(created_oq_task["id"]).decode()
    assert decoded.startswith("OpenquakeHazardTask:"), f"Unexpected ID: {decoded}"


def test_oq_task_fields(created_oq_task):
    t = created_oq_task
    assert t["state"] == "STARTED"
    assert t["result"] == "UNDEFINED"
    assert t["task_type"] == "HAZARD"
    assert t["executor"] == "openquake-3.16"
    assert t["arguments"] == [{"k": "max_sites_disagg", "v": "10"}]


# ── OpenquakeHazardSolution tests ─────────────────────────────────────────────


def test_oq_solution_id_encoding(created_oq_solution):
    decoded = base64.b64decode(created_oq_solution["id"]).decode()
    assert decoded.startswith("OpenquakeHazardSolution:")


def test_oq_solution_fields(created_oq_solution):
    s = created_oq_solution
    assert s["task_type"] == "HAZARD"
    assert s["created"] == "2024-05-01T06:00:00Z"
    assert s["metrics"] == [{"k": "num_sites", "v": "42"}]


def test_oq_solution_produced_by(created_oq_solution, created_oq_task):
    pb = created_oq_solution["produced_by"]
    assert pb is not None
    assert pb["id"] == created_oq_task["id"]
    assert pb["state"] == "STARTED"


def test_oq_solution_node_lookup(gql_context, created_oq_solution, created_oq_task):
    result = schema.execute_sync(
        NODE_QUERY,
        variable_values={"id": created_oq_solution["id"]},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["id"] == created_oq_solution["id"]
    assert node["task_type"] == "HAZARD"
    assert node["produced_by"]["id"] == created_oq_task["id"]


# ── update_openquake_hazard_task tests ────────────────────────────────────────


@pytest.fixture(scope="module")
def updated_oq_task(gql_context, created_oq_task, created_oq_solution):
    result = schema.execute_sync(
        UPDATE_OQ_TASK_MUTATION,
        variable_values={
            "input": {
                "task_id": created_oq_task["id"],
                "state": "DONE",
                "result": "SUCCESS",
                "hazard_solution": created_oq_solution["id"],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["update_openquake_hazard_task"]["openquake_hazard_task"]


def test_update_oq_task_state(updated_oq_task):
    assert updated_oq_task["state"] == "DONE"
    assert updated_oq_task["result"] == "SUCCESS"


def test_update_oq_task_hazard_solution(updated_oq_task, created_oq_solution):
    hs = updated_oq_task["hazard_solution"]
    assert hs is not None
    assert hs["id"] == created_oq_solution["id"]
    assert hs["task_type"] == "HAZARD"


def test_updated_task_node_lookup(gql_context, updated_oq_task, created_oq_solution):
    result = schema.execute_sync(
        NODE_QUERY,
        variable_values={"id": updated_oq_task["id"]},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["state"] == "DONE"
    assert node["hazard_solution"]["id"] == created_oq_solution["id"]


# ── OpenquakeHazardConfig tests ───────────────────────────────────────────────


@pytest.fixture(scope="module")
def template_archive_id(gql_context):
    return _seed_toshi_file(gql_context, "config_template.zip")


@pytest.fixture(scope="module")
def source_model_id(gql_context):
    return _seed_toshi_file(gql_context, "source_model.xml")


@pytest.fixture(scope="module")
def created_oq_config(gql_context, template_archive_id, source_model_id):
    result = schema.execute_sync(
        CREATE_OQ_CONFIG_MUTATION,
        variable_values={
            "input": {
                "template_archive": template_archive_id,
                "source_models": [source_model_id],
                "created": "2024-04-15T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_openquake_hazard_config"]["config"]


def test_oq_config_id_encoding(created_oq_config):
    decoded = base64.b64decode(created_oq_config["id"]).decode()
    assert decoded.startswith("OpenquakeHazardConfig:")


def test_oq_config_created(created_oq_config):
    assert created_oq_config["created"] == "2024-04-15T00:00:00Z"


def test_oq_config_template_archive(created_oq_config, template_archive_id):
    ta = created_oq_config["template_archive"]
    assert ta is not None
    assert ta["id"] == template_archive_id
    assert ta["file_name"] == "config_template.zip"


def test_oq_config_source_models(created_oq_config, source_model_id):
    sm = created_oq_config["source_models"]
    assert sm is not None and len(sm) == 1
    assert sm[0]["id"] == source_model_id
    assert sm[0]["file_name"] == "source_model.xml"


def test_oq_config_node_lookup(gql_context, created_oq_config, template_archive_id):
    result = schema.execute_sync(
        NODE_QUERY,
        variable_values={"id": created_oq_config["id"]},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["created"] == "2024-04-15T00:00:00Z"
    assert node["template_archive"]["id"] == template_archive_id


# ── DISAGG variant (COVERAGE_GAPS.md gap 4) ───────────────────────────────────

CREATE_OQ_TASK_DISAGG_MUTATION = """
mutation CreateDisaggTask($input: CreateOpenquakeHazardTaskInput!) {
    create_openquake_hazard_task(input: $input) {
        ok
        openquake_hazard_task { id task_type state result }
    }
}
"""

NODE_TASK_TASK_TYPE_QUERY = """
query GetNode($id: ID!) {
    node(id: $id) {
        id
        ... on OpenquakeHazardTask { task_type state }
    }
}
"""


@pytest.fixture(scope="module")
def disagg_oq_task(gql_context):
    result = schema.execute_sync(
        CREATE_OQ_TASK_DISAGG_MUTATION,
        variable_values={
            "input": {
                "state": "DONE",
                "result": "SUCCESS",
                "created": "2024-06-01T00:00:00Z",
                "task_type": "DISAGG",
                "executor": "openquake-3.16",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_openquake_hazard_task"]["openquake_hazard_task"]


def test_create_disagg_oq_task(disagg_oq_task):
    """task_type DISAGG round-trips through create mutation."""
    assert disagg_oq_task["task_type"] == "DISAGG"
    assert disagg_oq_task["state"] == "DONE"


def test_disagg_oq_task_node_lookup(gql_context, disagg_oq_task):
    result = schema.execute_sync(
        NODE_TASK_TASK_TYPE_QUERY,
        variable_values={"id": disagg_oq_task["id"]},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    assert result.data["node"]["task_type"] == "DISAGG"


# ── JSON tree fields (COVERAGE_GAPS.md gap 5) ─────────────────────────────────

CREATE_OQ_TASK_WITH_TREES_MUTATION = """
mutation CreateTaskTrees($input: CreateOpenquakeHazardTaskInput!) {
    create_openquake_hazard_task(input: $input) {
        ok
        openquake_hazard_task {
            id
            task_type
            model_type
            srm_logic_tree
            gmcm_logic_tree
            openquake_config
        }
    }
}
"""


@pytest.fixture(scope="module")
def oq_task_with_trees(gql_context):
    import json

    result = schema.execute_sync(
        CREATE_OQ_TASK_WITH_TREES_MUTATION,
        variable_values={
            "input": {
                "state": "DONE",
                "result": "SUCCESS",
                "created": "2024-06-02T00:00:00Z",
                "task_type": "HAZARD",
                "model_type": "CRUSTAL",
                "srm_logic_tree": json.dumps({"srm": "tree"}),
                "gmcm_logic_tree": json.dumps({"gmcm": "tree"}),
                "openquake_config": json.dumps({"calc": "config"}),
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_openquake_hazard_task"]["openquake_hazard_task"]


def test_oq_task_srm_logic_tree_round_trip(oq_task_with_trees):
    import json

    assert json.loads(oq_task_with_trees["srm_logic_tree"]) == {"srm": "tree"}


def test_oq_task_gmcm_logic_tree_round_trip(oq_task_with_trees):
    import json

    assert json.loads(oq_task_with_trees["gmcm_logic_tree"]) == {"gmcm": "tree"}


def test_oq_task_openquake_config_round_trip(oq_task_with_trees):
    import json

    assert json.loads(oq_task_with_trees["openquake_config"]) == {"calc": "config"}


def test_oq_task_model_type(oq_task_with_trees):
    assert oq_task_with_trees["model_type"] == "CRUSTAL"


# ── OpenquakeHazardSolution archive fields (COVERAGE_GAPS.md gap 6) ───────────

CREATE_OQ_SOLUTION_FULL_MUTATION = """
mutation CreateSolutionFull($input: CreateOpenquakeHazardSolutionInput!) {
    create_openquake_hazard_solution(input: $input) {
        ok
        openquake_hazard_solution {
            id
            task_type
            csv_archive { ... on File { id file_name } }
            hdf5_archive { ... on File { id file_name } }
            task_args { ... on File { id file_name } }
            predecessors { id depth relationship }
        }
    }
}
"""


@pytest.fixture(scope="module")
def csv_archive_id(gql_context):
    return _seed_toshi_file(gql_context, "results.csv")


@pytest.fixture(scope="module")
def hdf5_archive_id(gql_context):
    return _seed_toshi_file(gql_context, "results.hdf5")


@pytest.fixture(scope="module")
def task_args_id(gql_context):
    return _seed_toshi_file(gql_context, "args.json")


@pytest.fixture(scope="module")
def oq_solution_with_archives(
    gql_context, created_oq_task, csv_archive_id, hdf5_archive_id, task_args_id
):
    result = schema.execute_sync(
        CREATE_OQ_SOLUTION_FULL_MUTATION,
        variable_values={
            "input": {
                "produced_by": created_oq_task["id"],
                "task_type": "HAZARD",
                "created": "2024-06-03T00:00:00Z",
                "csv_archive": csv_archive_id,
                "hdf5_archive": hdf5_archive_id,
                "task_args": task_args_id,
                "predecessors": [{"id": csv_archive_id, "depth": -1}],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_openquake_hazard_solution"]["openquake_hazard_solution"]


def test_oq_solution_csv_archive_resolves(oq_solution_with_archives, csv_archive_id):
    assert oq_solution_with_archives["csv_archive"]["id"] == csv_archive_id
    assert oq_solution_with_archives["csv_archive"]["file_name"] == "results.csv"


def test_oq_solution_hdf5_archive_resolves(oq_solution_with_archives, hdf5_archive_id):
    assert oq_solution_with_archives["hdf5_archive"]["id"] == hdf5_archive_id


def test_oq_solution_task_args_resolves(oq_solution_with_archives, task_args_id):
    assert oq_solution_with_archives["task_args"]["id"] == task_args_id


def test_oq_solution_predecessors(oq_solution_with_archives, csv_archive_id):
    preds = oq_solution_with_archives["predecessors"]
    assert preds is not None
    assert len(preds) == 1
    assert preds[0]["id"] == csv_archive_id
    assert preds[0]["depth"] == -1
    assert preds[0]["relationship"].lower() == "parent"


# ── Legacy OpenquakeHazardTask.config field ───────────────────────────────────
#
# Old OpenquakeHazardTask records (created before the field was deprecated in
# Graphene) carry a `config` attribute holding the relay GlobalID of an
# OpenquakeHazardConfig. Runzi's AutomationTaskPageQuery still selects
# `config { id created source_models { ... } template_archive { ... } }` on
# those tasks. The Strawberry schema needs to keep that field around (as
# deprecated, read-only) for drop-in client parity. Regression test for the
# error reproduced on the test deployment: "Cannot query field 'config' on
# type 'OpenquakeHazardTask'."

OQ_TASK_LEGACY_CONFIG_QUERY = """
query GetTaskWithLegacyConfig($id: ID!) {
    node(id: $id) {
        id
        ... on OpenquakeHazardTask {
            config {
                id
                created
                template_archive { id file_name }
                source_models {
                    ... on File { id file_name }
                }
            }
        }
    }
}
"""


@pytest.fixture(scope="module")
def legacy_oq_task_with_config(gql_context, created_oq_config):
    """Seed a legacy-shape OpenquakeHazardTask carrying the deprecated `config`
    GlobalID directly via create_thing (the field is no longer accepted by the
    create mutation)."""
    from data.dynamo import create_thing  # noqa: PLC0415

    data = create_thing(
        gql_context["dynamodb"],
        "OpenquakeHazardTask",
        {
            "state": "DONE",
            "result": "SUCCESS",
            "created": "2024-05-01T00:00:00Z",
            "task_type": "HAZARD",
            "config": created_oq_config["id"],
        },
    )
    return base64.b64encode(f"OpenquakeHazardTask:{data['object_id']}".encode()).decode()


def test_oq_task_legacy_config_field_resolves(
    gql_context, legacy_oq_task_with_config, created_oq_config, template_archive_id
):
    result = schema.execute_sync(
        OQ_TASK_LEGACY_CONFIG_QUERY,
        variable_values={"id": legacy_oq_task_with_config},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    config = result.data["node"]["config"]
    assert config is not None
    assert config["id"] == created_oq_config["id"]
    assert config["template_archive"]["id"] == template_archive_id


def test_oq_task_config_null_when_absent(gql_context, created_oq_task):
    """Tasks created via the modern mutation have no `config` — it must
    resolve to null without erroring."""
    result = schema.execute_sync(
        OQ_TASK_LEGACY_CONFIG_QUERY,
        variable_values={"id": created_oq_task["id"]},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    assert result.data["node"]["config"] is None
