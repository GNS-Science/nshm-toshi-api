"""
Relay cursor pagination tests.

Verifies that Strawberry's relay.ListConnection correctly handles
first/after/page_info for top-level connection fields.

No production code changes needed — the mechanism is built into
@relay.connection(relay.ListConnection[T]) and works in-memory over
the list returned by each resolver.

Run with:
    uv run --extra dev pytest tests/test_pagination.py -v
"""

import pytest

from schema import schema

PAGINATED_QUERY = """
query Paginated($first: Int, $after: String) {
    general_tasks(first: $first, after: $after) {
        page_info {
            has_next_page
            has_previous_page
            start_cursor
            end_cursor
        }
        edges {
            cursor
            node { id title }
        }
    }
}
"""

CREATE_GT = """
mutation CreateGT($title: String!) {
    create_general_task(input: { title: $title, created: "2024-01-01T00:00Z" }) {
        general_task { id title }
    }
}
"""


@pytest.fixture(scope="module")
def paginated_tasks(gql_context):
    """Create 4 GeneralTasks and return their IDs in creation order."""
    ids = []
    for i in range(4):
        result = schema.execute_sync(
            CREATE_GT,
            context_value=gql_context,
            variable_values={"title": f"Pagination Task {i}"},
        )
        assert result.errors is None, result.errors
        ids.append(result.data["create_general_task"]["general_task"]["id"])
    return ids


def _query(gql_context, first=None, after=None):
    vars = {}
    if first is not None:
        vars["first"] = first
    if after is not None:
        vars["after"] = after
    result = schema.execute_sync(PAGINATED_QUERY, context_value=gql_context, variable_values=vars)
    assert result.errors is None, result.errors
    return result.data["general_tasks"]


def test_first_returns_subset(paginated_tasks, gql_context):
    """first: 2 returns exactly 2 edges."""
    conn = _query(gql_context, first=2)
    assert len(conn["edges"]) == 2


def test_pageinfo_has_next_page(paginated_tasks, gql_context):
    """first: 2 with 4 total → has_next_page True, end_cursor set."""
    conn = _query(gql_context, first=2)
    assert conn["page_info"]["has_next_page"] is True
    assert conn["page_info"]["end_cursor"]


def test_pageinfo_no_next_page_on_last_page(paginated_tasks, gql_context):
    """Fetching page 2 of 2 → has_next_page False."""
    page1 = _query(gql_context, first=2)
    cursor = page1["page_info"]["end_cursor"]
    page2 = _query(gql_context, first=2, after=cursor)
    assert page2["page_info"]["has_next_page"] is False


def test_cursor_advances_correctly(paginated_tasks, gql_context):
    """Page 1 and page 2 IDs are disjoint; together they cover all 4 tasks."""
    page1 = _query(gql_context, first=2)
    cursor = page1["page_info"]["end_cursor"]
    page2 = _query(gql_context, first=2, after=cursor)

    ids_p1 = {e["node"]["id"] for e in page1["edges"]}
    ids_p2 = {e["node"]["id"] for e in page2["edges"]}

    assert ids_p1.isdisjoint(ids_p2), "Pages overlap — cursor not advancing"
    assert len(ids_p1 | ids_p2) == 4, "Pages don't cover all 4 tasks"
    # All created IDs are present across both pages
    for task_id in paginated_tasks:
        assert task_id in (ids_p1 | ids_p2)


def test_first_exceeding_total(paginated_tasks, gql_context):
    """first: 100 with only 4 tasks → all returned, has_next_page False."""
    conn = _query(gql_context, first=100)
    assert conn["page_info"]["has_next_page"] is False
    returned_ids = {e["node"]["id"] for e in conn["edges"]}
    for task_id in paginated_tasks:
        assert task_id in returned_ids


def test_no_args_returns_all(paginated_tasks, gql_context):
    """No pagination args → all 4 tasks present (default behaviour unchanged)."""
    conn = _query(gql_context)
    returned_ids = {e["node"]["id"] for e in conn["edges"]}
    for task_id in paginated_tasks:
        assert task_id in returned_ids
