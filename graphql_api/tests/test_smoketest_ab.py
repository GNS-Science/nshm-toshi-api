"""
A/B smoketest — mirrors graphql_api/tests/smoketests.py setup sequence.

Mutation strings are intentionally kept as close as possible to the originals
in smoketests.py so this file can serve as a diff to document any remaining
API surface differences.

Key differences from the original smoketest:
  - No search() queries (no Elasticsearch in POC)
  - IDs captured from mutation responses rather than hardcoded
    (no TOSHI_FIX_RANDOM_SEED dependency)
  - Verification via node() and list queries instead of search()
"""

import pytest

from graphql_api.schema import schema

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def ids(gql_context):
    """
    Run the full setup mutation sequence and collect returned IDs.
    Mutation strings mirror graphql_api/tests/smoketests.py test_setup.
    """
    import requests as _requests

    ep = gql_context.get("es_endpoint", "")
    idx = gql_context.get("es_index", "toshi-index-mapped")
    if ep:
        # Wipe any stale data from previous runs so search results only
        # contain objects created by this fixture.
        _requests.delete(f"{ep}/{idx}", timeout=5)

    collected = {}

    def run(query, variables=None):
        result = schema.execute_sync(query, context_value=gql_context, variable_values=variables or {})
        assert result.errors is None, result.errors
        return result.data

    # 1. StrongMotionStation — mirrors smoketests.py "new_sms"
    data = run("""
        mutation new_sms {
            create_strong_motion_station(input: {
                site_code: "ABCD"
                created: "2020-10-10T23:00Z"
                site_class_basis: SPT
                Vs30_mean: [200.0]
                site_class: B
            }) {
                strong_motion_station { id }
            }
        }
    """)
    collected["sms_id"] = data["create_strong_motion_station"]["strong_motion_station"]["id"]

    # 2. First RuptureGenerationTask — mirrors "new_ruptgen_task"
    data = run("""
        mutation new_ruptgen_task {
            create_rupture_generation_task(input: {
                created: "2020-10-10T23:00Z"
                state: SCHEDULED
                result: UNDEFINED
                task_type: RUPTURE_SET
            }) {
                task_result { id created }
            }
        }
    """)
    collected["rgt1_id"] = data["create_rupture_generation_task"]["task_result"]["id"]

    # 3. Update RuptureGenerationTask — mirrors "update_ruptgen_task"
    data = run(
        """
        mutation update_ruptgen_task($task_id: ID!) {
            update_rupture_generation_task(input: {
                task_id: $task_id
                result: SUCCESS
                state: DONE
            }) {
                task_result { id }
            }
        }
    """,
        {"task_id": collected["rgt1_id"]},
    )
    assert data["update_rupture_generation_task"]["task_result"]["id"] == collected["rgt1_id"]

    # 4. File — mirrors "new_rupt_file"
    data = run("""
        mutation new_rupt_file {
            create_file(file_name: "myfile2.txt"
                file_size: 2000
                md5_digest: "abc123"
                meta: [{ k: "encoding", v: "utf8" }]) {
                file_result { id meta { k v } }
            }
        }
    """)
    collected["file_id"] = data["create_file"]["file_result"]["id"]

    # 5. File → RuptureGenerationTask relation — mirrors "new_rupt_file_relation"
    data = run(
        """
        mutation new_rupt_file_relation($file_id: ID!, $thing_id: ID!) {
            create_file_relation(file_id: $file_id
                thing_id: $thing_id
                role: WRITE) { ok }
        }
    """,
        {"file_id": collected["file_id"], "thing_id": collected["rgt1_id"]},
    )
    assert data["create_file_relation"]["ok"] is True

    # 6. SmsFile — mirrors "new_sms_file"
    data = run("""
        mutation new_sms_file {
            create_sms_file(input: {
                file_name: "my_sms_File2.txt"
                file_size: 2000
                file_type: CPT
                md5_digest: "def456"
            }) {
                file_result { id file_type }
            }
        }
    """)
    collected["sms_file_id"] = data["create_sms_file"]["file_result"]["id"]

    # 7. SmsFile → StrongMotionStation relation — mirrors "new_sms_file_relation"
    data = run(
        """
        mutation new_sms_file_relation($file_id: ID!, $thing_id: ID!) {
            create_file_relation(file_id: $file_id
                thing_id: $thing_id
                role: UNDEFINED) { ok }
        }
    """,
        {"file_id": collected["sms_file_id"], "thing_id": collected["sms_id"]},
    )
    assert data["create_file_relation"]["ok"] is True

    # 8. GeneralTask — mirrors "new_general_task"
    data = run("""
        mutation new_general_task {
            create_general_task(input: {
                created: "2020-10-10T23:00:00+00:00"
                title: "My First Manual task"
                description: "##Some notes go here"
                agent_name: "chrisbc"
            }) {
                general_task { id created }
            }
        }
    """)
    collected["gt_id"] = data["create_general_task"]["general_task"]["id"]

    # 9. File → GeneralTask relation — mirrors "new_gt_file_relation"
    data = run(
        """
        mutation new_gt_file_relation($file_id: ID!, $thing_id: ID!) {
            create_file_relation(file_id: $file_id
                thing_id: $thing_id
                role: READ) { ok }
        }
    """,
        {"file_id": collected["file_id"], "thing_id": collected["gt_id"]},
    )
    assert data["create_file_relation"]["ok"] is True

    # 10. SmsFile → GeneralTask relation — mirrors "new_gt_smsfile_relation"
    data = run(
        """
        mutation new_gt_smsfile_relation($file_id: ID!, $thing_id: ID!) {
            create_file_relation(file_id: $file_id
                thing_id: $thing_id
                role: UNDEFINED) { ok }
        }
    """,
        {"file_id": collected["sms_file_id"], "thing_id": collected["gt_id"]},
    )
    assert data["create_file_relation"]["ok"] is True

    # 11. GeneralTask → RuptureGenerationTask — mirrors "new_task_subtask_relation"
    data = run(
        """
        mutation new_task_subtask_relation($child_id: ID!, $parent_id: ID!) {
            create_task_relation(child_id: $child_id
                parent_id: $parent_id) {
                thing_relation {
                    parent { ... on GeneralTask { id } }
                    child  { ... on RuptureGenerationTask { id } }
                }
            }
        }
    """,
        {"child_id": collected["rgt1_id"], "parent_id": collected["gt_id"]},
    )
    rel = data["create_task_relation"]["thing_relation"]
    assert rel["parent"]["id"] == collected["gt_id"]
    assert rel["child"]["id"] == collected["rgt1_id"]

    # 12. AutomationTask — mirrors "new_inversion"
    data = run("""
        mutation new_inversion {
            create_automation_task(input: {
                task_type: INVERSION
                result: UNDEFINED
                state: UNDEFINED
                created: "2020-10-10T23:00Z"
                arguments: [{ k: "max_jump_distance", v: "55.5" }]
                environment: [
                    { k: "gitref_opensha_ucerf3", v: "ABC" }
                    { k: "JAVA", v: "-Xmx24G" }
                ]
            }) {
                task_result { id created arguments { k v } }
            }
        }
    """)
    collected["at_id"] = data["create_automation_task"]["task_result"]["id"]

    # 13. Second RuptureGenerationTask with full args — mirrors "new_ruptgen_new_task"
    data = run("""
        mutation new_ruptgen_new_task {
            create_rupture_generation_task(input: {
                state: UNDEFINED
                result: UNDEFINED
                task_type: RUPTURE_SET
                created: "2020-10-10T23:00Z"
                duration: 600.0
                arguments: [
                    { k: "max_jump_distance", v: "55.5" }
                    { k: "max_sub_section_length", v: "2" }
                    { k: "max_cumulative_azimuth", v: "590" }
                    { k: "min_sub_sections_per_parent", v: "2" }
                    { k: "permutation_strategy", v: "DOWNDIP" }
                ]
                environment: [
                    { k: "gitref_opensha_ucerf3", v: "ABC" }
                    { k: "host", v: "tryharder-ubuntu" }
                    { k: "JAVA", v: "-Xmx24G" }
                ]
                metrics: [
                    { k: "subsection_count", v: "3600" }
                    { k: "total_energy", v: "3280.2333" }
                ]
            }) {
                task_result { id created duration arguments { k v } }
            }
        }
    """)
    collected["rgt2_id"] = data["create_rupture_generation_task"]["task_result"]["id"]

    return collected


