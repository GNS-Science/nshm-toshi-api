"""
Tests for the PageInfo backwards-compatibility layer.

ADR-001 Phase 1: expose the Relay Connection spec's camelCase PageInfo
field names (`pageInfo`, `hasNextPage`, etc.) as the preferred form on
every connection, with the legacy snake_case forms as `@deprecated`
aliases. Existing clients continue to work; new clients see the
modern names in autocomplete and codegen.
"""

import pytest

from schema import schema


CREATE_TASK_MUTATION = """
mutation CreateTask($input: CreateGeneralTaskInput!) {
    create_general_task(input: $input) { general_task { id } }
}
"""

# Both query forms should work — camelCase preferred, snake_case deprecated alias
GENERAL_TASKS_CAMEL_QUERY = """
query GeneralTasksCamel {
    general_tasks(first: 2) {
        pageInfo {
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }
        edges { node { id title } }
    }
}
"""

GENERAL_TASKS_SNAKE_QUERY = """
query GeneralTasksSnake {
    general_tasks(first: 2) {
        page_info {
            has_next_page
            has_previous_page
            start_cursor
            end_cursor
        }
        edges { node { id title } }
    }
}
"""

GENERAL_TASKS_MIXED_QUERY = """
query GeneralTasksMixed {
    general_tasks(first: 2) {
        pageInfo {
            has_next_page
            endCursor
        }
        edges { node { id } }
    }
}
"""


@pytest.fixture(scope="module")
def seeded_tasks(gql_context):
    """Create a handful of GeneralTasks so pagination has something to page through."""
    ids = []
    for i in range(5):
        result = schema.execute_sync(
            CREATE_TASK_MUTATION,
            variable_values={"input": {"title": f"pageinfo-task-{i}", "agent_name": "pytest"}},
            context_value=gql_context,
        )
        assert result.errors is None, result.errors
        ids.append(result.data["create_general_task"]["general_task"]["id"])
    return ids


def test_camel_case_page_info_works(gql_context, seeded_tasks):
    """The Relay-spec camelCase form (pageInfo + hasNextPage etc.) works."""
    result = schema.execute_sync(GENERAL_TASKS_CAMEL_QUERY, context_value=gql_context)
    assert result.errors is None, result.errors
    pi = result.data["general_tasks"]["pageInfo"]
    assert pi["hasNextPage"] is True  # we seeded >2, requested first 2
    assert pi["hasPreviousPage"] is False
    assert isinstance(pi["startCursor"], str)
    assert isinstance(pi["endCursor"], str)


def test_snake_case_page_info_works_as_deprecated_alias(gql_context, seeded_tasks):
    """The legacy snake_case form (page_info + has_next_page etc.) still works."""
    result = schema.execute_sync(GENERAL_TASKS_SNAKE_QUERY, context_value=gql_context)
    assert result.errors is None, result.errors
    pi = result.data["general_tasks"]["page_info"]
    assert pi["has_next_page"] is True
    assert pi["has_previous_page"] is False
    assert isinstance(pi["start_cursor"], str)
    assert isinstance(pi["end_cursor"], str)


def test_both_forms_return_consistent_data(gql_context, seeded_tasks):
    """camelCase and snake_case forms must return the same values."""
    camel = schema.execute_sync(GENERAL_TASKS_CAMEL_QUERY, context_value=gql_context)
    snake = schema.execute_sync(GENERAL_TASKS_SNAKE_QUERY, context_value=gql_context)
    assert camel.errors is None
    assert snake.errors is None
    camel_pi = camel.data["general_tasks"]["pageInfo"]
    snake_pi = snake.data["general_tasks"]["page_info"]
    assert camel_pi["hasNextPage"] == snake_pi["has_next_page"]
    assert camel_pi["hasPreviousPage"] == snake_pi["has_previous_page"]
    assert camel_pi["startCursor"] == snake_pi["start_cursor"]
    assert camel_pi["endCursor"] == snake_pi["end_cursor"]


def test_mixed_naming_query_works(gql_context, seeded_tasks):
    """Mixed-naming queries (pageInfo.has_next_page) work — the aliases compose."""
    result = schema.execute_sync(GENERAL_TASKS_MIXED_QUERY, context_value=gql_context)
    assert result.errors is None, result.errors
    pi = result.data["general_tasks"]["pageInfo"]
    assert pi["has_next_page"] is True
    assert isinstance(pi["endCursor"], str)


# ── Introspection: deprecation_reason is surfaced ─────────────────────────────


def test_page_info_type_has_both_naming_forms_in_schema():
    """The PageInfo SDL contains camelCase (no deprecation) AND snake_case (deprecated)."""
    sdl = schema.as_str()
    # PageInfo type block
    import re

    match = re.search(r"type PageInfo \{[^}]+\}", sdl, re.DOTALL)
    assert match is not None
    block = match.group(0)
    # Modern Relay-spec camelCase form, no deprecation marker on these lines
    assert "hasNextPage: Boolean!" in block
    assert "hasPreviousPage: Boolean!" in block
    assert "startCursor: String" in block
    assert "endCursor: String" in block
    # Legacy snake_case aliases, marked deprecated
    assert 'has_next_page: Boolean! @deprecated(reason: "Use hasNextPage' in block
    assert 'has_previous_page: Boolean! @deprecated(reason: "Use hasPreviousPage' in block
    assert 'start_cursor: String @deprecated(reason: "Use startCursor' in block
    assert 'end_cursor: String @deprecated(reason: "Use endCursor' in block


def test_connection_pageinfo_field_has_alias_and_deprecation():
    """Each connection's `pageInfo` field is the primary; `page_info` is deprecated."""
    sdl = schema.as_str()
    # Check a relay-derived connection (GeneralTaskConnection auto-generated from
    # @relay.connection(CompatListConnection[GeneralTask]))
    import re

    match = re.search(r"type GeneralTaskConnection \{[^}]+\}", sdl, re.DOTALL)
    assert match is not None
    block = match.group(0)
    assert "pageInfo: PageInfo!" in block
    assert 'page_info: PageInfo! @deprecated(reason: "Use pageInfo' in block


def test_introspection_marks_deprecation_reason():
    """GraphQL introspection surfaces the deprecation reason — that's what
    powers IDE warnings in Apollo Studio / GraphiQL."""
    result = schema.execute_sync(
        """
        {
            __type(name: "PageInfo") {
                fields(includeDeprecated: true) {
                    name
                    isDeprecated
                    deprecationReason
                }
            }
        }
        """
    )
    assert result.errors is None, result.errors
    fields = {f["name"]: f for f in result.data["__type"]["fields"]}

    # camelCase forms are NOT deprecated
    assert fields["hasNextPage"]["isDeprecated"] is False
    assert fields["endCursor"]["isDeprecated"] is False

    # snake_case forms ARE deprecated with a reason
    assert fields["has_next_page"]["isDeprecated"] is True
    assert "hasNextPage" in fields["has_next_page"]["deprecationReason"]
    assert fields["end_cursor"]["isDeprecated"] is True
    assert "endCursor" in fields["end_cursor"]["deprecationReason"]
