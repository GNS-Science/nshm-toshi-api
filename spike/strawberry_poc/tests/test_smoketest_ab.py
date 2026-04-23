"""
A/B smoketest — mirrors graphql_api/tests/smoketests.py setup sequence.

Runs the same domain operations against the Strawberry POC schema (moto-backed
DynamoDB, no HTTP) and verifies the resulting data via node lookups and list
queries. Search queries are excluded because the POC has no Elasticsearch layer.

Differences from the original smoketest:
  - IDs are captured from mutation responses (not hardcoded) — no TOSHI_FIX_RANDOM_SEED needed.
  - Mutations return the type directly (no payload wrapper like task_result / file_result).
  - Field names use camelCase (Strawberry default for Python snake_case attributes).
  - search() queries are absent; verification uses node() and list queries instead.
"""
import pytest

from schema import schema


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def ids(gql_context):
    """
    Run the full setup mutation sequence and collect returned IDs.

    Returns a dict of logical name → relay GlobalID string.
    """
    collected = {}

    def run(query, variables=None):
        result = schema.execute_sync(query, context_value=gql_context, variable_values=variables or {})
        assert result.errors is None, result.errors
        return result.data

    # 1. StrongMotionStation
    data = run("""
        mutation {
            createStrongMotionStation(input: {
                siteCode: "ABCD"
                created: "2020-10-10T23:00Z"
                siteClassBasis: SPT
                vs30Mean: [200.0]
                siteClass: B
            }) {
                id
                siteCode
                siteClass
                siteClassBasis
                vs30Mean
            }
        }
    """)
    collected["sms_id"] = data["createStrongMotionStation"]["id"]

    # 2. First RuptureGenerationTask
    data = run("""
        mutation {
            createRuptureGenerationTask(input: {
                created: "2020-10-10T23:00Z"
                state: SCHEDULED
                result: UNDEFINED
                taskType: RUPTURE_SET
            }) {
                id
                created
                state
                result
            }
        }
    """)
    collected["rgt1_id"] = data["createRuptureGenerationTask"]["id"]

    # 3. Update first RuptureGenerationTask
    data = run("""
        mutation UpdateRGT($taskId: ID!) {
            updateRuptureGenerationTask(input: {
                taskId: $taskId
                result: SUCCESS
                state: DONE
            }) {
                id
                result
                state
            }
        }
    """, {"taskId": collected["rgt1_id"]})
    assert data["updateRuptureGenerationTask"]["result"] == "SUCCESS"

    # 4. File
    data = run("""
        mutation {
            createFile(input: {
                fileName: "myfile2.txt"
                fileSize: 2000
                md5Digest: "abc123"
                meta: [{ k: "encoding", v: "utf8" }]
            }) {
                id
                fileName
                fileSize
                meta { k v }
            }
        }
    """)
    collected["file_id"] = data["createFile"]["id"]

    # 5. File → RuptureGenerationTask relation
    data = run("""
        mutation CreateFileRel($fileId: ID!, $thingId: ID!) {
            createFileRelation(input: {
                fileId: $fileId
                thingId: $thingId
                role: WRITE
            })
        }
    """, {"fileId": collected["file_id"], "thingId": collected["rgt1_id"]})
    assert data["createFileRelation"] is True

    # 6. SmsFile
    data = run("""
        mutation {
            createSmsFile(input: {
                fileName: "my_sms_File2.txt"
                fileSize: 2000
                fileType: CPT
                md5Digest: "def456"
            }) {
                id
                fileName
                fileType
            }
        }
    """)
    collected["sms_file_id"] = data["createSmsFile"]["id"]

    # 7. SmsFile → StrongMotionStation relation
    data = run("""
        mutation CreateSmsRel($fileId: ID!, $thingId: ID!) {
            createFileRelation(input: {
                fileId: $fileId
                thingId: $thingId
                role: UNDEFINED
            })
        }
    """, {"fileId": collected["sms_file_id"], "thingId": collected["sms_id"]})
    assert data["createFileRelation"] is True

    # 8. GeneralTask
    data = run("""
        mutation {
            createGeneralTask(input: {
                created: "2020-10-10T23:00:00+00:00"
                title: "My First Manual task"
                description: "##Some notes go here"
                agentName: "chrisbc"
            }) {
                id
                created
                title
                description
                agentName
            }
        }
    """)
    collected["gt_id"] = data["createGeneralTask"]["id"]

    # 9. File → GeneralTask relation
    data = run("""
        mutation CreateGTFileRel($fileId: ID!, $thingId: ID!) {
            createFileRelation(input: {
                fileId: $fileId
                thingId: $thingId
                role: READ
            })
        }
    """, {"fileId": collected["file_id"], "thingId": collected["gt_id"]})
    assert data["createFileRelation"] is True

    # 10. SmsFile → GeneralTask relation
    data = run("""
        mutation CreateGTSmsRel($fileId: ID!, $thingId: ID!) {
            createFileRelation(input: {
                fileId: $fileId
                thingId: $thingId
                role: UNDEFINED
            })
        }
    """, {"fileId": collected["sms_file_id"], "thingId": collected["gt_id"]})
    assert data["createFileRelation"] is True

    # 11. GeneralTask → RuptureGenerationTask task relation
    data = run("""
        mutation CreateTaskRel($parentId: ID!, $childId: ID!) {
            createTaskRelation(input: {
                parentId: $parentId
                childId: $childId
            }) {
                parent { ... on GeneralTask { id title } }
                child { ... on RuptureGenerationTask { id state result } }
            }
        }
    """, {"parentId": collected["gt_id"], "childId": collected["rgt1_id"]})
    rel = data["createTaskRelation"]
    assert rel["parent"]["title"] == "My First Manual task"
    assert rel["child"]["state"] == "DONE"
    assert rel["child"]["result"] == "SUCCESS"

    # 12. AutomationTask (inversion)
    data = run("""
        mutation {
            createAutomationTask(input: {
                taskType: INVERSION
                result: UNDEFINED
                state: UNDEFINED
                created: "2020-10-10T23:00Z"
                arguments: [{ k: "max_jump_distance", v: "55.5" }]
                environment: [
                    { k: "gitref_opensha_ucerf3", v: "ABC" }
                    { k: "JAVA", v: "-Xmx24G" }
                ]
            }) {
                id
                created
                taskType
                arguments { k v }
            }
        }
    """)
    collected["at_id"] = data["createAutomationTask"]["id"]
    assert data["createAutomationTask"]["taskType"] == "INVERSION"
    assert data["createAutomationTask"]["arguments"][0]["k"] == "max_jump_distance"

    # 13. Second RuptureGenerationTask with full arguments
    data = run("""
        mutation {
            createRuptureGenerationTask(input: {
                state: UNDEFINED
                result: UNDEFINED
                taskType: RUPTURE_SET
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
                id
                created
                duration
                arguments { k v }
            }
        }
    """)
    collected["rgt2_id"] = data["createRuptureGenerationTask"]["id"]
    assert data["createRuptureGenerationTask"]["duration"] == 600.0
    assert len(data["createRuptureGenerationTask"]["arguments"]) == 5

    return collected


