"""Edge-case coverage for `swept_arguments` resolver semantics.

The resolver rule is simple — `swept_arguments` returns keys where
`len(argument_lists[i].v) > 1`. But the edge cases are easy to break
silently, especially after #322 widened nullability everywhere:

  - v: ["A", "B"]    → swept (len > 1)
  - v: ["A"]         → NOT swept (len == 1)
  - v: [null]        → NOT swept (len == 1, even though only element is null)
  - v: [null, null]  → swept (len == 2, even though all elements are null)
  - v: ["A", null]   → swept (len == 2)
  - v: []            → NOT swept (len == 0)
  - argument_lists absent → swept_arguments returns [] (not null)

Locking these so future regressions show up immediately rather than as
a vague "the swept_args got weird" report.
"""

import datetime as dt

from dateutil.tz import tzutc

from graphql_api.schema import schema

CREATE_GT = """
mutation ($created: DateTime!, $argument_lists: [KeyValueListPairInput]) {
  create_general_task(input: {
    created: $created
    title: "edge-cases"
    description: "edge-cases"
    agent_name: "tester"
    argument_lists: $argument_lists
  })
  {
    general_task {
      id
      argument_lists { k v }
      swept_arguments
    }
  }
}
"""


def _create(gql_context, argument_lists):
    res = schema.execute_sync(
        CREATE_GT,
        variable_values={
            "created": dt.datetime.now(tzutc()).isoformat(),
            "argument_lists": argument_lists,
        },
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    return res.data["create_general_task"]["general_task"]


def test_two_string_values_is_swept(gql_context):
    gt = _create(gql_context, [{"k": "alpha", "v": ["A", "B"]}])
    assert gt["swept_arguments"] == ["alpha"]


def test_single_string_value_is_not_swept(gql_context):
    gt = _create(gql_context, [{"k": "alpha", "v": ["A"]}])
    assert gt["swept_arguments"] == []


def test_single_null_value_is_not_swept(gql_context):
    """`v: [null]` (one element, null) — NOT swept. Legacy production shape."""
    gt = _create(gql_context, [{"k": "alpha", "v": [None]}])
    assert gt["swept_arguments"] == []


def test_two_null_values_is_swept(gql_context):
    """`v: [null, null]` (two elements, both null) — IS swept (len > 1).
    The rule is strictly about list length, not content.
    """
    gt = _create(gql_context, [{"k": "alpha", "v": [None, None]}])
    assert gt["swept_arguments"] == ["alpha"]


def test_string_and_null_is_swept(gql_context):
    gt = _create(gql_context, [{"k": "alpha", "v": ["A", None]}])
    assert gt["swept_arguments"] == ["alpha"]


def test_empty_value_list_is_not_swept(gql_context):
    """`v: []` (empty list) — NOT swept (len == 0)."""
    gt = _create(gql_context, [{"k": "alpha", "v": []}])
    assert gt["swept_arguments"] == []


def test_mixed_swept_and_unswept(gql_context):
    """Multiple keys, some swept, some not."""
    gt = _create(
        gql_context,
        [
            {"k": "swept1", "v": ["A", "B"]},
            {"k": "unswept1", "v": ["X"]},
            {"k": "swept2", "v": ["1", "2", "3"]},
            {"k": "unswept2", "v": [None]},
        ],
    )
    assert sorted(gt["swept_arguments"]) == ["swept1", "swept2"]


def test_no_argument_lists_returns_empty(gql_context):
    """When argument_lists is omitted entirely, swept_arguments returns [].

    Specifically NOT null — clients iterate over the result and a null
    here would crash any naive consumer.
    """
    gt = _create(gql_context, None)
    # Strawberry serialises an absent list as null on the way in, but the
    # resolver short-circuits to []; assert that explicitly.
    assert gt["swept_arguments"] == []