# ── Verification tests ────────────────────────────────────────────────────────


def test_setup_returns_all_ids(ids):
    assert all(k in ids for k in ["sms_id", "rgt1_id", "file_id", "sms_file_id", "gt_id", "at_id", "rgt2_id"])
    for key, val in ids.items():
        assert val and len(val) > 4, f"{key} has empty ID"


def test_node_strong_motion_station(ids, gql_context):
    result = schema.execute_sync(
        """
        query GetSMS($id: ID!) {
            node(id: $id) {
                __typename
                ... on StrongMotionStation {
                    id
                    site_code
                    site_class
                    site_class_basis
                    Vs30_mean
                }
            }
        }
    """,
        context_value=gql_context,
        variable_values={"id": ids["sms_id"]},
    )
    assert result.errors is None
    node = result.data["node"]
    assert node["__typename"] == "StrongMotionStation"
    assert node["site_code"] == "ABCD"
    assert node["site_class"] == "B"
    assert node["site_class_basis"] == "SPT"
    assert node["Vs30_mean"] == [200.0]


def test_node_rgt_after_update(ids, gql_context):
    result = schema.execute_sync(
        """
        query GetRGT($id: ID!) {
            node(id: $id) {
                __typename
                ... on RuptureGenerationTask {
                    id
                    created
                    state
                    result
                    duration
                }
            }
        }
    """,
        context_value=gql_context,
        variable_values={"id": ids["rgt1_id"]},
    )
    assert result.errors is None
    node = result.data["node"]
    assert node["__typename"] == "RuptureGenerationTask"
    assert node["state"] == "DONE"
    assert node["result"] == "SUCCESS"
    assert node["duration"] is None