# ── Verification tests ────────────────────────────────────────────────────────

def test_setup_returns_all_ids(ids):
    """Verify all expected IDs were collected during setup."""
    assert all(k in ids for k in [
        "sms_id", "rgt1_id", "file_id", "sms_file_id", "gt_id", "at_id", "rgt2_id"
    ])
    # All IDs are non-empty relay global IDs
    for key, val in ids.items():
        assert val and len(val) > 4, f"{key} has empty ID"


def test_node_strong_motion_station(ids, gql_context):
    """node() lookup returns StrongMotionStation with correct fields."""
    result = schema.execute_sync("""
        query GetSMS($id: ID!) {
            node(id: $id) {
                __typename
                ... on StrongMotionStation {
                    id
                    siteCode
                    siteClass
                    siteClassBasis
                    vs30Mean
                }
            }
        }
    """, context_value=gql_context, variable_values={"id": ids["sms_id"]})
    assert result.errors is None
    node = result.data["node"]
    assert node["__typename"] == "StrongMotionStation"
    assert node["siteCode"] == "ABCD"
    assert node["siteClass"] == "B"
    assert node["siteClassBasis"] == "SPT"
    assert node["vs30Mean"] == [200.0]


def test_node_rupture_generation_task_after_update(ids, gql_context):
    """RuptureGenerationTask node reflects the updated state/result."""
    result = schema.execute_sync("""
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
    """, context_value=gql_context, variable_values={"id": ids["rgt1_id"]})
    assert result.errors is None
    node = result.data["node"]
    assert node["__typename"] == "RuptureGenerationTask"
    assert node["state"] == "DONE"
    assert node["result"] == "SUCCESS"
    assert node["created"] == "2020-10-10T23:00Z"
    assert node["duration"] is None


