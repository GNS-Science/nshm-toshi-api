"""
Unit tests for auth.middleware._is_mutation and _extract_graphql_args.

These cover the cases the old regex could not handle:
  - multi-operation documents with operationName selection
  - "mutation" appearing in string literals or comments
  - anonymous vs named operations
  - malformed documents (fail-closed behaviour)
"""

from auth.middleware import _is_mutation

# ── Plain queries and mutations ───────────────────────────────────────────────


def test_simple_query_is_not_mutation():
    assert _is_mutation('{ generalTasks { edges { node { id } } } }') is False


def test_explicit_query_keyword():
    assert _is_mutation('query GetTasks { generalTasks { edges { node { id } } } }') is False


def test_simple_mutation():
    assert _is_mutation('mutation { createGeneralTask(input: {}) { generalTask { id } } }') is True


def test_named_mutation():
    assert _is_mutation('mutation CreateGT { createGeneralTask(input: {}) { generalTask { id } } }') is True


# ── Cases the regex got wrong ─────────────────────────────────────────────────


def test_mutation_in_string_literal_is_not_mutation():
    """'mutation' inside a string value must not trigger write-scope enforcement."""
    q = '{ search(term: "mutation foo") { edges { node { id } } } }'
    assert _is_mutation(q) is False


def test_mutation_in_comment_is_not_mutation():
    """'mutation' in a GraphQL comment must not trigger write-scope enforcement."""
    q = '# this is a mutation example\n{ generalTasks { edges { node { id } } } }'
    assert _is_mutation(q) is False


def test_multi_op_selects_query_by_operation_name():
    """Doc has both a query and a mutation; operationName selects the query."""
    q = '''
        query GetTasks { generalTasks { edges { node { id } } } }
        mutation CreateGT { createGeneralTask(input: {}) { generalTask { id } } }
    '''
    assert _is_mutation(q, operation_name='GetTasks') is False


def test_multi_op_selects_mutation_by_operation_name():
    """Doc has both a query and a mutation; operationName selects the mutation."""
    q = '''
        query GetTasks { generalTasks { edges { node { id } } } }
        mutation CreateGT { createGeneralTask(input: {}) { generalTask { id } } }
    '''
    assert _is_mutation(q, operation_name='CreateGT') is True


def test_multi_op_no_operation_name_returns_true_if_any_mutation():
    """No operationName with a mutation present → treat as mutation (conservative)."""
    q = '''
        query GetTasks { generalTasks { edges { node { id } } } }
        mutation CreateGT { createGeneralTask(input: {}) { generalTask { id } } }
    '''
    assert _is_mutation(q) is True


# ── Edge cases ────────────────────────────────────────────────────────────────


def test_empty_query_is_not_mutation():
    assert _is_mutation('') is False


def test_malformed_query_fails_closed():
    """Unparseable document → True (deny by default)."""
    assert _is_mutation('this is not graphql %%%') is True


def test_subscription_is_not_mutation():
    assert _is_mutation('subscription { onTaskUpdate { id } }') is False