def test_node_file_with_relations(ids, gql_context):
    result = schema.execute_sync(
        """
        query GetFile($id: ID!) {
            node(id: $id) {
                ... on File {
                    file_name
                    file_size
                    meta { k v }
                    relations {
                        edges {
                            node {
                                ... on FileRelation {
                                    role
                                    thing { __typename }
                                }
                            }
                        }
                    }
                }
            }
        }
    """,
        context_value=gql_context,
        variable_values={"id": ids["file_id"]},
    )
    assert result.errors is None
    node = result.data["node"]
    assert node["file_name"] == "myfile2.txt"
    assert node["file_size"] == 2000
    assert node["meta"] == [{"k": "encoding", "v": "utf8"}]
    typenames = {e["node"]["thing"]["__typename"] for e in node["relations"]["edges"]}
    assert "RuptureGenerationTask" in typenames
    assert "GeneralTask" in typenames


def test_node_sms_file_with_relation(ids, gql_context):
    result = schema.execute_sync(
        """
        query GetSmsFile($id: ID!) {
            node(id: $id) {
                ... on SmsFile {
                    file_name
                    file_type
                    relations {
                        edges {
                            node {
                                ... on FileRelation {
                                    role
                                    thing {
                                        __typename
                                        ... on StrongMotionStation { site_code }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    """,
        context_value=gql_context,
        variable_values={"id": ids["sms_file_id"]},
    )
    assert result.errors is None
    node = result.data["node"]
    assert node["file_name"] == "my_sms_File2.txt"
    assert node["file_type"] == "CPT"
    things = [e["node"]["thing"] for e in node["relations"]["edges"]]
    sms = next(t for t in things if t["__typename"] == "StrongMotionStation")
    assert sms["site_code"] == "ABCD"