def test_node_file_with_relations(ids, gql_context):
    """File node shows relations to both RuptureGenerationTask and GeneralTask."""
    result = schema.execute_sync("""
        query GetFile($id: ID!) {
            node(id: $id) {
                ... on ToshiFile {
                    fileName
                    fileSize
                    meta { k v }
                    relations {
                        edges {
                            node {
                                ... on FileRelation {
                                    role
                                    thing {
                                        __typename
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    """, context_value=gql_context, variable_values={"id": ids["file_id"]})
    assert result.errors is None
    node = result.data["node"]
    assert node["fileName"] == "myfile2.txt"
    assert node["fileSize"] == 2000
    assert node["meta"] == [{"k": "encoding", "v": "utf8"}]
    typenames = {e["node"]["thing"]["__typename"] for e in node["relations"]["edges"]}
    assert "RuptureGenerationTask" in typenames
    assert "GeneralTask" in typenames


def test_node_sms_file_with_relation(ids, gql_context):
    """SmsFile node shows relation to StrongMotionStation."""
    result = schema.execute_sync("""
        query GetSmsFile($id: ID!) {
            node(id: $id) {
                ... on SmsFile {
                    fileName
                    fileType
                    relations {
                        edges {
                            node {
                                ... on FileRelation {
                                    role
                                    thing {
                                        __typename
                                        ... on StrongMotionStation {
                                            siteCode
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    """, context_value=gql_context, variable_values={"id": ids["sms_file_id"]})
    assert result.errors is None
    node = result.data["node"]
    assert node["fileName"] == "my_sms_File2.txt"
    assert node["fileType"] == "CPT"
    things = [e["node"]["thing"] for e in node["relations"]["edges"]]
    sms = next(t for t in things if t["__typename"] == "StrongMotionStation")
    assert sms["siteCode"] == "ABCD"


def test_node_general_task_with_children_and_files(ids, gql_context):
    """GeneralTask shows its child RuptureGenerationTask and both file relations."""
    result = schema.execute_sync("""
        query GetGT($id: ID!) {
            node(id: $id) {
                ... on GeneralTask {
                    id
                    title
                    description
                    agentName
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
                                        ... on ToshiFile {
                                            fileName
                                            fileSize
                                        }
                                        ... on SmsFile {
                                            fileName
                                            fileType
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    """, context_value=gql_context, variable_values={"id": ids["gt_id"]})
    assert result.errors is None
    node = result.data["node"]
    assert node["title"] == "My First Manual task"
    assert node["agentName"] == "chrisbc"

    # Child relation
    children = node["children"]["edges"]
    assert len(children) == 1
    child = children[0]["node"]["child"]
    assert child["__typename"] == "RuptureGenerationTask"
    assert child["id"] == ids["rgt1_id"]
    assert child["state"] == "DONE"

    # File relations: one ToshiFile (READ) and one SmsFile (UNDEFINED)
    file_edges = node["files"]["edges"]
    assert len(file_edges) == 2
    roles = {e["node"]["role"] for e in file_edges}
    assert "READ" in roles
    assert "UNDEFINED" in roles
    typenames = {e["node"]["file"]["__typename"] for e in file_edges}
    assert "ToshiFile" in typenames
    assert "SmsFile" in typenames


def test_node_rgt_with_files_and_parents(ids, gql_context):
    """RuptureGenerationTask shows file relation and parent GeneralTask."""
    result = schema.execute_sync("""
        query GetRGT($id: ID!) {
            node(id: $id) {
                ... on RuptureGenerationTask {
                    id
                    state
                    result
                    files {
                        edges {
                            node {
                                ... on FileRelation {
                                    role
                                    file {
                                        ... on ToshiFile {
                                            fileName
                                        }
                                    }
                                }
                            }
                        }
                    }
                    parents {
                        edges {
                            node {
                                parent {
                                    ... on GeneralTask {
                                        title
                                        description
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    """, context_value=gql_context, variable_values={"id": ids["rgt1_id"]})
    assert result.errors is None
    node = result.data["node"]
    assert node["state"] == "DONE"

    files = node["files"]["edges"]
    assert len(files) == 1
    assert files[0]["node"]["role"] == "WRITE"
    assert files[0]["node"]["file"]["fileName"] == "myfile2.txt"

    parents = node["parents"]["edges"]
    assert len(parents) == 1
    assert parents[0]["node"]["parent"]["title"] == "My First Manual task"


