"""
Enforcement tests for auth.middleware.check_auth().

Exercises the actual before_request scope gate end-to-end (which test_middleware.py
does not — it only covers the pure _is_mutation helper):
  - every authenticated caller needs toshi/read
  - GraphQL mutations additionally need toshi/write

check_auth() is a no-op when TESTING=1 or SLS_OFFLINE=1 (the test default), so we
patch both flags off and drive it through a real Flask request context, injecting
the authorizer context via the X-Auth-* header fallback that the middleware supports.
"""

import json
from unittest import mock

import flask
import pytest
from werkzeug.exceptions import Forbidden

import auth.middleware as mw

QUERY = json.dumps({'query': '{ generalTasks { edges { node { id } } } }'})
MUTATION = json.dumps({'query': 'mutation { createGeneralTask(input: {}) { generalTask { id } } }'})

_app = flask.Flask(__name__)


def _run_check(method, body, scopes):
    """Invoke check_auth() inside a request context with enforcement turned on."""
    headers = {'X-Auth-Userid': 'u1', 'X-Auth-Scopes': scopes, 'X-Auth-Method': 'jwt'}
    with mock.patch.object(mw, 'TESTING', False), mock.patch.object(mw, 'IS_OFFLINE', False):
        with _app.test_request_context(
            '/graphql', method=method, data=body, headers=headers, content_type='application/json'
        ):
            return mw.check_auth()


def test_reader_can_query():
    assert _run_check('POST', QUERY, 'toshi/read') is None


def test_reader_blocked_on_mutation():
    with pytest.raises(Forbidden):
        _run_check('POST', MUTATION, 'toshi/read')


def test_writer_allowed_on_mutation():
    assert _run_check('POST', MUTATION, 'toshi/read toshi/write') is None


def test_writer_can_query():
    assert _run_check('POST', QUERY, 'toshi/read toshi/write') is None


def test_no_read_scope_denied():
    with pytest.raises(Forbidden):
        _run_check('POST', QUERY, '')


def test_options_preflight_allowed_without_scopes():
    assert _run_check('OPTIONS', b'', '') is None