def test_node_general_task_children_and_files(ids, gql_context):
    result = schema.execute_sync(
        """
        query GetGT($id: ID!) {
            node(id: $id) {
                ... on GeneralTask {
                    id
                    title
                    description
                    agent_name
                    created
                    children {
                        edges {
                            node {
                                child {
                                    __typename
                                    ... on RuptureGenerationTask {
                                        id
                                        state
                                        result
                                        created
                                    }
                                }
                            }
                        }
                    }
                    files {
                        edges {
                            node {
                                ... on FileRelation {
                                    role
                                    file {
                                        __typename
                                        ... on File { file_name file_size }
                                        ... on SmsFile { file_name file_size file_type }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    """,
        context_value=gql_context,
        variable_values={"id": ids["gt_id"]},
    )
    assert result.errors is None
    node = result.data["node"]
    assert node["title"] == "My First Manual task"
    assert node["agent_name"] == "chrisbc"

    children = node["children"]["edges"]
    assert len(children) == 1
    child = children[0]["node"]["child"]
    assert child["__typename"] == "RuptureGenerationTask"
    assert child["id"] == ids["rgt1_id"]
    assert child["state"] == "DONE"
    assert child["result"] == "SUCCESS"

    file_edges = node["files"]["edges"]
    assert len(file_edges) == 2
    roles = {e["node"]["role"] for e in file_edges}
    assert "READ" in roles
    assert "UNDEFINED" in roles
    typenames = {e["node"]["file"]["__typename"] for e in file_edges}
    assert "File" in typenames
    assert "SmsFile" in typenames


def test_node_rgt_files_and_parents(ids, gql_context):
    result = schema.execute_sync(
        """
        query GetRGT($id: ID!) {
            node(id: $id) {
                ... on RuptureGenerationTask {
                    state
                    result
                    files {
                        edges {
                            node {
                                ... on FileRelation {
                                    role
                                    file { ... on File { file_name } }
                                }
                            }
                        }
                    }
                    parents {
                        edges {
                            node {
                                parent {
                                    ... on GeneralTask { title description }
                                }
                            }
                        }
                    }
                }
            }
        }
    """,
        context_value=gql_context,
        variable_values={"id": ids["rgt1_id"]},
    )
    assert result.errors is None
    node = result.data["node"]
    assert node["state"] == "DONE"
    assert node["files"]["edges"][0]["node"]["file"]["file_name"] == "myfile2.txt"
    assert node["parents"]["edges"][0]["node"]["parent"]["title"] == "My First Manual task"


def test_node_automation_task(ids, gql_context):
    result = schema.execute_sync(
        """
        query GetAT($id: ID!) {
            node(id: $id) {
                __typename
                ... on AutomationTask {
                    id
                    created
                    task_type
                    arguments { k v }
                }
            }
        }
    """,
        context_value=gql_context,
        variable_values={"id": ids["at_id"]},
    )
    assert result.errors is None
    node = result.data["node"]
    assert node["__typename"] == "AutomationTask"
    assert node["task_type"] == "INVERSION"
    assert node["arguments"] == [{"k": "max_jump_distance", "v": "55.5"}]


def test_node_rgt2_arguments_and_metrics(ids, gql_context):
    result = schema.execute_sync(
        """
        query GetRGT2($id: ID!) {
            node(id: $id) {
                __typename
                ... on RuptureGenerationTask {
                    id
                    created
                    duration
                    arguments { k v }
                    metrics { k v }
                }
            }
        }
    """,
        context_value=gql_context,
        variable_values={"id": ids["rgt2_id"]},
    )
    assert result.errors is None
    node = result.data["node"]
    assert node["__typename"] == "RuptureGenerationTask"
    assert node["duration"] == 600.0
    assert len(node["arguments"]) == 5
    assert len(node["metrics"]) == 2


def test_list_general_tasks(ids, gql_context):
    result = schema.execute_sync(
        """
        query { general_tasks { edges { node { id title agent_name } } } }
    """,
        context_value=gql_context,
    )
    assert result.errors is None
    nodes = [e["node"] for e in result.data["general_tasks"]["edges"]]
    assert any(n["id"] == ids["gt_id"] and n["title"] == "My First Manual task" for n in nodes)