def test_node_automation_task(ids, gql_context):
    """AutomationTask node returns correct type and arguments."""
    result = schema.execute_sync("""
        query GetAT($id: ID!) {
            node(id: $id) {
                __typename
                ... on AutomationTask {
                    id
                    created
                    taskType
                    arguments { k v }
                }
            }
        }
    """, context_value=gql_context, variable_values={"id": ids["at_id"]})
    assert result.errors is None
    node = result.data["node"]
    assert node["__typename"] == "AutomationTask"
    assert node["taskType"] == "INVERSION"
    assert node["arguments"] == [{"k": "max_jump_distance", "v": "55.5"}]


def test_node_rgt2_with_arguments(ids, gql_context):
    """Second RuptureGenerationTask has correct arguments, duration, metrics."""
    result = schema.execute_sync("""
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
    """, context_value=gql_context, variable_values={"id": ids["rgt2_id"]})
    assert result.errors is None
    node = result.data["node"]
    assert node["__typename"] == "RuptureGenerationTask"
    assert node["duration"] == 600.0
    assert len(node["arguments"]) == 5
    arg_keys = [a["k"] for a in node["arguments"]]
    assert "max_jump_distance" in arg_keys
    assert "permutation_strategy" in arg_keys
    assert len(node["metrics"]) == 2


def test_list_general_tasks(ids, gql_context):
    """generalTasks list returns the created GeneralTask."""
    result = schema.execute_sync("""
        query {
            generalTasks {
                edges {
                    node {
                        id
                        title
                        agentName
                    }
                }
            }
        }
    """, context_value=gql_context)
    assert result.errors is None
    nodes = [e["node"] for e in result.data["generalTasks"]["edges"]]
    assert any(n["id"] == ids["gt_id"] and n["title"] == "My First Manual task" for n in nodes)


def test_list_rupture_generation_tasks(ids, gql_context):
    """ruptureGenerationTasks list returns both created tasks."""
    result = schema.execute_sync("""
        query {
            ruptureGenerationTasks {
                edges {
                    node {
                        id
                        state
                        result
                    }
                }
            }
        }
    """, context_value=gql_context)
    assert result.errors is None
    nodes = [e["node"] for e in result.data["ruptureGenerationTasks"]["edges"]]
    ids_found = {n["id"] for n in nodes}
    assert ids["rgt1_id"] in ids_found
    assert ids["rgt2_id"] in ids_found
    # rgt1 was updated to DONE/SUCCESS
    rgt1 = next(n for n in nodes if n["id"] == ids["rgt1_id"])
    assert rgt1["state"] == "DONE"
    assert rgt1["result"] == "SUCCESS"


def test_list_strong_motion_stations(ids, gql_context):
    """strongMotionStations list returns the created station."""
    result = schema.execute_sync("""
        query {
            strongMotionStations {
                edges {
                    node {
                        id
                        siteCode
                        siteClass
                    }
                }
            }
        }
    """, context_value=gql_context)
    assert result.errors is None
    nodes = [e["node"] for e in result.data["strongMotionStations"]["edges"]]
    assert any(n["id"] == ids["sms_id"] and n["siteCode"] == "ABCD" for n in nodes)


def test_list_sms_files(ids, gql_context):
    """smsFiles list returns the created SmsFile."""
    result = schema.execute_sync("""
        query {
            smsFiles {
                edges {
                    node {
                        id
                        fileName
                        fileType
                    }
                }
            }
        }
    """, context_value=gql_context)
    assert result.errors is None
    nodes = [e["node"] for e in result.data["smsFiles"]["edges"]]
    assert any(n["id"] == ids["sms_file_id"] and n["fileType"] == "CPT" for n in nodes)


def test_list_automation_tasks(ids, gql_context):
    """automationTasks list returns the INVERSION task."""
    result = schema.execute_sync("""
        query {
            automationTasks {
                edges {
                    node {
                        id
                        taskType
                    }
                }
            }
        }
    """, context_value=gql_context)
    assert result.errors is None
    nodes = [e["node"] for e in result.data["automationTasks"]["edges"]]
    assert any(n["id"] == ids["at_id"] and n["taskType"] == "INVERSION" for n in nodes)