def test_list_rupture_generation_tasks(ids, gql_context):
    result = schema.execute_sync(
        """
        query { rupture_generation_tasks { edges { node { id state result } } } }
    """,
        context_value=gql_context,
    )
    assert result.errors is None
    nodes = [e["node"] for e in result.data["rupture_generation_tasks"]["edges"]]
    found = {n["id"] for n in nodes}
    assert ids["rgt1_id"] in found
    assert ids["rgt2_id"] in found
    rgt1 = next(n for n in nodes if n["id"] == ids["rgt1_id"])
    assert rgt1["state"] == "DONE"
    assert rgt1["result"] == "SUCCESS"


def test_list_strong_motion_stations(ids, gql_context):
    result = schema.execute_sync(
        """
        query { strong_motion_stations { edges { node { id site_code site_class } } } }
    """,
        context_value=gql_context,
    )
    assert result.errors is None
    nodes = [e["node"] for e in result.data["strong_motion_stations"]["edges"]]
    assert any(n["id"] == ids["sms_id"] and n["site_code"] == "ABCD" for n in nodes)


def test_list_sms_files(ids, gql_context):
    result = schema.execute_sync(
        """
        query { sms_files { edges { node { id file_name file_type } } } }
    """,
        context_value=gql_context,
    )
    assert result.errors is None
    nodes = [e["node"] for e in result.data["sms_files"]["edges"]]
    assert any(n["id"] == ids["sms_file_id"] and n["file_type"] == "CPT" for n in nodes)


def test_list_automation_tasks(ids, gql_context):
    result = schema.execute_sync(
        """
        query { automation_tasks { edges { node { id task_type } } } }
    """,
        context_value=gql_context,
    )
    assert result.errors is None
    nodes = [e["node"] for e in result.data["automation_tasks"]["edges"]]
    assert any(n["id"] == ids["at_id"] and n["task_type"] == "INVERSION" for n in nodes)


# ── Integration tests — require live ES (ES_ENDPOINT env var) ─────────────────
# Run with: ES_ENDPOINT=http://localhost:9200 uv run --extra dev pytest tests/ -m integration -v

SEARCH_FRAGMENT = """
fragment sr on SearchResult {
    __typename
    ... on File {
        id
        file_name
        relations {
            edges {
                node {
                    ... on FileRelation {
                        role
                        thing {
                            __typename
                            ... on RuptureGenerationTask { created }
                        }
                    }
                }
            }
        }
    }
    ... on SmsFile {
        id
        file_name
        file_type
        relations {
            edges {
                node {
                    ... on FileRelation {
                        role
                        thing {
                            __typename
                            ... on StrongMotionStation { site_code }
                        }
                    }
                }
            }
        }
    }
    ... on RuptureGenerationTask {
        id
        result
        state
        arguments { k v }
        files {
            edges {
                node {
                    ... on FileRelation {
                        role
                        file {
                            ... on File { id file_name file_size }
                        }
                    }
                }
            }
        }
    }
    ... on StrongMotionStation {
        id
        created
        site_code
        site_class
        site_class_basis
        liquefiable
        Vs30_mean
        files {
            edges {
                node {
                    ... on FileRelation {
                        role
                        file {
                            ... on SmsFile { file_name file_size }
                        }
                    }
                }
            }
        }
    }
    ... on GeneralTask {
        id
        created
        updated
        title
        description
        agent_name
        children {
            edges {
                node {
                    child {
                        __typename
                        ... on RuptureGenerationTask {
                            id
                            state
                            result
                            created
                        }
                    }
                }
            }
        }
        files {
            edges {
                node {
                    ... on FileRelation {
                        role
                        file {
                            __typename
                            ... on File { file_name file_size }
                            ... on SmsFile { file_name file_size file_type }
                        }
                    }
                }
            }
        }
    }
    ... on AutomationTask {
        id
        created
        task_type
        arguments { k v }
    }
}
"""

SEARCH_QUERY = (
    SEARCH_FRAGMENT
    + """
query Search($term: String!) {
    search(search_term: $term) {
        search_result {
            edges {
                node { ...sr }
            }
        }
    }
}
"""
)


def _search(gql_context, term):
    result = schema.execute_sync(SEARCH_QUERY, context_value=gql_context, variable_values={"term": term})
    assert result.errors is None, result.errors
    return result.data["search"]["search_result"]["edges"]


@pytest.mark.integration
def test_search_sms_by_site_class_basis(ids, gql_context):
    """Mirrors smoketests.py search_sms query."""
    import time

    time.sleep(1)  # allow ES to index
    edges = _search(gql_context, "site_class_basis:SPT")
    nodes = [e["node"] for e in edges]
    sms = next((n for n in nodes if n["__typename"] == "StrongMotionStation"), None)
    assert sms is not None
    assert sms["id"] == ids["sms_id"]
    assert sms["site_code"] == "ABCD"
    assert sms["site_class"] == "B"
    assert sms["site_class_basis"] == "SPT"
    assert sms["Vs30_mean"] == [200.0]
    # File relation to SmsFile
    file_nodes = [e["node"]["file"] for e in sms["files"]["edges"]]
    assert any(f and f.get("file_name") == "my_sms_File2.txt" for f in file_nodes)


@pytest.mark.integration
def test_search_rupture_generation_task_by_result(ids, gql_context):
    """Mirrors smoketests.py search_rupture query."""
    edges = _search(gql_context, "result:SUCCESS")
    nodes = [e["node"] for e in edges]
    rgt = next((n for n in nodes if n["__typename"] == "RuptureGenerationTask"), None)
    assert rgt is not None
    assert rgt["id"] == ids["rgt1_id"]
    assert rgt["result"] == "SUCCESS"
    assert rgt["state"] == "DONE"
    file_nodes = [e["node"] for e in rgt["files"]["edges"]]
    assert any(e["role"] == "WRITE" and e["file"] and e["file"]["file_name"] == "myfile2.txt" for e in file_nodes)


@pytest.mark.integration
def test_search_sms_file_by_name(ids, gql_context):
    """Mirrors smoketests.py search_file query."""
    edges = _search(gql_context, "file_name:my_sms*")
    nodes = [e["node"] for e in edges]
    sms_file = next((n for n in nodes if n["__typename"] == "SmsFile"), None)
    assert sms_file is not None
    assert sms_file["id"] == ids["sms_file_id"]
    assert sms_file["file_name"] == "my_sms_File2.txt"
    assert sms_file["file_type"] == "CPT"
    things = [e["node"]["thing"] for e in sms_file["relations"]["edges"]]
    assert any(t["__typename"] == "StrongMotionStation" and t["site_code"] == "ABCD" for t in things)


@pytest.mark.integration
def test_search_general_task_by_agent(ids, gql_context):
    """Mirrors smoketests.py search_general_task query."""
    edges = _search(gql_context, "agent_name:chrisbc")
    nodes = [e["node"] for e in edges]
    gt = next((n for n in nodes if n["__typename"] == "GeneralTask"), None)
    assert gt is not None
    assert gt["id"] == ids["gt_id"]
    assert gt["title"] == "My First Manual task"
    assert gt["agent_name"] == "chrisbc"
    # Child relation
    children = [e["node"]["child"] for e in gt["children"]["edges"]]
    assert any(c["__typename"] == "RuptureGenerationTask" and c["state"] == "DONE" for c in children)
    # File relations
    file_nodes = [e["node"] for e in gt["files"]["edges"]]
    roles = {e["role"] for e in file_nodes}
    assert "READ" in roles
    assert "UNDEFINED" in roles


@pytest.mark.integration
def test_search_automation_task_by_task_type(ids, gql_context):
    """Mirrors smoketests.py search_automation_task query."""
    edges = _search(gql_context, "task_type:inversion")
    nodes = [e["node"] for e in edges]
    at = next((n for n in nodes if n["__typename"] == "AutomationTask"), None)
    assert at is not None
    assert at["id"] == ids["at_id"]
    assert at["task_type"] == "INVERSION"
    assert at["arguments"] == [{"k": "max_jump_distance", "v": "55.5"}]
